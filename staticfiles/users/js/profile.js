/**
 * Profile Page JavaScript
 * Handles profile updates and photo management
 */

document.addEventListener('DOMContentLoaded', function() {
    const profileForm = document.getElementById('profileForm');
    const changePhotoBtn = document.getElementById('changePhotoBtn');
    const profileImageInput = document.getElementById('profileImageInput');
    const profileCameraInput = document.getElementById('profileCameraInput');
    const profileImagePreview = document.getElementById('profileImagePreview');
    const cancelBtn = document.getElementById('cancelBtn');
    const saveBtn = document.getElementById('saveBtn');
    const confirmationModal = document.getElementById('confirmationModal');
    const closeConfirmModal = document.getElementById('closeConfirmModal');
    const cancelConfirm = document.getElementById('cancelConfirm');
    const confirmSave = document.getElementById('confirmSave');
    const editProfileBtn = document.getElementById('editProfileBtn');
    const editActions = document.getElementById('editActions');
    const formFields = [
        document.getElementById('name'),
        document.getElementById('email'),
        document.getElementById('phone_number'),
        document.getElementById('password'),
        document.getElementById('password_confirm')
    ];

    // Numeric-only input for phone number
    const phoneInput = document.getElementById('phone_number');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^\d]/g, '');
        });
    }

    // Store original values for cancel functionality
    const originalValues = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        phone_number: document.getElementById('phone_number').value,
        profile_image: profileImagePreview.src
    };

    // Edit mode logic
    function setEditMode(isEdit) {
        if (isEdit) {
            formFields.forEach(f => {
                f.removeAttribute('disabled');
                f.classList.add('edit-animate');
                setTimeout(() => f.classList.remove('edit-animate'), 600);
            });
            editActions.style.display = 'flex';
            // Toggle Edit button to Cancel
            editProfileBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg> Cancel`;
            editProfileBtn.classList.add('btn-cancel-edit');
            if (changePhotoBtn) {
                changePhotoBtn.removeAttribute('disabled');
                changePhotoBtn.style.pointerEvents = 'auto';
                changePhotoBtn.style.opacity = '1';
            }
        } else {
            formFields.forEach(f => f.setAttribute('disabled', 'disabled'));
            editActions.style.display = 'none';
            // Toggle Cancel button back to Edit
            editProfileBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19.5 3 21l1.5-4L16.5 3.5z"/></svg> Edit`;
            editProfileBtn.classList.remove('btn-cancel-edit');
            if (changePhotoBtn) {
                changePhotoBtn.setAttribute('disabled', 'disabled');
                changePhotoBtn.style.pointerEvents = 'none';
                changePhotoBtn.style.opacity = '0.5';
            }
        }
        editProfileBtn.setAttribute('data-edit-mode', isEdit ? 'true' : 'false');
    }

    // Start in view mode
    setEditMode(false);

    // Edit button toggles edit/cancel mode
    if (editProfileBtn) {
        editProfileBtn.addEventListener('click', function () {
            const isEdit = editProfileBtn.getAttribute('data-edit-mode') === 'true';
            if (!isEdit) {
                setEditMode(true);
            } else {
                // Act as cancel: restore original values and disable fields
                document.getElementById('name').value = originalValues.name;
                document.getElementById('email').value = originalValues.email;
                document.getElementById('phone_number').value = originalValues.phone_number;
                profileImagePreview.src = originalValues.profile_image;
                document.getElementById('password').value = '';
                document.getElementById('password_confirm').value = '';
                profileImageInput.value = '';
                profileCameraInput.value = '';
                setEditMode(false);
                showNotification('Changes discarded', 'success', 1500);
            }
        });
    }

    // Cancel button restores original values and disables fields
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('name').value = originalValues.name;
            document.getElementById('email').value = originalValues.email;
            document.getElementById('phone_number').value = originalValues.phone_number;
            profileImagePreview.src = originalValues.profile_image;
            document.getElementById('password').value = '';
            document.getElementById('password_confirm').value = '';
            profileImageInput.value = '';
            profileCameraInput.value = '';
            setEditMode(false);
            showNotification('Changes discarded', 'success', 1500);
        });
    }

    // Save button triggers confirmation modal
    if (saveBtn) {
        saveBtn.addEventListener('click', function(e) {
            e.preventDefault();
            openModal('confirmationModal');
        });
    }

    // Handle Change Photo Button
    if (changePhotoBtn) {
        changePhotoBtn.addEventListener('click', function() {
            // Check if photo modal is available
            if (window.photoModal) {
                const hasPhoto = profileImagePreview.src && !profileImagePreview.src.includes('ui-avatars.com');
                
                window.photoModal.show({
                    photoInputId: 'profileImageInput',
                    cameraInputId: 'profileCameraInput',
                    hasPhoto: hasPhoto,
                    onPhotoSelected: function(file) {
                        handlePhotoSelection(file);
                    },
                    onPhotoRemoved: function() {
                        handlePhotoRemoval();
                    }
                });
            } else {
                // Fallback: open file input directly
                profileImageInput.click();
            }
        });
    }

    // Handle direct file input change (fallback)
    if (profileImageInput) {
        profileImageInput.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) {
                handlePhotoSelection(e.target.files[0]);
            }
        });
    }

    // Handle camera input change
    if (profileCameraInput) {
        profileCameraInput.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) {
                handlePhotoSelection(e.target.files[0]);
            }
        });
    }

    // Handle photo selection
    function handlePhotoSelection(file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            profileImagePreview.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    // Handle photo removal
    function handlePhotoRemoval() {
        // Call backend to delete the photo file
        fetch('/users/profile/delete_photo/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Accept': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const username = document.getElementById('username').value;
                profileImagePreview.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(username)}&size=150&background=22c55e&color=ffffff&bold=true`;
                profileImageInput.value = '';
                profileCameraInput.value = '';
                showNotification('Profile photo deleted.', 'success', 1500);
            } else {
                showNotification(data.message || 'Could not delete photo.', 'error');
            }
        })
        .catch(() => {
            showNotification('Could not delete photo.', 'error');
        });
    }

    // Handle Profile Form Submission - Show confirmation modal
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const password = document.getElementById('password').value;
            const passwordConfirm = document.getElementById('password_confirm').value;

            // Validate passwords match if provided
            if (password || passwordConfirm) {
                if (password !== passwordConfirm) {
                    showNotification('Passwords do not match!', 'error');
                    return;
                }
                if (password.length < 6) {
                    showNotification('Password must be at least 6 characters long', 'error');
                    return;
                }
            }

            // Show confirmation modal
            openModal('confirmationModal');
        });
    }

    // Handle Confirm Save
    if (confirmSave) {
        confirmSave.addEventListener('click', function() {
            closeModal('confirmationModal');
            submitProfileForm();
        });
    }

    // Handle Close Confirmation Modal
    if (closeConfirmModal) {
        closeConfirmModal.addEventListener('click', function() {
            closeModal('confirmationModal');
        });
    }

    if (cancelConfirm) {
        cancelConfirm.addEventListener('click', function() {
            closeModal('confirmationModal');
        });
    }

    // Submit profile form
    function submitProfileForm() {
        const formData = new FormData(profileForm);

        fetch(window.location.pathname, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success', 2000);
                
                // Update profile image if returned
                if (data.profile_image_url) {
                    // Add cache-busting query string to force reload
                    const url = data.profile_image_url + '?t=' + new Date().getTime();
                    profileImagePreview.src = url;
                    originalValues.profile_image = url;
                }
                
                // Update original values
                originalValues.name = document.getElementById('name').value;
                originalValues.email = document.getElementById('email').value;
                originalValues.phone_number = document.getElementById('phone_number').value;
                
                // Clear password fields
                document.getElementById('password').value = '';
                document.getElementById('password_confirm').value = '';
                
                // Toggle edit button back to view mode
                setEditMode(false);
            } else {
                showNotification(data.message || 'Error updating profile', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred. Please try again.', 'error');
        });
    }

    // Modal functions
    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    // Close modals when clicking outside
    if (confirmationModal) {
        confirmationModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal('confirmationModal');
            }
        });
    }

    // Close modals on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (confirmationModal && confirmationModal.classList.contains('active')) {
                closeModal('confirmationModal');
            }
        }
    });

    // Helper function to get CSRF token
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
});