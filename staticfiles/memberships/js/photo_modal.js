/**
 * Photo Options Modal
 * Handles photo selection, camera capture, and photo removal
 */

class PhotoModal {
	constructor() {
		this.modal = document.getElementById('photoOptionsModal');
		this.closeBtn = document.getElementById('closePhotoOptionsBtn');
		this.galleryBtn = document.getElementById('chooseFromGalleryBtn');
		this.cameraBtn = document.getElementById('takePhotoBtn');
		this.removeBtn = document.getElementById('removePhotoBtn');
		
		this.photoInputId = null;
		this.cameraInputId = null;
		this.onPhotoSelected = null;
		this.onPhotoRemoved = null;
		this.hasPhoto = false;
		
		this.init();
	}
	
	init() {
		// Close button
		if (this.closeBtn) {
			this.closeBtn.addEventListener('click', () => this.close());
		}
		
		// Gallery button
		if (this.galleryBtn) {
			this.galleryBtn.addEventListener('click', () => this.openGallery());
		}
		
		// Camera button
		if (this.cameraBtn) {
			this.cameraBtn.addEventListener('click', () => this.openCamera());
		}
		
		// Remove button
		if (this.removeBtn) {
			this.removeBtn.addEventListener('click', () => this.removePhoto());
		}
		
		// Click outside to close
		if (this.modal) {
			this.modal.addEventListener('click', (e) => {
				if (e.target === this.modal) {
					this.close();
				}
			});
		}
		
		// Escape key to close
		document.addEventListener('keydown', (e) => {
			if (e.key === 'Escape' && this.modal && this.modal.style.display !== 'none') {
				this.close();
			}
		});
	}
	
	/**
	 * Show photo options modal
	 * @param {Object} options - Configuration options
	 * @param {string} options.photoInputId - ID of file input for gallery
	 * @param {string} options.cameraInputId - ID of file input for camera
	 * @param {Function} options.onPhotoSelected - Callback when photo selected
	 * @param {Function} options.onPhotoRemoved - Callback when photo removed
	 * @param {boolean} options.hasPhoto - Whether current entity has a photo
	 */
	show(options) {
		const {
			photoInputId,
			cameraInputId,
			onPhotoSelected,
			onPhotoRemoved,
			hasPhoto = false
		} = options;
		
		this.photoInputId = photoInputId;
		this.cameraInputId = cameraInputId;
		this.onPhotoSelected = onPhotoSelected;
		this.onPhotoRemoved = onPhotoRemoved;
		this.hasPhoto = hasPhoto;
		
		// Show/hide remove button based on whether photo exists
		if (this.removeBtn) {
			this.removeBtn.style.display = hasPhoto ? 'flex' : 'none';
		}
		
		// Show modal
		if (this.modal) {
			this.modal.style.display = 'flex';
			document.body.style.overflow = 'hidden';
		}
	}
	
	close() {
		if (this.modal) {
			this.modal.style.display = 'none';
			document.body.style.overflow = 'auto';
		}
	}
	
	openGallery() {
		const photoInput = document.getElementById(this.photoInputId);
		if (photoInput) {
			photoInput.click();
		}
		this.close();
	}
	
	openCamera() {
		const cameraInput = document.getElementById(this.cameraInputId);
		const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
		
		if (isMobile) {
			// Mobile: use native camera
			if (cameraInput) {
				cameraInput.click();
			}
		} else {
			// Desktop: try MediaDevices API
			if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
				this.openCameraModal();
			} else {
				alert('Camera access is not available on this device. Please use "Choose from Gallery" instead.');
				this.openGallery();
			}
		}
		this.close();
	}
	
	openCameraModal() {
		const modal = document.createElement('div');
		modal.id = 'cameraModal';
		modal.className = 'modal camera-modal-overlay';
		modal.style.display = 'flex';
		modal.innerHTML = `
			<div class="camera-modal-container">
				<div class="camera-preview-wrapper">
					<video id="cameraVideo" autoplay playsinline class="camera-video-preview"></video>
					<button class="camera-close-btn" onclick="window.photoModal.closeCameraModal()">&times;</button>
				</div>
				<div class="camera-modal-footer">
					<button type="button" class="camera-btn camera-btn-cancel" onclick="window.photoModal.closeCameraModal()">Cancel</button>
					<button type="button" class="camera-btn camera-btn-capture" onclick="window.photoModal.capturePhoto()">
						<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<circle cx="12" cy="12" r="10"></circle>
						</svg>
						Capture
					</button>
				</div>
				<canvas id="cameraCanvas" class="camera-canvas-hidden"></canvas>
			</div>
		`;
		
		document.body.appendChild(modal);
		
		// Start camera stream
		navigator.mediaDevices.getUserMedia({ 
			video: { 
				facingMode: 'user',
				aspectRatio: 1,
				width: { ideal: 720 },
				height: { ideal: 720 }
			} 
		})
		.then(stream => {
			const video = document.getElementById('cameraVideo');
			if (video) {
				video.srcObject = stream;
			}
		})
		.catch(err => {
			console.error('Error accessing camera:', err);
			this.closeCameraModal();
			alert('Unable to access camera. Please check permissions or use "Choose from Gallery" instead.');
		});
	}
	
	closeCameraModal() {
		const modal = document.getElementById('cameraModal');
		const video = document.getElementById('cameraVideo');
		
		// Stop camera stream
		if (video && video.srcObject) {
			const tracks = video.srcObject.getTracks();
			tracks.forEach(track => track.stop());
		}
		
		if (modal) {
			modal.remove();
		}
	}
	
	capturePhoto() {
		const video = document.getElementById('cameraVideo');
		const canvas = document.getElementById('cameraCanvas');
		
		if (!video || !canvas) return;
		
		const context = canvas.getContext('2d');
		
		// Make canvas square by using the smaller dimension
		const size = Math.min(video.videoWidth, video.videoHeight);
		canvas.width = size;
		canvas.height = size;
		
		// Calculate crop position to center the square
		const sx = (video.videoWidth - size) / 2;
		const sy = (video.videoHeight - size) / 2;
		
		// Draw cropped square image
		context.drawImage(video, sx, sy, size, size, 0, 0, size, size);
		
		canvas.toBlob(blob => {
			const file = new File([blob], 'camera-photo.jpg', { type: 'image/jpeg' });
			
			// Store file in camera input
			const cameraInput = document.getElementById(this.cameraInputId);
			if (cameraInput) {
				const dataTransfer = new DataTransfer();
				dataTransfer.items.add(file);
				cameraInput.files = dataTransfer.files;
			}
			
			// Call callback
			if (this.onPhotoSelected && typeof this.onPhotoSelected === 'function') {
				this.onPhotoSelected(file);
			}
			
			this.closeCameraModal();
		}, 'image/jpeg', 0.9);
	}
	
	removePhoto() {
		// Call callback to remove photo (no confirmation needed, user will confirm via Save Changes button)
		if (this.onPhotoRemoved && typeof this.onPhotoRemoved === 'function') {
			this.onPhotoRemoved();
		}
		this.close();
	}
}

// Initialize photo modal when DOM is loaded
let photoModal;

document.addEventListener('DOMContentLoaded', () => {
	photoModal = new PhotoModal();
	window.photoModal = photoModal; // Make it globally accessible
});

// Export for use in other scripts
if (typeof window !== 'undefined') {
	window.PhotoModal = PhotoModal;
	window.getPhotoModal = () => photoModal;
}
