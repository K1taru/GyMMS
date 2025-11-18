// metrics/static/metrics/js/bar_graph.js
// Requires Chart.js (add <script src="https://cdn.jsdelivr.net/npm/chart.js"></script> in metrics.html)
document.addEventListener('DOMContentLoaded', function() {
  const ctx = document.getElementById('barGraphCanvas');
  if (!ctx) return;

  // Example data, replace with AJAX/fetch for real data
  let chartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
    datasets: [
      {
        label: 'Check-ins',
        data: [120, 150, 180, 90, 200, 170, 210],
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
        borderRadius: 8,
        barPercentage: 0.7,
        categoryPercentage: 0.6,
      }
    ]
  };

  let chartOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `Check-ins: ${context.parsed.y}`;
          }
        }
      }
    },
    animation: {
      duration: 900,
      easing: 'easeOutQuart'
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#22223b', font: { weight: 'bold' } }
      },
      y: {
        beginAtZero: true,
        grid: { color: '#e0e7ef' },
        ticks: { color: '#22223b' }
      }
    }
  };

  let barChart = new Chart(ctx, {
    type: 'bar',
    data: chartData,
    options: chartOptions
  });

  // Timeframe buttons
  document.querySelectorAll('.bar-graph-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      document.querySelectorAll('.bar-graph-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      // TODO: Fetch and update chartData based on this.dataset.period
      // Example: updateChartData('1w');
    });
  });
});
