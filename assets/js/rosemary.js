document.addEventListener('DOMContentLoaded', () => {

    const toggleModeBtn = document.getElementById('toggleModeBtn');
    const videoContainer = document.querySelector('.video-container');
    const musicList = document.querySelector('.music-list');
    
    // Ini memastikan elemen-elemen penting ada
    if (!toggleModeBtn || !videoContainer || !musicList) {
        return; 
    }

    const videoIcon = toggleModeBtn.querySelector('.video-icon');
    const musicIcon = toggleModeBtn.querySelector('.music-icon');
    const buttonText = toggleModeBtn.querySelector('.button-text');
    
    let currentMode = toggleModeBtn.dataset.mode || 'video';
    
    updateDisplayMode(currentMode);

    function stopAllMedia() {
        document.querySelectorAll('video, audio').forEach(player => {
            if (!player.paused) {
                player.pause();
                player.currentTime = 0;
            }
        });
    }

    function updateDisplayMode(mode) {
        if (mode === 'video') {
            videoContainer.classList.remove('hidden');
            musicList.classList.add('hidden');
            videoIcon.classList.remove('hidden');
            musicIcon.classList.add('hidden');
            buttonText.textContent = 'Switch to Music Mode';
        } else {
            videoContainer.classList.add('hidden');
            musicList.classList.remove('hidden');
            videoIcon.classList.add('hidden');
            musicIcon.classList.remove('hidden');
            buttonText.textContent = 'Switch to Video Mode';
        }
    }
    
    toggleModeBtn.addEventListener('click', () => {
        stopAllMedia();
        currentMode = (currentMode === 'video') ? 'music' : 'video';
        toggleModeBtn.dataset.mode = currentMode;
        updateDisplayMode(currentMode);
    });

    // Hentikan media lain saat salah satunya diputar
    document.querySelectorAll('video, audio').forEach(player => {
        player.addEventListener('play', () => {
            document.querySelectorAll('video, audio').forEach(otherPlayer => {
                if (otherPlayer !== player && !otherPlayer.paused) {
                    otherPlayer.pause();
                }
            });
        });
    });

    const uploadForm = document.querySelector('.upload-form');
    if (uploadForm) {
        const mainFileInput = uploadForm.querySelector('input[name="file"]');
        const albumArtInput = uploadForm.querySelector('input[name="album_art_file"]');
        const uploadOverlay = document.getElementById('upload-overlay');
        const uploadStatusText = document.getElementById('upload-status-text');
        
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

            if (uploadOverlay) {
                uploadOverlay.classList.remove('hidden');
            }
            if (uploadStatusText) {
                uploadStatusText.textContent = 'File sedang diunggah. Mohon tunggu...';
            }
            uploadForm.querySelector('button[type="submit"]').disabled = true;

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
                if (uploadOverlay) {
                    uploadOverlay.classList.add('hidden');
                }
                if (data.success) {
                    alert(data.message);
                    window.location.reload();
                } else {
                    alert('Gagal: ' + data.message);
                }
            })
            .catch(error => {
                if (uploadOverlay) {
                    uploadOverlay.classList.add('hidden');
                }
                alert('Terjadi kesalahan: ' + error.message);
                console.error('Error:', error);
            })
            .finally(() => {
                uploadForm.querySelector('button[type="submit"]').disabled = false;
            });
        });
    }
});
