document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const cameraButton = document.getElementById('cameraButton');
    const uploadButton = document.getElementById('uploadButton');
    const imageUpload = document.getElementById('imageUpload');
    const cameraView = document.getElementById('cameraView');
    const video = document.getElementById('video');
    const captureButton = document.getElementById('captureButton');
    const closeCamera = document.getElementById('closeCamera');
    const canvas = document.getElementById('canvas');
    const imagePreview = document.getElementById('imagePreview');
    const processButton = document.getElementById('processButton');
    const clearButton = document.getElementById('clearButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsSection = document.getElementById('resultsSection');
    const diseaseTitle = document.getElementById('diseaseTitle');
    const confidenceBar = document.getElementById('confidenceBar');
    const diseaseDescription = document.getElementById('diseaseDescription');
    const diseaseTreatment = document.getElementById('diseaseTreatment');
    const newAnalysisButton = document.getElementById('newAnalysisButton');
    
    // Track stream to stop it when needed
    let stream = null;
    
    // Camera functionality
    cameraButton.addEventListener('click', async () => {
        try {
            // Hide any previous results
            resultsSection.classList.add('d-none');
            imagePreview.classList.add('d-none');
            
            // Request camera access
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment', // Use rear camera on mobile devices
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                } 
            });
            
            // Show camera view
            video.srcObject = stream;
            cameraView.classList.remove('d-none');
        } catch (err) {
            console.error('Error accessing camera:', err);
            alert('Unable to access camera. Please check permissions or try uploading an image instead.');
        }
    });
    
    // Capture photo
    captureButton.addEventListener('click', () => {
        // Set canvas dimensions to match video
        const videoWidth = video.videoWidth;
        const videoHeight = video.videoHeight;
        canvas.width = videoWidth;
        canvas.height = videoHeight;
        
        // Draw video frame to canvas
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, videoWidth, videoHeight);
        
        // Hide camera view and show preview
        cameraView.classList.add('d-none');
        imagePreview.classList.remove('d-none');
        
        // Stop camera stream
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });
    
    // Close camera
    closeCamera.addEventListener('click', () => {
        // Stop camera stream
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        
        // Hide camera view
        cameraView.classList.add('d-none');
    });
    
    // Handle file upload
    uploadButton.addEventListener('click', () => {
        // Trigger file input click
        imageUpload.click();
    });
    
    imageUpload.addEventListener('change', (event) => {
        if (event.target.files && event.target.files[0]) {
            // Hide any previous results
            resultsSection.classList.add('d-none');
            
            const file = event.target.files[0];
            const reader = new FileReader();
            
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    // Set canvas dimensions to match image
                    canvas.width = img.width;
                    canvas.height = img.height;
                    
                    // Draw image on canvas
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    
                    // Show preview
                    imagePreview.classList.remove('d-none');
                };
                img.src = e.target.result;
            };
            
            reader.readAsDataURL(file);
        }
    });
    
    // Clear image
    clearButton.addEventListener('click', () => {
        // Clear canvas
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Hide preview
        imagePreview.classList.add('d-none');
        
        // Reset file input
        imageUpload.value = '';
    });
    
    // Process image
    processButton.addEventListener('click', async () => {
        try {
            // Get image data from canvas
            const imageData = canvas.toDataURL('image/jpeg');
            
            // Show loading indicator
            loadingIndicator.classList.remove('d-none');
            imagePreview.classList.add('d-none');
            
            // Send image to backend for processing
            const formData = new FormData();
            formData.append('imageData', imageData);
            
            const response = await fetch('/predict', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const result = await response.json();
            
            // Hide loading indicator
            loadingIndicator.classList.add('d-none');
            
            // Display results
            displayResults(result);
            
        } catch (error) {
            console.error('Error processing image:', error);
            loadingIndicator.classList.add('d-none');
            alert('Error processing image. Please try again.');
        }
    });
    
    // Display results
    function displayResults(result) {
        if (result.error) {
            alert(`Error: ${result.error}`);
            return;
        }
        
        // Update result elements
        diseaseTitle.textContent = result.disease_name;
        
        // Update confidence bar
        const confidence = result.confidence;
        confidenceBar.style.width = `${confidence}%`;
        confidenceBar.textContent = `${confidence.toFixed(2)}%`;
        
        // Set appropriate color for confidence
        confidenceBar.className = 'progress-bar';
        if (confidence >= 90) {
            confidenceBar.classList.add('bg-success');
        } else if (confidence >= 70) {
            confidenceBar.classList.add('bg-info');
        } else if (confidence >= 50) {
            confidenceBar.classList.add('bg-warning');
        } else {
            confidenceBar.classList.add('bg-danger');
        }
        
        // Update disease description
        diseaseDescription.textContent = result.description;
        
        // Set appropriate alert class based on disease
        if (result.disease === 'healthy') {
            diseaseDescription.className = 'alert alert-success';
        } else {
            diseaseDescription.className = 'alert alert-warning';
        }
        
        // Update treatment info
        diseaseTreatment.textContent = result.treatment;
        
        // Show results section
        resultsSection.classList.remove('d-none');
    }
    
    // New analysis button
    newAnalysisButton.addEventListener('click', () => {
        // Hide results
        resultsSection.classList.add('d-none');
        
        // Clear canvas
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Reset file input
        imageUpload.value = '';
    });
});
