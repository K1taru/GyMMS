// ===== TRANSACTION HISTORY JAVASCRIPT =====

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const searchInput = document.getElementById('searchInput');
    const dateFrom = document.getElementById('dateFrom');
    const dateTo = document.getElementById('dateTo');
    const paymentMethodFilter = document.getElementById('paymentMethodFilter');
    const clearFiltersBtn = document.getElementById('clearFilters');
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');
    const pageInput = document.getElementById('pageInput');
    const perPageSelect = document.getElementById('perPageSelect');
    const periodBtns = document.querySelectorAll('.period-btn');

    let filterTimeout = null;

    // ===== TIME PERIOD FILTER FOR STATS =====

    periodBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Update active state
            periodBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            // Fetch stats for selected period
            const period = this.getAttribute('data-period');
            fetchStats(period);
        });
    });

    function fetchStats(period) {
        // Add loading state to stat cards
        document.querySelectorAll('.stat-card').forEach(card => {
            card.classList.add('loading');
        });

        // Fetch stats from server
        fetch(`/payments/transactions/stats/?period=${period}`)
            .then(response => response.json())
            .then(data => {
                // Update stat values with animation
                updateStatValue('totalRevenue', `₱${parseFloat(data.total_revenue || 0).toFixed(2)}`);
                updateStatValue('totalCount', data.total_count || 0);
                updateStatValue('averageAmount', `₱${parseFloat(data.average_amount || 0).toFixed(2)}`);

                // Remove loading state
                document.querySelectorAll('.stat-card').forEach(card => {
                    card.classList.remove('loading');
                });
            })
            .catch(error => {
                console.error('Error fetching stats:', error);
                showNotification('Failed to load statistics', 'error');
                
                // Remove loading state
                document.querySelectorAll('.stat-card').forEach(card => {
                    card.classList.remove('loading');
                });
            });
    }

    function updateStatValue(elementId, newValue) {
        const element = document.getElementById(elementId);
        if (element) {
            // Fade out
            element.style.opacity = '0';
            
            setTimeout(() => {
                element.textContent = newValue;
                // Fade in
                element.style.opacity = '1';
            }, 150);
        }
    }

    // ===== FILTER HANDLING =====

    // Search input with debounce
    searchInput.addEventListener('input', function() {
        if (filterTimeout) {
            clearTimeout(filterTimeout);
        }
        filterTimeout = setTimeout(() => {
            applyFilters();
        }, 500);
    });

    // Date filters
    dateFrom.addEventListener('change', function() {
        // Ensure dateTo is not before dateFrom
        if (dateTo.value && this.value > dateTo.value) {
            dateTo.value = this.value;
        }
        applyFilters();
    });

    dateTo.addEventListener('change', function() {
        // Ensure dateTo is not before dateFrom
        if (dateFrom.value && this.value < dateFrom.value) {
            dateFrom.value = this.value;
        }
        applyFilters();
    });

    // Payment method filter
    paymentMethodFilter.addEventListener('change', function() {
        applyFilters();
    });

    // Clear filters
    clearFiltersBtn.addEventListener('click', function() {
        searchInput.value = '';
        dateFrom.value = '';
        dateTo.value = '';
        paymentMethodFilter.value = '';
        
        // Redirect to base URL without filters
        window.location.href = '/payments/transactions';
    });

    // ===== PAGINATION HANDLING =====

    // Previous page
    prevPageBtn.addEventListener('click', function() {
        const currentPage = parseInt(pageInput.value);
        if (currentPage > 1) {
            pageInput.value = currentPage - 1;
            applyFilters();
        }
    });

    // Next page
    nextPageBtn.addEventListener('click', function() {
        const currentPage = parseInt(pageInput.value);
        const maxPage = parseInt(pageInput.max);
        if (currentPage < maxPage) {
            pageInput.value = currentPage + 1;
            applyFilters();
        }
    });

    // Page input direct entry
    pageInput.addEventListener('change', function() {
        let page = parseInt(this.value);
        const maxPage = parseInt(this.max);
        
        // Validate page number
        if (isNaN(page) || page < 1) {
            page = 1;
        } else if (page > maxPage) {
            page = maxPage;
        }
        
        this.value = page;
        applyFilters();
    });

    // Prevent non-numeric input
    pageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            this.blur();
        }
    });

    // Per page selector
    perPageSelect.addEventListener('change', function() {
        // Reset to page 1 when changing items per page
        pageInput.value = 1;
        applyFilters();
    });

    // ===== APPLY FILTERS FUNCTION =====

    function applyFilters() {
        const url = new URL(window.location);
        
        // Clear existing params
        url.search = '';
        
        // Add search query
        const searchQuery = searchInput.value.trim();
        if (searchQuery) {
            url.searchParams.set('search', searchQuery);
        }
        
        // Add date range
        if (dateFrom.value) {
            url.searchParams.set('date_from', dateFrom.value);
        }
        if (dateTo.value) {
            url.searchParams.set('date_to', dateTo.value);
        }
        
        // Add payment method filter
        if (paymentMethodFilter.value) {
            url.searchParams.set('payment_method', paymentMethodFilter.value);
        }
        
        // Add pagination
        const page = parseInt(pageInput.value);
        if (page && page > 1) {
            url.searchParams.set('page', page);
        }
        
        // Add per page
        const perPage = parseInt(perPageSelect.value);
        if (perPage && perPage !== 10) {
            url.searchParams.set('per_page', perPage);
        }
        
        // Navigate to filtered URL
        window.location.href = url.toString();
    }

    // ===== KEYBOARD SHORTCUTS =====

    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
            searchInput.select();
        }
        
        // Arrow keys for pagination (when not in input)
        if (document.activeElement !== pageInput && document.activeElement !== searchInput) {
            if (e.key === 'ArrowLeft' && !prevPageBtn.disabled) {
                e.preventDefault();
                prevPageBtn.click();
            } else if (e.key === 'ArrowRight' && !nextPageBtn.disabled) {
                e.preventDefault();
                nextPageBtn.click();
            }
        }
    });

    // ===== COPY TRANSACTION ID =====

    // Add click to copy functionality for transaction IDs
    document.querySelectorAll('.transaction-id').forEach(element => {
        element.addEventListener('click', function() {
            const fullId = this.getAttribute('title');
            
            // Copy to clipboard
            navigator.clipboard.writeText(fullId).then(() => {
                showNotification('Transaction ID copied to clipboard!', 'success');
            }).catch(err => {
                console.error('Failed to copy:', err);
                showNotification('Failed to copy transaction ID', 'error');
            });
        });
        
        // Add pointer cursor
        element.style.cursor = 'pointer';
    });

    // ===== UTILITY FUNCTIONS =====

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
        if (!document.querySelector('style[data-notification]')) {
            style.setAttribute('data-notification', 'true');
            document.head.appendChild(style);
        }

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

    // ===== EXPORT FUNCTIONALITY (Optional) =====

    // Add export button dynamically if needed
    function addExportButton() {
        const header = document.querySelector('.page-header');
        if (header && !document.getElementById('exportBtn')) {
            const exportBtn = document.createElement('button');
            exportBtn.id = 'exportBtn';
            exportBtn.className = 'btn-export';
            exportBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" x2="12" y1="15" y2="3"/>
                </svg>
                Export CSV
            `;
            exportBtn.style.cssText = `
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.75rem 1.5rem;
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            `;
            
            exportBtn.addEventListener('click', function() {
                // Build export URL with current filters
                const exportUrl = new URL('/payments/transactions/export', window.location.origin);
                const params = new URLSearchParams(window.location.search);
                params.forEach((value, key) => {
                    exportUrl.searchParams.set(key, value);
                });
                
                // Trigger download
                window.location.href = exportUrl.toString();
            });
            
            header.appendChild(exportBtn);
        }
    }

    // Uncomment to enable export button
    // addExportButton();

    // ===== INITIALIZE =====

    // Load initial stats (1D by default)
    fetchStats('1d');

    console.log('Transaction history page initialized');
    
    // Set filter values from URL params on load
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('payment_method')) {
        paymentMethodFilter.value = urlParams.get('payment_method');
    }

    // ===== NOTIFICATION FUNCTION =====

    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'error' ? '#ef4444' : '#10b981'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
});
