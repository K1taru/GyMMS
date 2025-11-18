/**
 * Memberships Management JavaScript
 */

// Modal Management
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
        document.body.style.overflow = 'auto';
        
        // Reset form if it exists
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }
}

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        closeModal(e.target.id);
    }
});

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    // Add Member Button
    const addMemberBtn = document.getElementById('addMemberBtn');
    if (addMemberBtn) {
        addMemberBtn.addEventListener('click', () => {
            openModal('addMemberModal');
        });
    }

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', filterMembers);
    }

    // Status filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', filterMembers);
    }

    // Sort filter - default to newest
    const sortFilter = document.getElementById('sortFilter');
    if (sortFilter) {
        sortFilter.value = 'newest'; // Set default to newest first
        sortFilter.addEventListener('change', sortMembers);
        // Trigger initial sort
        sortMembers();
    }

    // Apply URL filter parameter if present
    if (typeof filterParam !== 'undefined' && filterParam) {
        applyUrlFilter(filterParam);
    }

    // Set default dates for add member form
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput && endDateInput) {
        // Set start date to today
        const today = new Date().toISOString().split('T')[0];
        startDateInput.value = today;
        
        // Set end date to 30 days from today
        const endDate = new Date();
        endDate.setDate(endDate.getDate() + 30);
        endDateInput.value = endDate.toISOString().split('T')[0];
        
        // Update end date when start date changes
        startDateInput.addEventListener('change', () => {
            const start = new Date(startDateInput.value);
            const end = new Date(start);
            end.setDate(end.getDate() + 30);
            endDateInput.value = end.toISOString().split('T')[0];
            endDateInput.min = startDateInput.value;
        });
    }

    // Photo upload functionality
    const photoInput = document.getElementById('member_photo');
    const cameraInput = document.getElementById('camera_input');
    const openPhotoModalBtn = document.getElementById('openPhotoModalBtn');
    const photoPreview = document.getElementById('photoPreview');

    if (photoInput) {
        photoInput.addEventListener('change', (e) => {
            handlePhotoUpload(e.target.files[0]);
        });
    }

    if (cameraInput) {
        cameraInput.addEventListener('change', (e) => {
            handlePhotoUpload(e.target.files[0]);
        });
    }

    if (openPhotoModalBtn) {
        openPhotoModalBtn.addEventListener('click', () => {
            // Check if photo exists
            const hasPhoto = photoPreview.querySelector('img') !== null;
            
            // Open photo modal
            const photoModal = window.getPhotoModal();
            if (photoModal) {
                photoModal.show({
                    photoInputId: 'member_photo',
                    cameraInputId: 'camera_input',
                    hasPhoto: hasPhoto,
                    onPhotoSelected: (file) => {
                        handlePhotoUpload(file);
                    },
                    onPhotoRemoved: () => {
                        removePhotoPreview();
                    }
                });
            }
        });
    }
});

// Handle photo upload preview
function handlePhotoUpload(file) {
    if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const photoPreview = document.getElementById('photoPreview');
            photoPreview.innerHTML = `<img src="${e.target.result}" alt="Member photo">`;
        };
        reader.readAsDataURL(file);
    }
}

// Remove photo preview
function removePhotoPreview() {
    const photoPreview = document.getElementById('photoPreview');
    photoPreview.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
        </svg>
    `;
    
    // Clear file inputs
    const photoInput = document.getElementById('member_photo');
    const cameraInput = document.getElementById('camera_input');
    if (photoInput) photoInput.value = '';
    if (cameraInput) cameraInput.value = '';
}

// Search and Filter Members
function filterMembers() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    const table = document.getElementById('membersTable');
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

    for (let row of rows) {
        // Skip empty state row
        if (row.cells.length === 1) continue;

        const memberName = row.querySelector('.member-name')?.textContent.toLowerCase() || '';
        const memberEmail = row.querySelector('.member-email')?.textContent.toLowerCase() || '';
        const memberId = row.querySelector('.member-id')?.textContent.toLowerCase() || '';
        const phone = row.cells[2]?.textContent.toLowerCase() || '';
        const status = row.dataset.status || '';

        // Check search match
        const searchMatch = !searchTerm || 
            memberName.includes(searchTerm) || 
            memberEmail.includes(searchTerm) || 
            memberId.includes(searchTerm) || 
            phone.includes(searchTerm);

        // Check status filter
        let statusMatch = true;
        if (statusFilter !== 'all') {
            statusMatch = status === statusFilter;
        }

        // Show/hide row with smooth transition
        if (searchMatch && statusMatch) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    }
}

// Filter by status (for clickable stat cards)
function filterByStatus(status) {
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.value = status;
        filterMembers();
    }
}

// Sort Members
function sortMembers() {
    const sortValue = document.getElementById('sortFilter').value;
    const table = document.getElementById('membersTable');
    const tbody = table.getElementsByTagName('tbody')[0];
    const rows = Array.from(tbody.getElementsByTagName('tr'));

    // Skip if only empty state row
    if (rows.length <= 1 && rows[0]?.cells.length === 1) return;

    // Filter out empty state row if it exists
    const dataRows = rows.filter(row => row.cells.length > 1);

    dataRows.sort((a, b) => {
        switch (sortValue) {
            case 'newest':
                const createdA = parseFloat(a.dataset.created || 0);
                const createdB = parseFloat(b.dataset.created || 0);
                return createdB - createdA; // Newest first
            
            case 'oldest':
                const createdOldA = parseFloat(a.dataset.created || 0);
                const createdOldB = parseFloat(b.dataset.created || 0);
                return createdOldA - createdOldB; // Oldest first
            
            case 'name':
                const nameA = (a.dataset.name || '').toLowerCase();
                const nameB = (b.dataset.name || '').toLowerCase();
                return nameA.localeCompare(nameB);
            
            case 'expiring':
                const endDateA = new Date(a.dataset.endDate || '');
                const endDateB = new Date(b.dataset.endDate || '');
                const today = new Date();
                
                // Calculate days until expiry
                const daysA = Math.ceil((endDateA - today) / (1000 * 60 * 60 * 24));
                const daysB = Math.ceil((endDateB - today) / (1000 * 60 * 60 * 24));
                
                // Prioritize expiring soon (0-3 days), then sort by days
                const isExpiringA = daysA >= 0 && daysA <= 3;
                const isExpiringB = daysB >= 0 && daysB <= 3;
                
                if (isExpiringA && !isExpiringB) return -1;
                if (!isExpiringA && isExpiringB) return 1;
                
                return daysA - daysB;
            
            case 'expired':
                const expEndDateA = new Date(a.dataset.endDate || '');
                const expEndDateB = new Date(b.dataset.endDate || '');
                const nowDate = new Date();
                
                // Check if expired
                const isExpiredA = expEndDateA < nowDate;
                const isExpiredB = expEndDateB < nowDate;
                
                // Expired first, then sort by end date (most recently expired first)
                if (isExpiredA && !isExpiredB) return -1;
                if (!isExpiredA && isExpiredB) return 1;
                
                return expEndDateB - expEndDateA;
            
            default:
                return 0;
        }
    });

    // Clear tbody and re-append in sorted order without animation
    tbody.innerHTML = '';
    dataRows.forEach(row => {
        tbody.appendChild(row);
    });
}

// View Member Details - Both view and edit in one page
function viewMember(memberId) {
    // Redirect to member detail page
    window.location.href = `/memberships/member/${memberId}/edit/`;
}

// Go directly to payment page without modal
function goToPayment(memberId) {
    // Redirect directly to payments page with member ID
    window.location.href = `/payments/?member_id=${encodeURIComponent(memberId)}`;
}

// Edit Member - Same as view, uses same page
function editMember(memberId) {
    // Redirect to member detail page (same as view)
    window.location.href = `/memberships/member/${memberId}/edit/`;
}

// Delete Member
function deleteMember(memberId, isActive) {
	// Get member name from the table row
	const row = document.querySelector(`tr[data-member-id="${memberId}"]`);
	const memberName = row ? row.dataset.name : memberId;
	
	// Show delete modal
	const modal = window.getDeleteModal();
	if (modal) {
		modal.show({
			memberId: memberId,
			memberName: memberName,
			isActive: isActive,
			onConfirm: (id) => {
				performDelete(id);
			}
		});
	}
}

// Perform actual deletion
function performDelete(memberId) {
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
			// Remove row from table with animation
			const row = document.querySelector(`tr[data-member-id="${memberId}"]`);
			if (row) {
				row.style.transition = 'opacity 0.3s ease';
				row.style.opacity = '0';
				setTimeout(() => {
					row.remove();
					// Check if table is empty
					checkEmptyTable();
				}, 300);
			}
			
			// Show success message (you can replace this with a toast notification)
			showNotification('Member deleted successfully', 'success');
		} else {
			showNotification(data.message || 'Failed to delete member. Please try again.', 'error');
		}
	})
	.catch(error => {
		console.error('Error:', error);
		showNotification('An error occurred. Please try again.', 'error');
	});
}

// Check if table is empty and show empty state
function checkEmptyTable() {
	const tbody = document.querySelector('#membersTable tbody');
	const rows = tbody.querySelectorAll('tr');
	const dataRows = Array.from(rows).filter(row => row.cells.length > 1);
	
	if (dataRows.length === 0) {
		tbody.innerHTML = `
			<tr>
				<td colspan="7" class="empty-state">
					<div class="empty-icon">👥</div>
					<p>No members found</p>
					<button class="btn-secondary" onclick="document.getElementById('addMemberBtn').click()">Add Your First Member</button>
				</td>
			</tr>
		`;
	}
}

// Show notification (simple version - you can enhance this)
function showNotification(message, type = 'info') {
	// Create notification element
	const notification = document.createElement('div');
	notification.className = `notification notification-${type}`;
	notification.style.cssText = `
		position: fixed;
		top: 20px;
		right: 20px;
		padding: 1rem 1.5rem;
		background: ${type === 'success' ? '#10b981' : '#ef4444'};
		color: white;
		border-radius: 8px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		z-index: 10000;
		animation: slideIn 0.3s ease;
		max-width: 400px;
	`;
	notification.textContent = message;
	
	// Add animation
	const style = document.createElement('style');
	style.textContent = `
		@keyframes slideIn {
			from {
				transform: translateX(400px);
				opacity: 0;
			}
			to {
				transform: translateX(0);
				opacity: 1;
			}
		}
		@keyframes slideOut {
			from {
				transform: translateX(0);
				opacity: 1;
			}
			to {
				transform: translateX(400px);
				opacity: 0;
			}
		}
	`;
	document.head.appendChild(style);
	
	document.body.appendChild(notification);
	
	// Auto remove after 3 seconds
	setTimeout(() => {
		notification.style.animation = 'slideOut 0.3s ease';
		setTimeout(() => {
			notification.remove();
			style.remove();
		}, 300);
	}, 3000);
}// Get CSRF token from cookies
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

// Apply URL filter parameter
function applyUrlFilter(filter) {
    const statusFilter = document.getElementById('statusFilter');
    const sortFilter = document.getElementById('sortFilter');
    
    switch(filter) {
        case 'active':
            // Set status filter to active
            if (statusFilter) {
                statusFilter.value = 'active';
                filterMembers();
            }
            break;
        
        case 'expiring':
            // Set status filter to expiring
            if (statusFilter) {
                statusFilter.value = 'expiring';
                filterMembers();
            }
            // Optionally also sort by expiring
            if (sortFilter) {
                sortFilter.value = 'expiring';
                sortMembers();
            }
            break;
        
        case 'newest':
            // Already defaults to newest, just ensure it's set
            if (sortFilter) {
                sortFilter.value = 'newest';
                sortMembers();
            }
            break;
    }
}

// Form validation
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('addMemberForm');
    if (form) {
        form.addEventListener('submit', (e) => {
            const startDate = new Date(document.getElementById('start_date').value);
            const endDate = new Date(document.getElementById('end_date').value);
            
            if (endDate <= startDate) {
                e.preventDefault();
                alert('End date must be after start date');
                return false;
            }
        });
    }
});
