document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.querySelector('.form-upload');
    const fileInput = document.getElementById('file-upload'); 

    const statusDiv = document.createElement('div');
    statusDiv.id = 'upload-status';
    if (uploadForm) {
        uploadForm.parentNode.insertBefore(statusDiv, uploadForm.nextSibling);

        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const files = fileInput.files;
            if (files.length === 0) {
                alert('Pilih setidaknya satu file.');
                return;
            }

            const description = document.querySelector('input[name="description"]').value;
            const category = document.querySelector('select[name="category"]').value;
            const tags = document.querySelector('input[name="tags"]').value;

            statusDiv.textContent = `Memulai pengunggahan ${files.length} gambar...`;
            const uploadPromises = [];

            
            const formData = new FormData();
            for (const file of files) {
                formData.append('files', file); 
            }
            
            formData.append('description', description);
            formData.append('category', category);
            formData.append('tags', tags);

            try {
                const response = await fetch(uploadForm.action, {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    throw new Error('Gagal mengunggah file.');
                }

                const data = await response.json();
                
                let successCount = 0;
                let failCount = 0;
                data.results.forEach(result => {
                    if (result.success) {
                        successCount++;
                    } else {
                        failCount++;
                        console.error(`Gagal: ${result.filename} - ${result.error}`);
                    }
                });

                statusDiv.textContent = `Selesai: ${successCount} berhasil, ${failCount} gagal.`;
                alert(`Selesai: ${successCount} berhasil, ${failCount} gagal.`);
                window.location.reload();

            } catch (error) {
                statusDiv.textContent = `Terjadi kesalahan saat mengunggah: ${error.message}`;
                console.error('Error:', error);
            }
        });
    }
});
