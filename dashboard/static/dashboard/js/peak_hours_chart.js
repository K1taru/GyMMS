/**
 * Peak Hours Chart - Bar Graph Visualization
 * Shows check-in frequency for each hour (00:00 to 23:00)
 * Refreshes daily to show today's data
 */

document.addEventListener('DOMContentLoaded', function() {
    initializePeakHoursChart();
});

function initializePeakHoursChart() {
    const chartBarsContainer = document.getElementById('chartBars');
    const yAxisTicks = document.getElementById('yAxisTicks');
    const totalCheckInsEl = document.getElementById('totalCheckIns');
    const peakHourEl = document.getElementById('peakHour');
    
    if (!chartBarsContainer) {
        console.error('[PEAK HOURS] Chart container not found');
        return;
    }
    
    // Get data from Django (passed via window.peakHoursData)
    const hourlyData = window.peakHoursData || [];
    
    console.log('[PEAK HOURS] Raw data:', hourlyData);
    
    // Create array for all 24 hours (0-23)
    const allHours = Array.from({ length: 24 }, (_, i) => ({
        hour: i,
        count: 0
    }));
    
    // Populate with actual data
    hourlyData.forEach(data => {
        const hour = parseInt(data.hour);
        if (hour >= 0 && hour < 24) {
            allHours[hour].count = data.count;
        }
    });
    
    console.log('[PEAK HOURS] Processed data:', allHours);
    
    // Calculate max count for scaling - starts at 15, increments by 3 if data exceeds
    const dataMaxCount = Math.max(...allHours.map(h => h.count), 0);
    let maxCount = 15; // Start with 15
    
    // If data exceeds 15, round up to next multiple of 3
    if (dataMaxCount > 15) {
        maxCount = Math.ceil(dataMaxCount / 3) * 3;
    }
    
    const totalCheckIns = allHours.reduce((sum, h) => sum + h.count, 0);
    
    console.log('[PEAK HOURS] Data max count:', dataMaxCount);
    console.log('[PEAK HOURS] Scale max count:', maxCount);
    
    // Find peak hour - if multiple hours have the same count, use the latest one
    const peakData = allHours.reduce((max, h) => {
        if (h.count > max.count) {
            return h; // New maximum found
        } else if (h.count === max.count && h.count > 0) {
            return h.hour > max.hour ? h : max; // Same count, prefer later hour
        }
        return max;
    }, allHours[0]);
    
    // Format hour to AM/PM
    function formatHourAMPM(hour) {
        if (hour === 0) return '12:00 AM';
        if (hour === 12) return '12:00 PM';
        if (hour < 12) return `${hour}:00 AM`;
        return `${hour - 12}:00 PM`;
    }
    
    const peakHourFormatted = peakData.count > 0 
        ? `${formatHourAMPM(peakData.hour)} (${peakData.count} check-ins)`
        : 'No check-ins yet';
    
    // Update stats
    if (totalCheckInsEl) totalCheckInsEl.textContent = totalCheckIns;
    if (peakHourEl) peakHourEl.textContent = peakHourFormatted;
    
    // Generate Y-axis ticks - increments of 3 (0, 3, 6, 9, 12, 15, 18, ...)
    const yAxisHTML = [];
    const tickCount = (maxCount / 3) + 1; // Number of ticks (0, 3, 6, ..., maxCount)
    
    // Generate from 0 to max in increments of 3 (will be reversed by CSS flex-direction: column-reverse)
    for (let i = 0; i < tickCount; i++) {
        const value = i * 3;
        yAxisHTML.push(`<div class="y-axis-tick">${value}</div>`);
    }
    
    if (yAxisTicks) {
        yAxisTicks.innerHTML = yAxisHTML.join('');
    }
    
    // Generate bars for all 24 hours
    const barsHTML = allHours.map((hourData, index) => {
        const height = maxCount > 0 ? (hourData.count / maxCount * 100) : 0;
        const hasData = hourData.count > 0;
        const hourLabel = formatHourAMPM(hourData.hour);
        const tooltip = `${hourLabel} - ${hourData.count} check-in${hourData.count !== 1 ? 's' : ''}`;
        
        return `
            <div class="chart-bar ${!hasData ? 'no-data' : ''} animate" 
                 style="height: ${height}%; animation-delay: ${index * 20}ms;"
                 data-hour="${hourData.hour}"
                 data-count="${hourData.count}"
                 data-tooltip="${tooltip}">
            </div>
        `;
    }).join('');
    
    chartBarsContainer.innerHTML = barsHTML;
    
    console.log('[PEAK HOURS] Chart rendered successfully');
    console.log('[PEAK HOURS] Total check-ins:', totalCheckIns);
    console.log('[PEAK HOURS] Peak hour:', peakHourFormatted);
}

// Auto-refresh at midnight to show new day's data
function scheduleNextDayRefresh() {
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    
    const msUntilMidnight = tomorrow - now;
    
    console.log('[PEAK HOURS] Next refresh in:', Math.round(msUntilMidnight / 1000 / 60), 'minutes');
    
    setTimeout(() => {
        console.log('[PEAK HOURS] New day - refreshing page...');
        window.location.reload();
    }, msUntilMidnight);
}

// Initialize auto-refresh
scheduleNextDayRefresh();

// Optional: Expose function for manual refresh
window.refreshPeakHours = function() {
    console.log('[PEAK HOURS] Manual refresh triggered');
    initializePeakHoursChart();
};
