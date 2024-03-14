function uploadFile() {
    var fileInput = document.getElementById('csvFile');
    var file = fileInput.files[0];
    var formData = new FormData();

    // Check if a file is selected
    if (file) {
        formData.append('file', file);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);

        xhr.onload = function() {
            if (xhr.status === 200) {
                // Success message
                document.getElementById('uploadStatus').innerText = 'File uploaded successfully!';
            } else {
                // Error message from server
                document.getElementById('uploadStatus').innerText = xhr.responseText;
            }
        };

        xhr.onerror = function() {
            // Network or transmission error
            document.getElementById('uploadStatus').innerText = 'Error uploading file. Please check your connection and try again.';
        };

        xhr.send(formData);
    } else {
        // No file selected message
        document.getElementById('uploadStatus').innerText = 'No file selected. Please choose a file.';
    }

    // Prevent form from submitting traditionally
    return false;
}
