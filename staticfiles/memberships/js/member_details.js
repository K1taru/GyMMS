/**
 * Member Details JavaScript - View/Edit Mode
 */

document.addEventListener('DOMContentLoaded', () => {
    let isEditMode = false;
    const toggleEditBtn = document.getElementById('toggleEditMode');
    const editModeText = document.getElementById('editModeText');
    const formActions = document.getElementById('formActions');
    const cancelEditBtn = document.getElementById('cancelEdit');
    const form = document.getElementById('memberForm');
    const deleteMemberBtn = document.getElementById('deleteMemberBtn');
    const memberAvatarContainer = document.getElementById('memberAvatarContainer');
    const photoEditOverlay = document.getElementById('photoEditOverlay');
    
    // Get editable form inputs (exclude always-readonly/disabled ones)
    const formInputs = form.querySelectorAll('input:not([type="hidden"]):not([type="file"]):not(.always-readonly), select:not(.always-disabled), textarea:not(.always-readonly)');
    
    // Store original values
    const originalValues = {};
    formInputs.forEach(input => {
        originalValues[input.name] = input.value;
    });
    
    // Photo upload functionality for edit mode
    const photoInputEdit = document.getElementById('member_photo_edit');
    const cameraInputEdit = document.getElementById('camera_input_edit');
    
    if (photoInputEdit) {
        photoInputEdit.addEventListener('change', (e) => {
            handlePhotoUploadEdit(e.target.files[0]);
        });
    }
    
    if (cameraInputEdit) {
        cameraInputEdit.addEventListener('change', (e) => {
            handlePhotoUploadEdit(e.target.files[0]);
        });
    }
    
    // Avatar click handler for photo options
    if (memberAvatarContainer) {
        memberAvatarContainer.addEventListener('click', () => {
            if (isEditMode) {
                // Check if member has a photo
                const hasPhoto = memberAvatarContainer.querySelector('img') !== null;
                
                // Open photo modal
                const photoModal = window.getPhotoModal();
                if (photoModal) {
                    photoModal.show({
                        photoInputId: 'member_photo_edit',
                        cameraInputId: 'camera_input_edit',
                        hasPhoto: hasPhoto,
                        onPhotoSelected: (file) => {
                            handlePhotoUploadEdit(file);
                        },
                        onPhotoRemoved: () => {
                            handleRemovePhoto();
                        }
                    });
                }
            }
        });
    }
    
    // Toggle edit mode
    function toggleEdit() {
        isEditMode = !isEditMode;
        
        if (isEditMode) {
            // Enable edit mode
            editModeText.textContent = 'Cancel';
            formActions.style.display = 'flex';
            if (memberAvatarContainer) {
                memberAvatarContainer.classList.add('editable');
                const overlay = document.getElementById('photoEditOverlay');
                if (overlay) overlay.style.display = 'flex';
            }
            
            formInputs.forEach(input => {
                if (input.tagName === 'SELECT') {
                    input.disabled = false;
                } else {
                    input.readOnly = false;
                }
            });
        } else {
            // Disable edit mode
            editModeText.textContent = 'Edit';
            formActions.style.display = 'none';
            if (memberAvatarContainer) {
                memberAvatarContainer.classList.remove('editable');
                const overlay = document.getElementById('photoEditOverlay');
                if (overlay) overlay.style.display = 'none';
            }
            
            // Restore original values
            formInputs.forEach(input => {
                input.value = originalValues[input.name];
                
                if (input.tagName === 'SELECT') {
                    input.disabled = true;
                } else {
                    input.readOnly = true;
                }
            });
        }
    }
    
    // Event listeners
    if (toggleEditBtn) {
        toggleEditBtn.addEventListener('click', toggleEdit);
    }
    
    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', toggleEdit);
    }
    
    // Delete member functionality
    if (deleteMemberBtn) {
        deleteMemberBtn.addEventListener('click', () => {
            // Get member ID from the card
            const memberIdElement = document.querySelector('.member-id-value');
            const memberId = memberIdElement ? memberIdElement.textContent.trim() : '';
            
            // Get member name from the card
            const memberNameElement = document.querySelector('.member-name');
            const memberName = memberNameElement ? memberNameElement.textContent.trim() : '';
            
            // Check if member is active or expiring (both have active subscriptions)
            const statusBadge = document.querySelector('.status-badge');
            const isActive = statusBadge && (statusBadge.classList.contains('active') || statusBadge.classList.contains('expiring'));
            
            // Show delete modal
            const modal = window.getDeleteModal();
            if (modal) {
                modal.show({
                    memberId: memberId,
                    memberName: memberName,
                    isActive: isActive,
                    onConfirm: (id) => {
                        handleDeleteMember(id);
                    }
                });
            }
        });
    }
    
    // Date validation (only if fields are not readonly)
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput && endDateInput && !startDateInput.readOnly && !endDateInput.readOnly) {
        // Set min date for end date when start date changes
        startDateInput.addEventListener('change', () => {
            endDateInput.min = startDateInput.value;
            
            // If end date is before start date, update it
            if (endDateInput.value && new Date(endDateInput.value) < new Date(startDateInput.value)) {
                const start = new Date(startDateInput.value);
                const end = new Date(start);
                end.setDate(end.getDate() + 30);
                endDateInput.value = end.toISOString().split('T')[0];
            }
        });
        
        // Trigger validation on load
        endDateInput.min = startDateInput.value;
    }
    
    // Form submission validation (skip date validation if fields are readonly)
    if (form) {
        form.addEventListener('submit', (e) => {
            const startDateField = document.getElementById('start_date');
            const endDateField = document.getElementById('end_date');
            
            // Only validate dates if they are not readonly
            if (startDateField && endDateField && !startDateField.readOnly && !endDateField.readOnly) {
                const startDate = new Date(startDateField.value);
                const endDate = new Date(endDateField.value);
                
                if (endDate <= startDate) {
                    e.preventDefault();
                    alert('End date must be after start date');
                    return false;
                }
            }
            
            // Update original values after successful save
            formInputs.forEach(input => {
                originalValues[input.name] = input.value;
            });
        });
    }
    
    // Confirm before leaving with unsaved changes
    let formChanged = false;
    
    formInputs.forEach(input => {
        input.addEventListener('change', () => {
            if (isEditMode) {
                formChanged = true;
            }
        });
    });
    
    window.addEventListener('beforeunload', (e) => {
        if (formChanged && isEditMode) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
    
    // Reset flag when form is submitted or edit is cancelled
    form.addEventListener('submit', () => {
        formChanged = false;
    });
    
});


// Handle delete member
function handleDeleteMember(memberId) {
    // Send delete request
    fetch(`/memberships/member/${memberId}/delete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/memberships/';
        } else {
            alert(data.message || 'Failed to delete member. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while deleting the member. Please try again.');
    });
}

// Handle photo upload preview for edit mode
function handlePhotoUploadEdit(file) {
    if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const memberAvatarContainer = document.getElementById('memberAvatarContainer');
            const existingImg = memberAvatarContainer.querySelector('img');
            
            if (existingImg) {
                existingImg.src = e.target.result;
            } else {
                // Replace initial with image
                memberAvatarContainer.innerHTML = `
                    <img src="${e.target.result}" alt="Member Photo" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">
                    <div class="photo-edit-overlay" id="photoEditOverlay" style="display: flex;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                            <circle cx="12" cy="13" r="4"></circle>
                        </svg>
                    </div>
                `;
                if (!memberAvatarContainer.classList.contains('editable')) {
                    memberAvatarContainer.classList.add('editable');
                }
            }
        };
        reader.readAsDataURL(file);
    }
}

// Handle remove photo
function handleRemovePhoto() {
    const memberAvatarContainer = document.getElementById('memberAvatarContainer');
    const memberName = document.querySelector('input[name="name"]').value;
    const firstLetter = memberName.charAt(0).toUpperCase();
    
    // Replace with initial
    memberAvatarContainer.innerHTML = `
        ${firstLetter}
        <div class="photo-edit-overlay" id="photoEditOverlay" style="display: flex;">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                <circle cx="12" cy="13" r="4"></circle>
            </svg>
        </div>
    `;
    if (!memberAvatarContainer.classList.contains('editable')) {
        memberAvatarContainer.classList.add('editable');
    }
    
    // Clear the file inputs
    const photoInputEdit = document.getElementById('member_photo_edit');
    const cameraInputEdit = document.getElementById('camera_input_edit');
    if (photoInputEdit) photoInputEdit.value = '';
    if (cameraInputEdit) cameraInputEdit.value = '';
    
    // Add a hidden input to signal photo removal
    let removePhotoInput = document.getElementById('remove_photo_flag');
    if (!removePhotoInput) {
        removePhotoInput = document.createElement('input');
        removePhotoInput.type = 'hidden';
        removePhotoInput.id = 'remove_photo_flag';
        removePhotoInput.name = 'remove_photo';
        removePhotoInput.value = 'true';
        document.getElementById('memberForm').appendChild(removePhotoInput);
    } else {
        removePhotoInput.value = 'true';
    }
}

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
