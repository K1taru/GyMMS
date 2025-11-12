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
    let isSubmitting = false; // Track submission state to prevent double-clicks

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

        console.log('[PAYMENT] Form submitted');

        // Prevent multiple submissions
        if (isSubmitting) {
            console.log('[PAYMENT] Form submission already in progress, ignoring...');
            return;
        }

        // Validation
        if (!memberIdHidden.value) {
            console.log('[PAYMENT] Validation failed: No member selected');
            if (typeof showNotification === 'function') {
                showNotification('Please select a member', 'error');
            } else {
                alert('Please select a member');
            }
            return;
        }

        const pricingSelect = document.getElementById('pricing_id');
        if (!pricingSelect.value) {
            console.log('[PAYMENT] Validation failed: No pricing selected');
            if (typeof showNotification === 'function') {
                showNotification('Please select a membership plan', 'error');
            } else {
                alert('Please select a membership plan');
            }
            return;
        }

        if (!paymentMethodSelect.value) {
            console.log('[PAYMENT] Validation failed: No payment method selected');
            if (typeof showNotification === 'function') {
                showNotification('Please select a payment method', 'error');
            } else {
                alert('Please select a payment method');
            }
            return;
        }

        // Check reference number for digital payments - REQUIRED
        const method = paymentMethodSelect.value;
        if (digitalMethods.includes(method)) {
            const refValue = referenceInput.value.trim();
            if (!refValue) {
                console.log('[PAYMENT] Validation failed: Reference number required for digital payment');
                if (typeof showNotification === 'function') {
                    showNotification('Reference/Transaction number is required for digital payments', 'error');
                } else {
                    alert('Reference/Transaction number is required for digital payments');
                }
                referenceInput.focus();
                return;
            }
        }

        console.log('[PAYMENT] Validation passed, submitting payment...');

        // Set submitting flag
        isSubmitting = true;

        // Prepare form data
        const formData = new FormData(paymentForm);
        
        // Disable submit button to prevent double submission
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = true;

        // Submit payment
        fetch('/payments/process/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => {
            // Check if response is ok before parsing JSON
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Payment processing failed');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('[PAYMENT] Response received:', data);
            
            if (data.success) {
                console.log('[PAYMENT] Payment successful, showing notification');
                
                // Check if showNotification exists
                if (typeof showNotification === 'function') {
                    showNotification(data.message, 'success');
                } else {
                    console.error('[PAYMENT] showNotification is not defined!');
                    alert(data.message); // Fallback to alert
                }
                
                // Reset form to default state
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
                
                // Add payment to recent payments list immediately
                if (data.payment) {
                    console.log('[PAYMENT] Adding payment to recent list');
                    addPaymentToRecentList(data.payment);
                }
                
                // Reset submission state and re-enable button
                isSubmitting = false;
                submitBtn.disabled = false;
                console.log('[PAYMENT] Button re-enabled');
                
                // If walk-in, redirect to dashboard after short delay
                if (data.is_walkin) {
                    console.log('[PAYMENT] Walk-in detected, redirecting to dashboard');
                    setTimeout(() => {
                        window.location.href = '/dashboard/';
                    }, 1500);
                }
            } else {
                console.log('[PAYMENT] Payment failed:', data.message);
                
                if (typeof showNotification === 'function') {
                    showNotification(data.message || 'Payment processing failed', 'error');
                } else {
                    alert(data.message || 'Payment processing failed');
                }
                
                // Restore button state
                isSubmitting = false;
                submitBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('[PAYMENT] Error processing payment:', error);
            
            if (typeof showNotification === 'function') {
                showNotification(error.message || 'An error occurred while processing payment', 'error');
            } else {
                alert(error.message || 'An error occurred while processing payment');
            }
            
            // Restore button state
            isSubmitting = false;
            submitBtn.disabled = false;
        });
    });

    // ===== HELPER FUNCTION: ADD PAYMENT TO RECENT LIST =====
    
    function addPaymentToRecentList(payment) {
        const tableBody = document.querySelector('.payments-table tbody');
        if (!tableBody) return;
        
        // Check if there's an empty state message and remove it
        const emptyState = tableBody.querySelector('.empty-state');
        if (emptyState) {
            emptyState.parentElement.remove();
        }
        
        // Create new row
        const newRow = document.createElement('tr');
        newRow.classList.add('newly-added'); // For animation
        
        // Determine method badge class
        const methodClass = `method-${payment.payment_method.toLowerCase().replace(/\s+/g, '')}`;
        
        newRow.innerHTML = `
            <td>${payment.payment_date}</td>
            <td><span class="member-id-badge">${payment.stored_member_id}</span></td>
            <td>${payment.stored_member_name}</td>
            <td class="amount">₱${parseFloat(payment.amount).toFixed(2)}</td>
            <td><span class="method-badge ${methodClass}">${payment.payment_method}</span></td>
            <td>${payment.reference_number}</td>
            <td><span class="status-badge status-${payment.status.toLowerCase()}">${payment.status}</span></td>
            <td>${payment.processed_by}</td>
        `;
        
        // Insert at the top
        tableBody.insertBefore(newRow, tableBody.firstChild);
        
        // Trigger animation
        setTimeout(() => {
            newRow.classList.add('fade-in');
        }, 10);
        
        // Keep only the 5 most recent payments
        const rows = tableBody.querySelectorAll('tr');
        if (rows.length > 5) {
            for (let i = 5; i < rows.length; i++) {
                rows[i].remove();
            }
        }
    }

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

    // Note: showNotification is now loaded globally from core/static/core/js/notifications.js

    // ===== INITIALIZE =====
    
    // Member info card is always visible now (no need to show/hide)
    
    console.log('Payment processing page initialized');
});
