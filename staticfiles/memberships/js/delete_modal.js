/**
 * Delete Confirmation Modal
 * Reusable delete confirmation system for memberships module
 */

class DeleteModal {
	constructor() {
		this.modal = document.getElementById('deleteConfirmationModal');
		this.titleElement = document.getElementById('deleteModalTitle');
		this.messageElement = document.getElementById('deleteModalMessage');
		this.warningElement = document.getElementById('deleteModalWarning');
		this.cancelBtn = document.getElementById('cancelDeleteBtn');
		this.confirmBtn = document.getElementById('confirmDeleteBtn');
		this.confirmBtnText = document.getElementById('confirmDeleteBtnText');
		this.closeBtn = document.getElementById('closeDeleteModalBtn');
		
		this.currentCallback = null;
		this.currentMemberId = null;
		
		this.init();
	}
	
	init() {
		// Close button
		if (this.closeBtn) {
			this.closeBtn.addEventListener('click', () => this.close());
		}
		
		// Cancel button
		if (this.cancelBtn) {
			this.cancelBtn.addEventListener('click', () => this.close());
		}
		
		// Confirm button
		if (this.confirmBtn) {
			this.confirmBtn.addEventListener('click', () => this.confirm());
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
	 * Show delete confirmation modal
	 * @param {Object} options - Configuration options
	 * @param {string} options.memberId - Member ID
	 * @param {string} options.memberName - Member name
	 * @param {boolean} options.isActive - Whether member has active subscription
	 * @param {Function} options.onConfirm - Callback function when confirmed
	 * @param {string} options.title - Modal title (optional)
	 * @param {string} options.confirmText - Confirm button text (optional)
	 */
	show(options) {
		const {
			memberId,
			memberName,
			isActive = false,
			onConfirm,
			title = 'Are you absolutely sure?',
			confirmText = 'Yes, Delete Member'
		} = options;
		
		this.currentMemberId = memberId;
		this.currentCallback = onConfirm;
		
		// Set title
		if (this.titleElement) {
			this.titleElement.textContent = title;
		}
		
		// Check if member has active subscription
		if (isActive) {
			this.showActiveWarning(memberName, memberId);
		} else {
			this.showDeleteConfirmation(memberName, memberId, confirmText);
		}
		
		// Show modal
		if (this.modal) {
			this.modal.classList.add('delete-modal-active');
			document.body.style.overflow = 'hidden';
		}
	}
	
	/**
	 * Show warning for active members
	 */
	showActiveWarning(memberName, memberId) {
		// Change title
		if (this.titleElement) {
			this.titleElement.textContent = 'Cannot delete active member';
		}
		
		// Set message
		if (this.messageElement) {
			this.messageElement.innerHTML = `
				This will permanently delete <strong>${memberName}</strong> (${memberId}).
				<div class="delete-modal-active-warning">
					<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<circle cx="12" cy="12" r="10"></circle>
						<line x1="12" y1="8" x2="12" y2="12"></line>
						<line x1="12" y1="16" x2="12.01" y2="16"></line>
					</svg>
					Cannot delete member with active subscription. Please wait until membership expires or deactivate manually.
				</div>
			`;
		}
		
		// Hide warning text
		if (this.warningElement) {
			this.warningElement.style.display = 'none';
		}
		
		// Disable confirm button
		if (this.confirmBtn) {
			this.confirmBtn.disabled = true;
		}
		
		// Change confirm button text
		if (this.confirmBtnText) {
			this.confirmBtnText.textContent = 'Cannot Delete';
		}
	}
	
	/**
	 * Show delete confirmation
	 */
	showDeleteConfirmation(memberName, memberId, confirmText) {
		// Set message
		if (this.messageElement) {
			this.messageElement.innerHTML = `
				This will permanently delete <strong>${memberName}</strong> (${memberId}) and all associated data.
			`;
		}
		
		// Show warning text
		if (this.warningElement) {
			this.warningElement.style.display = 'block';
			this.warningElement.textContent = 'This action cannot be undone!';
		}
		
		// Enable confirm button
		if (this.confirmBtn) {
			this.confirmBtn.disabled = false;
			this.confirmBtn.style.opacity = '1';
		}
		
		// Set confirm button text
		if (this.confirmBtnText) {
			this.confirmBtnText.textContent = confirmText;
		}
	}
	
	/**
	 * Close modal
	 */
	close() {
		if (this.modal) {
			this.modal.classList.remove('delete-modal-active');
			document.body.style.overflow = '';
		}
		
		// Reset state
		this.currentCallback = null;
		this.currentMemberId = null;
	}
	
	/**
	 * Confirm deletion
	 */
	confirm() {
		if (this.currentCallback && typeof this.currentCallback === 'function') {
			this.currentCallback(this.currentMemberId);
		}
		this.close();
	}
}

// Initialize delete modal when DOM is loaded
let deleteModal;

// Export for use in other scripts immediately
if (typeof window !== 'undefined') {
	window.DeleteModal = DeleteModal;
	window.getDeleteModal = () => {
		// Initialize on first access if not already initialized
		if (!deleteModal) {
			deleteModal = new DeleteModal();
		}
		return deleteModal;
	};
}

document.addEventListener('DOMContentLoaded', () => {
	// Initialize delete modal if not already done
	if (!deleteModal) {
		deleteModal = new DeleteModal();
	}
});
