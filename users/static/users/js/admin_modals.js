// Admin Modals JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin Modals JS loaded');

    // Staff Management
    const addStaffBtn = document.getElementById('addStaffBtn');
    const staffModal = document.getElementById('staffModal');
    const staffForm = document.getElementById('staffForm');
    const staffModalTitle = document.getElementById('staffModalTitle');

    if (addStaffBtn) {
        addStaffBtn.addEventListener('click', function() {
            staffModalTitle.textContent = 'Add Staff Member';
            staffForm.reset();
            document.getElementById('staffId').value = '';
            document.getElementById('staffPassword').required = true;
            document.getElementById('staffPasswordConfirm').required = true;
            
            // Reset username field to editable
            const usernameField = document.getElementById('staffUsername');
            usernameField.readOnly = false;
            usernameField.style.backgroundColor = '';
            usernameField.style.cursor = '';
            document.getElementById('usernameHelpText').style.display = 'none';
            
            // Show password fields when adding new staff
            const passwordGroup = document.getElementById('passwordGroup');
            const passwordConfirmGroup = document.getElementById('passwordConfirmGroup');
            if (passwordGroup) passwordGroup.style.display = '';
            if (passwordConfirmGroup) passwordConfirmGroup.style.display = '';
            
            // Reset password fields
            const passwordField = document.getElementById('staffPassword');
            const confirmField = document.getElementById('staffPasswordConfirm');
            if (passwordField) {
                passwordField.removeAttribute('disabled');
                passwordField.required = true;
            }
            if (confirmField) {
                confirmField.removeAttribute('disabled');
                confirmField.required = true;
            }
            
            openModal('staffModal');
        });
    }

    if (staffForm) {
        staffForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const password = document.getElementById('staffPassword').value;
            const confirmPassword = document.getElementById('staffPasswordConfirm').value;
            const staffId = document.getElementById('staffId').value;

            // Password validation (only if adding new staff or changing password)
            if (password && password !== confirmPassword) {
                showNotification('Passwords do not match!', 'error');
                return;
            }

            if (!staffId && password.length < 6) {
                showNotification('Password must be at least 6 characters long', 'error');
                return;
            }

            const formData = new FormData(staffForm);
            const url = staffId ? '/users/admin/staff/update/' : '/users/admin/staff/create/';

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
                    closeModal('staffModal');
                    location.reload();
                } else {
                    showNotification(data.message || 'Error processing request', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('An error occurred. Please try again.', 'error');
            });
        });
    }

    // Pricing Management
    const addPricingBtn = document.getElementById('addPricingBtn');
    const pricingModal = document.getElementById('pricingModal');
    const pricingForm = document.getElementById('pricingForm');
    const pricingModalTitle = document.getElementById('pricingModalTitle');

    if (addPricingBtn) {
        addPricingBtn.addEventListener('click', function() {
            pricingModalTitle.textContent = 'Add Pricing Plan';
            pricingForm.reset();
            document.getElementById('pricingId').value = '';
            openModal('pricingModal');
        });
    }

    if (pricingForm) {
        pricingForm.addEventListener('submit', function(e) {
            e.preventDefault();

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
                    closeModal('pricingModal');
                    location.reload();
                } else {
                    showNotification(data.message || 'Error processing request', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('An error occurred. Please try again.', 'error');
            });
        });
    }

    // Delete Modal
    const deleteModal = document.getElementById('deleteModal');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    let deleteCallback = null;

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            if (deleteCallback) {
                deleteCallback();
            }
            closeModal('deleteModal');
        });
    }

    // Global functions for inline onclick handlers
    window.editStaff = function(staffId) {
        fetch(`/users/admin/staff/${staffId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    staffModalTitle.textContent = 'Edit Staff Member';
                    document.getElementById('staffId').value = data.staff.id;
                    document.getElementById('staffUsername').value = data.staff.username;
                    document.getElementById('staffName').value = data.staff.name || '';
                    document.getElementById('staffEmail').value = data.staff.email;
                    document.getElementById('staffPhone').value = data.staff.phone_number || '';
                    document.getElementById('staffRole').value = data.staff.role;
                    
                    // Make username readonly when editing
                    const usernameField = document.getElementById('staffUsername');
                    usernameField.readOnly = true;
                    usernameField.style.backgroundColor = '#f1f5f9';
                    usernameField.style.cursor = 'not-allowed';
                    document.getElementById('usernameHelpText').style.display = 'block';
                    
                    // Hide password fields when editing (owner cannot change password)
                    const passwordGroup = document.getElementById('passwordGroup');
                    const passwordConfirmGroup = document.getElementById('passwordConfirmGroup');
                    if (passwordGroup) passwordGroup.style.display = 'none';
                    if (passwordConfirmGroup) passwordConfirmGroup.style.display = 'none';
                    
                    // Make password fields optional for editing
                    const passwordField = document.getElementById('staffPassword');
                    const confirmField = document.getElementById('staffPasswordConfirm');
                    passwordField.required = false;
                    confirmField.required = false;
                    passwordField.value = '';
                    confirmField.value = '';
                    
                    openModal('staffModal');
                } else {
                    showNotification(data.message || 'Error loading staff data', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to load staff data', 'error');
            });
    };

    window.deleteStaff = function(staffId, staffName) {
        document.getElementById('deleteMessage').textContent = 
            `Are you sure you want to delete ${staffName}? This action cannot be undone.`;
        
        deleteCallback = function() {
            fetch(`/users/admin/staff/delete/${staffId}/`, {
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
                    location.reload();
                } else {
                    showNotification(data.message || 'Error deleting staff', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to delete staff', 'error');
            });
        };
        
        openModal('deleteModal');
    };

    window.editPricing = function(pricingId) {
        fetch(`/users/admin/pricing/${pricingId}/`)
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
    };

    window.deletePricing = function(pricingId, planName) {
        document.getElementById('deleteMessage').textContent = 
            `Are you sure you want to delete the "${planName}" pricing plan? This action cannot be undone.`;
        
        deleteCallback = function() {
            fetch(`/users/admin/pricing/delete/${pricingId}/`, {
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
                    location.reload();
                } else {
                    showNotification(data.message || 'Error deleting pricing', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to delete pricing', 'error');
            });
        };
        
        openModal('deleteModal');
    };

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
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    };

    // Helper function to get CSRF token
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

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

    // Password strength indicator (optional enhancement)
    const passwordInput = document.getElementById('staffPassword');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strengthBar = document.querySelector('.password-strength-bar');
            
            if (!strengthBar) return;

            if (password.length === 0) {
                strengthBar.style.width = '0%';
                strengthBar.className = 'password-strength-bar';
            } else if (password.length < 6) {
                strengthBar.className = 'password-strength-bar weak';
            } else if (password.length < 10) {
                strengthBar.className = 'password-strength-bar medium';
            } else {
                strengthBar.className = 'password-strength-bar strong';
            }
        });
    }
});
