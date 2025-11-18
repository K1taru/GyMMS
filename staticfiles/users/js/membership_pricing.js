// Membership Pricing JavaScript
document.addEventListener('DOMContentLoaded', function() {

        // Numeric-only input for price and duration fields
        const priceInput = document.getElementById('pricingPrice');
        if (priceInput) {
            priceInput.addEventListener('input', function(e) {
                this.value = this.value.replace(/[^\d.]/g, '');
            });
        }
        const durationInput = document.getElementById('pricingDuration');
        if (durationInput) {
            durationInput.addEventListener('input', function(e) {
                this.value = this.value.replace(/[^\d]/g, '');
            });
        }
    console.log('Membership Pricing JS loaded');

    const addPricingBtn = document.getElementById('addPricingBtn');
    const pricingModal = document.getElementById('pricingModal');
    const pricingForm = document.getElementById('pricingForm');
    const pricingModalTitle = document.getElementById('pricingModalTitle');
    const deleteModal = document.getElementById('deleteModal');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    let deleteCallback = null;

    // Add Pricing Button
    if (addPricingBtn) {
        addPricingBtn.addEventListener('click', function() {
            pricingModalTitle.textContent = 'Add Pricing Plan';
            pricingForm.reset();
            document.getElementById('pricingId').value = '';
            openModal('pricingModal');
        });
    }

    // Pricing Form Submit
    if (pricingForm) {
        pricingForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Prevent double submission
            const submitBtn = pricingForm.querySelector('button[type="submit"]');
            if (submitBtn.disabled) return;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Saving...';

            const formData = new FormData(pricingForm);
            const pricingId = document.getElementById('pricingId').value;
            const url = pricingId ? '/users/admin/pricing/update/' : '/users/admin/pricing/create/';

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    
                    // Close modal with smooth animation
                    setTimeout(() => {
                        closeModal('pricingModal');
                    }, 800);
                    
                    // Reload the page to show updated pricing
                    setTimeout(() => {
                        location.reload();
                    }, 1500);
                } else {
                    showNotification(data.message || 'Error processing request', 'error');
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Save Plan';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('An error occurred. Please try again.', 'error');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save Plan';
            });
        });
    }

    // Event delegation for pricing card buttons
    document.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.pricing-card .btn-secondary');
        const deleteBtn = e.target.closest('.pricing-card .btn-danger');
        
        if (editBtn) {
            const card = editBtn.closest('.pricing-card');
            const planId = card.getAttribute('data-plan-id');
            editPricing(planId);
        }
        
        if (deleteBtn) {
            const card = deleteBtn.closest('.pricing-card');
            const planId = card.getAttribute('data-plan-id');
            const planName = card.querySelector('.plan-header h3').textContent;
            deletePricing(planId, planName, card);
        }
    });

    // Delete confirmation
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            if (deleteCallback) {
                // Prevent double clicks
                if (confirmDeleteBtn.disabled) return;
                confirmDeleteBtn.disabled = true;
                confirmDeleteBtn.textContent = 'Deleting...';
                
                deleteCallback();
            }
        });
    }

    // Edit Pricing Function
    function editPricing(planId) {
        fetch(`/users/admin/pricing/${planId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    pricingModalTitle.textContent = 'Edit Pricing Plan';
                    document.getElementById('pricingId').value = data.plan.id;
                    document.getElementById('pricingName').value = data.plan.duration_label;
                    document.getElementById('pricingPrice').value = data.plan.price;
                    document.getElementById('pricingDuration').value = data.plan.duration_days;
                    openModal('pricingModal');
                } else {
                    showNotification(data.message || 'Error loading pricing data', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to load pricing data', 'error');
            });
    }

    // Delete Pricing Function
    function deletePricing(planId, planName, card) {
        document.getElementById('deleteMessage').textContent = 
            `Are you sure you want to delete the "${planName}" pricing plan? This action cannot be undone.`;
        
        deleteCallback = function() {
            fetch(`/users/admin/pricing/delete/${planId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    
                    // Close delete modal with delay
                    setTimeout(() => {
                        closeModal('deleteModal');
                    }, 800);
                    
                    // Remove the card from DOM with smooth animation after modal closes
                    setTimeout(() => {
                        card.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
                        card.style.opacity = '0';
                        card.style.transform = 'scale(0.9) translateY(-10px)';
                        
                        setTimeout(() => {
                            card.remove();
                            
                            // Check if there are any cards left
                            const remainingCards = document.querySelectorAll('.pricing-card');
                            if (remainingCards.length === 0) {
                                const grid = document.querySelector('.pricing-grid');
                                grid.innerHTML = '<div class="empty-state" style="opacity: 0;">No pricing plans found</div>';
                                
                                // Fade in empty state
                                setTimeout(() => {
                                    const emptyState = grid.querySelector('.empty-state');
                                    if (emptyState) {
                                        emptyState.style.transition = 'opacity 0.5s ease';
                                        emptyState.style.opacity = '1';
                                    }
                                }, 50);
                            }
                            
                            // Re-enable delete button
                            confirmDeleteBtn.disabled = false;
                            confirmDeleteBtn.textContent = 'Delete';
                        }, 500);
                    }, 900);
                } else {
                    showNotification(data.message || 'Error deleting pricing', 'error');
                    confirmDeleteBtn.disabled = false;
                    confirmDeleteBtn.textContent = 'Delete';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to delete pricing', 'error');
                confirmDeleteBtn.disabled = false;
                confirmDeleteBtn.textContent = 'Delete';
            });
        };
        
        openModal('deleteModal');
    }

    // Helper function to get CSRF token
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    // Modal functions
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            const modalContent = modal.querySelector('.modal-content');
            
            // Add closing animation
            if (modalContent) {
                modalContent.style.animation = 'slideDownScale 0.3s ease forwards';
            }
            modal.style.animation = 'fadeOut 0.3s ease forwards';
            
            // Remove active class and reset after animation
            setTimeout(() => {
                modal.classList.remove('active');
                document.body.style.overflow = '';
                
                // Reset animations
                if (modalContent) {
                    modalContent.style.animation = '';
                }
                modal.style.animation = '';
            }, 300);
        }
    };

    // Close modals when clicking outside
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this.id);
            }
        });
    });

    // Close modals on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(modal => {
                closeModal(modal.id);
            });
        }
    });
});
