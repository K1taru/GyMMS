/**
 * Dashboard JavaScript - Real-time Clock and Features
 */

// Update clock every second
function updateClock() {
    const clockElement = document.getElementById('currentTime');
    if (!clockElement) return;

    const now = new Date();
    
    // Format: January 15, 2024 - 02:30 PM
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    };
    
    const formattedTime = now.toLocaleString('en-US', options).replace(',', ' -');
    clockElement.textContent = formattedTime;
}

// Initialize clock
document.addEventListener('DOMContentLoaded', () => {
    // Update immediately
    updateClock();
    
    // Update every second
    setInterval(updateClock, 1000);
    
    // Animate stat cards on load
    animateStatCards();
    
    // Setup chart animations
    animateChartBars();
    
    // Setup revenue privacy toggle
    setupRevenueToggle();
});

// Animate stat cards
function animateStatCards() {
    const statCards = document.querySelectorAll('.stat-card');
    
    statCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            
            requestAnimationFrame(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            });
        }, index * 100);
    });
}

// Animate chart bars
function animateChartBars() {
    const chartBars = document.querySelectorAll('.chart-bar');
    
    chartBars.forEach((bar, index) => {
        const finalHeight = bar.style.height;
        bar.style.height = '0%';
        
        setTimeout(() => {
            bar.style.transition = 'height 0.8s ease';
            bar.style.height = finalHeight;
        }, index * 80);
    });
}

// Revenue Privacy Toggle
function setupRevenueToggle() {
    const toggleBtn = document.getElementById('revenueToggle');
    if (!toggleBtn) return;
    
    const revenueAmount = document.querySelector('.revenue-amount');
    const revenueMonthly = document.querySelector('.revenue-monthly');
    const eyeIcon = toggleBtn.querySelector('.eye-icon');
    const eyeOffIcon = toggleBtn.querySelector('.eye-off-icon');
    
    // Always start hidden on page load
    let isHidden = true;
    
    // Get values from data attributes
    const todayValue = revenueAmount.dataset.today;
    const monthlyValue = revenueMonthly.dataset.monthly;
    
    console.log('[REVENUE TOGGLE] Today value:', todayValue);
    console.log('[REVENUE TOGGLE] Monthly value:', monthlyValue);
    
    // Format number with commas
    function formatCurrency(value) {
        const num = parseFloat(value);
        return num.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    
    // Hide revenue immediately on page load (always default to hidden)
    const todayAsterisks = '₱' + '*'.repeat(formatCurrency(todayValue).length);
    const monthlyAsterisks = '₱' + '*'.repeat(formatCurrency(monthlyValue).length);
    
    revenueAmount.textContent = todayAsterisks;
    revenueMonthly.textContent = monthlyAsterisks;
    
    // Show eye-off icon
    eyeIcon.style.display = 'none';
    eyeOffIcon.style.display = 'block';
    
    toggleBtn.addEventListener('click', () => {
        isHidden = !isHidden;
        
        if (isHidden) {
            // Hide revenue - show asterisks
            const todayAsterisks = '₱' + '*'.repeat(formatCurrency(todayValue).length);
            const monthlyAsterisks = '₱' + '*'.repeat(formatCurrency(monthlyValue).length);
            
            revenueAmount.textContent = todayAsterisks;
            revenueMonthly.textContent = monthlyAsterisks;
            
            // Swap icons
            eyeIcon.style.display = 'none';
            eyeOffIcon.style.display = 'block';
        } else {
            // Show revenue - restore values with comma formatting
            revenueAmount.textContent = '₱' + formatCurrency(todayValue);
            revenueMonthly.textContent = '₱' + formatCurrency(monthlyValue);
            
            // Swap icons
            eyeIcon.style.display = 'block';
            eyeOffIcon.style.display = 'none';
        }
        
        console.log('[REVENUE TOGGLE] Is hidden:', isHidden);
        console.log('[REVENUE TOGGLE] Today displayed:', revenueAmount.textContent);
        console.log('[REVENUE TOGGLE] Monthly displayed:', revenueMonthly.textContent);
    });
}

// Optional: Auto-refresh dashboard data (if needed)
function refreshDashboardData() {
    // This could be used to fetch updated stats via AJAX
    // For now, we'll just reload the page
    window.location.reload();
}

// Optional: Setup auto-refresh (commented out by default)
// setInterval(refreshDashboardData, 60000); // Refresh every minute
