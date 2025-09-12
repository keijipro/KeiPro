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
