import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url
from cloudinary.uploader import upload
from flask_sqlalchemy import SQLAlchemy
import psycopg2
from flask_migrate import Migrate
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer as Serializer
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
kei = Flask(__name__, static_folder='projec', static_url_path='/static')
kei.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
kei.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

kei.config['MAIL_SERVER'] = 'smtp.gmail.com'
kei.config['MAIL_PORT'] = 587
kei.config['MAIL_USE_TLS'] = True
kei.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
kei.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
kei.config['MAIL_DEFAULT_SENDER'] = os.environ.get('EMAIL_USER')
mail = Mail(kei)

login_manager = LoginManager()
login_manager.init_app(kei)
login_manager.login_view = 'login'


class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    profile_image_url = db.Column(db.String(255), nullable=True, default='/static/images/logo.png')
    subscription_plan = db.Column(db.String(50), nullable=False, default='free')
    todos = db.relationship('Todo', backref='owner', lazy=True)
    images = db.relationship('GalleryImage', backref='uploader', lazy=True)
    categories = db.relationship('Category', backref='creator', lazy=True)
    comments = db.relationship('Comment', backref='commenter', lazy=True)
    likes = db.relationship('Like', backref='liker', lazy=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    bio = db.Column(db.String(255))
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id], backref=db.backref('followed', lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')
    following = db.relationship('Follow', foreign_keys=[Follow.follower_id], backref=db.backref('follower', lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')
    is_admin = db.Column(db.Boolean, default=False)
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
    notifications = db.relationship('Notifications', backref='user', lazy=True)
    music_tracks = db.relationship('Music', backref='user', lazy=True)

    def has_liked_image(self, image):
        return Like.query.filter_by(user_id=self.id, image_id=image.id).count() > 0

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.following.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return self.following.filter_by(followed_id=user.id).first() is not None

class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    artist = db.Column(db.String(100), nullable=False)
    video_url = db.Column(db.String(255), nullable=True)
    video_public_id = db.Column(db.String(100), nullable=True)
    audio_url = db.Column(db.String(255), nullable=True)
    audio_public_id = db.Column(db.String(100), nullable=True)
    album_art_url = db.Column(db.String(255), nullable=True)
    album_art_public_id = db.Column(db.String(100), nullable=True)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    images = db.relationship('GalleryImage', backref='category', lazy=True)
    def __repr__(self):
        return f"<Category {self.name}>"

image_tags = db.Table('image_tags',
    db.Column('image_id', db.Integer, db.ForeignKey('gallery_image.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)
class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(200), nullable=False)
    secure_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True) 

    comments = db.relationship('Comment', backref='image', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('Like', backref='image', lazy=True, cascade="all, delete-orphan")
    tags = db.relationship('Tag', secondary=image_tags, backref='images_with_tag', lazy='dynamic')

    def __repr__(self):
        return f"<GalleryImage {self.public_id}>"

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<Tag {self.name}>"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('gallery_image.id'), nullable=False)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('gallery_image.id'), nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'image_id', name='_user_image_uc'),)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return '<Task %r>' % self.id

class WeatherSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(200), nullable=False)
    city_name = db.Column(db.String(100), nullable=False)

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(100), nullable=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Notifications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    image_id = db.Column(db.Integer, db.ForeignKey('gallery_image.id'), nullable=True)

    def __repr__(self):
        return f"<Notifications '{self.message}'>"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_reset_token(user, expires_sec=1800):
    s = Serializer(str(current_app.config['SECRET_KEY']).encode('utf-8'), expires_sec)
    return s.dumps({'user_id': user.id}).decode('utf-8')

def verify_reset_token(token):
    s = Serializer(str(current_app.config['SECRET_KEY']).encode('utf-8'))
    try:
        user_id = s.loads(token)['user_id']
    except:
        return None
    return User.query.get(user_id)

@kei.route('/image/<int:image_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_image(image_id):
    image = GalleryImage.query.get_or_404(image_id)
    if image.uploader.id != current_user.id:
        flash("Anda tidak memiliki izin untuk mengedit gambar ini.", "danger")
        return redirect(url_for('gallery'))

    if request.method == 'POST':
        action = request.form.get('action')
        try:
            if action in ['rotate_90', 'rotate_180', 'rotate_270']:
                angle = 0
                if action == 'rotate_90':
                    angle = 90
                elif action == 'rotate_180':
                    angle = 180
                elif action == 'rotate_270':
                    angle = 270
                if angle:
                    transformed_url, _ = cloudinary_url(
                        image.public_id,
                        transformation=[{'angle': angle}],
                        secure=True
                    )
                    image.secure_url = transformed_url
                    db.session.commit()
                    flash("Gambar berhasil dirotasi!", "success")
            elif action == 'crop':
                x = int(request.form.get('x', 0))
                y = int(request.form.get('y', 0))
                width = int(request.form.get('width', 0))
                height = int(request.form.get('height', 0))
                if width <= 0 or height <= 0:
                    flash("Lebar dan tinggi pemotongan harus lebih dari 0.", "danger")
                else:
                    transformed_url, _ = cloudinary_url(
                        image.public_id,
                        transformation=[{'crop': 'crop', 'x': x, 'y': y, 'width': width, 'height': height}],
                        secure=True
                    )
                    image.secure_url = transformed_url
                    db.session.commit()
                    flash("Gambar berhasil dipotong!", "success")
            elif action == 'watermark':
                watermark_text = request.form.get('watermark_text')
                if not watermark_text:
                    flash("Teks watermark tidak boleh kosong.", "danger")
                else:
                    response_img = requests.get(image.secure_url)
                    img = Image.open(BytesIO(response_img.content)).convert("RGBA")
                    txt_img = Image.new('RGBA', img.size, (255, 255, 255, 0))
                    draw = ImageDraw.Draw(txt_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", 40)
                    except IOError:
                        font = ImageFont.load_default()
                    bbox = draw.textbbox((0, 0), watermark_text, font=font)
                    textwidth = bbox[2] - bbox[0]
                    textheight = bbox[3] - bbox[1]
                    x = (img.width - textwidth) / 2
                    y = (img.height - textheight) / 2
                    draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 128))
                    watermarked_img = Image.alpha_composite(img, txt_img).convert("RGB")
                    buffer = BytesIO()
                    watermarked_img.save(buffer, format="JPEG")
                    buffer.seek(0)
                    upload_result = cloudinary.uploader.upload(
                        buffer.getvalue(),
                        public_id=image.public_id,
                        overwrite=True,
                        resource_type="image"
                    )
                    image.secure_url = upload_result['secure_url']
                    db.session.commit()
                    flash("Gambar berhasil diberi watermark!", "success")
            elif action == 'perspective':
                coords = [float(request.form.get(f'coord_{i}', 0)) for i in range(8)]
                coords_str = ",".join(map(str, coords))
                transformed_url, _ = cloudinary_url(
                    image.public_id,
                    transformation=[{'effect': 'distort', 'coords': coords_str}],
                    secure=True
                )
                image.secure_url = transformed_url
                db.session.commit()
                flash("Gambar berhasil diubah perspektifnya!", "success")
            else:
                flash("Tindakan tidak valid.", "danger")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saat mengedit gambar: {e}")
            flash(f"Gagal mengedit gambar: {e}", "danger")
        return redirect(url_for('edit_image', image_id=image.id))
    return render_template('edit_image.html', image=image)


@kei.route("/music/<int:music_id>/delete", methods=['POST'])
@login_required
def delete_music(music_id):
    music_item = Music.query.get_or_404(music_id)

    if music_item.user != current_user and not current_user.is_admin:
        abort(403)

    try:
        if music_item.video_public_id:
            cloudinary.uploader.destroy(music_item.video_public_id, resource_type="video")

        if music_item.audio_public_id:
            cloudinary.uploader.destroy(music_item.audio_public_id, resource_type="raw")

        if music_item.album_art_public_id:
            cloudinary.uploader.destroy(music_item.album_art_public_id, resource_type="image")

        flash("Semua file terkait berhasil dihapus dari Cloudinary.", "info")
    except Exception as e:
        logging.error(f"Gagal menghapus file Cloudinary: {e}")
        flash(f"Gagal menghapus beberapa file dari Cloudinary: {e}", "warning")

    db.session.delete(music_item)
    db.session.commit()
    flash(f"Media '{music_item.title}' berhasil dihapus!", "success")

    return redirect(url_for('music_room'))

@kei.route('/delete/image/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    image = GalleryImage.query.get_or_404(image_id)
    if not current_user.is_admin and current_user.id != image.uploader.id:
        flash("Anda tidak memiliki izin untuk menghapus gambar ini.", "danger")
        return redirect(url_for('gallery'))
    db.session.delete(image)
    db.session.commit()
    flash("Gambar berhasil dihapus.", "success")
    return redirect(url_for('gallery'))

@kei.route('/delete/comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if not current_user.is_admin and current_user.id != comment.commenter.id:
        flash("Anda tidak memiliki izin untuk menghapus komentar ini.", "danger")
        return redirect(url_for('gallery'))
    db.session.delete(comment)
    db.session.commit()
    flash("Komentar berhasil dihapus.", "success")
    return redirect(request.referrer)

@kei.route('/MyMusic')
@login_required
def music_room():
    music_library = Music.query.filter_by(user_id=current_user.id).order_by(Music.date_uploaded.desc()).all()
    return render_template('music.html', music_library=music_library)



@kei.route('/upload-music', methods=['POST'])
@login_required
def upload_music():
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('Tidak ada file utama yang dipilih.', 'danger')
        return redirect(url_for('music_room'))

    main_file = request.files['file']
    album_art_file = request.files.get('album_art_file')

    if main_file:
        try:
            upload_result = cloudinary.uploader.upload(main_file, resource_type="auto", folder="music_room")

            video_url = upload_result.get('secure_url')
            video_public_id = upload_result.get('public_id')
            resource_type_from_cloudinary = upload_result.get('resource_type', '')

            audio_url = None
            audio_public_id = None

            if 'video' in resource_type_from_cloudinary:

                new_music_video_url = video_url
                new_music_video_public_id = video_public_id

                if new_music_video_url:
                    audio_url = new_music_video_url.replace("/upload/", "/upload/f_mp3/")
                    audio_public_id = video_public_id
            elif 'audio' in resource_type_from_cloudinary or 'raw' in resource_type_from_cloudinary: # Jika file utama diidentifikasi sebagai audio murni
                new_music_video_url = None
                new_music_video_public_id = None

                audio_url = video_url
                audio_public_id = video_public_id
            else:
                new_music_video_url = None
                new_music_video_public_id = None
                audio_url = None
                audio_public_id = None

            album_art_url = None
            album_art_public_id = None
            if album_art_file and album_art_file.filename != '':
                album_art_upload_result = cloudinary.uploader.upload(
                    album_art_file,
                    resource_type="image",
                    folder="music_room/album_art"
                )
                album_art_url = album_art_upload_result.get('secure_url')
                album_art_public_id = album_art_upload_result.get('public_id')

            new_music = Music(
                title=request.form.get('title', 'Untitled'),
                artist=request.form.get('artist', 'Unknown Artist'),
                video_url=new_music_video_url,
                video_public_id=new_music_video_public_id,
                audio_url=audio_url,
                audio_public_id=audio_public_id,
                album_art_url=album_art_url,
                album_art_public_id=album_art_public_id,
                user_id=current_user.id
            )

            db.session.add(new_music)
            db.session.commit()
            flash('Musik/Video berhasil diunggah!', 'success')
            print("--- END UPLOAD PROCESS (SUCCESS) ---") # DEBUG
        except Exception as e:
            db.session.rollback()
            logging.error(f"Gagal mengunggah file: {e}")
            flash(f"Gagal mengunggah file: {e}", 'danger')
    return redirect(url_for('music_room'))


@kei.route('/inbox')
@login_required
def inbox():
    inbox_messages = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.date_posted.desc()).all()
    sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.date_posted.desc()).all()
    return render_template('inbox.html', inbox_messages=inbox_messages, sent_messages=sent_messages, active_page='inbox')

@kei.route('/send_message', methods=['POST'])
@login_required
def send_message():
    recipient_username = request.form.get('recipient_username')
    recipient_id = request.form.get('recipient_id', type=int)
    content = request.form.get('content')
    recipient = None
    if recipient_id:
        recipient = User.query.get(recipient_id)
    elif recipient_username:
        recipient = User.query.filter(User.username.ilike(recipient_username)).first()
    if not recipient:
        flash('Pengguna tidak ditemukan.', 'danger')
        return redirect(request.referrer or url_for('HomeKei'))
    if not content:
        flash('Pesan tidak boleh kosong.', 'danger')
        return redirect(request.referrer or url_for('HomeKei'))
    new_message = Message(
        content=content,
        sender_id=current_user.id,
        recipient_id=recipient.id
    )
    db.session.add(new_message)
    if recipient.id != current_user.id:
         new_notification = Notifications(
            user_id=recipient.id,
            message=f"Pesan baru dari {current_user.username}",
            message_id=new_message.id
        )
         db.session.add(new_notification)
    db.session.commit()
    flash('Pesan berhasil dikirim!', 'success')
    return redirect(request.referrer or url_for('HomeKei'))


def get_weather(api_key, city=None, lat=None, lon=None):
    if not api_key:
        logging.error("API Key cuaca belum disupply.")
        return None
    if not city and (not lat or not lon):
        logging.error("Parameter 'city' atau ('lat' dan 'lon') harus disertakan.")
        return None

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {}

    if city:
        params["q"] = city
    elif lat and lon:
        params["lat"] = lat
        params["lon"] = lon

    params["appid"] = api_key
    params["units"] = "metric"
    params["lang"] = "id"

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        weather_data = response.json()

        if weather_data.get("cod") == "404": 
            logging.warning(f"Kota tidak ditemukan: {weather_data.get('message', 'Unknown Error')}")
            return None
        if weather_data.get("cod") == 401: 
            logging.error(f"API Key tidak valid: {weather_data.get('message', 'Unknown Error')}")
            return None
        if weather_data.get("cod") not in [200, "200"]:
            logging.error(f"Error tidak dikenal dari OpenWeatherMap API: {weather_data.get('message', 'Unknown Error')} (Code: {weather_data.get('cod')})")
            return None

        weather = {
            "temperature": int(weather_data['main']['temp']),
            "condition": weather_data['weather'][0]['description'].capitalize(),
            "location": weather_data['name']
        }
        return weather
    except requests.exceptions.RequestException as err:
        logging.error(f"Error saat mengambil data cuaca: {err}")
        return None

@kei.route('/admin_room', methods=['GET', 'POST'])
@login_required
def admin_room():
    if not current_user.is_admin:
        flash('Ruang Pribadi Whyd1.gnt.bgt(Kei).', 'danger')
        return redirect(url_for('HomeKei'))

    if request.method == 'POST':
        if 'send_broadcast_message' in request.form:
            content = request.form.get('content')
            if not content:
                flash('Isi Dulu Boy.', 'danger')
            else:
                all_users = User.query.all()
                for user in all_users:
                    if user.id != current_user.id:
                        new_message = Message(
                            content=content,
                            sender_id=current_user.id,
                            recipient_id=user.id
                        )
                        db.session.add(new_message)
                        new_notification = Notifications(
                            user_id=user.id,
                            message=f"Pesan baru dari Administrator",
                            message_id=new_message.id
                        )
                        db.session.add(new_notification)
                db.session.commit()
                flash('Pesan berhasil dikirim!', 'success')
            return redirect(url_for('admin_room'))

        elif 'update_weather' in request.form:
            api_key = request.form.get('api_key')
            city_name = request.form.get('city_name')

            if api_key and city_name:
                WeatherSetting.query.delete()
                weather_setting = WeatherSetting(api_key=api_key, city_name=city_name)
                db.session.add(weather_setting)
                db.session.commit()
                flash('Pengaturan cuaca berhasil diperbarui!', 'success')
            else:
                flash('..', 'danger')
            return redirect(url_for('admin_room'))

        elif 'update_quote' in request.form:
            quote_content = request.form.get('quote_content')
            author = request.form.get('author')

            if quote_content:
                Quote.query.delete()
                new_quote = Quote(content=quote_content, author=author)
                db.session.add(new_quote)
                db.session.commit()
                flash('Success!', 'success')
            else:
                flash('Isi kutipan tidak boleh kosong.', 'danger')
            return redirect(url_for('admin_room'))

    messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.date_posted.desc()).all()
    current_weather_setting = WeatherSetting.query.first()
    current_quote = Quote.query.first()

    weather_preview = None
    if current_weather_setting and current_weather_setting.api_key and current_weather_setting.city_name:
        weather_preview = get_weather(
            api_key=current_weather_setting.api_key,
            city=current_weather_setting.city_name
        )

    return render_template('admin.html',
                           messages=messages,
                           current_weather_setting=current_weather_setting,
                           current_quote=current_quote,
                           weather_preview=weather_preview)

@kei.route('/api/get_weather')
def api_get_weather():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    settings = WeatherSetting.query.first()

    if not settings or not settings.api_key:
        logging.error("Weather API Key not configured in Admin Settings.")
        return jsonify({"error": "Weather API Key not configured in Admin Settings."}), 400

    weather_info = None

    if lat and lon:
        weather_info = get_weather(api_key=settings.api_key, lat=lat, lon=lon)

    if not weather_info and settings.city_name:
        logging.warning("Failed to get weather by lat/lon, trying default city from admin.")
        weather_info = get_weather(api_key=settings.api_key, city=settings.city_name)

    if weather_info:
        return jsonify(weather_info)

    logging.error("Failed to get weather data after all attempts.")
    return jsonify({"error": "Failed to get weather data. Check your API Key, city name, or location access."}), 400


@kei.route('/')
@login_required
def HomeKei():
    latest_todos = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.date_created.desc()).limit(3).all()
    latest_images = GalleryImage.query.filter_by(user_id=current_user.id).order_by(GalleryImage.date_uploaded.desc()).limit(5).all()
    total_users = User.query.count()
    total_images = GalleryImage.query.count()
    total_comments = Comment.query.count()
    total_likes = Like.query.count()
    quote = Quote.query.first()
    latest_music = Music.query.order_by(Music.date_uploaded.desc()).limit(3).all()
    weather_setting = WeatherSetting.query.first()

    return render_template('home.html',
                           latest_todos=latest_todos,
                           latest_images=latest_images,
                           total_users=total_users,
                           total_images=total_images,
                           total_comments=total_comments,
                           total_likes=total_likes,
                           quote=quote,
                           weather_setting=weather_setting,
                           latest_music=latest_music)


@kei.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('HomeKei'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user_by_username = User.query.filter_by(username=username).first()
        user_by_email = User.query.filter_by(email=email).first()
        if user_by_username:
            flash('Username sudah terdaftar. Pilih yang lain.')
            return redirect(url_for('register'))
        if user_by_email:
            flash('Email sudah terdaftar. Gunakan email lain.')
            return redirect(url_for('register'))
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registrasi berhasil! Anda sekarang bisa login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@kei.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('HomeKei'))
    if request.method == 'POST':
        email_or_username = request.form['email_or_username']
        password = request.form['password']
        user = User.query.filter(
            (User.username == email_or_username) | (User.email == email_or_username)
        ).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('HomeKei'))
        else:
            flash('Login gagal. Periksa username/email dan password Anda.')
    return render_template('login.html')

@kei.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('HomeKei'))

@kei.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and allowed_file(file.filename):
                try:
                    upload_result = cloudinary.uploader.upload(file)
                    current_user.profile_image_url = upload_result['secure_url']
                    flash('Foto profil berhasil diperbarui!')
                except Exception as e:
                    logging.error(f"Gagal mengunggah foto profil: {e}")
                    flash(f"Gagal mengunggah foto profil: {e}", "danger")
            elif file.filename != '':
                flash("Format file Salah.", "danger")

        current_user.username = request.form['username']
        current_user.email = request.form['email']
        current_user.bio = request.form.get('bio')

        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('profile.html')

@kei.route('/todo', methods=['GET', 'POST'])
@login_required
def todo_list():
    sort_by = request.args.get('sort', 'date_desc')
    tasks_query = Todo.query.filter_by(user_id=current_user.id)
    if sort_by == 'date_asc':
        tasks = tasks_query.order_by(Todo.date_created.asc()).all()
    elif sort_by == 'completed':
        tasks = tasks_query.order_by(Todo.completed.desc()).all()
    else:
        tasks = tasks_query.order_by(Todo.date_created.desc()).all()
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Todo(content=task_content, user_id=current_user.id)
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for('todo_list'))
        except:
            return 'Ada masalah saat menambahkan tugas.'
    else:
        return render_template('todo.html', tasks=tasks, sort_by=sort_by)

@kei.route('/todo/delete/<int:id>')
@login_required
def todo_delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    if task_to_delete.user_id != current_user.id:
        return 'Anda tidak diizinkan menghapus tugas ini.'
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect(url_for('todo_list'))
    except:
        return 'Ada masalah saat menghapus tugas.'

@kei.route('/todo/update/<int:id>', methods=['GET', 'POST'])
@login_required
def todo_update(id):
    task = Todo.query.get_or_404(id)
    if task.user_id != current_user.id:
        return 'Anda tidak diizinkan mengedit tugas ini.'
    if request.method == 'POST':
        task.completed = 'completed' in request.form
        task.content = request.form['content']
        try:
            db.session.commit()
            return redirect(url_for('todo_list'))
        except:
            return 'Ada masalah saat memperbarui tugas.'
    else:
        return render_template('update.html', task=task)

@kei.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    if request.method == 'POST':
        category_name = request.form['name']
        new_category = Category(name=category_name, user_id=current_user.id)
        try:
            db.session.add(new_category)
            db.session.commit()
            flash('Kategori berhasil ditambahkan!')
        except:
            flash('Kategori sudah ada atau gagal ditambahkan.', 'danger')
        return redirect(url_for('manage_categories'))
    user_categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('categories.html', categories=user_categories)

@kei.route('/categories/delete/<int:id>')
@login_required
def delete_category(id):
    category_to_delete = Category.query.get_or_404(id)
    if category_to_delete.user_id != current_user.id:
        flash('Anda tidak diizinkan menghapus kategori ini.', 'danger')
        return redirect(url_for('manage_categories'))
    try:
        db.session.delete(category_to_delete)
        db.session.commit()
        flash('Kategori berhasil dihapus!')
    except:
        flash('Gagal menghapus kategori.', 'danger')
    return redirect(url_for('manage_categories'))

@kei.route('/like/<int:image_id>', methods=['POST'])
@login_required
def like_image(image_id):
    is_ajax = request.is_json
    try:
        image = GalleryImage.query.get_or_404(image_id)
        user_like = Like.query.filter_by(user_id=current_user.id, image_id=image_id).first()
        if user_like:
            db.session.delete(user_like)
            liked_status = False
        else:
            new_like = Like(user_id=current_user.id, image_id=image_id)
            db.session.add(new_like)
            liked_status = True
            if image.user_id != current_user.id:
                message = f"{current_user.username} menyukai foto Anda."
                new_notification = Notifications(
                    user_id=image.user_id,
                    message=message
                )
                db.session.add(new_notification)
        db.session.commit()
        new_like_count = len(image.likes)
        if is_ajax:
            return jsonify({
                'success': True,
                'liked': liked_status,
                'like_count': new_like_count
            })
        else:
            return redirect(url_for('HomeKei'))
    except Exception as e:
        db.session.rollback()
        logging.error(f"Terjadi kesalahan saat like gambar: {e}")
        if is_ajax:
            return jsonify({'success': False, 'error': str(e)}), 500
        else:
            flash(f"Terjadi kesalahan: {e}", "danger")
            return redirect(url_for('HomeKei'))

@kei.route('/comment/<int:image_id>', methods=['POST'])
@login_required
def comment_image(image_id):
    content = request.form['content']
    if not content:
        flash('Komentar tidak boleh kosong.', 'danger')
        return redirect(url_for('gallery'))
    image = GalleryImage.query.get_or_404(image_id)
    new_comment = Comment(content=content, user_id=current_user.id, image_id=image.id)
    db.session.add(new_comment)
    if image.user_id != current_user.id:
        message = f"{current_user.username} mengomentari foto Anda."
        new_notification = Notifications(
            user_id=image.user_id,
            message=message,
            image_id=image.id
        )
        db.session.add(new_notification)
    db.session.commit()
    flash('Komentar berhasil ditambahkan.', 'success')
    return redirect(request.referrer or url_for('gallery'))

@kei.route('/gallery', methods=['GET', 'POST'])
@login_required
def gallery():
    user_categories = Category.query.filter_by(user_id=current_user.id).all()
    selected_category_id = request.args.get('category_id', type=int)
    search_query = request.args.get('search', '')
    selected_tag = request.args.get('tag', '')
    if request.method == 'POST':
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or uploaded_files[0].filename == '':
            flash('Tidak ada file yang dipilih untuk diunggah.', 'danger')
            return redirect(request.url)
        description = request.form.get('description', '')
        category_id = request.form.get('category')
        tags_input = request.form.get('tags', '')
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                try:
                    upload_result = cloudinary.uploader.upload(file)
                    new_image = GalleryImage(
                        public_id=upload_result['public_id'],
                        secure_url=upload_result['secure_url'],
                        description=description,
                        user_id=current_user.id,
                        category_id=category_id if category_id != 'none' else None
                    )
                    db.session.add(new_image)
                    if tags_input:
                        tag_names = [name.strip().lower() for name in tags_input.split(',') if name.strip()]
                        for tag_name in tag_names:
                            tag = Tag.query.filter_by(name=tag_name).first()
                            if not tag:
                                tag = Tag(name=tag_name)
                                db.session.add(tag)
                            new_image.tags.append(tag)
                    db.session.commit()
                    flash(f'Gambar {file.filename} berhasil diunggah!', 'success')
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"Gagal mengunggah file {file.filename}: {e}")
                    flash(f"Gagal mengunggah file {file.filename}: {e}", 'danger')
            else:
                flash(f"Gagal mengunggah file {file.filename}: Format tidak diizinkan.", 'danger')
        return redirect(url_for('gallery'))
    image_files_query = GalleryImage.query.filter_by(user_id=current_user.id)
    if search_query:
        search_like = f"%{search_query}%"
        image_files_query = image_files_query.filter(GalleryImage.description.ilike(search_like))
    if selected_category_id:
        image_files_query = image_files_query.filter_by(category_id=selected_category_id)
    if selected_tag:
        tag = Tag.query.filter_by(name=selected_tag).first()
        if tag:
            image_files_query = image_files_query.filter(GalleryImage.tags.contains(tag))
    image_files = image_files_query.order_by(GalleryImage.date_uploaded.desc()).all()
    all_tags = Tag.query.all()
    try:
        resources_result = cloudinary.api.resources(
            type="upload",
            prefix="",
            max_results=500
        )
        folder_names = set()
        for resource in resources_result.get('resources', []):
            if '/' in resource['public_id']:
                folder = resource['public_id'].split('/')[0]
                folder_names.add(folder)
        folder_names = sorted(list(folder_names))
    except Exception as e:
        logging.error(f"Gagal mengambil folder dari Cloudinary: {e}")
        folder_names = []
    return render_template('gallery.html',
        image_files=image_files,
        categories=user_categories,
        selected_category_id=selected_category_id,
        all_tags=all_tags,
        search_query=search_query,
        selected_tag=selected_tag,
        cloudinary_folders=folder_names
    )

@kei.route("/NewsVaganca")
def news():
    api_key = "cbc5b991dd704acdae96cf37940e102d"
    url = f"https://newsapi.org/v2/everything?domains=wsj.com&apiKey=cbc5b991dd704acdae96cf37940e102d"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        articles = data.get('articles', [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Error saat mengambil berita: {e}")
        articles = []
    return render_template('news.html', articles=articles)

@kei.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('HomeKei'))
    user = verify_reset_token(token)
    if user is None:
        flash('Itu adalah token yang tidak valid atau kedaluwarsa.', 'danger')
        return redirect(url_for('reset_request'))
    if request.method == 'POST':
        password = request.form['password']
        user.set_password(password)
        db.session.commit()
        flash('Kata sandi Anda telah diperbarui! Anda sekarang dapat login.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html')

def send_reset_email(user):
    if user:
        token = get_reset_token(user)
        msg = Message('Permintaan Reset Kata Sandi',
                      recipients=[user.email])
        msg.body = f'''Untuk mereset kata sandi Anda, kunjungi tautan berikut:
{url_for('reset_token', token=token, _external=True)}
Jika Anda tidak meminta ini, abaikan email ini.
'''
        mail.send(msg)

@kei.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('HomeKei'))
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        send_reset_email(user)
        flash('Tautan reset password telah dikirim.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html')

@kei.route('/profile/<username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    images = GalleryImage.query.filter_by(user_id=user.id).order_by(GalleryImage.date_uploaded.desc()).all()
    total_likes = sum(len(img.likes) for img in images)
    total_comments = sum(len(img.comments) for img in images)
    follower_count = user.followers.count()
    following_count = user.following.count()
    is_following = False
    if current_user.id != user.id:
        is_following = current_user.is_following(user)
    return render_template(
        'user_profile.html',
        user=user,
        images=images,
        total_likes=total_likes,
        total_comments=total_comments,
        follower_count=follower_count,
        following_count=following_count,
        is_following=is_following
    )

@kei.route('/follow/<username>')
@login_required
def follow_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user.id == current_user.id:
        flash("Anda tidak dapat mengikuti diri sendiri!", "warning")
        return redirect(url_for('user_profile', username=username))
    if current_user.is_following(user):
        flash("Anda sudah mengikuti pengguna ini.", "info")
    else:
        current_user.follow(user)
        db.session.commit()
        flash(f"Anda sekarang mengikuti {username}.", "success")
    return redirect(url_for('user_profile', username=username))

@kei.route('/unfollow/<username>')
@login_required
def unfollow_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user.id == current_user.id:
        flash("Anda tidak dapat berhenti mengikuti diri sendiri!", "warning")
        return redirect(url_for('user_profile', username=username))
    if not current_user.is_following(user):
        flash("Anda tidak mengikuti pengguna ini.", "info")
    else:
        current_user.unfollow(user)
        db.session.commit()
        flash(f"Anda berhenti mengikuti {username}.", "success")
    return redirect(url_for('user_profile', username=username))

@kei.route('/feed')
@login_required
def feed():
    search_query = request.args.get('search', '')
    image_query = GalleryImage.query.order_by(GalleryImage.date_uploaded.desc())
    if search_query:
        search_like = f"%{search_query}%"
        image_query = image_query.filter(GalleryImage.description.ilike(search_like))
    image_files = image_query.all()
    music_query = Music.query
    if search_query:
        search_like = f"%{search_query}%"
        music_query = music_query.filter(
            (Music.title.ilike(search_like)) |
            (Music.artist.ilike(search_like))
        )
    all_music = music_query.all()
    user_categories = Category.query.all()
    return render_template('feed.html',
                           image_files=image_files,
                           categories=user_categories,
                           search_query=search_query,
                           music_library=all_music,
                           active_page='feed')

@kei.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        unread_count = Notifications.query.filter_by(user_id=current_user.id, is_read=False).count()
        return dict(unread_count=unread_count)
    return dict(unread_count=0)

@kei.route('/read_notification/<int:notification_id>')
@login_required
def read_notifications(notification_id):
    notification = Notifications.query.get_or_404(notification_id)
    if notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
        flash('Notifikasi berhasil ditandai sebagai sudah dibaca.', 'success')
    return redirect(url_for('notifications'))

@kei.route('/notifications')
@login_required
def notifications():
    notifications = Notifications.query.filter_by(user_id=current_user.id).order_by(Notifications.date_created.desc()).all()
    return render_template('notifications.html', notifications=notifications)

@kei.route('/plans')
@login_required
def show_plans():
    return render_template('subsc.html')

@kei.route('/choose_plan/<plan>')
@login_required
def choose_plan(plan):
    if plan in ['free', 'basic', 'premium']:
        current_user.subscription_plan = plan
        db.session.commit()
        flash(f'Paket langganan Anda telah diperbarui ke {plan.capitalize()}.', 'success')
        return redirect(url_for('HomeKei'))
    else:
        flash('Paket tidak valid.', 'danger')
        return redirect(url_for('show_plans'))

