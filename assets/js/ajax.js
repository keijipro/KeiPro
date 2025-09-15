document.addEventListener('DOMContentLoaded', function() {
    function updateHeartIcon(svgElement, isLiked) {
        if (isLiked) {
            svgElement.setAttribute('fill', '#ff6b6b');
            svgElement.setAttribute('stroke', 'none');
        } else {
            svgElement.setAttribute('fill', 'none');
            svgElement.setAttribute('stroke', '#ccc');
            svgElement.setAttribute('stroke-width', '2'); 
        }
    }

    document.querySelectorAll('.heart-icon').forEach(svgElement => {
        const isLikedInitial = svgElement.dataset.liked === 'true'; 
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
                    updateHeartIcon(svgIcon, data.liked); 
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
});
