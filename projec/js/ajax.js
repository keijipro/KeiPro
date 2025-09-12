document.addEventListener('DOMContentLoaded', function() {
    function updateHeartIcon(svgElement, isLiked) {
        if (isLiked) {
            svgElement.setAttribute('fill', '#ff6b6b');
            svgElement.setAttribute('stroke', 'none');
        } else {
            svgElement.setAttribute('fill', 'none');
            svgElement.setAttribute('stroke', '#ccc');   // Garis tepi abu-abu (atau warna default kamu)
            svgElement.setAttribute('stroke-width', '2'); // Tebal garis
        }
    }

    document.querySelectorAll('.heart-icon').forEach(svgElement => {
        const isLikedInitial = svgElement.dataset.liked === 'true'; // Baca status dari data-liked HTML
        updateHeartIcon(svgElement, isLikedInitial);
    });

    document.querySelectorAll('.like-button').forEach(button => {
        button.addEventListener('click', function() {
            const imageId = this.dataset.imageId;
            const svgIcon = this.querySelector('.heart-icon');
            const likeCountSpan = this.querySelector('.like-count');

            fetch(`/like/${imageId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    likeCountSpan.textContent = data.like_count;
                    updateHeartIcon(svgIcon, data.liked); // data.liked ini dari respons JSON server (Python)
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
});
