const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('csv_file');
const dropzone = document.getElementById('uploadDropzone');
const selectedFileName = document.getElementById('selectedFileName');
const uploadButton = document.getElementById('uploadButton');
const uploadSpinner = document.getElementById('uploadSpinner');
const uploadButtonText = document.getElementById('uploadButtonText');
const uploadStatus = document.getElementById('uploadStatus');

function updateSelectedFile() {
  const file = fileInput.files && fileInput.files[0];
  selectedFileName.textContent = file ? file.name : 'No file selected';
  uploadStatus.textContent = file ? 'File selected and ready' : 'Ready to upload';
}

dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    fileInput.click();
  }
});

['dragenter', 'dragover'].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add('dragover');
  });
});

['dragleave', 'drop'].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove('dragover');
  });
});

dropzone.addEventListener('drop', (event) => {
  const files = event.dataTransfer.files;
  if (files && files.length) {
    fileInput.files = files;
    updateSelectedFile();
  }
});

fileInput.addEventListener('change', updateSelectedFile);

uploadForm.addEventListener('submit', (event) => {
  if (!fileInput.files || !fileInput.files.length) {
    event.preventDefault();
    uploadStatus.textContent = 'Choose a CSV file before uploading';
    return;
  }

  uploadButton.disabled = true;
  uploadSpinner.classList.remove('d-none');
  uploadButtonText.textContent = 'Processing...';
  uploadStatus.textContent = 'Uploading and processing your file';
});
