// Staff Management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Staff Management JS loaded');

    const addStaffBtn = document.getElementById('addStaffBtn');
    const staffModal = document.getElementById('staffModal');
    const staffForm = document.getElementById('staffForm');
    const staffModalTitle = document.getElementById('staffModalTitle');
    const deleteModal = document.getElementById('deleteModal');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    let deleteCallback = null;

    // Add Staff Button
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
            
            // Reset role field to editable
            const roleField = document.getElementById('staffRole');
            roleField.disabled = false;
            roleField.style.backgroundColor = '';
            roleField.style.cursor = '';
            
            // Show password fields when adding new staff
            const passwordGroup = document.getElementById('passwordGroup');
            const passwordConfirmGroup = document.getElementById('passwordConfirmGroup');
            if (passwordGroup) {
                passwordGroup.style.display = '';
                const label = passwordGroup.querySelector('label');
                if (label) label.innerHTML = 'Password <span class="required-indicator">*</span>';
            }
            if (passwordConfirmGroup) {
                passwordConfirmGroup.style.display = '';
                const label = passwordConfirmGroup.querySelector('label');
                if (label) label.innerHTML = 'Confirm Password <span class="required-indicator">*</span>';
            }
            
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

    // Staff Form Submit
    if (staffForm) {
        staffForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const password = document.getElementById('staffPassword').value;
            const confirmPassword = document.getElementById('staffPasswordConfirm').value;
            const staffId = document.getElementById('staffId').value;

            // Password validation (only if password is provided)
            if (password || confirmPassword) {
                if (password !== confirmPassword) {
                    showNotification('Passwords do not match!', 'error');
                    return;
                }
                if (password.length < 6) {
                    showNotification('Password must be at least 6 characters long', 'error');
                    return;
                }
            } else if (!staffId) {
                // Password is required when creating new staff
                showNotification('Password is required for new staff', 'error');
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
                    showNotification(data.message, 'success', 1000);
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

    // Event delegation for staff table buttons
    document.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.staff-table .btn-edit');
        const deleteBtn = e.target.closest('.staff-table .btn-delete');
        
        if (editBtn) {
            const row = editBtn.closest('tr');
            const staffId = row.getAttribute('data-staff-id');
            editStaff(staffId);
        }
        
        if (deleteBtn) {
            const row = deleteBtn.closest('tr');
            const staffId = row.getAttribute('data-staff-id');
            const staffName = row.querySelector('td:nth-child(2)').textContent;
            deleteStaff(staffId, staffName);
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

    // Edit Staff Function
    function editStaff(staffId) {
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
                    
                    // Make username and role readonly when editing
                    const usernameField = document.getElementById('staffUsername');
                    usernameField.readOnly = true;
                    usernameField.style.backgroundColor = '#f1f5f9';
                    usernameField.style.cursor = 'not-allowed';
                    document.getElementById('usernameHelpText').style.display = 'block';
                    
                    const roleField = document.getElementById('staffRole');
                    roleField.disabled = true;
                    roleField.style.backgroundColor = '#f1f5f9';
                    roleField.style.cursor = 'not-allowed';
                    
                    // Show password fields when editing (make them optional)
                    const passwordGroup = document.getElementById('passwordGroup');
                    const passwordConfirmGroup = document.getElementById('passwordConfirmGroup');
                    if (passwordGroup) {
                        passwordGroup.style.display = '';
                        const label = passwordGroup.querySelector('label');
                        if (label) label.innerHTML = 'New Password <small style="color: var(--muted);">(leave blank to keep current)</small>';
                    }
                    if (passwordConfirmGroup) {
                        passwordConfirmGroup.style.display = '';
                        const label = passwordConfirmGroup.querySelector('label');
                        if (label) label.innerHTML = 'Confirm New Password <small style="color: var(--muted);">(leave blank to keep current)</small>';
                    }
                    
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
    }

    // Delete Staff Function
    function deleteStaff(staffId, staffName) {
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
                    showNotification(data.message, 'success', 1000);
                    
                    // Close delete modal with delay
                    setTimeout(() => {
                        closeModal('deleteModal');
                    }, 800);
                    
                    // Remove row from table with smooth animation after modal closes
                    setTimeout(() => {
                        const row = document.querySelector(`tr[data-staff-id="${staffId}"]`);
                        if (row) {
                            // Add fade-out animation
                            row.style.transition = 'all 0.5s ease';
                            row.style.opacity = '0';
                            row.style.transform = 'translateX(-20px)';
                            
                            setTimeout(() => {
                                row.remove();
                                
                                // Check if table is empty
                                const tbody = document.getElementById('staffTableBody');
                                if (tbody.querySelectorAll('tr').length === 0) {
                                    tbody.innerHTML = '<tr><td colspan="7" class="empty-state" style="opacity: 0;">No staff members found</td></tr>';
                                    
                                    // Fade in empty state
                                    setTimeout(() => {
                                        const emptyState = tbody.querySelector('.empty-state');
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
                        }
                    }, 900);
                } else {
                    showNotification(data.message || 'Error deleting staff', 'error');
                    confirmDeleteBtn.disabled = false;
                    confirmDeleteBtn.textContent = 'Delete';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Failed to delete staff', 'error');
                confirmDeleteBtn.disabled = false;
                confirmDeleteBtn.textContent = 'Delete';
            });
        };
        
        openModal('deleteModal');
    }

    // Password strength indicator
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
