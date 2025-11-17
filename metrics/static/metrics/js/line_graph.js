// metrics/static/metrics/js/line_graph.js
// Chart.js Line Graph with animated transitions and time frame selection

document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('lineGraphCanvas');
    if (!ctx) return;
    const timeFrameBtns = ctx.closest('.bar-graph-container').querySelectorAll('.bar-graph-btn');

    // Example data for different time frames
    const dataSets = {
        '1d': [12, 19, 3, 5, 2, 3, 7],
        '1w': [10, 15, 8, 12, 6, 9, 14],
        '1m': [20, 25, 18, 22, 16, 19, 24],
        '3m': [30, 35, 28, 32, 26, 29, 34],
        '6m': [40, 45, 38, 42, 36, 39, 44],
        '1y': [50, 55, 48, 52, 46, 49, 54],
        '3y': [60, 65, 58, 62, 56, 59, 64],
        'all': [70, 75, 68, 72, 66, 69, 74],
    };
    let currentPeriod = '1d';

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Line Data',
                data: dataSets[currentPeriod],
                borderColor: '#36a2eb',
                backgroundColor: 'rgba(54,162,235,0.2)',
                fill: true,
                tension: 0.4,
            }]
        },
        options: {
            responsive: true,
            animation: {
                duration: 800,
                easing: 'easeInOutQuart',
            },
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    timeFrameBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            const period = btn.getAttribute('data-period');
            if (period && dataSets[period]) {
                chart.data.datasets[0].data = dataSets[period];
                chart.update();
                currentPeriod = period;
                timeFrameBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }
        });
    });

    // Set default active
    timeFrameBtns[0].classList.add('active');
});