    document.addEventListener('DOMContentLoaded', function() {
        const modal = document.getElementById("lightbox-modal");
        const modalImg = document.getElementById("lightbox-image");
        const closeBtn = document.querySelector(".close-button");

        const galleryImages = document.querySelectorAll(".combrok");

        galleryImages.forEach(image => {
            image.addEventListener('click', () => {
                modal.style.display = "block";
                modalImg.src = image.getAttribute('data-src');
            });
        });

        closeBtn.addEventListener('click', () => {
            modal.style.display = "none";
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = "none";
            }
        });
    });
