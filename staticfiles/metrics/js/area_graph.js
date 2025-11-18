// metrics/static/metrics/js/area_graph.js
// Chart.js Area Graph (line with fill) with animated transitions and time frame selection

document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('areaGraphCanvas');
    if (!ctx) return;
    const timeFrameBtns = ctx.closest('.bar-graph-container').querySelectorAll('.bar-graph-btn');

    // Example data for different time frames
    const dataSets = {
        '1d': [5, 9, 7, 8, 5, 6, 10],
        '1w': [8, 12, 10, 14, 9, 11, 13],
        '1m': [15, 18, 16, 20, 14, 17, 19],
        '3m': [22, 25, 23, 27, 21, 24, 26],
        '6m': [28, 32, 30, 34, 29, 31, 33],
        '1y': [35, 38, 36, 40, 34, 37, 39],
        '3y': [42, 45, 43, 47, 41, 44, 46],
        'all': [50, 53, 51, 55, 49, 52, 54],
    };
    let currentPeriod = '1d';

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Area Data',
                data: dataSets[currentPeriod],
                borderColor: '#4bc0c0',
                backgroundColor: 'rgba(75,192,192,0.3)',
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