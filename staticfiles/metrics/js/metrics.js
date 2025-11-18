// Dynamic Metrics Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('dynamicChart');
    if (!canvas) return;

    const metricSelect = document.getElementById('metricSelect');
    const graphTypeSelect = document.getElementById('graphTypeSelect');
    const timeframeBtns = document.querySelectorAll('.timeframe-btn');
    const dateFrom = document.getElementById('dateFrom');
    const dateTo = document.getElementById('dateTo');
    const clearDatesBtn = document.getElementById('clearDates');

    let currentChart = null;
    let currentMetric = 'check_ins';
    let currentGraphType = 'bar';
    let currentPeriod = '1d';
    let customDateFrom = '';
    let customDateTo = '';

    // Color schemes for different metrics (more aggressive for line charts)
    const colorSchemes = {
        check_ins: { border: '#3b82f6', background: 'rgba(59,130,246,0.15)' },
        walk_ins: { border: '#ec4899', background: 'rgba(236,72,153,0.15)' },
        member_check_ins: { border: '#f59e0b', background: 'rgba(245,158,11,0.15)' },
        total_transactions: { border: '#06b6d4', background: 'rgba(6,182,212,0.15)' },
        revenue: { border: '#10b981', background: 'rgba(16,185,129,0.15)' },
        new_members: { border: '#8b5cf6', background: 'rgba(139,92,246,0.15)' },
        active_members: { border: '#ef4444', background: 'rgba(239,68,68,0.15)' },
        revenue_per_member: { border: '#059669', background: 'rgba(5,150,105,0.15)' },
        payment_methods: { 
            border: ['#ef4444', '#3b82f6', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#14b8a6', '#a855f7', '#eab308'],
            background: ['rgba(239,68,68,0.8)', 'rgba(59,130,246,0.8)', 'rgba(245,158,11,0.8)', 'rgba(16,185,129,0.8)', 'rgba(139,92,246,0.8)', 'rgba(236,72,153,0.8)', 'rgba(6,182,212,0.8)', 'rgba(132,204,22,0.8)', 'rgba(249,115,22,0.8)', 'rgba(20,184,166,0.8)', 'rgba(168,85,247,0.8)', 'rgba(234,179,8,0.8)']
        }
    };

    // Metric labels
    const metricLabels = {
        check_ins: 'Check-ins',
        walk_ins: 'Walk-ins',
        member_check_ins: 'Member Check-ins (Total)',
        total_transactions: 'Transactions',
        revenue: 'Revenue (₱)',
        new_members: 'New Members',
        active_members: 'Active Members',
        revenue_per_member: 'Revenue per Member (₱)',
        payment_methods: 'Count'
    };

    function fetchAndUpdateChart() {
        // Build URL with all parameters
        let url = `/metrics/api/data/?metric=${currentMetric}&period=${currentPeriod}`;
        
        // Add custom date range if set
        if (customDateFrom) {
            url += `&date_from=${customDateFrom}`;
        }
        if (customDateTo) {
            url += `&date_to=${customDateTo}`;
        }
        
        // Show loading state
        const graphContainer = document.querySelector('.graph-container');
        graphContainer.classList.add('loading');
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                updateChart(data.labels, data.data, data.scale);
                graphContainer.classList.remove('loading');
            })
            .catch(error => {
                console.error('Error fetching metrics data:', error);
                graphContainer.classList.remove('loading');
            });
    }

    function updateChart(labels, data, scale) {
        // Destroy existing chart
        if (currentChart) {
            currentChart.destroy();
        }

        const colors = colorSchemes[currentMetric];
        const isDonut = currentGraphType === 'doughnut';
        const isPieOrDonut = isDonut;

        // Configure dataset based on graph type and metric
        const isAllPeriod = currentPeriod === 'all';
        const dataset = {
            label: metricLabels[currentMetric],
            data: data,
            borderWidth: currentGraphType === 'line' ? 4 : 2,
            tension: 0.4,  // Smooth curves for all graph types
            pointRadius: (currentGraphType === 'line' || currentGraphType === 'area') ? (isAllPeriod ? 2 : 6) : 4,
            pointHoverRadius: (currentGraphType === 'line' || currentGraphType === 'area') ? (isAllPeriod ? 4 : 9) : 6,
            pointBackgroundColor: colors.border,
            pointBorderColor: '#fff',
            pointBorderWidth: currentGraphType === 'line' ? 2 : 2,
            pointHoverBackgroundColor: colors.border,
            pointHoverBorderColor: '#fff',
            pointHoverBorderWidth: 2,
            spanGaps: true  // Connect points even with gaps in data
        };

        if (isPieOrDonut) {
            // For pie/donut charts, use multiple colors for each segment
            const donutColors = [
                '#ef4444', '#3b82f6', '#f59e0b', '#10b981', 
                '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16',
                '#f97316', '#6366f1', '#14b8a6', '#a855f7'
            ];
            const donutBackgrounds = [
                'rgba(239,68,68,0.8)', 'rgba(59,130,246,0.8)', 'rgba(245,158,11,0.8)', 'rgba(16,185,129,0.8)',
                'rgba(139,92,246,0.8)', 'rgba(236,72,153,0.8)', 'rgba(6,182,212,0.8)', 'rgba(132,204,22,0.8)',
                'rgba(249,115,22,0.8)', 'rgba(99,102,241,0.8)', 'rgba(20,184,166,0.8)', 'rgba(168,85,247,0.8)'
            ];
            
            dataset.backgroundColor = donutBackgrounds.slice(0, data.length);
            dataset.borderColor = donutColors.slice(0, data.length);
            dataset.borderWidth = 2;
        } else {
            // For other charts, use single color scheme
            dataset.borderColor = colors.border;
            dataset.backgroundColor = currentGraphType === 'line' ? 'transparent' : colors.background;
            if (currentGraphType === 'area') {
                dataset.fill = true;
                dataset.backgroundColor = colors.background;
            }
        }

        // Build scales configuration with dynamic scaling
        const scalesConfig = isPieOrDonut ? {} : {
            x: {
                ticks: {
                    font: {
                        size: 14,
                        weight: '600'
                    },
                    maxRotation: 45,
                    minRotation: 0
                }
            },
            y: {
                beginAtZero: true,
                suggestedMin: scale ? scale.suggestedMin : undefined,
                suggestedMax: scale ? scale.suggestedMax : undefined,
                ticks: {
                    font: {
                        size: 15,
                        weight: '600'
                    },
                    callback: function(value) {
                        if (currentMetric === 'revenue' || currentMetric === 'revenue_per_member') {
                            return '₱' + value.toLocaleString('en-PH');
                        }
                        return value;
                    }
                }
            }
        };

        // Create new chart
        currentChart = new Chart(canvas, {
            type: currentGraphType === 'area' ? 'line' : currentGraphType,
            data: {
                labels: labels,
                datasets: [dataset]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 800,
                    easing: 'easeInOutQuart'
                },
                plugins: {
                    legend: {
                        display: isPieOrDonut,
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 14,
                                weight: '600'
                            },
                            padding: 12
                        }
                    },
                    tooltip: {
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 14
                        },
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                const value = context.parsed.y !== undefined ? context.parsed.y : context.parsed;
                                
                                if (currentMetric === 'revenue' || currentMetric === 'revenue_per_member') {
                                    label += '₱' + value.toLocaleString('en-PH', {minimumFractionDigits: 2});
                                } else {
                                    label += value;
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: scalesConfig
            }
        });
    }

    // Event listeners
    metricSelect.addEventListener('change', function() {
        currentMetric = this.value;
        
        // Auto-switch to donut chart for payment methods
        if (currentMetric === 'payment_methods' && currentGraphType !== 'doughnut') {
            currentGraphType = 'doughnut';
            graphTypeSelect.value = 'doughnut';
        }
        
        fetchAndUpdateChart();
    });

    graphTypeSelect.addEventListener('change', function() {
        currentGraphType = this.value;
        fetchAndUpdateChart();
    });

    timeframeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            timeframeBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentPeriod = this.getAttribute('data-period');
            
            // Clear custom dates when using quick periods
            customDateFrom = '';
            customDateTo = '';
            dateFrom.value = '';
            dateTo.value = '';
            
            fetchAndUpdateChart();
        });
    });

    // Date range inputs
    dateFrom.addEventListener('change', function() {
        customDateFrom = this.value;
        
        // Deactivate quick period buttons when using custom dates
        if (customDateFrom || customDateTo) {
            timeframeBtns.forEach(b => b.classList.remove('active'));
        }
        
        // Validate date range
        if (customDateFrom && customDateTo && customDateFrom > customDateTo) {
            alert('Start date cannot be after end date');
            this.value = '';
            customDateFrom = '';
            return;
        }
        
        // Only fetch if we have both dates or just one (will use defaults)
        if (customDateFrom || customDateTo) {
            fetchAndUpdateChart();
        }
    });

    dateTo.addEventListener('change', function() {
        customDateTo = this.value;
        
        // Deactivate quick period buttons when using custom dates
        if (customDateFrom || customDateTo) {
            timeframeBtns.forEach(b => b.classList.remove('active'));
        }
        
        // Validate date range
        if (customDateFrom && customDateTo && customDateFrom > customDateTo) {
            alert('Start date cannot be after end date');
            this.value = '';
            customDateTo = '';
            return;
        }
        
        // Only fetch if we have both dates or just one (will use defaults)
        if (customDateFrom || customDateTo) {
            fetchAndUpdateChart();
        }
    });

    // Clear dates button
    clearDatesBtn.addEventListener('click', function() {
        customDateFrom = '';
        customDateTo = '';
        dateFrom.value = '';
        dateTo.value = '';
        
        // Reactivate default period
        if (!document.querySelector('.timeframe-btn.active')) {
            timeframeBtns.forEach(b => b.classList.remove('active'));
            const defaultBtn = document.querySelector('[data-period="1d"]');
            if (defaultBtn) defaultBtn.classList.add('active');
            currentPeriod = '1d';
        }
        
        fetchAndUpdateChart();
    });

    // Initial load
    fetchAndUpdateChart();
});
