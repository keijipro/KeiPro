document.addEventListener('DOMContentLoaded', () => {

    const toggleModeBtn = document.getElementById('toggleModeBtn');
    const videoContainer = document.querySelector('.video-container');
    const musicList = document.querySelector('.music-list');
    
    const videoIcon = toggleModeBtn ? toggleModeBtn.querySelector('.video-icon') : null;
    const musicIcon = toggleModeBtn ? toggleModeBtn.querySelector('.music-icon') : null;
    const buttonText = toggleModeBtn ? toggleModeBtn.querySelector('.button-text') : null;
    
    const playlist = [];
    document.querySelectorAll('.media-card-vertical video, .media-card-horizontal video').forEach(player => {
        if (!player.classList.contains('no-media')) {
            playlist.push(player);
        }
    });

    let currentTrackIndex = -1;

    function findCurrentTrackIndex(player) {
        return playlist.findIndex(track => track === player);
    }

    function playNextTrack() {
        currentTrackIndex++;
        if (currentTrackIndex >= playlist.length) {
            currentTrackIndex = 0;
        }

        if (playlist[currentTrackIndex]) {
            playlist[currentTrackIndex].play();
        }
    }

    function handlePlayerEnded() {
        playNextTrack();
    }

    if (toggleModeBtn) {
        if (!toggleModeBtn.dataset.mode) {
            toggleModeBtn.dataset.mode = 'video';
        }
        
        updateDisplayMode(toggleModeBtn.dataset.mode);

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
                if (videoContainer) videoContainer.classList.remove('hidden');
                if (musicList) musicList.classList.add('hidden');
            } else {
                if (videoContainer) videoContainer.classList.add('hidden');
                if (musicList) musicList.classList.remove('hidden');
            }
        }
        
        toggleModeBtn.addEventListener('click', () => {
            stopAllMedia();
            let currentGlobalMode = toggleModeBtn.dataset.mode;
            if (currentGlobalMode === 'video') {
                toggleModeBtn.dataset.mode = 'music';
                if (videoIcon) videoIcon.classList.add('hidden');
                if (musicIcon) musicIcon.classList.remove('hidden');
                if (buttonText) buttonText.textContent = 'Switch to Video Mode';
                updateDisplayMode('music');
            } else {
                toggleModeBtn.dataset.mode = 'video';
                if (videoIcon) videoIcon.classList.remove('hidden');
                if (musicIcon) musicIcon.classList.add('hidden');
                if (buttonText) buttonText.textContent = 'Switch to Music Mode';
                updateDisplayMode('video');
            }
        });

        document.querySelectorAll('video').forEach(player => {
            player.addEventListener('play', () => {
                stopAllMedia();
            });
            player.addEventListener('ended', handlePlayerEnded);
        });
    }

    const uploadForm = document.querySelector('.upload-form');
    if (!uploadForm) {
        return;
    }

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
});
