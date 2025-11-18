// metrics/static/metrics/js/donut_graph.js
// Chart.js Donut Graph with animated transitions and time frame selection

document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('donutGraphCanvas');
    if (!ctx) return;
    const timeFrameBtns = ctx.closest('.bar-graph-container').querySelectorAll('.bar-graph-btn');

    // Example data for different time frames
    const dataSets = {
        '1d': [30, 20, 50],
        '1w': [25, 35, 40],
        '1m': [40, 30, 30],
        '3m': [35, 25, 40],
        '6m': [20, 40, 40],
        '1y': [33, 33, 34],
        '3y': [45, 25, 30],
        'all': [50, 20, 30],
    };
    let currentPeriod = '1d';

    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['A', 'B', 'C'],
            datasets: [{
                label: 'Donut Data',
                data: dataSets[currentPeriod],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(255, 205, 86, 0.7)',
                    'rgba(54, 162, 235, 0.7)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 800,
                easing: 'easeInOutQuart',
            },
            plugins: {
                legend: { display: true },
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