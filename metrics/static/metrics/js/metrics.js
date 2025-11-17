// Dynamic Metrics Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('dynamicChart');
    if (!canvas) return;

    const metricSelect = document.getElementById('metricSelect');
    const graphTypeSelect = document.getElementById('graphTypeSelect');
    const timeframeBtns = document.querySelectorAll('.timeframe-btn');

    let currentChart = null;
    let currentMetric = 'check_ins';
    let currentGraphType = 'bar';
    let currentPeriod = '1m';

    // Color schemes for different metrics
    const colorSchemes = {
        check_ins: { border: '#4a90e2', background: 'rgba(74,144,226,0.2)' },
        revenue: { border: '#2ecc71', background: 'rgba(46,204,113,0.2)' },
        new_members: { border: '#9b59b6', background: 'rgba(155,89,182,0.2)' },
        active_members: { border: '#e74c3c', background: 'rgba(231,76,60,0.2)' },
        retention_rate: { border: '#1abc9c', background: 'rgba(26,188,156,0.2)' },
        churn_rate: { border: '#e67e22', background: 'rgba(230,126,34,0.2)' },
        revenue_per_member: { border: '#27ae60', background: 'rgba(39,174,96,0.2)' },
        avg_session_duration: { border: '#8e44ad', background: 'rgba(142,68,173,0.2)' },
        payment_methods: { 
            border: ['#ff6384', '#36a2eb', '#ffcd56', '#4bc0c0', '#9966ff', '#ff9f40', '#ff99cc', '#99ccff'],
            background: ['rgba(255,99,132,0.7)', 'rgba(54,162,235,0.7)', 'rgba(255,205,86,0.7)', 'rgba(75,192,192,0.7)', 'rgba(153,102,255,0.7)', 'rgba(255,159,64,0.7)', 'rgba(255,153,204,0.7)', 'rgba(153,204,255,0.7)']
        }
    };

    // Metric labels
    const metricLabels = {
        check_ins: 'Check-ins',
        revenue: 'Revenue (₱)',
        new_members: 'New Members',
        active_members: 'Active Members',
        retention_rate: 'Retention Rate (%)',
        churn_rate: 'Churn Rate (%)',
        revenue_per_member: 'Revenue per Member (₱)',
        avg_session_duration: 'Avg Session (min)',
        payment_methods: 'Count'
    };

    function fetchAndUpdateChart() {
        const url = `/metrics/api/data/?metric=${currentMetric}&period=${currentPeriod}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                updateChart(data.labels, data.data, data.scale);
            })
            .catch(error => {
                console.error('Error fetching metrics data:', error);
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
        const dataset = {
            label: metricLabels[currentMetric],
            data: data,
            borderWidth: 2,
            tension: 0.4
        };

        if (isPieOrDonut) {
            // For pie/donut charts, use multiple colors
            dataset.backgroundColor = Array.isArray(colors.background) ? colors.background : colors.background;
            dataset.borderColor = Array.isArray(colors.border) ? colors.border : colors.border;
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
            y: {
                beginAtZero: true,
                suggestedMin: scale ? scale.suggestedMin : undefined,
                suggestedMax: scale ? scale.suggestedMax : undefined,
                ticks: {
                    callback: function(value) {
                        if (currentMetric === 'revenue' || currentMetric === 'revenue_per_member') {
                            return '₱' + value.toLocaleString('en-PH');
                        } else if (currentMetric === 'retention_rate' || currentMetric === 'churn_rate') {
                            return value + '%';
                        } else if (currentMetric === 'avg_session_duration') {
                            return value + ' min';
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
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                const value = context.parsed.y !== undefined ? context.parsed.y : context.parsed;
                                
                                if (currentMetric === 'revenue' || currentMetric === 'revenue_per_member') {
                                    label += '₱' + value.toLocaleString('en-PH', {minimumFractionDigits: 2});
                                } else if (currentMetric === 'retention_rate' || currentMetric === 'churn_rate') {
                                    label += value + '%';
                                } else if (currentMetric === 'avg_session_duration') {
                                    label += value + ' minutes';
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
            fetchAndUpdateChart();
        });
    });

    // Initial load
    fetchAndUpdateChart();
});
