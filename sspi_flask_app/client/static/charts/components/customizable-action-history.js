/**
 * CustomizableActionHistory - Manages action history with undo/redo and cumulative change tracking
 * - Delta-based action recording
 * - Export functionality for backend processing
 */
class CustomizableActionHistory {
    constructor(sspiInstance) {
        this.sspi = sspiInstance;
        this.actions = [];
        this.currentIndex = -1;
        this.maxHistorySize = 100;
    }
    /**
     * Record an action with both undo/redo functions AND delta information
     * @param {Object} actionConfig - Action configuration
     * @param {string} actionConfig.type - Action type (e.g., 'add-indicator', 'move-category')
     * @param {string} actionConfig.message - Human-readable description
     * @param {Object} actionConfig.delta - Delta object with change details
     * @param {Function} actionConfig.undo - Function to undo the action
     * @param {Function} actionConfig.redo - Function to redo the action
     * @returns {Object} The recorded action
     */
    recordAction(actionConfig) {
        // Validate required fields
        if (!actionConfig.type || !actionConfig.message || !actionConfig.undo || !actionConfig.redo) {
            console.error('Invalid action config:', actionConfig);
            throw new Error('Action must have type, message, undo, and redo');
        }
        const action = {
            actionId: this.generateUUID(),
            timestamp: Date.now(),
            type: actionConfig.type,
            message: actionConfig.message,
            delta: actionConfig.delta || null,
            undo: actionConfig.undo,
            redo: actionConfig.redo
        };
        if (this.currentIndex < this.actions.length - 1) {
            this.actions = this.actions.slice(0, this.currentIndex + 1);
        }
        // Add to history
        this.actions.push(action);
        this.currentIndex++;
        if (this.actions.length > this.maxHistorySize) {
            const overflow = this.actions.length - this.maxHistorySize;
            this.actions = this.actions.slice(overflow);
            this.currentIndex -= overflow;
        }
        console.log('Recorded action:', action.type, '-', action.message, '(History size:', this.actions.length, ')');
        return action;
    }

    undo() {
        if (!this.canUndo()) {
            this.sspi.showNotification('Nothing\u0020to\u0020undo', 'info', 2000);
            return false;
        }
        const action = this.actions[this.currentIndex];
        try {
            action.undo();
            this.currentIndex--;
            this.sspi.showNotification(`↶\u0020Undo:\u0020${action.message}`, 'info', 2500);
            console.log('Undid action:', action.type, '-', action.message);
            return true;
        } catch (error) {
            console.error('Error during undo:', error);
            this.sspi.showNotification('Error\u0020during\u0020undo', 'error', 3000);
            return false;
        }
    }

    redo() {
        if (!this.canRedo()) {
            this.sspi.showNotification('Nothing\u0020to\u0020redo', 'info', 2000);
            return false;
        }
        const action = this.actions[this.currentIndex + 1];
        try {
            action.redo();
            this.currentIndex++;
            this.sspi.showNotification(`↷\u0020Redo:\u0020${action.message}`, 'info', 2500);
            console.log('Redid action:', action.type, '-', action.message);
            return true;
        } catch (error) {
            console.error('Error during redo:', error);
            this.sspi.showNotification('Error\u0020during\u0020redo', 'error', 3000);
            return false;
        }
    }

    canUndo() {
        return this.currentIndex >= 0;
    }

    canRedo() {
        return this.currentIndex < this.actions.length - 1;
    }

    clear() {
        this.actions = [];
        this.currentIndex = -1;
        console.log('Cleared action history');
    }

    exportActionLog() {
        const actionList = this.actions.slice(0, this.currentIndex + 1)
        return actoionList.map(action => ({
            actionId: action.actionId,
            type: action.type,
            timestamp: action.timestamp,
            message: action.message,
            delta: action.delta
        }));
    }

    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
}
