document.addEventListener('DOMContentLoaded', () => {
    
    const toggleModeBtn = document.getElementById('toggleModeBtn');
    const musicItems = document.querySelectorAll('.music-item');
    const videoIcon = toggleModeBtn ? toggleModeBtn.querySelector('.video-icon') : null;
    const musicIcon = toggleModeBtn ? toggleModeBtn.querySelector('.music-icon') : null;
    const buttonText = toggleModeBtn ? toggleModeBtn.querySelector('.button-text') : null;

    if (toggleModeBtn) {
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
                    if (videoPlayer && videoPlayer.src) {
                        videoPlayer.classList.remove('hidden');
                    } else if (albumArtFallback && albumArtFallback.src) {
                        albumArtFallback.classList.remove('hidden');
                    }
                } else { 
                    if (audioPlayer && audioPlayer.src) {
                        audioPlayer.classList.remove('hidden');
                    } else if (albumArtFallback && albumArtFallback.src) {
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
                if (videoIcon) videoIcon.classList.add('hidden');
                if (musicIcon) musicIcon.classList.remove('hidden');
                if (buttonText) buttonText.textContent = 'Switch to Video Mode';
                updateAllPlayersDisplay('music');
            } else {
                toggleModeBtn.dataset.mode = 'video';
                if (videoIcon) videoIcon.classList.remove('hidden');
                if (musicIcon) musicIcon.classList.add('hidden');
                if (buttonText) buttonText.textContent = 'Switch to Music Mode';
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
    }

    
    const uploadForm = document.querySelector('.upload-form');
    if (!uploadForm) {
        return;
    }

    const mainFileInput = uploadForm.querySelector('input[name="file"]');
    const albumArtInput = uploadForm.querySelector('input[name="album_art_file"]');
    
    
    const CLOUDINARY_CLOUD_NAME = 'di0sdr2no';
    const CLOUDINARY_UPLOAD_PRESET = 'KeiApp';

    
    const uploadFile = (file, resourceType) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('upload_preset', CLOUDINARY_UPLOAD_PRESET);
        
        return fetch(`https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD_NAME}/${resourceType}/upload`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json());
    };

    
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const mainFile = mainFileInput.files[0];
        const albumArtFile = albumArtInput.files[0];
        
        if (!mainFile) {
            alert('Silakan pilih file musik atau video terlebih dahulu!');
            return;
        }

        console.log('Mengunggah file...');

        Promise.all([
            uploadFile(mainFile, 'auto'),
            albumArtFile ? uploadFile(albumArtFile, 'image') : Promise.resolve(null)
        ])
        .then(([mainResult, albumArtResult]) => {
            if (!mainResult || !mainResult.secure_url) {
                throw new Error('Gagal mengunggah file utama.');
            }
            
            const formData = new FormData();
            formData.append('title', uploadForm.querySelector('input[name="title"]').value);
            formData.append('artist', uploadForm.querySelector('input[name="artist"]').value);
            formData.append('main_file_url', mainResult.secure_url);
            formData.append('main_public_id', mainResult.public_id);
            if (albumArtResult && albumArtResult.secure_url) {
                formData.append('album_art_url', albumArtResult.secure_url);
                formData.append('album_art_public_id', albumArtResult.public_id);
            }

            return fetch(uploadForm.action, {
                method: 'POST',
                body: formData
            });
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                window.location.reload();
            } else {
                alert('Gagal: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Terjadi kesalahan: ' + error.message);
        });
    });
});
