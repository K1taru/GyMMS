// ===== TRANSACTION HISTORY JAVASCRIPT WITH AJAX =====

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const searchInput = document.getElementById('searchInput');
    const dateFrom = document.getElementById('dateFrom');
    const dateTo = document.getElementById('dateTo');
    const paymentMethodFilter = document.getElementById('paymentMethodFilter');
    const memberTypeFilter = document.getElementById('memberTypeFilter');
    const clearFiltersBtn = document.getElementById('clearFilters');
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');
    const pageInput = document.getElementById('pageInput');
    const perPageSelect = document.getElementById('perPageSelect');
    const periodBtns = document.querySelectorAll('.period-btn');

    let filterTimeout = null;
    let currentFilters = {
        search: searchInput.value || '',
        date_from: dateFrom.value || '',
        date_to: dateTo.value || '',
        payment_method: paymentMethodFilter.value || '',
        member_type: memberTypeFilter.value || '',
        page: 1,
        per_page: parseInt(perPageSelect.value) || 10
    };

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

        // Build query string with current filters
        const params = new URLSearchParams();
        params.set('period', period);
        
        // Include current filters in stats request
        if (currentFilters.search) params.set('search', currentFilters.search);
        if (currentFilters.date_from) params.set('date_from', currentFilters.date_from);
        if (currentFilters.date_to) params.set('date_to', currentFilters.date_to);
        if (currentFilters.payment_method) params.set('payment_method', currentFilters.payment_method);
        if (currentFilters.member_type) params.set('member_type', currentFilters.member_type);

        // Fetch stats from server
        fetch(`/payments/transactions/stats/?${params.toString()}`)
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
            currentFilters.search = this.value.trim();
            currentFilters.page = 1; // Reset to first page
            applyFilters();
        }, 500);
    });

    // Date filters
    dateFrom.addEventListener('change', function() {
        // Ensure dateTo is not before dateFrom
        if (dateTo.value && this.value > dateTo.value) {
            dateTo.value = this.value;
        }
        currentFilters.date_from = this.value;
        currentFilters.page = 1;
        applyFilters();
    });

    dateTo.addEventListener('change', function() {
        // Ensure dateTo is not before dateFrom
        if (dateFrom.value && this.value < dateFrom.value) {
            dateFrom.value = this.value;
        }
        currentFilters.date_to = this.value;
        currentFilters.page = 1;
        applyFilters();
    });

    // Payment method filter
    paymentMethodFilter.addEventListener('change', function() {
        currentFilters.payment_method = this.value;
        currentFilters.page = 1;
        applyFilters();
    });

    // Member type filter
    memberTypeFilter.addEventListener('change', function() {
        console.log('[FILTER] Member type changed to:', this.value);
        currentFilters.member_type = this.value;
        currentFilters.page = 1;
        console.log('[FILTER] Current filters:', currentFilters);
        applyFilters();
    });

    // Clear filters
    clearFiltersBtn.addEventListener('click', function() {
        searchInput.value = '';
        dateFrom.value = '';
        dateTo.value = '';
        paymentMethodFilter.value = '';
        memberTypeFilter.value = '';
        
        currentFilters = {
            search: '',
            date_from: '',
            date_to: '',
            payment_method: '',
            member_type: '',
            page: 1,
            per_page: parseInt(perPageSelect.value) || 10
        };
        
        applyFilters();
    });

    // ===== PAGINATION HANDLING =====

    // Previous page
    prevPageBtn.addEventListener('click', function() {
        if (currentFilters.page > 1) {
            currentFilters.page--;
            applyFilters();
        }
    });

    // Next page
    nextPageBtn.addEventListener('click', function() {
        const maxPage = parseInt(pageInput.max);
        if (currentFilters.page < maxPage) {
            currentFilters.page++;
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
        currentFilters.page = page;
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
        currentFilters.per_page = parseInt(this.value);
        currentFilters.page = 1; // Reset to first page
        applyFilters();
    });

    // ===== APPLY FILTERS FUNCTION (AJAX) =====

    function applyFilters() {
        // Build query string
        const params = new URLSearchParams();
        
        if (currentFilters.search) params.set('search', currentFilters.search);
        if (currentFilters.date_from) params.set('date_from', currentFilters.date_from);
        if (currentFilters.date_to) params.set('date_to', currentFilters.date_to);
        if (currentFilters.payment_method) params.set('payment_method', currentFilters.payment_method);
        if (currentFilters.member_type) params.set('member_type', currentFilters.member_type);
        if (currentFilters.page > 1) params.set('page', currentFilters.page);
        if (currentFilters.per_page !== 10) params.set('per_page', currentFilters.per_page);
        
        console.log('[APPLY FILTERS] Params:', params.toString());
        console.log('[APPLY FILTERS] Current filters:', currentFilters);
        
        // Update URL without reload (for sharing/bookmarking)
        const newUrl = `/payments/transactions${params.toString() ? '?' + params.toString() : ''}`;
        window.history.pushState({}, '', newUrl);
        
        // Show loading state
        showLoading();
        
        // Fetch filtered data
        const ajaxUrl = `/payments/transactions/ajax/?${params.toString()}`;
        console.log('[APPLY FILTERS] Fetching from:', ajaxUrl);
        
        fetch(ajaxUrl)
            .then(response => {
                console.log('[APPLY FILTERS] Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('[APPLY FILTERS] Response:', data);
                updateTable(data.transactions);
                updatePagination(data.pagination);
                updateStats(data.stats);
                
                // Reset time period buttons to show "All" since we're using custom filters
                periodBtns.forEach(b => b.classList.remove('active'));
                const allBtn = document.querySelector('.period-btn[data-period="all"]');
                if (allBtn) {
                    allBtn.classList.add('active');
                }
                
                hideLoading();
            })
            .catch(error => {
                console.error('Error fetching transactions:', error);
                showNotification('Failed to load transactions. Please try again.', 'error');
                hideLoading();
            });
    }

    // ===== UPDATE TABLE FUNCTION =====

    function updateTable(transactions) {
        const tbody = document.querySelector('.transactions-table tbody');
        
        if (transactions.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="empty-state">
                        <div class="empty-icon">📊</div>
                        <p>No transactions found</p>
                        <small>Try adjusting your filters or search criteria</small>
                    </td>
                </tr>
            `;
            return;
        }
        
        let html = '';
        transactions.forEach(transaction => {
            const planInfo = transaction.stored_plan_label !== 'N/A' && transaction.stored_duration_days > 0
                ? `${transaction.stored_plan_label} <small>(${transaction.stored_duration_days} days)</small>`
                : transaction.stored_plan_label;
            
            html += `
                <tr>
                    <td>
                        <span class="transaction-id" title="${transaction.id}">
                            ${transaction.id}
                        </span>
                    </td>
                    <td>${transaction.payment_date}</td>
                    <td><span class="member-id-badge">${transaction.stored_member_id}</span></td>
                    <td>${transaction.stored_member_name}</td>
                    <td>
                        <span class="plan-info">
                            ${planInfo}
                        </span>
                    </td>
                    <td class="amount">₱${transaction.amount}</td>
                    <td>
                        <span class="method-badge method-${transaction.payment_method.toLowerCase().replace(/\s/g, '')}">
                            ${transaction.payment_method}
                        </span>
                    </td>
                    <td>${transaction.reference_number}</td>
                    <td>${transaction.processed_by}</td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
        
        // Re-attach click handlers for transaction IDs
        attachTransactionIdHandlers();
    }

    // ===== UPDATE PAGINATION FUNCTION =====

    function updatePagination(pagination) {
        // Update page input
        pageInput.value = pagination.current_page;
        pageInput.max = pagination.total_pages;
        
        // Update pagination info
        const paginationInfo = document.querySelector('.pagination-info');
        paginationInfo.textContent = `Showing ${pagination.start_index} to ${pagination.end_index} of ${pagination.total_count} transactions`;
        
        // Update button states
        prevPageBtn.disabled = !pagination.has_previous;
        nextPageBtn.disabled = !pagination.has_next;
        
        // Update current filters page
        currentFilters.page = pagination.current_page;
    }

    // ===== UPDATE STATS FUNCTION =====

    function updateStats(stats) {
        updateStatValue('totalRevenue', `₱${parseFloat(stats.total_revenue || 0).toFixed(2)}`);
        updateStatValue('totalCount', stats.total_count || 0);
        updateStatValue('averageAmount', `₱${parseFloat(stats.average_amount || 0).toFixed(2)}`);
    }

    // ===== LOADING STATE =====

    function showLoading() {
        const tbody = document.querySelector('.transactions-table tbody');
        tbody.style.opacity = '0.5';
        tbody.style.pointerEvents = 'none';
        
        // Add loading overlay if it doesn't exist
        if (!document.querySelector('.loading-overlay')) {
            const overlay = document.createElement('div');
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="loading-spinner"></div>
            `;
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.1);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            `;
            
            const spinner = overlay.querySelector('.loading-spinner');
            spinner.style.cssText = `
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
            `;
            
            // Add animation
            if (!document.querySelector('style[data-spinner]')) {
                const style = document.createElement('style');
                style.setAttribute('data-spinner', 'true');
                style.textContent = `
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                `;
                document.head.appendChild(style);
            }
            
            document.body.appendChild(overlay);
        }
    }

    function hideLoading() {
        const tbody = document.querySelector('.transactions-table tbody');
        tbody.style.opacity = '1';
        tbody.style.pointerEvents = 'auto';
        
        const overlay = document.querySelector('.loading-overlay');
        if (overlay) {
            overlay.remove();
        }
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

    // ===== ATTACH TRANSACTION ID CLICK HANDLERS =====

    function attachTransactionIdHandlers() {
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
        });
    }

    // ===== NOTIFICATION FUNCTION =====
    // Note: showNotification is now loaded globally from /static/global/js/notifications.js

    // ===== INITIALIZE =====

    // Set filter values from URL params on load
    const urlParams = new URLSearchParams(window.location.search);
    
    console.log('[INIT] URL Params:', urlParams.toString());
    console.log('[INIT] Initial currentFilters:', currentFilters);
    
    // Initialize filters from URL
    if (urlParams.has('search')) {
        searchInput.value = urlParams.get('search');
        currentFilters.search = urlParams.get('search');
    }
    if (urlParams.has('date_from')) {
        dateFrom.value = urlParams.get('date_from');
        currentFilters.date_from = urlParams.get('date_from');
    }
    if (urlParams.has('date_to')) {
        dateTo.value = urlParams.get('date_to');
        currentFilters.date_to = urlParams.get('date_to');
    }
    if (urlParams.has('payment_method')) {
        paymentMethodFilter.value = urlParams.get('payment_method');
        currentFilters.payment_method = urlParams.get('payment_method');
    }
    if (urlParams.has('member_type')) {
        const memberType = urlParams.get('member_type');
        console.log('[INIT] Setting member_type from URL:', memberType);
        memberTypeFilter.value = memberType;
        currentFilters.member_type = memberType;
        console.log('[INIT] memberTypeFilter.value after set:', memberTypeFilter.value);
    }
    if (urlParams.has('page')) {
        currentFilters.page = parseInt(urlParams.get('page'));
    }
    if (urlParams.has('per_page')) {
        const perPageValue = urlParams.get('per_page');
        perPageSelect.value = perPageValue;
        currentFilters.per_page = parseInt(perPageValue);
    }

    console.log('[INIT] Final currentFilters:', currentFilters);
    console.log('[INIT] memberTypeFilter element:', memberTypeFilter);
    console.log('[INIT] memberTypeFilter.value:', memberTypeFilter.value);

    // Load initial stats (1D by default)
    fetchStats('1d');

    // Attach initial transaction ID handlers
    attachTransactionIdHandlers();

    // Handle browser back/forward
    window.addEventListener('popstate', function() {
        location.reload();
    });

    console.log('Transaction history page initialized with AJAX filtering');
});
