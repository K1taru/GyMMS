/**
 * Payment Bridge Modal
 * Handles payment/renewal prompts with better UX
 */

class PaymentBridgeModal {
	constructor() {
		this.modal = document.getElementById('paymentBridgeModal');
		this.closeBtn = document.getElementById('closePaymentBridgeBtn');
		this.cancelBtn = document.getElementById('cancelPaymentBridgeBtn');
		this.confirmBtn = document.getElementById('confirmPaymentBridgeBtn');
		this.icon = document.getElementById('paymentBridgeIcon');
		this.title = document.getElementById('paymentBridgeTitle');
		this.message = document.getElementById('paymentBridgeMessage');
		this.info = document.getElementById('paymentBridgeInfo');
		this.footer = document.getElementById('paymentBridgeFooter');
		this.confirmBtnText = document.getElementById('confirmPaymentBridgeBtnText');
		
		this.onConfirm = null;
		this.currentStatus = null;
		
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
			this.confirmBtn.addEventListener('click', () => {
				if (this.onConfirm && typeof this.onConfirm === 'function') {
					this.onConfirm();
				}
				this.close();
			});
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
	 * Show payment bridge modal
	 * @param {Object} options - Configuration options
	 * @param {string} options.status - Member status: 'active', 'expired', 'expiring', or 'inactive'
	 * @param {string} options.memberName - Member's name
	 * @param {string} options.memberId - Member's ID
	 * @param {string} options.endDate - Membership end date
	 * @param {number} options.daysRemaining - Days remaining (for expiring and active status)
	 * @param {Function} options.onConfirm - Callback when confirmed
	 */
	show(options) {
		const {
			status,
			memberName,
			memberId,
			endDate,
			daysRemaining,
			onConfirm
		} = options;
		
		this.currentStatus = status;
		this.onConfirm = onConfirm;
		
		// Reset classes
		this.icon.className = 'payment-bridge-icon';
		this.confirmBtn.className = 'payment-bridge-btn payment-bridge-btn-primary';
		
		// Configure based on status
		if (status === 'active') {
			this.showActiveModal(memberName, memberId, endDate, daysRemaining);
		} else if (status === 'expired') {
			this.showExpiredModal(memberName, memberId, endDate);
		} else if (status === 'expiring') {
			this.showExpiringModal(memberName, memberId, endDate, daysRemaining);
		} else if (status === 'inactive') {
			this.showInactiveModal(memberName, memberId);
		}
		
		// Show modal
		if (this.modal) {
			this.modal.style.display = 'flex';
			document.body.style.overflow = 'hidden';
		}
	}
	
	showActiveModal(memberName, memberId, endDate, daysRemaining) {
		// Icon
		this.icon.classList.add('active');
		this.icon.innerHTML = `
			<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
				<polyline points="22 4 12 14.01 9 11.01"></polyline>
			</svg>
		`;
		
		// Title and message
		this.title.textContent = 'Active Membership';
		this.message.textContent = `${memberName}'s membership is currently active. You can renew early to extend the membership period.`;
		
		// Info section
		this.info.innerHTML = `
			<div class="payment-bridge-info-item">
				<span class="payment-bridge-info-label">Member ID</span>
				<span class="payment-bridge-info-value">${memberId}</span>
			</div>
			<div class="payment-bridge-info-item">
				<span class="payment-bridge-info-label">Valid Until</span>
				<span class="payment-bridge-info-value success">${endDate}</span>
			</div>
			<div class="payment-bridge-info-item">
				<span class="payment-bridge-info-label">Days Remaining</span>
				<span class="payment-bridge-info-value success">${daysRemaining} day${daysRemaining !== 1 ? 's' : ''}</span>
			</div>
			<div class="payment-bridge-info-item">
				<span class="payment-bridge-info-label">Status</span>
				<span class="payment-bridge-info-value success">ACTIVE</span>
			</div>
		`;
		
		// Button
		this.confirmBtn.classList.add('active');
		this.confirmBtnText.textContent = 'Renew Early';
	}
	
	showExpiredModal(memberName, memberId, endDate) {
		// Icon
		this.icon.classList.add('expired');
		this.icon.innerHTML = `
			<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<circle cx="12" cy="12" r="10"></circle>
				<line x1="12" y1="8" x2="12" y2="12"></line>
				<line x1="12" y1="16" x2="12.01" y2="16"></line>
			</svg>
		`;
		
		// Title and message
		this.title.textContent = 'Membership Expired';
		this.message.textContent = `${memberName}'s membership has expired. Would you like to renew it now?`;
		
		// Info section
		this.info.innerHTML = `
			<div class="payment-bridge-info-item">
				<span class="payment-bridge-info-label">Member ID</span>
				<span class="payment-bridge-info-value">${memberId}</span>
			</div>
			<div class="payment-bridge-info-item">
				<span class="payment-bridge-info-label">Expired On</span>
				<span class="payment-bridge-info-value highlight">${endDate}</span>
			</div>
			<div class="payment-bridge-info-item">
				<span class="payment-bridge-info-label">Status</span>
				<span class="payment-bridge-info-value highlight">EXPIRED</span>
			</div>
		`;
		
		// Button
		this.confirmBtn.classList.add('expired');
		this.confirmBtnText.textContent = 'Renew Membership';
	}
	
	showExpiringModal(memberName, memberId, endDate, daysRemaining) {
		// Icon
		this.icon.classList.add('expiring');
		this.icon.innerHTML = `
			<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<circle cx="12" cy="12" r="10"></circle>
				<polyline points="12 6 12 12 16 14"></polyline>
			</svg>
		`;
		
		// Title and message
		this.title.textContent = 'Membership Expiring Soon';
		this.message.textContent = `${memberName}'s membership will expire in ${daysRemaining} day${daysRemaining !== 1 ? 's' : ''}. Renew now to avoid service interruption.`;
		
		// Info section
		this.info.innerHTML = `
			<div class="payment-bridge-info-item">
				<span class="payment-bridge-info-label">Member ID</span>
				<span class="payment-bridge-info-value">${memberId}</span>
			</div>
			<div class="payment-bridge-info-item">
				<span class="payment-bridge-info-label">Expires On</span>
				<span class="payment-bridge-info-value warning">${endDate}</span>
			</div>
			<div class="payment-bridge-info-item">
				<span class="payment-bridge-info-label">Days Remaining</span>
				<span class="payment-bridge-info-value warning">${daysRemaining} day${daysRemaining !== 1 ? 's' : ''}</span>
			</div>
		`;
		
		// Button
		this.confirmBtn.classList.add('expiring');
		this.confirmBtnText.textContent = 'Renew Now';
	}
	
	showInactiveModal(memberName, memberId) {
		// Icon
		this.icon.classList.add('inactive');
		this.icon.innerHTML = `
			<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
				<line x1="12" y1="9" x2="12" y2="13"></line>
				<line x1="12" y1="17" x2="12.01" y2="17"></line>
			</svg>
		`;
		
		// Title and message
		this.title.textContent = 'Inactive Membership';
		this.message.textContent = `${memberName}'s membership is currently inactive. Activate it to provide access to gym facilities.`;
		
		// Info section
		this.info.innerHTML = `
			<div class="payment-bridge-info-item">
				<span class="payment-bridge-info-label">Member ID</span>
				<span class="payment-bridge-info-value">${memberId}</span>
			</div>
			<div class="payment-bridge-info-item">
				<span class="payment-bridge-info-label">Status</span>
				<span class="payment-bridge-info-value">INACTIVE</span>
			</div>
		`;
		
		// Button
		this.confirmBtnText.textContent = 'Activate Membership';
	}
	
	close() {
		if (this.modal) {
			this.modal.style.display = 'none';
			document.body.style.overflow = 'auto';
		}
		
		// Reset
		this.onConfirm = null;
		this.currentStatus = null;
	}
}

// Initialize payment bridge modal when DOM is loaded
let paymentBridgeModal;

document.addEventListener('DOMContentLoaded', () => {
	paymentBridgeModal = new PaymentBridgeModal();
	window.paymentBridgeModal = paymentBridgeModal; // Make it globally accessible
});

// Export for use in other scripts
if (typeof window !== 'undefined') {
	window.PaymentBridgeModal = PaymentBridgeModal;
	window.getPaymentBridgeModal = () => paymentBridgeModal;
}
