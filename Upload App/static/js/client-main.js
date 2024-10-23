document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('upload-form');
    const uploadButton = document.getElementById('upload-button');
    const spinnerBox = document.getElementById('spinnerBox');
    const successModal = $('#successModal');
    const uploadMoreButton = document.getElementById('upload-more-button');

    // Ensure the spinner box and success modal are hidden on page load
    spinnerBox.style.display = 'none';
    successModal.modal('hide');

    form.addEventListener('submit', function(event) {
        event.preventDefault();

        const formData = new FormData(form);
        uploadButton.disabled = true;
        spinnerBox.style.display = 'block';

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show the modal after 5 seconds
                setTimeout(() => {
                    spinnerBox.style.display = 'none';
                    successModal.modal('show');
                }, 5000);
            } 
        })
        .catch(error => {
            alert('An error occurred during the upload');
            spinnerBox.style.display = 'none';
            uploadButton.disabled = false;
        });

        // Hide the spinner and show the modal after 5 seconds regardless of the fetch response
        setTimeout(() => {
            spinnerBox.style.display = 'none';
            successModal.modal('show');
            uploadButton.disabled = false;
        }, 5000);
    });

    document.getElementById('file').addEventListener('change', function() {
        const fileName = this.files[0] ? this.files[0].name : 'Choose File:';
        document.getElementById('file-name').textContent = fileName;
    });

    window.clearFile = function() {
        document.getElementById('file').value = '';
        document.getElementById('file-name').textContent = 'Choose File:';
    };

    // Handle the "Yes" button click in the success modal
    uploadMoreButton.addEventListener('click', function() {
        successModal.modal('hide');
        document.getElementById('file').value = '';
        document.getElementById('file-name').textContent = 'Choose File:';
    });
});