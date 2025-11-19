/**
 * ChangesHistoryModal - Display history of changes made to SSPI structure
 *
 * Shows a chronological list of all modifications from the baseline SSPI,
 * with search, filtering, and expandable details. Supports both modal and
 * full-page rendering modes.
 */
class ChangesHistoryModal {
    /**
     * @param {Object} options - Configuration options
     * @param {Object} options.actionHistory - Reference to ActionHistory instance
     * @param {string} options.mode - Display mode: 'modal' (default) or 'page'
     * @param {HTMLElement} options.container - Container element for page mode
     */
    constructor(options = {}) {
        this.actionHistory = options.actionHistory;
        this.mode = options.mode || 'modal';
        this.container = options.container || null;
        this.modal = null;
        this.expandedItems = new Set();

        // Event handler references for cleanup
        this.escapeHandler = null;
        this.keyboardHandler = null;
        this.focusTrapHandler = null;
    }

    /**
     * Show the changes history modal or page
     */
    show() {
        if (this.mode === 'modal') {
            this.showAsModal();
        } else {
            this.showAsPage();
        }
    }

    /**
     * Show as modal overlay
     */
    showAsModal() {
        this.createModal();
        document.body.appendChild(this.modal);

        // Autofocus search input for accessibility
        const searchInput = this.modal.querySelector('#changes-search');
        if (searchInput) {
            setTimeout(() => searchInput.focus(), 100);
        }
    }

    /**
     * Show as full page
     */
    showAsPage() {
        if (!this.container) {
            console.error('Container element required for page mode');
            return;
        }

        const content = this.createModalContent();
        content.classList.remove('dataset-modal-content');
        content.classList.add('changes-page-container');

        this.container.innerHTML = '';
        this.container.appendChild(content);
        this.bindEvents(content);
    }

    /**
     * Create modal structure
     */
    createModal() {
        // Create overlay
        this.modal = document.createElement('div');
        this.modal.className = 'dataset-modal-overlay changes-modal-overlay';

        // Create content container
        const content = this.createModalContent();

        this.modal.appendChild(content);
        this.bindEvents(this.modal);
    }

    /**
     * Create modal content (header, search, filters, list)
     */
    createModalContent() {
        const content = document.createElement('div');
        content.className = 'dataset-modal-content enhanced changes-modal-content';

        // Header
        const header = this.createHeader();
        content.appendChild(header);

        // Changes list
        const listContainer = this.createListContainer();
        content.appendChild(listContainer);

        // Footer
        const footer = this.createFooter();
        content.appendChild(footer);

        return content;
    }

    /**
     * Create header with title, counter, and close button
     */
    createHeader() {
        const header = document.createElement('div');
        header.className = 'dataset-modal-header';

        const title = document.createElement('h3');
        title.className = 'dataset-modal-title';
        title.textContent = 'Changes History';

        const counter = document.createElement('div');
        counter.className = 'dataset-selection-counter';

        const changes = this.getFilteredChanges();
        const countSpan = document.createElement('span');
        countSpan.className = 'selected-count';
        countSpan.textContent = changes.length;

        const textSpan = document.createElement('span');
        textSpan.textContent = changes.length === 1 ? ' change from baseline' : ' changes from baseline';

        counter.appendChild(countSpan);
        counter.appendChild(textSpan);

        // Close button (only in modal mode)
        if (this.mode === 'modal') {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'modal-close-btn';
            closeBtn.id = 'changes-close-btn';
            closeBtn.setAttribute('aria-label', 'Close');
            closeBtn.setAttribute('tabindex', '0');
            closeBtn.innerHTML = '&times;';

            header.appendChild(title);
            header.appendChild(counter);
            header.appendChild(closeBtn);
        } else {
            header.appendChild(title);
            header.appendChild(counter);
        }

        return header;
    }

    /**
     * Create search container
     */
    createSearchContainer() {
        const container = document.createElement('div');
        container.className = 'dataset-search-container';

        const input = document.createElement('input');
        input.type = 'text';
        input.id = 'changes-search';
        input.className = 'dataset-search-input';
        input.placeholder = 'Search changes by description...';
        input.value = this.searchTerm;

        const resultsCount = document.createElement('div');
        resultsCount.className = 'search-results-count';
        resultsCount.id = 'changes-results-count';
        resultsCount.textContent = this.getResultsCountText();

        container.appendChild(input);
        container.appendChild(resultsCount);

        return container;
    }

    /**
     * Create filters container
     */
    createFiltersContainer() {
        const container = document.createElement('div');
        container.className = 'dataset-filters-container';

        const label = document.createElement('label');
        label.setAttribute('for', 'action-type-filter');
        label.className = 'visually-hidden';
        label.textContent = 'Action Type:';

        const select = document.createElement('select');
        select.id = 'action-type-filter';
        select.className = 'filter-select';

        // Action type options grouped by category
        const options = [
            { value: '', label: 'All Action Types' },
            { value: 'add-indicator', label: '➕ Add Indicator' },
            { value: 'add-category', label: '➕ Add Category' },
            { value: 'add-dataset', label: '➕ Add Dataset' },
            { value: 'remove-indicator', label: '➖ Remove Indicator' },
            { value: 'remove-category', label: '➖ Remove Category' },
            { value: 'remove-dataset', label: '➖ Remove Dataset' },
            { value: 'move-indicator', label: '↔️ Move Indicator' },
            { value: 'move-category', label: '↔️ Move Category' },
            { value: 'set-indicator-name', label: '✏️ Rename Indicator' },
            { value: 'set-category-name', label: '✏️ Rename Category' },
            { value: 'set-pillar-name', label: '✏️ Rename Pillar' },
            { value: 'set-score-function', label: '⚙️ Change Score Function' },
            { value: 'set-indicator-code', label: '🔖 Change Indicator Code' },
            { value: 'set-category-code', label: '🔖 Change Category Code' },
            { value: 'set-pillar-code', label: '🔖 Change Pillar Code' }
        ];

        options.forEach(opt => {
            const option = document.createElement('option');
            option.value = opt.value;
            option.textContent = opt.label;
            if (opt.value === this.filterType) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        container.appendChild(label);
        container.appendChild(select);

        return container;
    }

    /**
     * Create list container with changes
     */
    createListContainer() {
        const container = document.createElement('div');
        container.className = 'dataset-list-container changes-list-container';
        container.setAttribute('tabindex', '0');

        const list = document.createElement('div');
        list.id = 'changes-list';
        list.className = 'dataset-list enhanced changes-list';

        const changes = this.getFilteredChanges();

        if (changes.length === 0) {
            const emptyMsg = document.createElement('div');
            emptyMsg.className = 'changes-empty-message';
            emptyMsg.textContent = this.actionHistory.actions.length === 0
                ? 'No changes made yet.'
                : 'No changes match your search or filter.';
            list.appendChild(emptyMsg);
        } else {
            changes.forEach((action, index) => {
                const item = this.createChangeItem(action, index);
                list.appendChild(item);
            });
        }

        container.appendChild(list);
        return container;
    }

    /**
     * Create individual change item
     */
    createChangeItem(action, index) {
        const item = document.createElement('div');
        item.className = 'dataset-option enhanced compact change-item';
        item.dataset.actionId = action.actionId;
        item.dataset.actionType = action.type;

        // Header with type badge and timestamp (badge first, timestamp second)
        const header = document.createElement('div');
        header.className = 'dataset-compact-header change-item-header';

        const badge = document.createElement('span');
        badge.className = 'change-type-badge';
        badge.dataset.changeType = this.getChangeCategory(action.type);
        badge.textContent = this.formatActionType(action.type);

        const timestamp = document.createElement('div');
        timestamp.className = 'dataset-compact-code change-timestamp';
        timestamp.textContent = this.formatTimestamp(action.timestamp);

        header.appendChild(badge);
        header.appendChild(timestamp);
        item.appendChild(header);

        // Message
        const message = document.createElement('div');
        message.className = 'dataset-compact-name change-message';
        message.textContent = action.message;
        item.appendChild(message);

        // Item reference (show which item was affected)
        const itemRef = this.getItemReference(action);
        if (itemRef) {
            const refDiv = document.createElement('div');
            refDiv.className = 'dataset-compact-description change-item-reference';
            refDiv.textContent = itemRef;
            item.appendChild(refDiv);
        }

        // Delta details (expandable)
        if (action.delta && Object.keys(action.delta).length > 0) {
            const detailsContainer = this.createDetailsContainer(action);
            item.appendChild(detailsContainer);
        }

        return item;
    }

    /**
     * Create expandable details container for delta using HTML <details> element
     */
    createDetailsContainer(action) {
        // Use native HTML <details> element
        const details = document.createElement('details');
        details.className = 'change-details';
        details.dataset.actionId = action.actionId;

        // Check if this should be open by default
        const isExpanded = this.expandedItems.has(action.actionId);
        if (isExpanded) {
            details.open = true;
        }

        // Summary (the clickable toggle)
        const summary = document.createElement('summary');
        summary.className = 'change-details-summary';
        summary.textContent = 'Details';

        details.appendChild(summary);

        // Details content
        const content = document.createElement('div');
        content.className = 'change-details-content';

        // Format delta as readable key-value pairs
        const delta = action.delta;
        const dl = document.createElement('dl');
        dl.className = 'change-delta-list';

        Object.entries(delta).forEach(([key, value]) => {
            // Skip the 'type' field as it's shown in the badge
            if (key === 'type') return;

            const dt = document.createElement('dt');
            dt.textContent = this.formatDeltaKey(key);

            const dd = document.createElement('dd');
            dd.textContent = this.formatDeltaValue(key, value);

            dl.appendChild(dt);
            dl.appendChild(dd);
        });

        content.appendChild(dl);
        details.appendChild(content);

        return details;
    }

    /**
     * Create footer with actions
     */
    createFooter() {
        const footer = document.createElement('div');
        footer.className = 'changes-modal-footer';

        const exportBtn = document.createElement('button');
        exportBtn.className = 'changes-action-btn';
        exportBtn.id = 'export-changes-btn';
        exportBtn.textContent = '📥 Export Changes';
        exportBtn.title = 'Download changes as JSON';

        footer.appendChild(exportBtn);

        return footer;
    }

    /**
     * Bind event handlers
     */
    bindEvents(container) {
        // Close button (modal mode only)
        if (this.mode === 'modal') {
            const closeButton = container.querySelector('#changes-close-btn');
            if (closeButton) {
                closeButton.addEventListener('click', () => this.close());
                closeButton.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.close();
                    }
                });
            }

            // Close on overlay click
            container.addEventListener('click', (e) => {
                if (e.target === container && container.classList.contains('changes-modal-overlay')) {
                    this.close();
                }
            });

            // Close on ESC key
            this.escapeHandler = (e) => {
                if ((e.key === 'Escape' || e.keyCode === 27)) {
                    e.preventDefault();
                    this.close();
                }
            };
            document.addEventListener('keydown', this.escapeHandler);
        }

        // Track details open/close state
        container.addEventListener('toggle', (e) => {
            if (e.target.classList.contains('change-details')) {
                const actionId = e.target.dataset.actionId;
                if (e.target.open) {
                    this.expandedItems.add(actionId);
                } else {
                    this.expandedItems.delete(actionId);
                }
            }
        }, true); // Use capture to catch the event

        // Export button
        const exportBtn = container.querySelector('#export-changes-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportChanges());
        }
    }


    /**
     * Get all changes (newest first)
     */
    getFilteredChanges() {
        if (!this.actionHistory) {
            return [];
        }

        const changes = this.actionHistory.getCumulativeActions();

        // Reverse to show newest first
        return changes.reverse();
    }

    /**
     * Format timestamp as ISO date/time (YYYY-MM-DD HH:MM)
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);

        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');

        return `${year}-${month}-${day}\u0020${hours}:${minutes}`;
    }

    /**
     * Get item reference in format "Name (CODE)"
     */
    getItemReference(action) {
        const delta = action.delta;
        if (!delta) return null;

        // Try to find name and code from delta
        let name = null;
        let code = null;

        // Extract code (prefer the most specific code)
        code = delta.indicatorCode || delta.categoryCode || delta.pillarCode || delta.datasetCode;

        // For moves, use the item being moved
        if (action.type.startsWith('move-')) {
            code = delta.indicatorCode || delta.categoryCode;
        }

        // Extract name from various sources
        if (delta.to && typeof delta.to === 'string' && !delta.to.includes('Score =')) {
            name = delta.to;
        } else if (delta.name) {
            name = delta.name;
        }

        // Format as "Name (CODE)" if we have both, or just the code if no name
        if (name && code) {
            return `${name} (${code})`;
        } else if (code) {
            return `(${code})`;
        }

        return null;
    }

    /**
     * Format action type for display
     */
    formatActionType(type) {
        return type
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    /**
     * Get change category for styling
     */
    getChangeCategory(type) {
        if (type.startsWith('add-')) return 'add';
        if (type.startsWith('remove-')) return 'remove';
        if (type.startsWith('move-')) return 'move';
        if (type.startsWith('set-')) return 'rename';
        return 'other';
    }

    /**
     * Format delta key for display
     */
    formatDeltaKey(key) {
        const keyMap = {
            indicatorCode: 'Indicator Code',
            categoryCode: 'Category Code',
            pillarCode: 'Pillar Code',
            fromParentCode: 'From Category',
            toParentCode: 'To Category',
            fromPillarCode: 'From Pillar',
            toPillarCode: 'To Pillar',
            from: 'Previous Value',
            to: 'New Value',
            name: 'Name',
            scoreFunction: 'Score Function',
            datasetCode: 'Dataset Code',
            position: 'Position'
        };

        return keyMap[key] || key;
    }

    /**
     * Format delta value for display
     */
    formatDeltaValue(key, value) {
        if (value === null || value === undefined) {
            return '(none)';
        }

        if (typeof value === 'object') {
            return JSON.stringify(value, null, 2);
        }

        return String(value);
    }

    /**
     * Export changes as JSON file
     */
    exportChanges() {
        if (!this.actionHistory) {
            console.error('No action history available');
            return;
        }

        const changes = this.actionHistory.exportActionLog();
        const json = JSON.stringify(changes, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `sspi-changes-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Refresh the modal content
     */
    refresh() {
        const container = this.mode === 'modal' ? this.modal : this.container;
        if (!container) return;

        const content = container.querySelector('.changes-modal-content, .changes-page-container');
        if (!content) return;

        const newContent = this.createModalContent();
        newContent.className = content.className;

        content.replaceWith(newContent);
        this.bindEvents(this.mode === 'modal' ? this.modal : newContent);
    }

    /**
     * Close the modal
     */
    close() {
        if (this.mode !== 'modal') return;

        // Clean up event listeners
        if (this.escapeHandler) {
            document.removeEventListener('keydown', this.escapeHandler);
            this.escapeHandler = null;
        }

        if (this.keyboardHandler) {
            document.removeEventListener('keydown', this.keyboardHandler);
            this.keyboardHandler = null;
        }

        if (this.focusTrapHandler) {
            document.removeEventListener('keydown', this.focusTrapHandler);
            this.focusTrapHandler = null;
        }

        if (this.modal && this.modal.parentNode) {
            document.body.removeChild(this.modal);
        }
        this.modal = null;
    }
}

// Make available globally
window.ChangesHistoryModal = ChangesHistoryModal;
