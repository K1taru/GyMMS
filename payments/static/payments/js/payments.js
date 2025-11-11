// ===== PAYMENT PROCESSING JAVASCRIPT =====

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const memberSearchInput = document.getElementById('member_search');
    const searchResults = document.getElementById('searchResults');
    const memberIdHidden = document.getElementById('member_id');
    const memberInfoCard = document.getElementById('memberInfoCard');
    const paymentForm = document.getElementById('paymentForm');
    const paymentMethodSelect = document.getElementById('payment_method');
    const referenceSection = document.getElementById('referenceSection');
    const referenceInput = document.getElementById('reference_number');
    const paymentSearchInput = document.getElementById('paymentSearchInput');

    let searchTimeout = null;
    let selectedMember = null;

    // ===== MEMBER SEARCH AUTOCOMPLETE =====
    
    memberSearchInput.addEventListener('input', function() {
        const query = this.value.trim();

        // Clear previous timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }

        // Clear results if query is too short
        if (query.length < 2) {
            searchResults.classList.remove('active');
            searchResults.innerHTML = '';
            return;
        }

        // Debounce search
        searchTimeout = setTimeout(() => {
            searchMembers(query);
        }, 300);
    });

    // Trigger search on focus if there's existing text
    memberSearchInput.addEventListener('focus', function() {
        const query = this.value.trim();
        if (query.length >= 2) {
            // If we already have results displayed, just show them
            if (searchResults.innerHTML && searchResults.querySelector('.search-result-item, .no-results')) {
                searchResults.classList.add('active');
            } else {
                // Otherwise fetch new results
                searchMembers(query);
            }
        }
    });

    // Click outside to close search results
    document.addEventListener('click', function(e) {
        if (!memberSearchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.remove('active');
        }
    });

    // Search members via AJAX
    function searchMembers(query) {
        fetch(`/payments/search-members/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                displaySearchResults(data.members);
            })
            .catch(error => {
                console.error('Error searching members:', error);
                searchResults.innerHTML = '<div class="no-results">Error searching members</div>';
                searchResults.classList.add('active');
            });
    }

    // Display search results
    function displaySearchResults(members) {
        if (members.length === 0) {
            searchResults.innerHTML = '<div class="no-results">No members found</div>';
        } else {
            searchResults.innerHTML = members.map(member => `
                <div class="search-result-item" data-member='${JSON.stringify(member)}'>
                    <div class="search-result-name">${member.name}</div>
                    <div class="search-result-details">
                        ID: ${member.member_id} • Phone: ${member.phone_number || 'N/A'} • 
                        Status: <span style="color: ${member.status === 'active' ? '#10b981' : '#ef4444'}">${member.status}</span>
                    </div>
                </div>
            `).join('');

            // Add click listeners to results
            document.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', function() {
                    const member = JSON.parse(this.dataset.member);
                    selectMember(member);
                });
            });
        }

        searchResults.classList.add('active');
    }

    // Select a member
    function selectMember(member) {
        selectedMember = member;
        
        // Update hidden input
        memberIdHidden.value = member.member_id;
        
        // Update search input display
        memberSearchInput.value = `${member.member_id} - ${member.name}`;
        
        // Hide search results
        searchResults.classList.remove('active');
        
        // Update member info card
        updateMemberInfoCard(member);
    }

    // Update member info card
    function updateMemberInfoCard(member) {
        document.getElementById('display_member_id').textContent = member.member_id;
        document.getElementById('display_member_name').textContent = member.name;
        document.getElementById('display_member_phone').textContent = member.phone_number || 'N/A';
        document.getElementById('display_member_end_date').textContent = formatDate(member.end_date);
        
        // Update member avatar (photo or initials)
        const avatarContainer = document.getElementById('memberAvatarContainer');
        if (member.photo) {
            avatarContainer.innerHTML = `<img src="${member.photo}" alt="Member Photo" class="member-photo-img">`;
        } else {
            const initials = member.name ? member.name.charAt(0).toUpperCase() : '?';
            avatarContainer.innerHTML = `<div class="member-initials">${initials}</div>`;
        }
        
        // Update status badge with proper status logic
        const statusContainer = document.getElementById('display_member_status');
        let statusBadge = '';
        
        if (member.status === 'active') {
            if (member.is_expiring_soon) {
                statusBadge = '<span class="status-badge expiring">Expiring Soon</span>';
            } else {
                statusBadge = '<span class="status-badge active">Active</span>';
            }
        } else if (member.status === 'expired') {
            statusBadge = '<span class="status-badge expired">Expired</span>';
        } else if (member.status === 'inactive') {
            statusBadge = '<span class="status-badge inactive">Inactive</span>';
        } else if (member.status === 'expiring') {
            statusBadge = '<span class="status-badge expiring">Expiring Soon</span>';
        } else {
            // Fallback
            statusBadge = `<span class="status-badge">${member.status || '—'}</span>`;
        }
        
        statusContainer.innerHTML = statusBadge;
    }

    // Format date
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }

    // ===== PAYMENT METHOD HANDLING =====
    
    // Digital payment methods that require reference number
    const digitalMethods = ['GCash', 'Maya', 'GoTyme', 'Bank Transfer', 'PayPal', 'Debit Card', 'Credit Card'];
    const referenceRequired = document.getElementById('referenceRequired');
    
    paymentMethodSelect.addEventListener('change', function() {
        const method = this.value;
        
        // Enable/disable reference number field based on payment method
        if (digitalMethods.includes(method)) {
            referenceInput.disabled = false;
            referenceInput.required = true;
            referenceRequired.style.display = 'inline';
        } else {
            referenceInput.disabled = true;
            referenceInput.required = false;
            referenceInput.value = '';
            referenceRequired.style.display = 'none';
        }
    });

    // ===== FORM SUBMISSION =====
    
    paymentForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Validation
        if (!memberIdHidden.value) {
            showNotification('Please select a member', 'error');
            return;
        }

        const pricingSelect = document.getElementById('pricing_id');
        if (!pricingSelect.value) {
            showNotification('Please select a membership plan', 'error');
            return;
        }

        if (!paymentMethodSelect.value) {
            showNotification('Please select a payment method', 'error');
            return;
        }

        // Check reference number for digital payments - REQUIRED
        const method = paymentMethodSelect.value;
        if (digitalMethods.includes(method)) {
            const refValue = referenceInput.value.trim();
            if (!refValue) {
                showNotification('Reference/Transaction number is required for digital payments', 'error');
                referenceInput.focus();
                return;
            }
        }

        // Prepare form data
        const formData = new FormData(paymentForm);
        
        // Show loading state
        const submitBtn = document.getElementById('submitBtn');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <svg class="spinner" width="20" height="20" viewBox="0 0 50 50">
                <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="4"></circle>
            </svg>
            Processing...
        `;

        // Submit payment
        fetch('/payments/process/', {
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
                
                // Reset form
                paymentForm.reset();
                memberIdHidden.value = '';
                memberSearchInput.value = '';
                
                // Reset member info card to empty state
                document.getElementById('display_member_name').textContent = 'No member selected';
                document.getElementById('display_member_id').textContent = '—';
                document.getElementById('display_member_phone').textContent = '—';
                document.getElementById('display_member_end_date').textContent = '—';
                document.getElementById('display_member_status').innerHTML = '<span class="status-badge">—</span>';
                document.getElementById('memberAvatarContainer').innerHTML = '<div class="member-initials">?</div>';
                
                // Reset reference field to disabled state
                referenceInput.disabled = true;
                referenceInput.value = '';
                referenceRequired.style.display = 'none';
                selectedMember = null;
                
                // Reload page to show updated payment in table
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showNotification(data.message || 'Payment processing failed', 'error');
            }
        })
        .catch(error => {
            console.error('Error processing payment:', error);
            showNotification('An error occurred while processing payment', 'error');
        })
        .finally(() => {
            // Restore button state
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        });
    });

    // ===== PAYMENT SEARCH =====
    
    let paymentSearchTimeout = null;

    paymentSearchInput.addEventListener('input', function() {
        const query = this.value.trim();

        // Clear previous timeout
        if (paymentSearchTimeout) {
            clearTimeout(paymentSearchTimeout);
        }

        // Debounce search
        paymentSearchTimeout = setTimeout(() => {
            // Redirect to same page with search query
            const url = new URL(window.location);
            if (query) {
                url.searchParams.set('search', query);
            } else {
                url.searchParams.delete('search');
            }
            window.location.href = url.toString();
        }, 500);
    });

    // ===== UTILITY FUNCTIONS =====

    // Get CSRF token
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    // Show notification
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 2rem;
            right: 2rem;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 10000;
            font-weight: 600;
            animation: slideIn 0.3s ease;
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

        // Add to DOM
        document.body.appendChild(notification);

        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    // ===== INITIALIZE =====
    
    // Member info card is always visible now (no need to show/hide)
    
    console.log('Payment processing page initialized');
});
