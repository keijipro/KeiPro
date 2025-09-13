document.addEventListener('DOMContentLoaded', () => {
    const toggleModeBtn = document.getElementById('toggleModeBtn');
    const musicItems = document.querySelectorAll('.music-item');
    const videoIcon = toggleModeBtn.querySelector('.video-icon');
    const musicIcon = toggleModeBtn.querySelector('.music-icon');
    const buttonText = toggleModeBtn.querySelector('.button-text');

    if (!toggleModeBtn) {
        console.error("Tombol toggleModeBtn tidak ditemukan!");
        return;
    }

    if (!toggleModeBtn.dataset.mode) {
        toggleModeBtn.dataset.mode = 'video';
    }

    function stopAllMedia() {
        document.querySelectorAll('video, audio').forEach(player => {
            if (!player.paused) {
                player.pause();
                player.currentTime = 0;
            }
        });
    }

    function updateAllPlayersDisplay(globalMode) {
        musicItems.forEach(item => {
            const videoPlayer = item.querySelector('.video-player');
            const audioPlayer = item.querySelector('.audio-player');
            const albumArtFallback = item.querySelector('.album-art-fallback');

            if (videoPlayer) videoPlayer.classList.add('hidden');
            if (audioPlayer) audioPlayer.classList.add('hidden');
            if (albumArtFallback) albumArtFallback.classList.add('hidden');

            if (globalMode === 'video') {
                if (videoPlayer && videoPlayer.dataset.src) {
                    videoPlayer.src = videoPlayer.dataset.src; // Set src dari data-src
                    videoPlayer.classList.remove('hidden');
                } else if (albumArtFallback && albumArtFallback.src) {
                    albumArtFallback.classList.remove('hidden');
                }
            } else {
                if (audioPlayer && audioPlayer.dataset.src) {
                    audioPlayer.src = audioPlayer.dataset.src;
                    audioPlayer.classList.remove('hidden');
                }
                if (albumArtFallback && albumArtFallback.src) {
                    albumArtFallback.classList.remove('hidden');
                }
            }
        });
    }

    updateAllPlayersDisplay(toggleModeBtn.dataset.mode);

    toggleModeBtn.addEventListener('click', () => {
        stopAllMedia();

        let currentGlobalMode = toggleModeBtn.dataset.mode;

        if (currentGlobalMode === 'video') {
            toggleModeBtn.dataset.mode = 'music';
            videoIcon.classList.add('hidden');
            musicIcon.classList.remove('hidden');
            buttonText.textContent = 'Switch to Video Mode';
            updateAllPlayersDisplay('music');
        } else {
            toggleModeBtn.dataset.mode = 'video';
            videoIcon.classList.remove('hidden');
            musicIcon.classList.add('hidden');
            buttonText.textContent = 'Switch to Music Mode';
            updateAllPlayersDisplay('video');
        }
    });

    document.querySelectorAll('video, audio').forEach(player => {
        player.addEventListener('play', () => {
            document.querySelectorAll('video, audio').forEach(otherPlayer => {
                if (otherPlayer !== player) {
                    otherPlayer.pause();
                }
            });
        });
    });
});
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.querySelector('.upload-form');
    if (!uploadForm) {
        return;
    }

    if (typeof cloudinary === 'undefined') {
        console.error('erorrr Undefined');
        return;
    }

    const mainFileInput = document.querySelector('input[name="file"]');
    const albumArtInput = document.querySelector('input[name="album_art_file"]');

    const CLOUDINARY_CLOUD_NAME = 'di0sdr2no';
    const CLOUDINARY_UPLOAD_PRESET = 'KeiApp';

    mainFileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            const file = this.files[0];
            const formData = new FormData();
            formData.append('file', file);
            formData.append('upload_preset', CLOUDINARY_UPLOAD_PRESET);

            fetch(`https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD_NAME}/auto/upload`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.secure_url) {
                    mainFileInput.dataset.url = data.secure_url;
                    mainFileInput.dataset.public_id = data.public_id;
                    alert('File musik/video berhasil diunggah ke Cloudinary!');
                } else {
                    alert('Gagal mengunggah file ke Cloudinary. Periksa konfigurasi Anda.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Terjadi kesalahan saat mengunggah.');
            });
        }
    });

    albumArtInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            const file = this.files[0];
            const formData = new FormData();
            formData.append('file', file);
            formData.append('upload_preset', CLOUDINARY_UPLOAD_PRESET);

            fetch(`https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD_NAME}/image/upload`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.secure_url) {
                    albumArtInput.dataset.url = data.secure_url;
                    albumArtInput.dataset.public_id = data.public_id;
                    alert('Sampul album berhasil diunggah ke Cloudinary!');
                } else {
                    alert('Gagal mengunggah sampul album.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Terjadi kesalahan saat mengunggah.');
            });
        }
    });

    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const mainFileUrl = mainFileInput.dataset.url;
        const mainFilePublicId = mainFileInput.dataset.public_id;
        const albumArtUrl = albumArtInput.dataset.url || '';
        const albumArtPublicId = albumArtInput.dataset.public_id || '';

        if (!mainFileUrl) {
            alert('File musik/video belum berhasil diunggah ke Cloudinary!');
            return;
        }

        const formData = new FormData();
        formData.append('title', document.querySelector('input[name="title"]').value);
        formData.append('artist', document.querySelector('input[name="artist"]').value);
        formData.append('main_file_url', mainFileUrl);
        formData.append('main_public_id', mainFilePublicId);
        formData.append('album_art_url', albumArtUrl);
        formData.append('album_art_public_id', albumArtPublicId);

        fetch(uploadForm.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                window.location.reload(); // Muat ulang halaman
            } else {
                alert('Gagal: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Terjadi kesalahan saat mengirim data ke server.');
        });
    });
});
