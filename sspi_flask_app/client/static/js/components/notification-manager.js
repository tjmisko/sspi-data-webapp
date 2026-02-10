/**
 * NotificationManager - Global notification system
 * Replaces Flask flash messages with a cleaner, JavaScript-based notification system
 */
class NotificationManager {
    constructor() {
        this.notifications = [];
        this.history = [];
        this.nextId = 0;
    }

    /**
     * Show a notification to the user
     * @param {string} message - The message to display
     * @param {string} type - The notification type ('success', 'error', 'warning', 'info')
     * @param {number} duration - Duration in milliseconds (default: 3000, 0 = persistent)
     * @returns {Object} Notification object with id and element
     */
    show(message, type = 'info', duration = 3000) {
        const id = this.nextId++;

        const notification = document.createElement('div');
        notification.dataset.notificationId = id;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: normal;
            z-index: 10000;
            max-width: 450px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            animation: slideInRight 0.3s ease-out;
            word-wrap: break-word;
            line-height: 1.4;
            white-space: pre-line;
        `;

        // Set background color based on type
        switch(type) {
            case 'success':
                notification.style.backgroundColor = '#4CAF50';
                break;
            case 'error':
                notification.style.backgroundColor = '#f44336';
                break;
            case 'warning':
                notification.style.backgroundColor = '#ff9800';
                break;
            default:
                notification.style.backgroundColor = '#2196F3';
        }

        notification.textContent = message;

        // Add to DOM with stacking
        this._stackNotification(notification);

        const notificationObj = {
            id,
            element: notification,
            message,
            type,
            timestamp: Date.now()
        };

        this.notifications.push(notificationObj);
        this.history.push({...notificationObj, dismissed: false});

        // Auto-remove after duration (if not persistent)
        if (duration > 0) {
            setTimeout(() => {
                this.clear(id);
            }, duration);
        }

        return notificationObj;
    }

    /**
     * Stack notification with proper spacing
     * @private
     */
    _stackNotification(notification) {
        const existingNotifications = document.querySelectorAll('[data-notification-id]');
        let topOffset = 20;

        existingNotifications.forEach(existing => {
            const rect = existing.getBoundingClientRect();
            topOffset = Math.max(topOffset, rect.bottom - document.documentElement.getBoundingClientRect().top + 10);
        });

        notification.style.top = topOffset + 'px';
        document.body.appendChild(notification);
    }

    /**
     * Clear a specific notification by ID
     * @param {number} id - The notification ID
     */
    clear(id) {
        const index = this.notifications.findIndex(n => n.id === id);
        if (index === -1) return;

        const notificationObj = this.notifications[index];
        const notification = notificationObj.element;

        if (notification && notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }

        this.notifications.splice(index, 1);

        // Mark as dismissed in history
        const historyEntry = this.history.find(h => h.id === id);
        if (historyEntry) {
            historyEntry.dismissed = true;
            historyEntry.dismissedAt = Date.now();
        }

        // Restack remaining notifications
        this._restackNotifications();
    }

    /**
     * Restack all remaining notifications
     * @private
     */
    _restackNotifications() {
        setTimeout(() => {
            const existingNotifications = document.querySelectorAll('[data-notification-id]');
            let topOffset = 20;

            existingNotifications.forEach(notification => {
                notification.style.top = topOffset + 'px';
                const rect = notification.getBoundingClientRect();
                topOffset = rect.bottom - document.documentElement.getBoundingClientRect().top + 10;
            });
        }, 50);
    }

    /**
     * Clear all active notifications
     */
    clearAll() {
        const ids = this.notifications.map(n => n.id);
        ids.forEach(id => this.clear(id));
    }

    /**
     * Get notification history
     * @param {number} limit - Maximum number of history entries to return
     * @returns {Array} Array of notification history objects
     */
    getHistory(limit = 50) {
        return this.history.slice(-limit);
    }

    /**
     * Clear notification history
     */
    clearHistory() {
        this.history = [];
    }

    // Convenience methods
    success(message, duration = 3000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 4000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }
}

// Create global instance
window.notifications = new NotificationManager();
