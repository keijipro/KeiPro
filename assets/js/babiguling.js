    document.addEventListener('DOMContentLoaded', () => {
        const uploadForm = document.querySelector('.form-upload');
        const fileInput = document.getElementById('file-upload'); 

        const statusDiv = document.createElement('div');
        statusDiv.id = 'upload-status';
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

            for (const file of files) {
                const formData = new FormData();
                formData.append('files', file);
                formData.append('description', description);
                formData.append('category', category);
                formData.append('tags', tags);

                const uploadPromise = fetch(uploadForm.action, {
                    method: 'POST',
                    body: formData,
                })
                .then(response => {
                    if (response.redirected) {
                        return response.text().then(() => {
                            window.location.href = response.url;
                        });
                    }
                    if (!response.ok) {
                        throw new Error(response.statusText);
                    }
                })
                .then(() => {
                    statusDiv.textContent = `Berhasil mengunggah ${file.name}`;
                    console.log(`Berhasil: ${file.name}`);
                })
                .catch(error => {
                    statusDiv.textContent = `Gagal mengunggah ${file.name}: ${error.message}`;
                    console.error(`Error: ${file.name}`, error);
                });

                uploadPromises.push(uploadPromise);
            }

            await Promise.allSettled(uploadPromises);

            statusDiv.textContent = 'Semua gambar selesai diunggah!';
            alert('Semua gambar selesai diunggah!');
            window.location.reload();
        });
    });
