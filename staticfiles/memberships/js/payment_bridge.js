/**
 * Payment Bridge JavaScript
 * Handles the connection between memberships and payment processing
 */

document.addEventListener('DOMContentLoaded', () => {
    initializePaymentBridge();
});

/**
 * Initialize payment bridge functionality
 * Makes status badges clickable for all members
 */
function initializePaymentBridge() {
    const statusBadges = document.querySelectorAll('.status-badge');
    
    statusBadges.forEach(badge => {
        // Make all badges clickable (active, inactive, expired, expiring)
        badge.style.cursor = 'pointer';
        badge.style.transition = 'all 0.2s ease';
        
        // Set appropriate title based on status
        if (badge.classList.contains('active')) {
            badge.title = 'Click to view details and payment info';
        } else {
            badge.title = 'Click to process payment';
        }
        
        // Add hover effect
        badge.addEventListener('mouseenter', () => {
            badge.style.transform = 'translateY(-2px)';
            badge.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
        });
        
        badge.addEventListener('mouseleave', () => {
            badge.style.transform = 'scale(1)';
            badge.style.boxShadow = 'none';
        });
        
        // Add click handler
        badge.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent row click if any
            
            // Get member ID from the row
            const row = badge.closest('tr');
            const memberId = row ? row.dataset.memberId : null;
            
            if (memberId) {
                redirectToPayment(memberId, badge.textContent.trim());
            } else {
                console.error('Could not find member ID');
                alert('Error: Unable to process payment. Member ID not found.');
            }
        });
    });
}

/**
 * Redirect to payment processing page
 * @param {string} memberId - The member ID
 * @param {string} status - Current membership status
 */
function redirectToPayment(memberId, status) {
    // Get member data from the row
    const row = document.querySelector(`tr[data-member-id="${memberId}"]`);
    if (!row) {
        console.error('Could not find member row');
        return;
    }
    
    // Extract member information
    const memberName = row.dataset.name || 'Member';
    const endDateCell = row.cells[4]; // End date column
    const endDate = endDateCell ? endDateCell.textContent.trim() : '';
    
    // Calculate days remaining for expiring and active status
    let daysRemaining = 0;
    const statusLower = status.toLowerCase();
    if (statusLower === 'expiring' || statusLower === 'expiring soon' || statusLower === 'active') {
        const endDateStr = row.dataset.endDate;
        if (endDateStr) {
            const end = new Date(endDateStr);
            const today = new Date();
            today.setHours(0, 0, 0, 0); // Reset time to start of day
            end.setHours(0, 0, 0, 0);
            daysRemaining = Math.ceil((end - today) / (1000 * 60 * 60 * 24));
        }
    }
    
    // Construct payment URL
    const paymentUrl = `/payments/?member_id=${encodeURIComponent(memberId)}&status=${encodeURIComponent(status)}`;
    
    // Get payment bridge modal
    const modal = window.getPaymentBridgeModal();
    if (modal) {
        // Determine status for modal
        let modalStatus = statusLower;
        if (modalStatus === 'expiring soon') {
            modalStatus = 'expiring';
        }
        // Keep 'expiring' as 'expiring', don't convert to 'active'
        
        // Show modal
        modal.show({
            status: modalStatus,
            memberName: memberName,
            memberId: memberId,
            endDate: endDate,
            daysRemaining: daysRemaining,
            onConfirm: () => {
                // Redirect to payments page
                window.location.href = paymentUrl;
            }
        });
    } else {
        // Fallback to direct redirect if modal not available
        console.warn('Payment bridge modal not available, redirecting directly');
        window.location.href = paymentUrl;
    }
}

/**
 * Process payment for a specific member (can be called from other contexts)
 * @param {string} memberId - The member ID
 */
function processPaymentForMember(memberId) {
    if (!memberId) {
        console.error('Member ID is required');
        return;
    }
    
    // Redirect to payment page with member ID
    window.location.href = `/payments/?member_id=${encodeURIComponent(memberId)}`;
}

// Export function for use in other scripts if needed
window.processPaymentForMember = processPaymentForMember;
