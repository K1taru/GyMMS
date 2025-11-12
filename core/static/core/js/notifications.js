/**
 * Global Notification System
 * Sliding banner notifications for the entire site
 */

// Show notification banner

function showNotification(message, type = 'info', duration = 3000) {
    // Create notification container if not present
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 1.5rem;
            right: 1.5rem;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 0.5rem;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        font-weight: 600;
        max-width: 400px;
        min-width: 200px;
        word-wrap: break-word;
        opacity: 0;
        transform: translateY(-30px) scale(0.95);
        transition: opacity 0.25s, transform 0.25s;
        pointer-events: auto;
    `;
    notification.textContent = message;

    // Add to container
    container.appendChild(notification);

    // Animate in
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0) scale(1)';
    }, 10);

    // Animate out and remove
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-30px) scale(0.95)';
        setTimeout(() => {
            notification.remove();
            // Remove container if empty
            if (container.childElementCount === 0) {
                container.remove();
            }
        }, 300);
    }, duration);
}

// Make it globally available
window.showNotification = showNotification;
