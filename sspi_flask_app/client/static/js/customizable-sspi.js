// customizable-sspi.js
// SSPI Tree UI implementing full specification (three-column layout)

// ========== SECTION 1: ActionHistory Class ==========

/**
 * ActionHistory - Manages action history with undo/redo and cumulative change tracking
 *
 * Replaces UndoRedoManager with enhanced functionality:
 * - Baseline capture (default SSPI structure)
 * - Delta-based action recording
 * - Cumulative action log from baseline
 * - Export functionality for backend processing
 */
class ActionHistory {
    constructor(sspiInstance) {
        this.sspi = sspiInstance;
        this.baseline = null;              // Snapshot of default SSPI metadata
        this.actions = [];                 // Cumulative action log
        this.currentIndex = -1;            // Undo/redo pointer
        this.maxHistorySize = 100;         // Increased from 50
    }

    /**
     * Capture baseline metadata when default SSPI is loaded
     * @param {Array} metadata - Array of metadata items (SSPI, Pillars, Categories, Indicators)
     */
    captureBaseline(metadata) {
        this.baseline = JSON.parse(JSON.stringify(metadata));
        this.actions = [];
        this.currentIndex = -1;
        console.log('Captured baseline with', metadata.length, 'metadata items');
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

        // Truncate any actions after currentIndex (branching timeline)
        if (this.currentIndex < this.actions.length - 1) {
            this.actions = this.actions.slice(0, this.currentIndex + 1);
        }

        // Create action with unique ID and timestamp
        const action = {
            actionId: this.generateUUID(),
            timestamp: Date.now(),
            type: actionConfig.type,
            message: actionConfig.message,
            delta: actionConfig.delta || null,
            undo: actionConfig.undo,
            redo: actionConfig.redo
        };

        // Add to history
        this.actions.push(action);
        this.currentIndex++;

        // Enforce max size
        if (this.actions.length > this.maxHistorySize) {
            const overflow = this.actions.length - this.maxHistorySize;
            this.actions = this.actions.slice(overflow);
            this.currentIndex -= overflow;
        }

        console.log('Recorded action:', action.type, '-', action.message, '(History size:', this.actions.length, ')');
        return action;
    }

    /**
     * Undo the most recent action
     * @returns {boolean} Success status
     */
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

    /**
     * Redo the next action
     * @returns {boolean} Success status
     */
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

    /**
     * Check if undo is available
     * @returns {boolean}
     */
    canUndo() {
        return this.currentIndex >= 0;
    }

    /**
     * Check if redo is available
     * @returns {boolean}
     */
    canRedo() {
        return this.currentIndex < this.actions.length - 1;
    }

    /**
     * Get cumulative actions from baseline to current state
     * @returns {Array} Array of actions up to current index
     */
    getCumulativeActions() {
        return this.actions.slice(0, this.currentIndex + 1);
    }

    /**
     * Clear all action history
     */
    clear() {
        this.actions = [];
        this.currentIndex = -1;
        console.log('Cleared action history');
    }

    /**
     * Export action log for backend processing (without undo/redo functions)
     * @returns {Array} Array of action objects with actionId, type, timestamp, message, delta
     */
    exportActionLog() {
        return this.getCumulativeActions().map(action => ({
            actionId: action.actionId,
            type: action.type,
            timestamp: action.timestamp,
            message: action.message,
            delta: action.delta
        }));
    }

    /**
     * Get info about current history state
     * @returns {Object} History information
     */
    getInfo() {
        return {
            historySize: this.actions.length,
            currentIndex: this.currentIndex,
            canUndo: this.canUndo(),
            canRedo: this.canRedo(),
            hasBaseline: this.baseline !== null,
            baselineItems: this.baseline ? this.baseline.length : 0,
            recentActions: this.actions.slice(-5).map(a => ({
                type: a.type,
                message: a.message
            }))
        };
    }

    /**
     * Generate a UUID v4 string
     * @returns {string} UUID
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
}

class CustomizableSSPIStructure {
    constructor(parentElement, options = {}) {
        const {
            pillars = ['Sustainability', 'Market Structure', 'Public Goods'],
            autoLoad = true,
            loadingDelay = 100
        } = options;

        this.parentElement = parentElement;
        this.pillars = pillars;
        this.changeLog = [];

        this.autoLoad = autoLoad;
        this.loadingDelay = loadingDelay;

        // Cache version - increment when data structure changes
        this.CACHE_VERSION = '2.2.0'; // v2.2: Dataset details stored in separate map, not embedded in indicators
        this.unsavedChanges = false;
        this.isImporting = false; // Flag to suppress validation during bulk import
        this.draggedEl = null;
        this.origin = null;
        this.dropped = false;
        this.isLoading = false;
        this.cacheTimeout = null;
        // Initialize changelog system
        this.baselineMetadata = null;
        this.diffCache = null;
        // Visualization section state
        this.visualizationSection = null;
        this.isVisualizationOpen = false;
        this.currentChart = null;
        this.currentConfigId = null;
        // Dataset details storage (maps dataset code to full details)
        this.datasetDetails = {};
        // Initialize action history system
        this.actionHistory = new ActionHistory(this);
        this.initToolbar();
        this.initVisualizationSection();
        this.initRoot();
        this.addEventListeners();
        this.setupKeyboardShortcuts();
        this.loadConfigurationsList();
        // NOTE: Dataset details are loaded as part of default-structure API response (all_datasets field)
        // This eliminates the need for a separate API call to /api/v1/customize/datasets
        this.setupCacheSync();
        this.rigUnloadListener();
        
        // Auto-load cached modifications or default metadata if enabled
        if (this.autoLoad) {
            // Small delay to ensure DOM is ready
            setTimeout(() => {
                this.loadInitialData();
            }, this.loadingDelay);
        }
    }

    initToolbar() {
        const toolbar = document.createElement('div');
        toolbar.classList.add('sspi-toolbar');

        const importBtn = document.createElement('button');
        importBtn.textContent = 'Load Default SSPI';
        importBtn.addEventListener('click', async () => {
            try {
                this.showLoadingState('Loading default SSPI metadata...');

                // Clear ALL caches when explicitly loading default metadata
                this.clearCache();

                // Reload available datasets from server (fresh, no cache)
                await this.loadAvailableDatasets();

                const response = await this.fetch('/api/v1/customize/default-structure');
                if (response.success) {
                    console.log('Loading default SSPI metadata with', response.stats);

                    // Use datasetDetailsMap directly from backend (no transformation!)
                    if (response.datasetDetailsMap) {
                        this.datasetDetails = response.datasetDetailsMap;
                        console.log(`Loaded ${Object.keys(this.datasetDetails).length} dataset details from map`);
                    } else if (response.all_datasets && Array.isArray(response.all_datasets)) {
                        // Fallback for backwards compatibility
                        this.datasetDetails = {};
                        response.all_datasets.forEach(ds => {
                            this.datasetDetails[ds.DatasetCode] = ds;
                        });
                        console.log(`Populated ${response.all_datasets.length} dataset details from array`);
                    }

                    // Use async import for better performance with large metadata
                    await this.importDataAsync(response.metadata);

                    // Capture baseline for action history tracking
                    this.actionHistory.captureBaseline(response.metadata);

                    this.hideLoadingState();
                    this.flagUnsaved();
                } else {
                    this.hideLoadingState();
                    alert('Error loading default metadata: ' + response.error);
                }
            } catch (err) {
                this.hideLoadingState();
                console.error('Error loading default metadata:', err);
                alert('Error loading default metadata. Please try again.');
            }
        });
        this.saveButton = document.createElement('button');
        this.saveButton.textContent = 'Save';
        this.saveButton.addEventListener('click', async () => {
            await this.saveConfiguration();
        });
        const resetViewBtn = document.createElement('button');
        resetViewBtn.textContent = 'Reset View';
        resetViewBtn.title = 'Collapse all indicators, expand all categories';
        resetViewBtn.addEventListener('click', () => {
            this.resetView();
        });
        const expandAllBtn = document.createElement('button');
        expandAllBtn.textContent = 'Expand All';
        expandAllBtn.addEventListener('click', () => {
            this.expandAll();
        });

        const collapseAllBtn = document.createElement('button');
        collapseAllBtn.textContent = 'Collapse All';
        collapseAllBtn.addEventListener('click', () => {
            this.collapseAll();
        });

        const validateBtn = document.createElement('button');
        validateBtn.textContent = 'Validate';
        validateBtn.addEventListener('click', () => {
            this.showHierarchyStatus();
        });

        // View Changes button with badge
        const viewChangesBtn = document.createElement('button');
        viewChangesBtn.textContent = 'View Changes';
        viewChangesBtn.title = 'View history of all changes made to the SSPI structure';
        viewChangesBtn.id = 'view-changes-btn';
        viewChangesBtn.addEventListener('click', () => {
            this.showChangesHistory();
        });
        this.viewChangesButton = viewChangesBtn;

        this.discardButton = document.createElement('button');
        this.discardButton.textContent = 'Discard Changes';
        this.discardButton.style.opacity = '0.5';
        this.discardButton.style.cursor = 'not-allowed';
        this.discardButton.disabled = true;
        this.discardButton.addEventListener('click', async () => {
            if (this.unsavedChanges && confirm('Are you sure you want to discard all unsaved changes? This action cannot be undone.')) {
                await this.discardChanges();
            }
        });

        // Add "Score & Visualize" button
        const scoreVisualizeBtn = document.createElement('button');
        scoreVisualizeBtn.textContent = 'Score & Visualize';
        scoreVisualizeBtn.title = 'Generate scores and visualize this custom SSPI structure';
        scoreVisualizeBtn.style.backgroundColor = '#4CAF50';
        scoreVisualizeBtn.style.color = 'white';
        scoreVisualizeBtn.style.fontWeight = 'bold';
        scoreVisualizeBtn.addEventListener('click', async () => {
            await this.scoreAndVisualize();
        });

        toolbar.append(importBtn, this.saveButton, scoreVisualizeBtn, validateBtn, viewChangesBtn, this.discardButton, resetViewBtn, expandAllBtn, collapseAllBtn);
        this.parentElement.appendChild(toolbar);
    }

    async fetch(url) {
        const res = await window.fetch(url);
        if (!res.ok) throw new Error('Network response was not ok');
        return await res.json();
    }

    initRoot() {
        this.container = document.createElement('div');
        this.container.classList.add('pillars-container', 'pillars-grid');
        this.container.setAttribute('role', 'tree');
        this.pillars.forEach((name, index) => {
            const col = document.createElement('div');
            col.classList.add('pillar-column');
            col.dataset.pillar = name;
            col.setAttribute('aria-label', name + ' pillar');

            // Set default pillar codes
            const defaultCodes = ['SUS', 'MS', 'PG'];
            const defaultCode = defaultCodes[index] || 'PIL';

            const header = document.createElement('div');
            header.classList.add('customization-pillar-header', 'draggable-item');
            header.setAttribute('role', 'treeitem');
            header.dataset.type = 'pillar';
            header.innerHTML = `
                <div class="customization-pillar-header-content">
                    <div class="pillar-name" contenteditable="true" spellcheck="false" tabindex="0">${name}</div>
                    <div class="pillar-code-section">
                        <label class="code-label">Code:</label>
                        <input type="text" class="pillar-code-input" maxlength="3" placeholder="${defaultCode}"
                               pattern="[A-Z]{2,3}" title="2-3 uppercase letters required" value="${defaultCode}">
                        <span class="code-validation-message"></span>
                    </div>
                </div>
            `;
            col.appendChild(header);
            this.setupCodeValidation(header.querySelector('.pillar-code-input'), 'pillar');

            const categories = document.createElement('div');
            categories.classList.add('categories-container', 'drop-zone');
            categories.dataset.accept = 'category';
            col.appendChild(categories);

            const addCat = document.createElement('button');
            addCat.classList.add('add-category');
            addCat.textContent = '+ Add Category';
            addCat.setAttribute('aria-label', 'Add Category to ' + name);
            col.appendChild(addCat);

            this.container.appendChild(col);
        });
        this.parentElement.appendChild(this.container);
    }

    initVisualizationSection() {
        // Create the visualization section container
        this.visualizationSection = document.createElement('div');
        this.visualizationSection.classList.add('visualization-section');
        this.visualizationSection.style.display = 'none';

        // Create header
        const header = document.createElement('div');
        header.classList.add('visualization-header');

        // Collapse button (disclosure triangle on left)
        const collapseBtn = document.createElement('button');
        collapseBtn.classList.add('collapse-viz-btn');
        collapseBtn.innerHTML = '▼'; // Down arrow, will rotate when collapsed
        collapseBtn.title = 'Toggle visualization';
        collapseBtn.setAttribute('aria-label', 'Toggle visualization');
        collapseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleVisualizationCollapse();
        });

        const titleContainer = document.createElement('div');
        titleContainer.classList.add('visualization-title');
        titleContainer.innerHTML = `<h2>Scored Results</h2>`;

        const controls = document.createElement('div');
        controls.classList.add('visualization-controls');

        // Refresh button
        const refreshBtn = document.createElement('button');
        refreshBtn.classList.add('refresh-viz-btn');
        refreshBtn.textContent = 'Refresh';
        refreshBtn.title = 'Re-score with current structure';
        refreshBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.refreshVisualization();
        });

        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.classList.add('close-viz-btn');
        closeBtn.textContent = '✕';
        closeBtn.title = 'Close visualization';
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.closeVisualization();
        });

        controls.append(refreshBtn, closeBtn);
        header.append(collapseBtn, titleContainer, controls);

        // Make header clickable to toggle collapse (except when clicking buttons)
        header.addEventListener('click', (e) => {
            // Only toggle if clicking header itself, not the control buttons
            if (!e.target.closest('.visualization-controls')) {
                this.toggleVisualizationCollapse();
            }
        });

        // Create chart container
        const chartContainer = document.createElement('div');
        chartContainer.classList.add('visualization-chart-container');

        this.visualizationSection.append(header, chartContainer);
        this.parentElement.appendChild(this.visualizationSection);
    }

    addEventListeners() {
        // Pillar rename
        this.container.querySelectorAll('.customization-pillar-header').forEach(h =>
            h.addEventListener('keydown', e => {
                if (e.key === 'Enter') { e.preventDefault(); h.blur(); }
            })
        );

        // Collapse toggle buttons
        this.container.addEventListener('click', e => {
            const toggleBtn = e.target.closest('.collapse-toggle-btn');
            if (toggleBtn) {
                e.preventDefault();
                e.stopPropagation();
                this.handleToggle(toggleBtn);
                return;
            }
        });

        // Add Category / Indicator
        this.container.addEventListener('click', e => {
            if (e.target.classList.contains('add-category')) {
                const zone = e.target.previousElementSibling;
                const cat = this.createCategoryElement();
                zone.appendChild(cat);
                this.validate(zone);
                this.updateHierarchyOnAdd(cat, 'category');
            }
            if (e.target.classList.contains('add-indicator')) {
                // Find the indicators container (either directly previous sibling or within category-content)
                let list = e.target.previousElementSibling;
                if (!list || !list.classList.contains('indicators-container')) {
                    list = e.target.parentElement.querySelector('.indicators-container');
                }
                if (list) {
                    this.showIndicatorSelectionMenu(list);
                }
            }
        });

        // Drag & Drop with preview clone
        this.container.addEventListener('dragstart', e => {
            // Only allow dragging from headers (category-header or indicator-header)
            // Since only headers have draggable="true", this should be the case
            const isDraggingFromHeader = e.target.closest('.customization-category-header') ||
                                        e.target.closest('.customization-indicator-header');

            if (!isDraggingFromHeader) {
                e.preventDefault();
                return;
            }

            // Find the parent draggable item (category-box or indicator-card)
            const el = e.target.closest('.draggable-item');
            if (!el) return;

            this.draggedEl = el;
            this.origin = { parent: el.parentNode, next: el.nextSibling };
            this.dropped = false;

            // Check if element is expanded and store state
            const collapsibleEl = el.querySelector('[data-expanded]');
            this.wasExpanded = collapsibleEl && collapsibleEl.dataset.expanded === 'true';

            // Collapse element if expanded (for smoother dragging)
            if (this.wasExpanded && collapsibleEl) {
                collapsibleEl.dataset.expanded = 'false';
            }

            // Add dragging class (makes original invisible via opacity: 0)
            el.classList.add('dragging');

            // Create and style the drag ghost
            const clone = el.cloneNode(true);
            clone.style.position = 'absolute';
            clone.style.top = '-9999px';
            clone.style.left = '-9999px';
            clone.classList.add('drag-ghost');
            clone.classList.remove('dragging'); // Remove dragging class from clone
            document.body.appendChild(clone);

            const rect = el.getBoundingClientRect();
            e.dataTransfer.setDragImage(clone, rect.width/2, rect.height/2);

            // Keep clone a bit longer to ensure proper rendering
            setTimeout(() => {
                if (clone.parentNode) {
                    document.body.removeChild(clone);
                }
            }, 50);

            if (!el.id) el.id = `id-${Math.random().toString(36).substr(2,9)}`;
            e.dataTransfer.setData('text/plain', el.id);
            e.dataTransfer.effectAllowed = 'move';
        });

        this.container.addEventListener('dragend', () => {
            if (!this.dropped && this.origin && this.draggedEl) {
                this.origin.parent.insertBefore(this.draggedEl, this.origin.next);
            }

            // Re-expand element if it was previously expanded
            if (this.draggedEl && this.wasExpanded) {
                const collapsibleEl = this.draggedEl.querySelector('[data-expanded]');
                if (collapsibleEl) {
                    // Small delay to allow smooth transition after drop
                    setTimeout(() => {
                        collapsibleEl.dataset.expanded = 'true';
                    }, 100);
                }
            }

            if (this.draggedEl) this.draggedEl.classList.remove('dragging');
            this.draggedEl = null;
            this.origin = null;
            this.dropped = false;
            this.wasExpanded = false;
            this.clearIndicators();
        });

        this.container.addEventListener('dragover', e => {
            const z = e.target.closest('.drop-zone');
            if (!z || !this.draggedEl) return;
            e.preventDefault();
            z.classList.add('drag-over');
            this.clearIndicators(z);

            // Get all draggable items in this drop zone (excluding the dragged element)
            const items = Array.from(z.querySelectorAll('.draggable-item')).filter(item => item !== this.draggedEl);

            if (items.length === 0) {
                // Empty drop zone - show indicator at the top
                const indicator = document.createElement('div');
                indicator.className = 'insertion-indicator';
                z.insertBefore(indicator, z.firstChild);
            } else {
                // Find the correct insertion point based on mouse Y position
                let insertBeforeItem = null;

                for (let i = 0; i < items.length; i++) {
                    const item = items[i];
                    const rect = item.getBoundingClientRect();
                    const itemMiddle = rect.top + rect.height / 2;

                    if (e.clientY < itemMiddle) {
                        // Mouse is above the middle of this item
                        insertBeforeItem = item;
                        break;
                    }
                }

                // Create and insert the indicator
                const indicator = document.createElement('div');
                indicator.className = 'insertion-indicator';

                if (insertBeforeItem) {
                    // Insert before the found item (could be at top or middle)
                    z.insertBefore(indicator, insertBeforeItem);
                } else {
                    // Mouse is below all items - insert at end
                    z.appendChild(indicator);
                }
            }
        });

        this.container.addEventListener('dragleave', e => {
            const z = e.target.closest('.drop-zone');
            if (z) {
                z.classList.remove('drag-over');
                this.clearIndicators(z);
            }
        });

        this.container.addEventListener('drop', e => {
            const z = e.target.closest('.drop-zone');
            if (!z || !this.draggedEl) return;
            e.preventDefault();
            z.classList.remove('drag-over');

            // Capture state for undo/redo
            const movedElement = this.draggedEl;
            const fromParent = this.origin.parent;
            const fromNextSibling = this.origin.next;
            let toNextSibling = null;

            const indicator = z.querySelector('.insertion-indicator');
            if (indicator) {
                toNextSibling = indicator;
                z.insertBefore(this.draggedEl, indicator);
                indicator.remove();
            } else if (z.dataset.accept === this.draggedEl.dataset.type) {
                z.appendChild(this.draggedEl);
                toNextSibling = null;
            }

            const toParent = z;

            this.dropped = true;
            this.draggedEl.classList.remove('dragging');

            // Re-expand element if it was previously expanded
            if (this.wasExpanded) {
                const collapsibleEl = this.draggedEl.querySelector('[data-expanded]');
                if (collapsibleEl) {
                    // Small delay to allow smooth transition after drop
                    setTimeout(() => {
                        collapsibleEl.dataset.expanded = 'true';
                    }, 100);
                }
            }

            this.validate(z);
            this.flagUnsaved();
            this.markInvalidIndicatorPlacements();
            this.markInvalidNestedCategories();
            const order = Array.from(z.children).map(c => c.id);
            console.log('New order:', order);

            // Record the move action with proper action type
            const elementType = movedElement.dataset.type || 'item';
            const itemType = movedElement.dataset.itemType;
            const elementName = this.getElementName(movedElement);
            const fromLocation = this.getLocationName(fromParent);
            const toLocation = this.getLocationName(toParent);

            // Determine action type based on item type
            let actionType = 'move'; // fallback for unknown types
            if (itemType === 'Indicator') {
                actionType = 'move-indicator';
            } else if (itemType === 'Category') {
                actionType = 'move-category';
            }

            // Create delta with proper structure
            const delta = {
                type: actionType,
                itemType: itemType
            };

            // Add type-specific delta fields
            if (itemType === 'Indicator') {
                const indicatorCode = movedElement.dataset.indicatorCode;
                const fromParentCode = this.getParentCode(movedElement) || fromLocation;
                const toParentCode = toLocation; // Will be set after move completes

                delta.indicatorCode = indicatorCode;
                delta.fromParentCode = fromParentCode;
                delta.toParentCode = toParentCode;
            } else if (itemType === 'Category') {
                const categoryCode = movedElement.dataset.categoryCode;
                const fromPillarCode = fromLocation;
                const toPillarCode = toLocation;

                delta.categoryCode = categoryCode;
                delta.fromPillarCode = fromPillarCode;
                delta.toPillarCode = toPillarCode;
            }

            this.actionHistory.recordAction({
                type: actionType,
                message: `Moved\u0020${elementType}\u0020"${elementName}"\u0020from\u0020${fromLocation}\u0020to\u0020${toLocation}`,
                delta: delta,
                undo: () => {
                    // Move it back to original position
                    if (fromNextSibling && fromNextSibling.parentNode) {
                        fromParent.insertBefore(movedElement, fromNextSibling);
                    } else {
                        fromParent.appendChild(movedElement);
                    }
                    this.validate(fromParent);
                    this.validate(toParent);
                    this.markInvalidIndicatorPlacements();
                    this.markInvalidNestedCategories();
                    this.flagUnsaved();
                },
                redo: () => {
                    // Move it to the new position
                    if (toNextSibling && toNextSibling.parentNode) {
                        toParent.insertBefore(movedElement, toNextSibling);
                    } else {
                        toParent.appendChild(movedElement);
                    }
                    this.validate(fromParent);
                    this.validate(toParent);
                    this.markInvalidIndicatorPlacements();
                    this.markInvalidNestedCategories();
                    this.flagUnsaved();
                }
            });
        });

        // Prevent contenteditable elements from accepting drops during drag operations
        this.container.addEventListener('dragover', e => {
            const contentEditableEl = e.target.closest('[contenteditable="true"]');
            if (contentEditableEl && this.draggedEl) {
                // Prevent contenteditable from becoming a drop target
                e.stopPropagation();
            }
        }, true); // Use capture phase to intercept before other handlers

        this.container.addEventListener('drop', e => {
            const contentEditableEl = e.target.closest('[contenteditable="true"]');
            if (contentEditableEl && this.draggedEl) {
                // Prevent text insertion into contenteditable elements
                e.preventDefault();
                e.stopPropagation();
            }
        }, true); // Use capture phase to intercept before other handlers

        // Context menu & keyboard
        this.container.addEventListener('contextmenu', e => {
            // Check for dataset first (highest priority)
            const datasetItem = e.target.closest('.dataset-item');
            if (datasetItem) {
                e.preventDefault();
                e.stopPropagation();
                this.showContextMenu(e.pageX, e.pageY, datasetItem);
                return;
            }

            // Check for draggable items (indicators, categories, pillars)
            const draggableItem = e.target.closest('.draggable-item');
            if (!draggableItem) return;

            // Don't show indicator menu if clicking inside dataset selection area
            const isInDatasetArea = e.target.closest('.selected-datasets, .dataset-selection');
            if (isInDatasetArea) return;

            e.preventDefault();
            this.showContextMenu(e.pageX, e.pageY, draggableItem);
        });
        this.container.addEventListener('keydown', e => {
            if ((e.key === 'ContextMenu' || (e.shiftKey && e.key === 'F10')) && e.target.closest('.draggable-item')) {
                e.preventDefault(); const r = e.target.getBoundingClientRect();
                this.showContextMenu(r.right, r.bottom, e.target);
            }
        });

        // Indicator name placeholder clearing
        this.container.addEventListener('focus', e => {
            if (e.target.classList.contains('indicator-name')) {
                const indicatorName = e.target;
                if (indicatorName.textContent.trim() === 'New Indicator') {
                    indicatorName.textContent = '';
                }
            }
        }, true);

        this.container.addEventListener('blur', e => {
            if (e.target.classList.contains('indicator-name')) {
                const indicatorName = e.target;
                if (indicatorName.textContent.trim() === '') {
                    indicatorName.textContent = 'New Indicator';
                }
            }
        }, true);

        // Track contenteditable changes for undo/redo
        let editingElement = null;
        let originalValue = null;

        this.container.addEventListener('focus', e => {
            const editableElement = e.target;
            if (editableElement.isContentEditable &&
                (editableElement.classList.contains('indicator-name') ||
                 editableElement.classList.contains('customization-category-header-title') ||
                 editableElement.classList.contains('pillar-name') ||
                 editableElement.classList.contains('editable-score-function'))) {
                editingElement = editableElement;
                originalValue = editableElement.textContent.trim();
            }
        }, true);

        this.container.addEventListener('blur', e => {
            const editableElement = e.target;
            if (editableElement === editingElement && originalValue !== null) {
                const newValue = editableElement.textContent.trim();

                // Only record if the value actually changed and it's not empty
                if (newValue !== originalValue && newValue !== '' && originalValue !== '') {
                    // IMPORTANT: Create local copies to capture in closures
                    // The outer originalValue/newValue are shared and will be overwritten
                    const capturedOriginalValue = originalValue;
                    const capturedNewValue = newValue;

                    let elementType, actionType, itemCode, message;

                    // Determine element type and action
                    if (editableElement.classList.contains('indicator-name')) {
                        elementType = 'indicator';
                        actionType = 'set-indicator-name';
                        const indicatorCard = editableElement.closest('[data-indicator-code]');
                        itemCode = indicatorCard?.dataset.indicatorCode;
                        message = `Changed\u0020indicator\u0020name\u0020from\u0020"${capturedOriginalValue}"\u0020to\u0020"${capturedNewValue}"`;
                    } else if (editableElement.classList.contains('customization-category-header-title')) {
                        elementType = 'category';
                        actionType = 'set-category-name';
                        const categoryBox = editableElement.closest('[data-category-code]');
                        itemCode = categoryBox?.dataset.categoryCode;
                        message = `Changed\u0020category\u0020name\u0020from\u0020"${capturedOriginalValue}"\u0020to\u0020"${capturedNewValue}"`;
                    } else if (editableElement.classList.contains('pillar-name')) {
                        elementType = 'pillar';
                        actionType = 'set-pillar-name';
                        const pillarCol = editableElement.closest('[data-pillar-code]');
                        itemCode = pillarCol?.dataset.pillarCode;
                        message = `Changed\u0020pillar\u0020name\u0020from\u0020"${capturedOriginalValue}"\u0020to\u0020"${capturedNewValue}"`;
                    } else if (editableElement.classList.contains('editable-score-function')) {
                        elementType = 'score-function';
                        actionType = 'set-score-function';
                        const indicatorCard = editableElement.closest('[data-indicator-code]');
                        itemCode = indicatorCard?.dataset.indicatorCode;
                        message = `Changed\u0020score\u0020function\u0020for\u0020indicator\u0020${itemCode || 'unknown'}`;
                        console.log('[Score Function Edit] Recording action:', {
                            itemCode,
                            indicatorId: indicatorCard?.id,
                            capturedOriginalValue,
                            capturedNewValue,
                            elementExists: !!editableElement
                        });
                    } else {
                        elementType = 'item';
                        actionType = 'rename';
                        itemCode = null;
                        message = `Renamed\u0020${elementType}\u0020from\u0020"${capturedOriginalValue}"\u0020to\u0020"${capturedNewValue}"`;
                    }

                    // Create delta with proper structure
                    const delta = {
                        type: actionType,
                        from: capturedOriginalValue,
                        to: capturedNewValue
                    };

                    // Add code-specific fields
                    if (elementType === 'indicator' && itemCode) {
                        delta.indicatorCode = itemCode;
                    } else if (elementType === 'category' && itemCode) {
                        delta.categoryCode = itemCode;
                    } else if (elementType === 'pillar' && itemCode) {
                        delta.pillarCode = itemCode;
                    } else if (elementType === 'score-function' && itemCode) {
                        delta.indicatorCode = itemCode;
                        delta.scoreFunction = capturedNewValue; // Include the new score function
                    }

                    // Create undo/redo functions that find elements by code for reliability
                    let undoFn, redoFn;

                    if (elementType === 'score-function') {
                        // Score function: find by indicator code (if available), otherwise use element ID
                        const indicatorCard = editableElement.closest('[data-indicator-code]');

                        // Ensure indicator has an ID for fallback
                        if (!indicatorCard.id) {
                            indicatorCard.id = `indicator-${Math.random().toString(36).substr(2,9)}`;
                        }
                        const elementId = indicatorCard.id;

                        console.log('[Score Function] Setup undo/redo:', {
                            itemCode,
                            elementId,
                            hasCode: !!itemCode,
                            hasId: !!elementId
                        });

                        undoFn = () => {
                            console.log('[Score Function UNDO] Starting:', {
                                itemCode,
                                elementId,
                                capturedOriginalValue
                            });

                            let indicator;
                            if (itemCode) {
                                // Try finding by code first
                                indicator = this.findElementByCode(itemCode, 'Indicator');
                                console.log('[Score Function UNDO] Found by code:', !!indicator);
                            }
                            if (!indicator && elementId) {
                                // Fallback to finding by ID
                                indicator = document.getElementById(elementId);
                                console.log('[Score Function UNDO] Found by ID:', !!indicator);
                            }

                            const scoreFn = indicator?.querySelector('.editable-score-function');
                            console.log('[Score Function UNDO] Found scoreFn element:', !!scoreFn);

                            if (scoreFn) {
                                console.log('[Score Function UNDO] Setting textContent to:', capturedOriginalValue);
                                scoreFn.textContent = capturedOriginalValue;
                                console.log('[Score Function UNDO] After set, textContent is:', scoreFn.textContent);
                            } else {
                                console.warn('[Score Function UNDO] Could not find score function element!');
                            }
                            this.flagUnsaved();
                        };
                        redoFn = () => {
                            console.log('[Score Function REDO] Starting:', {
                                itemCode,
                                elementId,
                                capturedNewValue
                            });

                            let indicator;
                            if (itemCode) {
                                indicator = this.findElementByCode(itemCode, 'Indicator');
                                console.log('[Score Function REDO] Found by code:', !!indicator);
                            }
                            if (!indicator && elementId) {
                                indicator = document.getElementById(elementId);
                                console.log('[Score Function REDO] Found by ID:', !!indicator);
                            }

                            const scoreFn = indicator?.querySelector('.editable-score-function');
                            console.log('[Score Function REDO] Found scoreFn element:', !!scoreFn);

                            if (scoreFn) {
                                console.log('[Score Function REDO] Setting textContent to:', capturedNewValue);
                                scoreFn.textContent = capturedNewValue;
                                console.log('[Score Function REDO] After set, textContent is:', scoreFn.textContent);
                            } else {
                                console.warn('[Score Function REDO] Could not find score function element!');
                            }
                            this.flagUnsaved();
                        };
                    } else if (elementType === 'indicator') {
                        // Indicator name: find by code (if available), otherwise use element ID
                        const indicatorCard = editableElement.closest('[data-indicator-code]');
                        if (!indicatorCard.id) {
                            indicatorCard.id = `indicator-${Math.random().toString(36).substr(2,9)}`;
                        }
                        const elementId = indicatorCard.id;

                        undoFn = () => {
                            let indicator;
                            if (itemCode) {
                                indicator = this.findElementByCode(itemCode, 'Indicator');
                            }
                            if (!indicator && elementId) {
                                indicator = document.getElementById(elementId);
                            }
                            const nameEl = indicator?.querySelector('.indicator-name');
                            if (nameEl) nameEl.textContent = capturedOriginalValue;
                            this.flagUnsaved();
                        };
                        redoFn = () => {
                            let indicator;
                            if (itemCode) {
                                indicator = this.findElementByCode(itemCode, 'Indicator');
                            }
                            if (!indicator && elementId) {
                                indicator = document.getElementById(elementId);
                            }
                            const nameEl = indicator?.querySelector('.indicator-name');
                            if (nameEl) nameEl.textContent = capturedNewValue;
                            this.flagUnsaved();
                        };
                    } else if (elementType === 'category') {
                        // Category name: find by code (if available), otherwise use element ID
                        const categoryBox = editableElement.closest('[data-category-code]');
                        if (!categoryBox.id) {
                            categoryBox.id = `category-${Math.random().toString(36).substr(2,9)}`;
                        }
                        const elementId = categoryBox.id;

                        undoFn = () => {
                            let category;
                            if (itemCode) {
                                category = this.findElementByCode(itemCode, 'Category');
                            }
                            if (!category && elementId) {
                                category = document.getElementById(elementId);
                            }
                            const nameEl = category?.querySelector('.customization-category-header-title');
                            if (nameEl) nameEl.textContent = capturedOriginalValue;
                            this.flagUnsaved();
                        };
                        redoFn = () => {
                            let category;
                            if (itemCode) {
                                category = this.findElementByCode(itemCode, 'Category');
                            }
                            if (!category && elementId) {
                                category = document.getElementById(elementId);
                            }
                            const nameEl = category?.querySelector('.customization-category-header-title');
                            if (nameEl) nameEl.textContent = capturedNewValue;
                            this.flagUnsaved();
                        };
                    } else if (elementType === 'pillar' && itemCode) {
                        // Pillar name: find by code (pillar codes should always be set)
                        undoFn = () => {
                            const pillar = this.findElementByCode(itemCode, 'Pillar');
                            const nameEl = pillar?.querySelector('.pillar-name');
                            if (nameEl) nameEl.textContent = capturedOriginalValue;
                            this.flagUnsaved();
                        };
                        redoFn = () => {
                            const pillar = this.findElementByCode(itemCode, 'Pillar');
                            const nameEl = pillar?.querySelector('.pillar-name');
                            if (nameEl) nameEl.textContent = capturedNewValue;
                            this.flagUnsaved();
                        };
                    } else {
                        // Fallback: direct element reference (less reliable)
                        undoFn = () => {
                            editableElement.textContent = capturedOriginalValue;
                            this.flagUnsaved();
                        };
                        redoFn = () => {
                            editableElement.textContent = capturedNewValue;
                            this.flagUnsaved();
                        };
                    }

                    this.actionHistory.recordAction({
                        type: actionType,
                        message: message,
                        delta: delta,
                        undo: undoFn,
                        redo: redoFn
                    });

                    // Flag unsaved to trigger cache update
                    this.flagUnsaved();
                }

                editingElement = null;
                originalValue = null;
            }
        }, true);

        // Double-click to select all text in contenteditable fields
        this.container.addEventListener('dblclick', e => {
            const editableElement = e.target;
            if (editableElement.isContentEditable &&
                (editableElement.classList.contains('indicator-name') ||
                 editableElement.classList.contains('customization-category-header-title') ||
                 editableElement.classList.contains('pillar-name'))) {

                e.preventDefault();

                // Select all text in the element
                const range = document.createRange();
                range.selectNodeContents(editableElement);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
            }
        }, true);
    }

    setupKeyboardShortcuts() {
        // Set up keyboard shortcuts for undo/redo
        document.addEventListener('keydown', (e) => {
            // Check if we're in an input field or contenteditable element
            const isInInput = e.target.tagName === 'INPUT' ||
                            e.target.tagName === 'TEXTAREA' ||
                            e.target.isContentEditable;

            // Undo: Ctrl+Z (Windows/Linux) or Cmd+Z (Mac)
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey && !isInInput) {
                e.preventDefault();
                this.actionHistory.undo();
            }

            // Redo: Ctrl+Y or Ctrl+Shift+Z (Windows/Linux) or Cmd+Y or Cmd+Shift+Z (Mac)
            if ((((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'z') ||
                 ((e.ctrlKey || e.metaKey) && e.key === 'y')) && !isInInput) {
                e.preventDefault();
                this.actionHistory.redo();
            }
        });

        console.log('Keyboard shortcuts registered: Ctrl+Z (undo), Ctrl+Y or Ctrl+Shift+Z (redo)');
    }

    flagUnsaved() {
        this.saveButton.classList.add('unsaved-changes');
        this.unsavedChanges = true;
        
        // Enable the discard button
        this.discardButton.disabled = false;
        this.discardButton.style.opacity = '1';
        this.discardButton.style.cursor = 'pointer';
        
        // Cache the current state with debouncing
        this.debouncedCacheState();
    }
    
    clearUnsavedState() {
        this.unsavedChanges = false;
        this.saveButton.classList.remove('unsaved-changes');
        
        // Disable the discard button
        this.discardButton.disabled = true;
        this.discardButton.style.opacity = '0.5';
        this.discardButton.style.cursor = 'not-allowed';
    }
    
    setUnsavedState(hasChanges) {
        this.unsavedChanges = hasChanges;
        if (hasChanges) {
            this.saveButton.classList.add('unsaved-changes');
            this.discardButton.disabled = false;
            this.discardButton.style.opacity = '1';
            this.discardButton.style.cursor = 'pointer';
        } else {
            this.clearUnsavedState();
        }
    }

    clearIndicators(scope) {
        const parent = scope || this.container;
        parent.querySelectorAll('.insertion-indicator').forEach(node => node.remove());
    }

    // ========== SECTION 3: Helper Methods ==========

    /**
     * Find element by code using data attributes
     * @param {string} itemCode - The item code to search for
     * @param {string} itemType - The item type ('Indicator', 'Category', or 'Pillar')
     * @returns {HTMLElement|null} The found element or null
     */
    findElementByCode(itemCode, itemType) {
        if (!itemCode || !itemType) {
            console.warn('findElementByCode: itemCode and itemType are required');
            return null;
        }

        const selectors = {
            'Indicator': `[data-indicator-code="${itemCode}"]`,
            'Category': `[data-category-code="${itemCode}"]`,
            'Pillar': `[data-pillar-code="${itemCode}"]`
        };

        const selector = selectors[itemType];
        if (!selector) {
            console.warn('findElementByCode: Unknown itemType:', itemType);
            return null;
        }

        return this.container.querySelector(selector);
    }

    /**
     * Get parent code from element using DOM traversal
     * @param {HTMLElement} element - The element to find parent for
     * @returns {string|null} The parent code or null
     */
    getParentCode(element) {
        if (!element) return null;

        // For category: traverse to parent pillar
        if (element.dataset.itemType === 'Category') {
            const pillarCol = element.closest('[data-pillar-code]');
            return pillarCol?.dataset.pillarCode || null;
        }

        // For indicator: traverse to parent category or pillar
        if (element.dataset.itemType === 'Indicator') {
            const parent = element.closest('[data-category-code], [data-pillar-code]');
            return parent?.dataset.categoryCode || parent?.dataset.pillarCode || null;
        }

        return null;
    }

    /**
     * Get parent type from element using DOM traversal
     * @param {HTMLElement} element - The element to find parent type for
     * @returns {string|null} The parent type ('Pillar' or 'Category') or null
     */
    getParentType(element) {
        if (!element) return null;

        // For category: parent is always pillar
        if (element.dataset.itemType === 'Category') {
            return 'Pillar';
        }

        // For indicator: parent is category or pillar
        if (element.dataset.itemType === 'Indicator') {
            const parent = element.closest('[data-category-code], [data-pillar-code]');
            return parent?.dataset.itemType || null;
        }

        return null;
    }

    /**
     * Get item type from element data attribute
     * @param {HTMLElement} element - The element
     * @returns {string|null} The item type or null
     */
    getItemType(element) {
        return element?.dataset.itemType || null;
    }

    /**
     * Get position of element in parent's children of same type
     * @param {HTMLElement} element - The element
     * @returns {number} The zero-based index, or -1 if not found
     */
    getPositionInParent(element) {
        if (!element) return -1;

        const parent = element.parentElement;
        if (!parent) return -1;

        const itemType = element.dataset.itemType;
        const siblings = Array.from(parent.children)
            .filter(el => el.dataset.itemType === itemType);

        return siblings.indexOf(element);
    }

    /**
     * Update element's code data attributes when code changes
     * @param {HTMLElement} element - The element to update
     * @param {string} newCode - The new code value
     */
    updateElementCode(element, newCode) {
        if (!element || !newCode) return;

        const itemType = element.dataset.itemType;
        element.dataset.itemCode = newCode;

        if (itemType === 'Indicator') {
            element.dataset.indicatorCode = newCode;
        } else if (itemType === 'Category') {
            element.dataset.categoryCode = newCode;
        } else if (itemType === 'Pillar') {
            element.dataset.pillarCode = newCode;
        }
    }

    // ========== SECTION 4: API Methods - Indicators ==========

    /**
     * Set score function for an indicator
     * @param {string} indicatorCode - The indicator code
     * @param {Object} options - Options object
     * @param {string} options.scoreFunction - The new score function
     * @returns {Object} Result with success status and action
     */
    setScoreFunction(indicatorCode, { scoreFunction } = {}) {
        // Validate inputs
        if (!indicatorCode) {
            return { success: false, error: 'Indicator code is required' };
        }
        if (!scoreFunction) {
            return { success: false, error: 'Score function is required' };
        }

        // Find indicator element
        const indicatorEl = this.findElementByCode(indicatorCode, 'Indicator');
        if (!indicatorEl) {
            return { success: false, error: `Indicator ${indicatorCode} not found` };
        }

        // Find score function element
        const scoreFunctionEl = indicatorEl.querySelector('.editable-score-function');
        if (!scoreFunctionEl) {
            return { success: false, error: 'Score function element not found' };
        }

        // Capture old value
        const oldScoreFunction = scoreFunctionEl.textContent;

        // Don't record if no change
        if (oldScoreFunction === scoreFunction) {
            return { success: true, message: 'No change needed' };
        }

        // Apply change
        scoreFunctionEl.textContent = scoreFunction;

        // Record action
        const action = this.actionHistory.recordAction({
            type: 'set-score-function',
            message: `Updated score function for indicator "${indicatorCode}"`,
            delta: {
                type: 'set-score-function',
                indicatorCode: indicatorCode,
                from: oldScoreFunction,
                to: scoreFunction
            },
            undo: () => {
                scoreFunctionEl.textContent = oldScoreFunction;
                this.validate();
            },
            redo: () => {
                scoreFunctionEl.textContent = scoreFunction;
                this.validate();
            }
        });

        // Flag unsaved and validate
        this.flagUnsaved();
        this.validate();

        return { success: true, action: action };
    }

    /**
     * Set code for an indicator
     * @param {HTMLElement} indicatorElement - The indicator element
     * @param {Object} options - Options object
     * @param {string} options.newCode - The new code value
     * @returns {Object} Result with success status and action
     */
    setIndicatorCode(indicatorElement, { newCode } = {}) {
        // Validate element
        if (!(indicatorElement instanceof HTMLElement)) {
            return { success: false, error: 'Indicator element is required' };
        }

        // Validate new code
        if (!newCode) {
            return { success: false, error: 'New code is required' };
        }

        // Validate code format
        if (!this.validateCode(newCode, 'indicator')) {
            return { success: false, error: 'Invalid indicator code format (must be 6 uppercase letters/numbers)' };
        }

        // Ensure element has a stable ID for undo/redo
        if (!indicatorElement.id) {
            indicatorElement.id = `indicator-${Math.random().toString(36).substr(2,9)}`;
        }
        const elementId = indicatorElement.id;

        // Get old code from element's data attribute
        const oldCode = indicatorElement.dataset.indicatorCode || '';

        // Check if code is unique (excluding current element)
        const codeInput = indicatorElement.querySelector('.indicator-code-input');
        if (!this.isCodeUnique(newCode, 'indicator', codeInput)) {
            return { success: false, error: 'Code already in use' };
        }

        // Don't record if no change
        if (oldCode === newCode) {
            return { success: true, message: 'No change needed' };
        }

        // Apply change - update data attributes
        this.updateElementCode(indicatorElement, newCode);

        // Update input field
        if (codeInput) {
            codeInput.value = newCode;
        }

        // Record action with ID-based undo/redo (codes change, but IDs are stable)
        const action = this.actionHistory.recordAction({
            type: 'set-indicator-code',
            message: oldCode
                ? `Changed indicator code from "${oldCode}" to "${newCode}"`
                : `Set indicator code to "${newCode}"`,
            delta: {
                type: 'set-indicator-code',
                indicatorCode: newCode,  // New code for backend reference
                from: oldCode,
                to: newCode
            },
            undo: () => {
                // Find by stable ID (not by code which has changed)
                const el = document.getElementById(elementId);
                if (el) {
                    this.updateElementCode(el, oldCode);
                    const input = el.querySelector('.indicator-code-input');
                    if (input) input.value = oldCode;
                    this.validate();
                }
            },
            redo: () => {
                // Find by stable ID (not by code which has changed)
                const el = document.getElementById(elementId);
                if (el) {
                    this.updateElementCode(el, newCode);
                    const input = el.querySelector('.indicator-code-input');
                    if (input) input.value = newCode;
                    this.validate();
                }
            }
        });

        // Flag unsaved and validate
        this.flagUnsaved();
        this.validate();

        return { success: true, action: action };
    }

    /**
     * Add dataset to an indicator
     * @param {string} indicatorCode - The indicator code
     * @param {Object} options - Options object
     * @param {string} options.datasetCode - The dataset code to add
     * @param {Object} options.datasetDetails - The dataset details object (optional, will fetch if not provided)
     * @returns {Object} Result with success status and action
     */
    addDataset(indicatorCode, { datasetCode, datasetDetails } = {}) {
        // Validate inputs
        if (!indicatorCode) {
            return { success: false, error: 'Indicator code is required' };
        }
        if (!datasetCode) {
            return { success: false, error: 'Dataset code is required' };
        }

        // Find indicator element
        const indicatorEl = this.findElementByCode(indicatorCode, 'Indicator');
        if (!indicatorEl) {
            return { success: false, error: `Indicator ${indicatorCode} not found` };
        }

        // Find selected datasets container
        const selectedDatasetsDiv = indicatorEl.querySelector('.selected-datasets');
        if (!selectedDatasetsDiv) {
            return { success: false, error: 'Selected datasets container not found' };
        }

        // Check for duplicates
        const existing = selectedDatasetsDiv.querySelector(`[data-dataset-code="${datasetCode}"]`);
        if (existing) {
            return { success: false, error: 'Dataset already added to this indicator' };
        }

        // Get dataset details if not provided
        let details = datasetDetails;
        if (!details) {
            details = this.datasetDetails[datasetCode];
            if (!details) {
                return { success: false, error: `Dataset ${datasetCode} not found in datasetDetails` };
            }
        }

        // Get position before adding
        const position = selectedDatasetsDiv.querySelectorAll('.dataset-item').length;

        // Create dataset item using existing method
        // (We'll call addDatasetToIndicatorWithDetails but capture the element)
        const datasetName = details.DatasetName || 'Unknown Dataset';
        const datasetDescription = details.Description || 'No description available';
        const datasetOrg = details.Source?.OrganizationName || 'N/A';
        const datasetOrgCode = details.Source?.OrganizationCode || '';

        const formatNumber = (num) => {
            return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        };

        const unitHtml = details.Unit ? `
            <div class="detail-row">
                <span class="detail-label">Unit</span>
                <span class="detail-value">${details.Unit}</span>
            </div>` : '';

        const rangeHtml = details.Range ? `
            <div class="detail-row">
                <span class="detail-label">Range</span>
                <span class="detail-value">${formatNumber(details.Range.yMin)} – ${formatNumber(details.Range.yMax)}</span>
            </div>` : '';

        const datasetItem = document.createElement('div');
        datasetItem.classList.add('dataset-item');
        datasetItem.dataset.datasetCode = datasetCode;
        datasetItem.dataset.expanded = 'false';
        datasetItem.innerHTML = `
            <div class="dataset-item-header">
                <div class="dataset-info">
                    <span class="dataset-name">${datasetName}</span>
                    <span class="dataset-code">${datasetCode}</span>
                </div>
                <div class="dataset-actions">
                    <button class="remove-dataset" type="button" title="Remove dataset">×</button>
                </div>
            </div>
            <div class="dataset-details-slideout">
                <div class="detail-row">
                    <span class="detail-label">Description</span>
                    <span class="detail-value">${datasetDescription}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Organization</span>
                    <span class="detail-value">${datasetOrg}${datasetOrgCode ? ' (' + datasetOrgCode + ')' : ''}</span>
                </div>${unitHtml}${rangeHtml}
            </div>
        `;

        // Add toggle functionality
        const header = datasetItem.querySelector('.dataset-item-header');
        header.addEventListener('click', (e) => {
            if (!e.target.classList.contains('remove-dataset')) {
                const isExpanded = datasetItem.dataset.expanded === 'true';
                datasetItem.dataset.expanded = (!isExpanded).toString();
            }
        });

        // Add to DOM
        selectedDatasetsDiv.appendChild(datasetItem);

        // Record action
        const action = this.actionHistory.recordAction({
            type: 'add-dataset',
            message: `Added dataset "${datasetCode}" to indicator "${indicatorCode}"`,
            delta: {
                type: 'add-dataset',
                indicatorCode: indicatorCode,
                datasetCode: datasetCode,
                datasetDetails: details,
                position: position
            },
            undo: () => {
                datasetItem.remove();
                this.validate();
            },
            redo: () => {
                selectedDatasetsDiv.appendChild(datasetItem);
                this.validate();
            }
        });

        // Flag unsaved and validate
        this.flagUnsaved();
        this.validate();

        return { success: true, action: action };
    }

    /**
     * Remove dataset from an indicator
     * @param {string} indicatorCode - The indicator code
     * @param {Object} options - Options object
     * @param {string} options.datasetCode - The dataset code to remove
     * @returns {Object} Result with success status and action
     */
    removeDataset(indicatorCode, { datasetCode } = {}) {
        // Validate inputs
        if (!indicatorCode) {
            return { success: false, error: 'Indicator code is required' };
        }
        if (!datasetCode) {
            return { success: false, error: 'Dataset code is required' };
        }

        // Find indicator element
        const indicatorEl = this.findElementByCode(indicatorCode, 'Indicator');
        if (!indicatorEl) {
            return { success: false, error: `Indicator ${indicatorCode} not found` };
        }

        // Find selected datasets container
        const selectedDatasetsDiv = indicatorEl.querySelector('.selected-datasets');
        if (!selectedDatasetsDiv) {
            return { success: false, error: 'Selected datasets container not found' };
        }

        // Find dataset item
        const datasetItem = selectedDatasetsDiv.querySelector(`[data-dataset-code="${datasetCode}"]`);
        if (!datasetItem) {
            return { success: false, error: `Dataset ${datasetCode} not found in indicator` };
        }

        // Get position before removing
        const position = Array.from(selectedDatasetsDiv.children).indexOf(datasetItem);

        // Get dataset details for undo
        const details = this.datasetDetails[datasetCode];

        // Remove from DOM
        datasetItem.remove();

        // Record action
        const action = this.actionHistory.recordAction({
            type: 'remove-dataset',
            message: `Removed dataset "${datasetCode}" from indicator "${indicatorCode}"`,
            delta: {
                type: 'remove-dataset',
                indicatorCode: indicatorCode,
                datasetCode: datasetCode,
                datasetDetails: details,
                position: position
            },
            undo: () => {
                // Re-add at same position
                const siblings = Array.from(selectedDatasetsDiv.children);
                if (position >= siblings.length) {
                    selectedDatasetsDiv.appendChild(datasetItem);
                } else {
                    selectedDatasetsDiv.insertBefore(datasetItem, siblings[position]);
                }
                this.validate();
            },
            redo: () => {
                datasetItem.remove();
                this.validate();
            }
        });

        // Flag unsaved and validate
        this.flagUnsaved();
        this.validate();

        return { success: true, action: action };
    }

    /**
     * Add new indicator to a category or pillar
     * @param {string} parentCode - The parent category or pillar code
     * @param {Object} options - Options object
     * @param {string} options.indicatorCode - The indicator code (required)
     * @param {string} options.indicatorName - The indicator name (optional, defaults to "New Indicator")
     * @param {Array<string>} options.datasetCodes - Array of dataset codes (optional, defaults to [])
     * @param {string} options.scoreFunction - The score function (optional, defaults to "Score = 0")
     * @returns {Object} Result with success, action, and element
     */
    addIndicator(parentCode, { indicatorCode, indicatorName = 'New Indicator', datasetCodes = [], scoreFunction = 'Score = 0' } = {}) {
        // Validate inputs
        if (!parentCode) {
            return { success: false, error: 'Parent code is required' };
        }
        if (!indicatorCode) {
            return { success: false, error: 'Indicator code is required' };
        }

        // Find parent (category or pillar)
        let parentEl = this.findElementByCode(parentCode, 'Category');
        if (!parentEl) {
            parentEl = this.findElementByCode(parentCode, 'Pillar');
        }
        if (!parentEl) {
            return { success: false, error: `Parent ${parentCode} not found` };
        }

        const parentType = this.getItemType(parentEl);

        // Find indicators container
        const indicatorsContainer = parentEl.querySelector('.indicators-container');
        if (!indicatorsContainer) {
            return { success: false, error: 'Indicators container not found in parent' };
        }

        // Check for duplicate code
        const existing = this.findElementByCode(indicatorCode, 'Indicator');
        if (existing) {
            return { success: false, error: `Indicator code ${indicatorCode} already exists` };
        }

        // Get position
        const position = indicatorsContainer.querySelectorAll('.indicator-card').length;

        // Create indicator element
        const indEl = this.createIndicatorElement();

        // Set indicator details
        const indicatorNameEl = indEl.querySelector('.indicator-name');
        const indicatorCodeInput = indEl.querySelector('.indicator-code-input');
        const scoreFunctionEl = indEl.querySelector('.editable-score-function');

        if (indicatorNameEl) indicatorNameEl.textContent = indicatorName;
        if (indicatorCodeInput) indicatorCodeInput.value = indicatorCode;
        if (scoreFunctionEl) scoreFunctionEl.textContent = scoreFunction;

        // Set data attributes
        indEl.dataset.indicatorCode = indicatorCode;
        indEl.dataset.itemCode = indicatorCode;

        // Add datasets
        if (datasetCodes.length > 0) {
            const selectedDatasetsDiv = indEl.querySelector('.selected-datasets');
            if (selectedDatasetsDiv) {
                datasetCodes.forEach(datasetCode => {
                    const details = this.datasetDetails[datasetCode];
                    if (details) {
                        this.addDataset(indicatorCode, { datasetCode, datasetDetails: details });
                    }
                });
            }
        }

        // Add to DOM
        indicatorsContainer.appendChild(indEl);

        // Capture full indicator metadata for undo
        const indicatorMetadata = {
            ItemType: 'Indicator',
            ItemCode: indicatorCode,
            ItemName: indicatorName,
            DatasetCodes: datasetCodes,
            ScoreFunction: scoreFunction,
            Children: []
        };

        // Record action
        const action = this.actionHistory.recordAction({
            type: 'add-indicator',
            message: `Added indicator "${indicatorCode}" to ${parentType} "${parentCode}"`,
            delta: {
                type: 'add-indicator',
                indicatorCode: indicatorCode,
                parentCode: parentCode,
                parentType: parentType,
                indicatorMetadata: indicatorMetadata,
                position: position
            },
            undo: () => {
                indEl.remove();
                this.validate();
            },
            redo: () => {
                indicatorsContainer.appendChild(indEl);
                this.validate();
            }
        });

        // Flag unsaved and validate
        this.flagUnsaved();
        this.validate();

        return { success: true, action: action, element: indEl };
    }

    /**
     * Remove indicator
     * @param {string} indicatorCode - The indicator code
     * @returns {Object} Result with success, action, and metadata
     */
    removeIndicator(indicatorCode) {
        // Validate input
        if (!indicatorCode) {
            return { success: false, error: 'Indicator code is required' };
        }

        // Find indicator element
        const indEl = this.findElementByCode(indicatorCode, 'Indicator');
        if (!indEl) {
            return { success: false, error: `Indicator ${indicatorCode} not found` };
        }

        // Get parent info
        const parentCode = this.getParentCode(indEl);
        const parentType = this.getParentType(indEl);
        const position = this.getPositionInParent(indEl);

        // Capture indicator metadata for undo
        const indicatorNameEl = indEl.querySelector('.indicator-name');
        const scoreFunctionEl = indEl.querySelector('.editable-score-function');
        const datasetItems = indEl.querySelectorAll('.dataset-item');

        const indicatorMetadata = {
            ItemType: 'Indicator',
            ItemCode: indicatorCode,
            ItemName: indicatorNameEl?.textContent || '',
            DatasetCodes: Array.from(datasetItems).map(item => item.dataset.datasetCode),
            ScoreFunction: scoreFunctionEl?.textContent || 'Score = 0',
            Children: []
        };

        // Get parent element for undo/redo
        const parentEl = indEl.parentElement;

        // Remove from DOM
        indEl.remove();

        // Record action
        const action = this.actionHistory.recordAction({
            type: 'remove-indicator',
            message: `Removed indicator "${indicatorCode}" from ${parentType} "${parentCode}"`,
            delta: {
                type: 'remove-indicator',
                indicatorCode: indicatorCode,
                parentCode: parentCode,
                parentType: parentType,
                indicatorMetadata: indicatorMetadata,
                position: position
            },
            undo: () => {
                // Re-add at same position
                const siblings = Array.from(parentEl.children).filter(el => el.classList.contains('indicator-card'));
                if (position >= siblings.length) {
                    parentEl.appendChild(indEl);
                } else {
                    parentEl.insertBefore(indEl, siblings[position]);
                }
                this.validate();
            },
            redo: () => {
                indEl.remove();
                this.validate();
            }
        });

        // Flag unsaved and validate
        this.flagUnsaved();
        this.validate();

        return { success: true, action: action, metadata: indicatorMetadata };
    }

    /**
     * Move indicator to different category or pillar
     * @param {string} indicatorCode - The indicator code
     * @param {string} targetParentCode - The target parent code (category or pillar)
     * @returns {Object} Result with success and action
     */
    moveIndicator(indicatorCode, targetParentCode) {
        // Validate inputs
        if (!indicatorCode) {
            return { success: false, error: 'Indicator code is required' };
        }
        if (!targetParentCode) {
            return { success: false, error: 'Target parent code is required' };
        }

        // Find indicator element
        const indEl = this.findElementByCode(indicatorCode, 'Indicator');
        if (!indEl) {
            return { success: false, error: `Indicator ${indicatorCode} not found` };
        }

        // Get current parent info
        const fromParentCode = this.getParentCode(indEl);
        const fromParentType = this.getParentType(indEl);
        const fromPosition = this.getPositionInParent(indEl);

        // Find target parent
        let targetParentEl = this.findElementByCode(targetParentCode, 'Category');
        if (!targetParentEl) {
            targetParentEl = this.findElementByCode(targetParentCode, 'Pillar');
        }
        if (!targetParentEl) {
            return { success: false, error: `Target parent ${targetParentCode} not found` };
        }

        const toParentType = this.getItemType(targetParentEl);

        // Don't move if already in target
        if (fromParentCode === targetParentCode) {
            return { success: false, error: 'Indicator is already in target parent' };
        }

        // Find target indicators container
        const targetContainer = targetParentEl.querySelector('.indicators-container');
        if (!targetContainer) {
            return { success: false, error: 'Indicators container not found in target parent' };
        }

        // Get new position
        const toPosition = targetContainer.querySelectorAll('.indicator-card').length;

        // Get current parent element for undo
        const fromParentEl = indEl.parentElement;

        // Move to target
        targetContainer.appendChild(indEl);

        // Record action
        const action = this.actionHistory.recordAction({
            type: 'move-indicator',
            message: `Moved indicator "${indicatorCode}" from ${fromParentType} "${fromParentCode}" to ${toParentType} "${targetParentCode}"`,
            delta: {
                type: 'move-indicator',
                indicatorCode: indicatorCode,
                fromParentCode: fromParentCode,
                fromParentType: fromParentType,
                fromPosition: fromPosition,
                toParentCode: targetParentCode,
                toParentType: toParentType,
                toPosition: toPosition
            },
            undo: () => {
                // Move back to original position
                const siblings = Array.from(fromParentEl.children).filter(el => el.classList.contains('indicator-card'));
                if (fromPosition >= siblings.length) {
                    fromParentEl.appendChild(indEl);
                } else {
                    fromParentEl.insertBefore(indEl, siblings[fromPosition]);
                }
                this.validate();
            },
            redo: () => {
                targetContainer.appendChild(indEl);
                this.validate();
            }
        });

        // Flag unsaved and validate
        this.flagUnsaved();
        this.validate();

        return { success: true, action: action };
    }

    /**
     * Set indicator name
     * @param {string} indicatorCode - The indicator code
     * @param {Object} options - Options object
     * @param {string} options.indicatorName - The new indicator name
     * @returns {Object} Result with success and action
     */
    setIndicatorName(indicatorCode, { indicatorName } = {}) {
        // Validate inputs
        if (!indicatorCode) {
            return { success: false, error: 'Indicator code is required' };
        }
        if (!indicatorName) {
            return { success: false, error: 'Indicator name is required' };
        }

        // Find indicator element
        const indEl = this.findElementByCode(indicatorCode, 'Indicator');
        if (!indEl) {
            return { success: false, error: `Indicator ${indicatorCode} not found` };
        }

        // Find indicator name element
        const indicatorNameEl = indEl.querySelector('.indicator-name');
        if (!indicatorNameEl) {
            return { success: false, error: 'Indicator name element not found' };
        }

        // Capture old value
        const oldName = indicatorNameEl.textContent;

        // Don't record if no change
        if (oldName === indicatorName) {
            return { success: true, message: 'No change needed' };
        }

        // Apply change
        indicatorNameEl.textContent = indicatorName;

        // Record action
        const action = this.actionHistory.recordAction({
            type: 'set-indicator-name',
            message: `Updated indicator name from "${oldName}" to "${indicatorName}"`,
            delta: {
                type: 'set-indicator-name',
                indicatorCode: indicatorCode,
                from: oldName,
                to: indicatorName
            },
            undo: () => {
                indicatorNameEl.textContent = oldName;
            },
            redo: () => {
                indicatorNameEl.textContent = indicatorName;
            }
        });

        // Flag unsaved
        this.flagUnsaved();

        return { success: true, action: action };
    }
    // ========== SECTION 5: API Methods - Categories ==========

    /**
     * Add a new category to a pillar
     * @param {string} pillarCode - Parent pillar code
     * @param {Object} options
     * @param {string} options.categoryCode - Category code (3 chars)
     * @param {string} options.categoryName - Category name
     * @returns {Object} Result with success status and action
     */
    addCategory(pillarCode, { categoryCode, categoryName }) {
        // Validate inputs
        if (!pillarCode || typeof pillarCode !== 'string') {
            return { success: false, error: 'Invalid pillarCode' };
        }
        if (!categoryCode || !/^[A-Z]{3}$/.test(categoryCode)) {
            return { success: false, error: 'categoryCode must be 3 uppercase letters' };
        }
        if (!categoryName || typeof categoryName !== 'string') {
            return { success: false, error: 'Invalid categoryName' };
        }

        // Find pillar column
        const pillarCol = this.findElementByCode(pillarCode, 'Pillar');
        if (!pillarCol) {
            return { success: false, error: `Pillar ${pillarCode} not found` };
        }

        // Check for duplicate category code
        const existing = this.findElementByCode(categoryCode, 'Category');
        if (existing) {
            return { success: false, error: `Category ${categoryCode} already exists` };
        }

        // Find container for categories in pillar
        const categoriesContainer = pillarCol.querySelector('.categories-container');
        if (!categoriesContainer) {
            return { success: false, error: 'Categories container not found in pillar' };
        }

        // Create new category element
        const categoryEl = this.createCategoryElement();
        categoryEl.dataset.categoryCode = categoryCode;
        categoryEl.dataset.itemCode = categoryCode;

        // Set category name
        const nameEl = categoryEl.querySelector('.customization-category-header-title');
        if (nameEl) nameEl.textContent = categoryName;

        // Set category code input
        const codeInput = categoryEl.querySelector('.category-code-input');
        if (codeInput) codeInput.value = categoryCode;

        // Calculate position
        const position = this.getPositionInParent(categoriesContainer.lastElementChild || categoriesContainer);

        // Capture metadata for action
        const categoryMetadata = {
            ItemType: 'Category',
            ItemCode: categoryCode,
            ItemName: categoryName,
            CategoryCode: categoryCode,
            PillarCode: pillarCode,
            Children: [],
            IndicatorCodes: [],
            DocumentType: 'CategoryDetail',
            TreePath: `sspi/${pillarCode.toLowerCase()}/${categoryCode.toLowerCase()}`
        };

        // Add to DOM
        categoriesContainer.appendChild(categoryEl);

        // Setup handlers
        this.setupCategoryHandlers(categoryEl);

        // Record action
        const action = this.actionHistory.recordAction({
            type: 'add-category',
            message: `Added category "${categoryName}" (${categoryCode}) to pillar ${pillarCode}`,
            delta: {
                type: 'add-category',
                categoryCode: categoryCode,
                pillarCode: pillarCode,
                categoryMetadata: categoryMetadata,
                position: position
            },
            undo: () => {
                const el = this.findElementByCode(categoryCode, 'Category');
                if (el) el.remove();
            },
            redo: () => {
                const pillar = this.findElementByCode(pillarCode, 'Pillar');
                const container = pillar?.querySelector('.categories-container');
                if (container) {
                    const newEl = this.createCategoryElement();
                    newEl.dataset.categoryCode = categoryCode;
                    newEl.dataset.itemCode = categoryCode;
                    const name = newEl.querySelector('.customization-category-header-title');
                    if (name) name.textContent = categoryName;
                    const code = newEl.querySelector('.category-code-input');
                    if (code) code.value = categoryCode;
                    container.appendChild(newEl);
                    this.setupCategoryHandlers(newEl);
                }
            }
        });

        this.hasUnsavedChanges = true;
        this.validate();

        return { success: true, action: action };
    }

    /**
     * Set code for a category
     * @param {HTMLElement} categoryElement - The category element
     * @param {Object} options - Options object
     * @param {string} options.newCode - The new code value
     * @returns {Object} Result with success status and action
     */
    setCategoryCode(categoryElement, { newCode } = {}) {
        // Validate element
        if (!(categoryElement instanceof HTMLElement)) {
            return { success: false, error: 'Category element is required' };
        }

        // Validate new code
        if (!newCode) {
            return { success: false, error: 'New code is required' };
        }

        // Validate code format
        if (!this.validateCode(newCode, 'category')) {
            return { success: false, error: 'Invalid category code format (must be 3 uppercase letters)' };
        }

        // Ensure element has a stable ID for undo/redo
        if (!categoryElement.id) {
            categoryElement.id = `category-${Math.random().toString(36).substr(2,9)}`;
        }
        const elementId = categoryElement.id;

        // Get old code from element's data attribute
        const oldCode = categoryElement.dataset.categoryCode || '';

        // Check if code is unique (excluding current element)
        const codeInput = categoryElement.querySelector('.category-code-input');
        if (!this.isCodeUnique(newCode, 'category', codeInput)) {
            return { success: false, error: 'Code already in use' };
        }

        // Don't record if no change
        if (oldCode === newCode) {
            return { success: true, message: 'No change needed' };
        }

        // Apply change - update data attributes
        this.updateElementCode(categoryElement, newCode);

        // Update input field
        if (codeInput) {
            codeInput.value = newCode;
        }

        // Record action with ID-based undo/redo (codes change, but IDs are stable)
        const action = this.actionHistory.recordAction({
            type: 'set-category-code',
            message: oldCode
                ? `Changed category code from "${oldCode}" to "${newCode}"`
                : `Set category code to "${newCode}"`,
            delta: {
                type: 'set-category-code',
                categoryCode: newCode,  // New code for backend reference
                from: oldCode,
                to: newCode
            },
            undo: () => {
                // Find by stable ID (not by code which has changed)
                const el = document.getElementById(elementId);
                if (el) {
                    this.updateElementCode(el, oldCode);
                    const input = el.querySelector('.category-code-input');
                    if (input) input.value = oldCode;
                    this.validate();
                }
            },
            redo: () => {
                // Find by stable ID (not by code which has changed)
                const el = document.getElementById(elementId);
                if (el) {
                    this.updateElementCode(el, newCode);
                    const input = el.querySelector('.category-code-input');
                    if (input) input.value = newCode;
                    this.validate();
                }
            }
        });

        // Flag unsaved and validate
        this.flagUnsaved();
        this.validate();

        return { success: true, action: action };
    }

    /**
     * Remove a category (optionally cascading to remove nested indicators)
     * @param {string} categoryCode - Category code to remove
     * @param {Object} options
     * @param {boolean} options.cascade - If true, remove nested indicators (default: true)
     * @returns {Object} Result with success status and actions
     */
    removeCategory(categoryCode, { cascade = true } = {}) {
        // Validate input
        if (!categoryCode || typeof categoryCode !== 'string') {
            return { success: false, error: 'Invalid categoryCode' };
        }
        const categoryEl = this.findElementByCode(categoryCode, 'Category');
        if (!categoryEl) {
            return { success: false, error: `Category ${categoryCode} not found` };
        }
        const pillarCode = this.getParentCode(categoryEl);
        if (!pillarCode) {
            return { success: false, error: 'Could not determine parent pillar' };
        }
        const position = this.getPositionInParent(categoryEl);
        const categoryName = categoryEl.querySelector('.customization-category-header-title')?.textContent || '';
        const indicatorsContainer = categoryEl.querySelector('.indicators-container');
        const indicatorEls = indicatorsContainer ? Array.from(indicatorsContainer.querySelectorAll('[data-indicator-code]')) : [];
        const indicatorCodes = indicatorEls.map(el => el.dataset.indicatorCode);
        const categoryMetadata = {
            ItemType: 'Category',
            ItemCode: categoryCode,
            ItemName: categoryName,
            CategoryCode: categoryCode,
            PillarCode: pillarCode,
            Children: indicatorCodes,
            IndicatorCodes: indicatorCodes,
            DocumentType: 'CategoryDetail'
        };
        // Store full state for undo
        const categoryHTML = categoryEl.outerHTML;
        // Remove from DOM
        categoryEl.remove();
        // Record main action
        const mainAction = this.actionHistory.recordAction({
            type: 'remove-category',
            message: `Removed category "${categoryName}" (${categoryCode}) from pillar ${pillarCode}`,
            delta: {
                type: 'remove-category',
                categoryCode: categoryCode,
                pillarCode: pillarCode,
                categoryMetadata: categoryMetadata,
                position: position,
                cascadedIndicators: cascade ? indicatorCodes : []
            },
            undo: () => {
                const pillar = this.findElementByCode(pillarCode, 'Pillar');
                const container = pillar?.querySelector('.categories-container');
                if (container) {
                    const temp = document.createElement('div');
                    temp.innerHTML = categoryHTML;
                    const restored = temp.firstElementChild;
                    container.appendChild(restored);
                    this.setupCategoryHandlers(restored);
                }
            },
            redo: () => {
                const el = this.findElementByCode(categoryCode, 'Category');
                if (el) el.remove();
            }
        });
        const actions = [mainAction];
        // If cascade, record remove-indicator actions for each nested indicator
        if (cascade && indicatorCodes.length > 0) {
            for (const indicatorCode of indicatorCodes) {
                // Note: These indicators are already removed from DOM,
                // so we're just recording the actions for backend processing
                const indicatorAction = this.actionHistory.recordAction({
                    type: 'remove-indicator',
                    message: `Cascaded removal of indicator ${indicatorCode}`,
                    delta: {
                        type: 'remove-indicator',
                        indicatorCode: indicatorCode,
                        parentCode: categoryCode,
                        parentType: 'Category',
                        cascaded: true
                    },
                    undo: () => {
                        // Undo handled by parent category restoration
                    },
                    redo: () => {
                        // Redo handled by parent category removal
                    }
                });
                actions.push(indicatorAction);
            }
        }
        this.hasUnsavedChanges = true;
        this.validate();
        return { success: true, actions: actions };
    }

    /**
     * Move a category to a different pillar
     * IMPORTANT: This only changes the DOM position and pillar's CategoryCodes arrays.
     * The category metadata itself is UNCHANGED. Nested indicators are UNCHANGED.
     * @param {string} categoryCode - Category code to move
     * @param {string} targetPillarCode - Target pillar code
     * @returns {Object} Result with success status and action
     */
    moveCategory(categoryCode, targetPillarCode) {
        // Validate inputs
        if (!categoryCode || typeof categoryCode !== 'string') {
            return { success: false, error: 'Invalid categoryCode' };
        }
        if (!targetPillarCode || typeof targetPillarCode !== 'string') {
            return { success: false, error: 'Invalid targetPillarCode' };
        }
        // Find category element
        const categoryEl = this.findElementByCode(categoryCode, 'Category');
        if (!categoryEl) {
            return { success: false, error: `Category ${categoryCode} not found` };
        }

        // Find source pillar
        const fromPillarCode = this.getParentCode(categoryEl);
        if (!fromPillarCode) {
            return { success: false, error: 'Could not determine source pillar' };
        }

        // Check if already in target pillar
        if (fromPillarCode === targetPillarCode) {
            return { success: false, error: 'Category already in target pillar' };
        }

        // Find target pillar
        const targetPillar = this.findElementByCode(targetPillarCode, 'Pillar');
        if (!targetPillar) {
            return { success: false, error: `Target pillar ${targetPillarCode} not found` };
        }

        // Find target container
        const targetContainer = targetPillar.querySelector('.categories-container');
        if (!targetContainer) {
            return { success: false, error: 'Target categories container not found' };
        }

        // Capture positions
        const fromPosition = this.getPositionInParent(categoryEl);

        // Move to target (DOM only)
        targetContainer.appendChild(categoryEl);

        const toPosition = this.getPositionInParent(categoryEl);

        // Record action
        // IMPORTANT: Only 1 action created, type='move-category'
        // No indicator actions created - indicators move with category but metadata unchanged
        const action = this.actionHistory.recordAction({
            type: 'move-category',
            message: `Moved category ${categoryCode} from pillar ${fromPillarCode} to ${targetPillarCode}`,
            delta: {
                type: 'move-category',
                categoryCode: categoryCode,
                fromPillarCode: fromPillarCode,
                fromPosition: fromPosition,
                toPillarCode: targetPillarCode,
                toPosition: toPosition
                // NOTE: Category metadata UNCHANGED (including PillarCode field)
                // NOTE: Nested indicators UNCHANGED
            },
            undo: () => {
                const el = this.findElementByCode(categoryCode, 'Category');
                if (el) {
                    const sourcePillar = this.findElementByCode(fromPillarCode, 'Pillar');
                    const sourceContainer = sourcePillar?.querySelector('.categories-container');
                    if (sourceContainer) {
                        sourceContainer.appendChild(el);
                    }
                }
            },
            redo: () => {
                const el = this.findElementByCode(categoryCode, 'Category');
                if (el) {
                    const tgtPillar = this.findElementByCode(targetPillarCode, 'Pillar');
                    const tgtContainer = tgtPillar?.querySelector('.categories-container');
                    if (tgtContainer) {
                        tgtContainer.appendChild(el);
                    }
                }
            }
        });

        this.hasUnsavedChanges = true;
        this.validate();

        return { success: true, action: action };
    }

    /**
     * Set category name
     * @param {string} categoryCode - Category code
     * @param {Object} options
     * @param {string} options.categoryName - New category name
     * @returns {Object} Result with success status and action
     */
    setCategoryName(categoryCode, { categoryName }) {
        // Validate inputs
        if (!categoryCode || typeof categoryCode !== 'string') {
            return { success: false, error: 'Invalid categoryCode' };
        }
        if (!categoryName || typeof categoryName !== 'string') {
            return { success: false, error: 'Invalid categoryName' };
        }

        // Find category element
        const categoryEl = this.findElementByCode(categoryCode, 'Category');
        if (!categoryEl) {
            return { success: false, error: `Category ${categoryCode} not found` };
        }

        // Find name element
        const nameEl = categoryEl.querySelector('.customization-category-header-title');
        if (!nameEl) {
            return { success: false, error: 'Category name element not found' };
        }

        // Capture old name
        const oldName = nameEl.textContent;

        // Check if name actually changed
        if (oldName === categoryName) {
            return { success: false, error: 'New name is same as current name' };
        }

        // Update name
        nameEl.textContent = categoryName;

        // Record action
        const action = this.actionHistory.recordAction({
            type: 'set-category-name',
            message: `Changed category ${categoryCode} name from "${oldName}" to "${categoryName}"`,
            delta: {
                type: 'set-category-name',
                categoryCode: categoryCode,
                from: oldName,
                to: categoryName
            },
            undo: () => {
                const el = this.findElementByCode(categoryCode, 'Category');
                const name = el?.querySelector('.customization-category-header-title');
                if (name) name.textContent = oldName;
            },
            redo: () => {
                const el = this.findElementByCode(categoryCode, 'Category');
                const name = el?.querySelector('.customization-category-header-title');
                if (name) name.textContent = categoryName;
            }
        });

        this.hasUnsavedChanges = true;
        this.validate();

        return { success: true, action: action };
    }

    // ========== SECTION 6: API Methods - Pillars ==========

    /**
     * Set pillar name
     * Note: Pillar codes are fixed (SUS, MS, PG) and cannot be changed
     * @param {string} pillarCode - Pillar code
     * @param {Object} options
     * @param {string} options.pillarName - New pillar name
     * @returns {Object} Result with success status and action
     */
    setPillarName(pillarCode, { pillarName }) {
        // Validate inputs
        if (!pillarCode || typeof pillarCode !== 'string') {
            return { success: false, error: 'Invalid pillarCode' };
        }
        if (!pillarName || typeof pillarName !== 'string') {
            return { success: false, error: 'Invalid pillarName' };
        }

        // Find pillar column
        const pillarCol = this.findElementByCode(pillarCode, 'Pillar');
        if (!pillarCol) {
            return { success: false, error: `Pillar ${pillarCode} not found` };
        }

        // Find pillar name element
        const nameEl = pillarCol.querySelector('.pillar-name');
        if (!nameEl) {
            return { success: false, error: 'Pillar name element not found' };
        }

        // Capture old name
        const oldName = nameEl.textContent;

        // Check if name actually changed
        if (oldName === pillarName) {
            return { success: false, error: 'New name is same as current name' };
        }

        // Update name
        nameEl.textContent = pillarName;

        // Record action
        const action = this.actionHistory.recordAction({
            type: 'set-pillar-name',
            message: `Changed pillar ${pillarCode} name from "${oldName}" to "${pillarName}"`,
            delta: {
                type: 'set-pillar-name',
                pillarCode: pillarCode,
                from: oldName,
                to: pillarName
            },
            undo: () => {
                const el = this.findElementByCode(pillarCode, 'Pillar');
                const name = el?.querySelector('.pillar-name');
                if (name) name.textContent = oldName;
            },
            redo: () => {
                const el = this.findElementByCode(pillarCode, 'Pillar');
                const name = el?.querySelector('.pillar-name');
                if (name) name.textContent = pillarName;
            }
        });

        this.hasUnsavedChanges = true;
        this.validate();

        return { success: true, action: action };
    }

    /**
     * Set code for a pillar
     * @param {HTMLElement} pillarElement - The pillar element
     * @param {Object} options - Options object
     * @param {string} options.newCode - The new code value
     * @returns {Object} Result with success status and action
     */
    setPillarCode(pillarElement, { newCode } = {}) {
        // Validate element
        if (!(pillarElement instanceof HTMLElement)) {
            return { success: false, error: 'Pillar element is required' };
        }

        // Validate new code
        if (!newCode) {
            return { success: false, error: 'New code is required' };
        }

        // Validate code format
        if (!this.validateCode(newCode, 'pillar')) {
            return { success: false, error: 'Invalid pillar code format (must be 2-3 uppercase letters)' };
        }

        // Ensure element has a stable ID for undo/redo
        if (!pillarElement.id) {
            pillarElement.id = `pillar-${Math.random().toString(36).substr(2,9)}`;
        }
        const elementId = pillarElement.id;

        // Get old code from element's data attribute
        const oldCode = pillarElement.dataset.pillarCode || '';

        // Check if code is unique (excluding current element)
        const codeInput = pillarElement.querySelector('.pillar-code-input');
        if (!this.isCodeUnique(newCode, 'pillar', codeInput)) {
            return { success: false, error: 'Code already in use' };
        }

        // Don't record if no change
        if (oldCode === newCode) {
            return { success: true, message: 'No change needed' };
        }

        // Apply change - update data attributes
        this.updateElementCode(pillarElement, newCode);

        // Update input field
        if (codeInput) {
            codeInput.value = newCode;
        }

        // Record action with ID-based undo/redo (codes change, but IDs are stable)
        const action = this.actionHistory.recordAction({
            type: 'set-pillar-code',
            message: oldCode
                ? `Changed pillar code from "${oldCode}" to "${newCode}"`
                : `Set pillar code to "${newCode}"`,
            delta: {
                type: 'set-pillar-code',
                pillarCode: newCode,  // New code for backend reference
                from: oldCode,
                to: newCode
            },
            undo: () => {
                // Find by stable ID (not by code which has changed)
                const el = document.getElementById(elementId);
                if (el) {
                    this.updateElementCode(el, oldCode);
                    const input = el.querySelector('.pillar-code-input');
                    if (input) input.value = oldCode;
                    this.validate();
                }
            },
            redo: () => {
                // Find by stable ID (not by code which has changed)
                const el = document.getElementById(elementId);
                if (el) {
                    this.updateElementCode(el, newCode);
                    const input = el.querySelector('.pillar-code-input');
                    if (input) input.value = newCode;
                    this.validate();
                }
            }
        });

        // Flag unsaved and validate
        this.flagUnsaved();
        this.validate();

        return { success: true, action: action };
    }

    createCategoryElement() {
        const cat = document.createElement('div');
        cat.classList.add('category-box','draggable-item');
        // Assign stable ID for reliable element tracking (especially for undo/redo)
        cat.id = `category-${Math.random().toString(36).substr(2,9)}`;
        // Don't set draggable on the entire box - only on the header
        cat.setAttribute('role','group');
        cat.dataset.type='category';
        // Add data attributes for efficient querying
        cat.dataset.itemType = 'Category';
        cat.dataset.categoryCode = '';  // Will be set when code is entered
        cat.dataset.itemCode = '';  // Will be set when code is entered
        cat.innerHTML = `
<div class="category-collapsible" data-expanded="true">
    <div class="customization-category-header" draggable="true">
        <button class="collapse-toggle-btn category-toggle" type="button">
            <span class="collapse-icon">▼</span>
        </button>
        <div class="category-name-wrapper">
            <h4 class="customization-category-header-title" contenteditable="true" spellcheck="false">New Category</h4>
        </div>
        <div class="category-code-section">
            <label class="code-label">Code:</label>
            <input type="text" class="category-code-input" maxlength="3" placeholder="CAT"
                   pattern="[A-Z]{3}" title="Exactly 3 uppercase letters required">
            <span class="code-validation-message"></span>
        </div>
    </div>
    <div class="category-content">
        <div class="indicators-container drop-zone" data-accept="indicator" role="group"></div>
        <button class="add-indicator" aria-label="Add Indicator">+\u0020Add\u0020Indicator</button>
    </div>
</div>
`;
        this.setupCodeValidation(cat.querySelector('.category-code-input'), 'category');
        this.setupCollapsibleHandlers(cat);
        return cat;
    }

    createIndicatorElement() {
        const ind = document.createElement('div');
        ind.classList.add('indicator-card','draggable-item');
        // Assign stable ID for reliable element tracking (especially for undo/redo)
        ind.id = `indicator-${Math.random().toString(36).substr(2,9)}`;
        // Don't set draggable on the entire card - only on the header
        ind.setAttribute('role','treeitem');
        ind.dataset.type='indicator';
        // Add data attributes for efficient querying
        ind.dataset.itemType = 'Indicator';
        ind.dataset.indicatorCode = '';  // Will be set when code is entered
        ind.dataset.itemCode = '';  // Will be set when code is entered
        ind.innerHTML = `
<div class="indicator-collapsible" data-expanded="false">
    <div class="customization-indicator-header" draggable="true">
        <button class="collapse-toggle-btn indicator-toggle" type="button">
            <span class="collapse-icon">▼</span>
        </button>
        <div class="indicator-name-wrapper">
            <h5 class="indicator-name" contenteditable="true" spellcheck="false">New Indicator</h5>
        </div>
        <div class="indicator-code-section">
            <div class="code-validation-message"></div>
            <div class="code-input-container">
                <label class="code-label">Code:</label>
                <input type="text" class="indicator-code-input" maxlength="6" placeholder="INDIC1"
                   pattern="[A-Z0-9]{6}" title="Exactly 6 uppercase letters/numbers required">
            </div>
        </div>
    </div>
    <div class="indicator-config">
    <div class="dataset-selection">
        <label>Datasets</label>
        <div class="selected-datasets"></div>
        <button class="add-dataset-btn" type="button">+\u0020Add\u0020Dataset</button>
    </div>
    <div class="score-function">
        <label>Score Function</label>
        <pre class="editable-score-function" contenteditable="true" spellcheck="false" data-default-score-function="">Score = </pre>
    </div>
</div>
</div>
`;
        this.setupCodeValidation(ind.querySelector('.indicator-code-input'), 'indicator');
        this.setupDatasetSelection(ind);
        this.setupIndicatorChangeListeners(ind);
        this.setupCollapsibleHandlers(ind);
        return ind;
    }

    setupIndicatorChangeListeners(indicatorElement) {
        // Add change listeners for all inputs to flag unsaved changes
        const inputs = indicatorElement.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('change', () => this.flagUnsaved());
            input.addEventListener('input', () => this.flagUnsaved());
        });
    }

    setupCollapsibleHandlers(element) {
        // Handle collapse icon clicks to toggle details
        const collapseIcons = element.querySelectorAll('.category-collapse-icon, .indicator-collapse-icon');
        collapseIcons.forEach(icon => {
            icon.addEventListener('click', (e) => {
                e.stopPropagation();
                // Find the parent details element
                const details = icon.closest('details');
                if (details) {
                    details.open = !details.open;
                }
            });
        });
        // The CSS pointer-events: none on summary handles preventing default behavior
        // Child elements automatically get pointer-events: auto
        // No need for additional JavaScript event handling since CSS handles it
    }

    resetView() {
        // Collapse all indicators
        const indicators = this.container.querySelectorAll('.indicator-collapsible');
        indicators.forEach(collapsible => {
            collapsible.dataset.expanded = 'false';
            this.applyExpansionState(collapsible, false);
        });

        // Expand all categories
        const categories = this.container.querySelectorAll('.category-collapsible');
        categories.forEach(collapsible => {
            collapsible.dataset.expanded = 'true';
            this.applyExpansionState(collapsible, true);
        });
    }

    expandAll() {
        const allCollapsibles = this.container.querySelectorAll('[data-expanded]');
        allCollapsibles.forEach(collapsible => {
            collapsible.dataset.expanded = 'true';
            this.applyExpansionState(collapsible, true);
        });
    }

    collapseAll() {
        const allCollapsibles = this.container.querySelectorAll('[data-expanded]');
        allCollapsibles.forEach(collapsible => {
            collapsible.dataset.expanded = 'false';
            this.applyExpansionState(collapsible, false);
        });
    }

    flagUnsaved() {
        this.unsavedChanges = true;
        this.saveButton.classList.add('unsaved-changes');
        
        // Enable the discard button
        this.discardButton.disabled = false;
        this.discardButton.style.opacity = '1';
        this.discardButton.style.cursor = 'pointer';
        
        // Cache the current state with debouncing
        this.debouncedCacheState();
    }

    showIndicatorSelectionMenu(indicatorsContainer) {
        const menu = new IndicatorSelectionMenu({
            onCreateNew: (container) => {
                this.createNewIndicator(container);
            },
            onAddExisting: (container) => {
                this.showIndicatorSelector(container);
            }
        });
        menu.show(indicatorsContainer);
    }

    createNewIndicator(indicatorsContainer) {
        const ind = this.createIndicatorElement();
        indicatorsContainer.appendChild(ind);
        this.validate(indicatorsContainer);
        this.updateHierarchyOnAdd(ind, 'indicator');

        // Expand the indicator and focus on the name input
        const collapsible = ind.querySelector('.indicator-collapsible');
        if (collapsible) {
            // Expand the indicator
            collapsible.dataset.expanded = 'true';
            this.applyExpansionState(collapsible, true);

            // Focus on the indicator name
            const nameElement = ind.querySelector('.indicator-name');
            if (nameElement) {
                // Use setTimeout to ensure the expansion animation completes
                setTimeout(() => {
                    nameElement.focus();

                    // Select all text in the name field so user can immediately start typing
                    const range = document.createRange();
                    const selection = window.getSelection();
                    range.selectNodeContents(nameElement);
                    selection.removeAllRanges();
                    selection.addRange(range);

                    // Scroll into view if needed
                    nameElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 100);
            }
        }
    }

    showIndicatorSelector(indicatorsContainer) {
        const selector = new IndicatorSelector({
            onSelectionChange: (indicator) => {
                this.addExistingIndicator(indicatorsContainer, indicator);
            }
        });
        selector.show();
    }

    addExistingIndicator(indicatorsContainer, indicator) {
        // Create indicator element with pre-filled data
        const ind = this.createIndicatorElement();
        // Fill in the indicator data using backend field names
        const indicatorName = ind.querySelector('.indicator-name');
        const indicatorCodeInput = ind.querySelector('.indicator-code-input');
        const lowerGoalpost = ind.querySelector('.lower-goalpost');
        const upperGoalpost = ind.querySelector('.upper-goalpost');
        const invertedCheckbox = ind.querySelector('.inverted-checkbox');
        const scoreFunctionEl = ind.querySelector('.editable-score-function');

        // Use backend field names (IndicatorCode, Indicator/ItemName, etc.)
        if (indicatorName) indicatorName.textContent = indicator.Indicator || indicator.ItemName || '';
        if (indicatorCodeInput) indicatorCodeInput.value = indicator.IndicatorCode || '';
        if (lowerGoalpost) lowerGoalpost.value = indicator.LowerGoalpost || 0;
        if (upperGoalpost) upperGoalpost.value = indicator.UpperGoalpost || 100;
        if (invertedCheckbox) invertedCheckbox.checked = indicator.Inverted || false;

        // Populate score function if present
        if (scoreFunctionEl && indicator.ScoreFunction) {
            scoreFunctionEl.textContent = indicator.ScoreFunction;
        }

        // Add datasets if present (using backend field DatasetCodes)
        if (indicator.DatasetCodes && indicator.DatasetCodes.length > 0) {
            const selectedDatasetsDiv = ind.querySelector('.selected-datasets');
            indicator.DatasetCodes.forEach(datasetCode => {
                // Look up full dataset details if available
                const datasetDetail = this.datasetDetails && this.datasetDetails[datasetCode];
                if (datasetDetail) {
                    this.addDatasetToIndicatorWithDetails(selectedDatasetsDiv, datasetDetail);
                } else {
                    this.addDatasetToIndicator(selectedDatasetsDiv, datasetCode);
                }
            });
        }

        indicatorsContainer.appendChild(ind);
        this.validate(indicatorsContainer);
        this.updateHierarchyOnAdd(ind, 'indicator');

        // Expand the indicator to show all populated data
        const collapsible = ind.querySelector('.indicator-collapsible');
        if (collapsible) {
            collapsible.dataset.expanded = 'true';
            this.applyExpansionState(collapsible, true);

            // Scroll into view after a short delay
            setTimeout(() => {
                ind.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
        }
    }

    showContextMenu(x,y,target) {
        let m = document.getElementById('sspi-context-menu');
        if (m) m.remove();
        m = document.createElement('ul');
        m.id = 'sspi-context-menu';
        m.className = 'context-menu';
        m.style.position = 'absolute';
        m.style.top = `${y}px`;
        m.style.left = `${x}px`;

        // Check if target is a dataset
        const isDataset = target.classList.contains('dataset-item');
        const isPillar = target.dataset.type === 'pillar';

        let menuItems;

        if (isDataset) {
            // Special menu for datasets
            const isExpanded = target.dataset.expanded === 'true';
            const toggleText = isExpanded ? 'Hide Details' : 'Show Details';

            menuItems = [
                { name: toggleText, handler: () => {
                    // Toggle expansion state
                    const newState = target.dataset.expanded !== 'true';
                    target.dataset.expanded = newState.toString();

                    const slideout = target.querySelector('.dataset-details-slideout');
                    if (slideout) {
                        if (newState) {
                            slideout.style.maxHeight = slideout.scrollHeight + 'px';
                        } else {
                            slideout.style.maxHeight = '0';
                        }
                    }
                }},
                { name: 'Preview', handler: () => this.showDatasetPreviewModal(target) },
                { name: 'Delete', handler: () => {
                    if (confirm('Remove this dataset from the indicator?')) {
                        target.remove();
                        this.flagUnsaved();
                    }
                }}
            ];
        } else if (isPillar) {
            // Special menu for pillars (no move or delete)
            menuItems = [
                { name: 'Preview', handler: () => this.showPreviewModal(target) },
                { name: 'Rename', handler: () => this.renameItem(target) }
            ];
        } else {
            // Standard menu for indicators and categories
            menuItems = [
                { name: 'Preview', handler: () => this.showPreviewModal(target) },
                { name: 'Move to', handler: () => this.promptMove(target) },
                { name: 'Rename', handler: () => this.renameItem(target) },
                { name: 'Delete', handler: () => this.deleteItem(target) }
            ];

            // Only show "Edit Score Function" for indicators
            if (target.dataset.type === 'indicator') {
                menuItems.push({ name: 'Edit Score Function', handler: () => this.editScoreFunction(target) });
            }
        }

        menuItems.forEach(a => {
            const i = document.createElement('li');
            i.textContent = a.name;
            i.tabIndex = 0;
            i.addEventListener('click', () => { a.handler(); m.remove(); });
            m.appendChild(i);
        });
        document.body.appendChild(m);
        document.addEventListener('click', () => m.remove(), { once: true });
    }

    promptMove(el) {
        // Create styled modal for moving items
        const modal = this.createMoveToModal(el);
        document.body.appendChild(modal);

        // Focus on the input
        setTimeout(() => {
            const input = modal.querySelector('.move-pillar-input');
            if (input) input.focus();
        }, 100);
    }

    createMoveToModal(element) {
        const overlay = document.createElement('div');
        overlay.className = 'move-pillar-overlay';

        const elementType = element.dataset.type;
        const isIndicator = elementType === 'indicator';
        const isCategory = elementType === 'category';

        let destinationOptions = [];
        let destinationType = '';
        let instructionText = '';
        let titleText = '';

        if (isCategory) {
            // Categories move to pillars
            destinationType = 'pillar';
            titleText = 'Move\u0020Category\u0020to\u0020Pillar';
            instructionText = 'Select\u0020destination\u0020pillar\u0020or\u0020enter\u0020pillar\u0020name/code:';

            const pillarInfo = this.container.querySelectorAll('.pillar-column');
            destinationOptions = Array.from(pillarInfo).map(col => {
                const name = col.dataset.pillar;
                const codeInput = col.querySelector('.pillar-code-input');
                const code = codeInput ? codeInput.value.trim() : '';
                return { name, code, element: col };
            }).filter(p => p.name && p.code);
        } else if (isIndicator) {
            // Indicators move to categories
            destinationType = 'category';
            titleText = 'Move\u0020Indicator\u0020to\u0020Category';
            instructionText = 'Select\u0020destination\u0020category\u0020or\u0020enter\u0020category\u0020name/code:';

            const categoryBoxes = this.container.querySelectorAll('.category-box');
            destinationOptions = Array.from(categoryBoxes).map(cat => {
                const codeInput = cat.querySelector('.category-code-input');
                const nameEl = cat.querySelector('.customization-category-header-title');
                const code = codeInput ? codeInput.value.trim() : '';
                const name = nameEl ? nameEl.textContent.trim() : '';
                return { name, code, element: cat };
            }).filter(c => c.name && c.code);
        }

        const optionsHtml = destinationOptions.map(opt =>
            `<button class="pillar-option\u0020clickable" type="button" data-dest-name="${opt.name}" data-dest-code="${opt.code}">
                <strong>${opt.code}</strong>\u0020-\u0020${opt.name}
            </button>`
        ).join('');

        // Create dynamic placeholder from available codes
        const placeholderCodes = destinationOptions.slice(0, 3).map(p => p.code).join(',\u0020');
        const placeholder = placeholderCodes ? `Enter\u0020${destinationType}\u0020name\u0020or\u0020code\u0020(e.g.,\u0020${placeholderCodes})` : `Enter\u0020${destinationType}\u0020name\u0020or\u0020code`;

        overlay.innerHTML = `
            <div class="move-pillar-modal">
                <div class="move-pillar-header">
                    <h3>${titleText}</h3>
                    <button class="modal-close-btn" type="button">×</button>
                </div>
                <div class="move-pillar-body">
                    <p>${instructionText}</p>
                    <div class="pillar-options-list">
                        ${optionsHtml}
                    </div>
                    <input type="text" class="move-pillar-input" placeholder="${placeholder}">
                </div>
                <div class="move-pillar-actions">
                    <button class="modal-cancel-btn" type="button">Cancel</button>
                    <button class="modal-confirm-btn" type="button">Move</button>
                </div>
            </div>
        `;

        const modal = overlay.querySelector('.move-pillar-modal');
        const input = overlay.querySelector('.move-pillar-input');
        const confirmBtn = overlay.querySelector('.modal-confirm-btn');
        const cancelBtn = overlay.querySelector('.modal-cancel-btn');
        const closeBtn = overlay.querySelector('.modal-close-btn');
        const optionButtons = overlay.querySelectorAll('.pillar-option.clickable');

        // Add click handlers to destination option buttons
        optionButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const destCode = btn.dataset.destCode;
                input.value = destCode;
                input.focus();
            });
        });

        const handleMove = () => {
            const userInput = input.value.trim();
            if (!userInput) {
                overlay.remove();
                return;
            }
            // Find destination by name or code (case-insensitive)
            const destination = destinationOptions.find(opt => {
                return opt.name.toLowerCase() === userInput.toLowerCase() ||
                       opt.code.toLowerCase() === userInput.toLowerCase();
            });

            if (destination) {
                if (isCategory) {
                    // Move category to pillar's categories-container
                    const targetContainer = destination.element.querySelector('.categories-container');
                    if (targetContainer) {
                        targetContainer.appendChild(element);
                        this.flagUnsaved();
                        overlay.remove();
                        console.log(`Category\u0020moved\u0020to\u0020pillar:\u0020${userInput}`);
                    } else {
                        alert('Error:\u0020Could\u0020not\u0020find\u0020categories\u0020container\u0020in\u0020the\u0020target\u0020pillar');
                    }
                } else if (isIndicator) {
                    // Move indicator to category's indicators-container
                    const targetContainer = destination.element.querySelector('.indicators-container');
                    if (targetContainer) {
                        targetContainer.appendChild(element);
                        this.flagUnsaved();
                        overlay.remove();
                        console.log(`Indicator\u0020moved\u0020to\u0020category:\u0020${userInput}`);
                    } else {
                        alert('Error:\u0020Could\u0020not\u0020find\u0020indicators\u0020container\u0020in\u0020the\u0020target\u0020category');
                    }
                }
            } else {
                alert(`${destinationType.charAt(0).toUpperCase() + destinationType.slice(1)}\u0020"${userInput}"\u0020not\u0020found.\u0020Please\u0020use\u0020a\u0020valid\u0020${destinationType}\u0020name\u0020or\u0020code.`);
            }
        };

        const handleCancel = () => {
            overlay.remove();
        };

        // Event listeners
        confirmBtn.addEventListener('click', handleMove);
        cancelBtn.addEventListener('click', handleCancel);
        closeBtn.addEventListener('click', handleCancel);

        // Enter key to confirm
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleMove();
            }
        });

        // Escape key to cancel
        overlay.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                handleCancel();
            }
        });

        // Click outside to cancel
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                handleCancel();
            }
        });

        return overlay;
    }

    renameItem(el) {
        const ed = el.querySelector('[contenteditable]');
        if (ed) ed.focus();
    }

    deleteItem(el) {
        if (!confirm('Delete this item?')) return;

        // Determine item type and code
        const itemType = el.dataset.itemType;

        if (itemType === 'Indicator') {
            const indicatorCode = el.dataset.indicatorCode;
            if (indicatorCode) {
                // Use API method which handles removal and action recording
                const result = this.removeIndicator(indicatorCode);
                if (!result.success) {
                    console.warn('Failed to remove indicator:', result.error);
                    el.remove(); // Fallback to direct removal
                }
            } else {
                // No code set yet - just remove from DOM
                el.remove();
            }
        } else if (itemType === 'Category') {
            const categoryCode = el.dataset.categoryCode;
            if (categoryCode) {
                // Confirm cascade removal of nested indicators
                const indicatorsContainer = el.querySelector('.indicators-container');
                const indicatorCount = indicatorsContainer ? indicatorsContainer.querySelectorAll('[data-indicator-code]').length : 0;

                let cascade = true;
                if (indicatorCount > 0) {
                    cascade = confirm(`This category contains ${indicatorCount} indicator(s). Remove them as well?`);
                }

                // Use API method
                const result = this.removeCategory(categoryCode, { cascade });
                if (!result.success) {
                    console.warn('Failed to remove category:', result.error);
                    el.remove(); // Fallback to direct removal
                }
            } else {
                // No code set yet - just remove from DOM
                el.remove();
            }
        } else {
            // Unknown type - fallback to direct removal
            el.remove();
        }
    }

    editScoreFunction(indicatorCard) {
        // Find the collapsible section
        const collapsible = indicatorCard.querySelector('.indicator-collapsible');
        if (!collapsible) return;

        // Expand the indicator if it's collapsed
        if (collapsible.dataset.expanded !== 'true') {
            collapsible.dataset.expanded = 'true';
            this.applyExpansionState(collapsible, true);
        }

        // Find and focus the score function editor
        const scoreFunctionEl = indicatorCard.querySelector('.editable-score-function');
        if (scoreFunctionEl) {
            // Use setTimeout to ensure the expansion animation completes
            setTimeout(() => {
                scoreFunctionEl.focus();

                // Place cursor at the end of the content
                const range = document.createRange();
                const selection = window.getSelection();
                range.selectNodeContents(scoreFunctionEl);
                range.collapse(false); // false means collapse to end
                selection.removeAllRanges();
                selection.addRange(range);

                // Scroll into view if needed
                scoreFunctionEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
        }
    }

    showPreviewModal(target) {
        const itemType = target.dataset.type;
        let itemCode = '';
        let itemName = '';

        // Extract code and name based on type
        if (itemType === 'indicator') {
            const codeInput = target.querySelector('.indicator-code-input');
            const nameEl = target.querySelector('.indicator-name');
            itemCode = codeInput ? codeInput.value.trim().toUpperCase() : '';
            itemName = nameEl ? nameEl.textContent.trim() : 'Indicator';
        } else if (itemType === 'category') {
            const codeInput = target.querySelector('.category-code-input');
            const nameEl = target.querySelector('.customization-category-header-title');
            itemCode = codeInput ? codeInput.value.trim().toUpperCase() : '';
            itemName = nameEl ? nameEl.textContent.trim() : 'Category';
        } else if (itemType === 'pillar') {
            const codeInput = target.querySelector('.pillar-code-input');
            const nameEl = target.querySelector('.pillar-name');
            itemCode = codeInput ? codeInput.value.trim().toUpperCase() : '';
            itemName = nameEl ? nameEl.textContent.trim() : 'Pillar';
        }

        // Validate we have a code
        if (!itemCode) {
            alert('Cannot\u0020preview:\u0020No\u0020code\u0020assigned\u0020to\u0020this\u0020item\u0020yet.');
            return;
        }

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'preview-modal-overlay';

        overlay.innerHTML = `
            <div class="preview-modal">
                <div class="preview-modal-header">
                    <h3>\u0020${itemName}\u0020(${itemCode})</h3>
                    <button class="modal-close-btn" type="button">×</button>
                </div>
                <div class="preview-modal-body">
                    <div id="preview-chart-container"></div>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const modal = overlay.querySelector('.preview-modal');
        const closeBtn = overlay.querySelector('.modal-close-btn');
        const chartContainer = overlay.querySelector('#preview-chart-container');

        // Store chart reference for cleanup
        let chartInstance = null;

        // Instantiate appropriate chart
        try {
            if (itemType === 'indicator') {
                chartInstance = new IndicatorPanelChart(chartContainer, itemCode);
            } else {
                chartInstance = new ScorePanelChart(chartContainer, itemCode);
            }

            // Add to global charts array for tracking
            if (window.SSPICharts) {
                window.SSPICharts.push(chartInstance);
            }
        } catch (error) {
            console.error('Error creating preview chart:', error);
            chartContainer.innerHTML = `<div style="padding: 2rem; text-align: center; color: var(--error-color);">
                <p>Error\u0020loading\u0020preview\u0020chart.</p>
                <p>${error.message}</p>
            </div>`;
        }

        // Close handler
        const closeModal = () => {
            // Destroy chart if it exists
            if (chartInstance && typeof chartInstance.destroy === 'function') {
                try {
                    chartInstance.destroy();
                } catch (error) {
                    console.error('Error destroying chart:', error);
                }
            }

            // Remove from global charts array
            if (window.SSPICharts && chartInstance) {
                const index = window.SSPICharts.indexOf(chartInstance);
                if (index > -1) {
                    window.SSPICharts.splice(index, 1);
                }
            }

            // Remove overlay
            overlay.remove();
        };

        // Event listeners for closing
        closeBtn.addEventListener('click', closeModal);

        // Close on escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);

        // Close on click outside modal
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeModal();
            }
        });
    }

    showDatasetPreviewModal(datasetItem) {
        // Extract dataset code from the data attribute
        const datasetCode = datasetItem.dataset.datasetCode;

        if (!datasetCode) {
            alert('Cannot\u0020preview:\u0020No\u0020dataset\u0020code\u0020found.');
            return;
        }

        // Get dataset name from the UI
        const datasetNameEl = datasetItem.querySelector('.dataset-name');
        const datasetName = datasetNameEl ? datasetNameEl.textContent.trim() : datasetCode;

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'preview-modal-overlay';

        overlay.innerHTML = `
            <div class="preview-modal">
                <div class="preview-modal-header">
                    <h3>Dataset\u0020:\u0020${datasetName}\u0020(${datasetCode})</h3>
                    <button class="modal-close-btn" type="button">×</button>
                </div>
                <div class="preview-modal-body">
                    <div id="preview-chart-container"></div>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const modal = overlay.querySelector('.preview-modal');
        const closeBtn = overlay.querySelector('.modal-close-btn');
        const chartContainer = overlay.querySelector('#preview-chart-container');

        // Store chart reference for cleanup
        let chartInstance = null;

        // Instantiate DatasetPanelChart
        try {
            chartInstance = new DatasetPanelChart(chartContainer, datasetCode);

            // Add to global charts array for tracking
            if (window.SSPICharts) {
                window.SSPICharts.push(chartInstance);
            }
        } catch (error) {
            console.error('Error creating dataset preview chart:', error);
            chartContainer.innerHTML = `<div style="padding: 2rem; text-align: center; color: var(--error-color);">
                <p>Error\u0020loading\u0020dataset\u0020preview\u0020chart.</p>
                <p>${error.message}</p>
            </div>`;
        }

        // Close handler
        const closeModal = () => {
            // Destroy chart if it exists
            if (chartInstance && typeof chartInstance.destroy === 'function') {
                try {
                    chartInstance.destroy();
                } catch (error) {
                    console.error('Error destroying chart:', error);
                }
            }

            // Remove from global charts array
            if (window.SSPICharts && chartInstance) {
                const index = window.SSPICharts.indexOf(chartInstance);
                if (index > -1) {
                    window.SSPICharts.splice(index, 1);
                }
            }

            // Remove overlay
            overlay.remove();
        };

        // Event listeners for closing
        closeBtn.addEventListener('click', closeModal);

        // Close on escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);

        // Close on click outside modal
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeModal();
            }
        });
    }

    markInvalidIndicatorPlacements() {
        /**
         * Scans all pillar columns and marks indicators that are placed
         * outside of categories as temporarily invalid.
         * This provides visual feedback that these indicators need to be
         * moved into a category.
         */
        const pillarColumns = this.container.querySelectorAll('.pillar-column');

        pillarColumns.forEach(col => {
            // Check direct children of pillar column
            Array.from(col.children).forEach(child => {
                if (child.classList.contains('indicator-card')) {
                    // This indicator is a direct child of pillar (not in category)
                    if (!child.classList.contains('temporary-invalid-placement')) {
                        child.classList.add('temporary-invalid-placement');
                        child.title = 'This indicator needs to be moved into a category';
                    }
                } else if (child.dataset && child.dataset.type === 'indicator') {
                    // Catch any other indicator types
                    if (!child.classList.contains('temporary-invalid-placement')) {
                        child.classList.add('temporary-invalid-placement');
                        child.title = 'This indicator needs to be moved into a category';
                    }
                }
            });

            // Check direct children of categories-container
            const categoriesContainer = col.querySelector('.categories-container');
            if (categoriesContainer) {
                Array.from(categoriesContainer.children).forEach(child => {
                    // If it's an indicator card but NOT inside a category-box
                    if (child.classList.contains('indicator-card') && !child.closest('.category-box')) {
                        if (!child.classList.contains('temporary-invalid-placement')) {
                            child.classList.add('temporary-invalid-placement');
                            child.title = 'This indicator needs to be moved into a category';
                        }
                    } else if (child.dataset && child.dataset.type === 'indicator' && !child.closest('.category-box')) {
                        if (!child.classList.contains('temporary-invalid-placement')) {
                            child.classList.add('temporary-invalid-placement');
                            child.title = 'This indicator needs to be moved into a category';
                        }
                    }
                });
            }

            // Remove invalid class from indicators that ARE properly in categories
            const categoriesInPillar = col.querySelectorAll('.category-box');
            categoriesInPillar.forEach(category => {
                const indicatorsInCategory = category.querySelectorAll('.indicator-card');
                indicatorsInCategory.forEach(indicator => {
                    indicator.classList.remove('temporary-invalid-placement');
                    if (indicator.title === 'This indicator needs to be moved into a category') {
                        indicator.removeAttribute('title');
                    }
                });
            });
        });
    }

    markInvalidNestedCategories() {
        /**
         * Scans all categories and marks any that contain nested categories
         * as temporarily invalid. This provides visual feedback that nested
         * categories are not allowed.
         */

        // First, remove all nested category warnings
        this.container.querySelectorAll('.category-box').forEach(category => {
            category.classList.remove('nested-category-invalid');
            if (category.title === 'This category contains nested categories - please move them out') {
                category.removeAttribute('title');
            }
        });

        // Check all categories for nested categories
        this.container.querySelectorAll('.category-box').forEach(category => {
            const nestedCategories = category.querySelectorAll('.category-box');

            if (nestedCategories.length > 0) {
                // Mark this category as invalid
                category.classList.add('nested-category-invalid');
                category.title = 'This category contains nested categories - please move them out';

                // Also mark each nested category as invalid
                nestedCategories.forEach(nested => {
                    nested.classList.add('nested-category-invalid');
                    nested.title = 'This is a nested category - please move it to the pillar level';
                });
            }
        });
    }

    validate(z) {
        // If no specific zone provided, validate all drop zones
        if (!z) {
            this.container.querySelectorAll('.drop-zone').forEach(zone => this.validate(zone));
            return;
        }

        const selector = z.dataset.accept === 'indicator' ? '.indicator-card' : '.category-box';
        const items = z.querySelectorAll(selector);
        const ok = items.length >= 1 && items.length <= 10;
        z.classList.toggle('invalid', !ok);
        if (!ok) {
            z.title = 'Must have 1–10 items';
        } else {
            z.removeAttribute('title');
        }
    }

    exportMetadata() {
        const metadataItems = [];
        const pillars = {};
        const categories = {};
        const indicators = {};

        // Track indices for TreeIndex construction
        const pillarIndexMap = {};
        const categoryIndexMap = {};
        const indicatorIndexMap = {};

        // Collect all items from the DOM
        this.container.querySelectorAll('.pillar-column').forEach((pillarCol, pillarIdx) => {
            const pillarName = pillarCol.querySelector('.pillar-name').textContent.trim();
            const pillarCode = pillarCol.querySelector('.pillar-code-input').value.trim();
            if (pillarCode) {
                pillarIndexMap[pillarCode] = pillarIdx;
                pillars[pillarCode] = {
                    code: pillarCode,
                    name: pillarName,
                    categories: [],
                    itemOrder: pillarIdx,  // Start from 0
                    pillarIdx: pillarIdx
                };

                pillarCol.querySelectorAll('.category-box').forEach((catBox, catIdx) => {
                    const categoryName = catBox.querySelector('.customization-category-header-title').textContent.trim();
                    const categoryCode = catBox.querySelector('.category-code-input').value.trim();
                    if (categoryCode) {
                        pillars[pillarCode].categories.push(categoryCode);
                        categoryIndexMap[categoryCode] = { pillarIdx, catIdx };
                        categories[categoryCode] = {
                            code: categoryCode,
                            name: categoryName,
                            pillarCode: pillarCode,
                            indicators: [],
                            itemOrder: catIdx,  // Start from 0
                            pillarIdx: pillarIdx,
                            catIdx: catIdx
                        };

                        catBox.querySelectorAll('.indicator-card').forEach((indCard, indIdx) => {
                            const indicatorName = indCard.querySelector('.indicator-name').textContent.trim();
                            const indicatorCode = indCard.querySelector('.indicator-code-input').value.trim();
                            if (indicatorCode) {
                                categories[categoryCode].indicators.push(indicatorCode);
                                indicatorIndexMap[indicatorCode] = { pillarIdx, catIdx, indIdx };

                                const datasetCodes = [];
                                indCard.querySelectorAll('.dataset-item').forEach(item => {
                                    const datasetCode = item.dataset.datasetCode;
                                    if (datasetCode) {
                                        datasetCodes.push(datasetCode);
                                    }
                                });

                                // Read score function from contenteditable element
                                const scoreFunctionEl = indCard.querySelector('.editable-score-function');
                                const scoreFunction = scoreFunctionEl?.textContent?.trim() || '';

                                indicators[indicatorCode] = {
                                    code: indicatorCode,
                                    name: indicatorName,
                                    categoryCode: categoryCode,
                                    pillarCode: pillarCode,
                                    datasetCodes: datasetCodes,
                                    scoreFunction: scoreFunction,
                                    itemOrder: indIdx,  // Start from 0
                                    pillarIdx: pillarIdx,
                                    catIdx: catIdx,
                                    indIdx: indIdx
                                };
                            }
                        });
                    }
                });
            }
        });

        // Create root SSPI item
        const pillarCodes = Object.keys(pillars).sort();
        if (pillarCodes.length > 0) {
            metadataItems.push({
                DocumentType: "SSPIDetail",
                ItemType: "SSPI",
                ItemCode: "SSPI",
                ItemName: "Custom SSPI",
                Children: pillarCodes,
                PillarCodes: pillarCodes,
                TreeIndex: [0, -1, -1, -1],
                TreePath: "sspi",
                ItemOrder: 0
            });
        }

        // Create pillar items
        Object.values(pillars).forEach(pillar => {
            metadataItems.push({
                DocumentType: "PillarDetail",
                ItemType: "Pillar",
                ItemCode: pillar.code,
                ItemName: pillar.name,
                Children: pillar.categories,
                CategoryCodes: pillar.categories,
                Pillar: pillar.name,
                PillarCode: pillar.code,
                TreeIndex: [0, pillar.pillarIdx, -1, -1],
                TreePath: `sspi/${pillar.code.toLowerCase()}`,
                ItemOrder: pillar.itemOrder
            });
        });

        // Create category items
        Object.values(categories).forEach(category => {
            metadataItems.push({
                DocumentType: "CategoryDetail",
                ItemType: "Category",
                ItemCode: category.code,
                ItemName: category.name,
                Children: category.indicators,
                IndicatorCodes: category.indicators,
                Category: category.name,
                CategoryCode: category.code,
                Divisor: category.indicators.length,
                TreeIndex: [0, category.pillarIdx, category.catIdx, -1],
                TreePath: `sspi/${category.pillarCode.toLowerCase()}/${category.code.toLowerCase()}`,
                ItemOrder: category.itemOrder
            });
        });

        // Create indicator items
        Object.values(indicators).forEach(indicator => {
            metadataItems.push({
                DocumentType: "IndicatorDetail",
                ItemType: "Indicator",
                ItemCode: indicator.code,
                ItemName: indicator.name,
                Children: [],
                DatasetCodes: indicator.datasetCodes,
                Indicator: indicator.name,
                IndicatorCode: indicator.code,
                Divisor: 1,
                Footnote: null,
                ScoreFunction: indicator.scoreFunction,
                TreeIndex: [0, indicator.pillarIdx, indicator.catIdx, indicator.indIdx],
                TreePath: `sspi/${indicator.pillarCode.toLowerCase()}/${indicator.categoryCode.toLowerCase()}/${indicator.code.toLowerCase()}`,
                ItemOrder: indicator.itemOrder
            });
        });

        console.log(metadataItems)
        return metadataItems;
    }

    /**
     * Export data in format suitable for scoring pipeline
     * @returns {Object} Structure data with metadata for scoring
     */
    exportForScoring() {
        const metadata = this.exportMetadata();
        const structureData = this.convertMetadataToStructure(metadata);
        
        return {
            metadata: metadata,
            structure: structureData,
            exportedAt: new Date().toISOString(),
            totalItems: metadata.length,
            hasUnsavedChanges: this.unsavedChanges
        };
    }

    /**
     * Convert metadata format to frontend structure format for compatibility
     * @param {Array} metadata - SSPI metadata items
     * @returns {Array} Structure items for frontend consumption
     */
    convertMetadataToStructure(metadata) {
        const structure = [];
        
        // Find all indicators and build structure from them
        const indicators = metadata.filter(item => item.ItemType === 'Indicator');
        
        indicators.forEach(indicator => {
            // Find related pillar and category
            const pillar = metadata.find(item => 
                item.ItemType === 'Pillar' && 
                item.ItemCode === indicator.PillarCode
            );
            const category = metadata.find(item => 
                item.ItemType === 'Category' && 
                item.ItemCode === indicator.CategoryCode
            );
            
            // Convert datasets to expected format
            const datasets = (indicator.DatasetCodes || []).map(code => ({
                code: code
            }));
            
            structure.push({
                Indicator: indicator.ItemName || indicator.Indicator || indicator.ItemCode,
                IndicatorCode: indicator.ItemCode,
                Category: category ? (category.ItemName || category.Category || category.ItemCode) : 'Unknown',
                CategoryCode: indicator.CategoryCode,
                Pillar: pillar ? (pillar.ItemName || pillar.Pillar || pillar.ItemCode) : 'Unknown',
                PillarCode: indicator.PillarCode,
                ItemOrder: indicator.ItemOrder || 1,  // Default to 1 if not set (must be positive)
                datasets: datasets
            });
        });
        
        // Sort by item order and codes
        structure.sort((a, b) => {
            if (a.ItemOrder !== b.ItemOrder) {
                return a.ItemOrder - b.ItemOrder;
            }
            return a.IndicatorCode.localeCompare(b.IndicatorCode);
        });
        
        return structure;
    }

    /**
     * Toggle the collapse state of the visualization section
     */
    toggleVisualizationCollapse() {
        const section = this.visualizationSection;

        // Toggle collapsed state - arrow rotation handled by CSS
        section.classList.toggle('collapsed');
    }

    /**
     * Refresh the visualization by re-scoring the current structure
     */
    async refreshVisualization() {
        if (!this.isVisualizationOpen) return;

        // Show confirmation if there are unsaved changes
        if (this.unsavedChanges) {
            const proceed = confirm('You have unsaved changes to the structure. Would you like to score the current (unsaved) structure?');
            if (!proceed) return;
        }

        // Re-run the scoring process
        await this.scoreAndVisualize();
    }

    /**
     * Close the visualization section
     */
    closeVisualization() {
        if (!this.visualizationSection) return;

        // Destroy chart instance if exists
        if (this.currentChart && typeof this.currentChart.destroy === 'function') {
            this.currentChart.destroy();
            this.currentChart = null;
        }

        // Hide the section
        this.visualizationSection.style.display = 'none';
        this.isVisualizationOpen = false;
        this.currentConfigId = null;

        // Update button text back to original
        const scoreBtn = document.querySelector('.sspi-toolbar button[title*="Generate scores"]');
        if (scoreBtn) {
            scoreBtn.textContent = 'Score & Visualize';
        }
    }

    /**
     * Show the visualization section with loading state
     */
    showVisualizationSection() {
        if (!this.visualizationSection) return;

        this.visualizationSection.style.display = 'block';
        this.isVisualizationOpen = true;

        // Ensure not collapsed (arrow rotation handled by CSS)
        this.visualizationSection.classList.remove('collapsed');

        // Update button text
        const scoreBtn = document.querySelector('.sspi-toolbar button[title*="Generate scores"]');
        if (scoreBtn) {
            scoreBtn.textContent = 'Update Visualization';
        }
    }

    /**
     * Show loading state in visualization container
     */
    showVisualizationLoading(message = 'Scoring structure...') {
        const chartContainer = this.visualizationSection.querySelector('.visualization-chart-container');
        chartContainer.classList.add('loading');
        chartContainer.innerHTML = `
            <div class="visualization-loading-spinner"></div>
            <div class="visualization-loading-text">${message}</div>
        `;
    }

    /**
     * Show error state in visualization container
     */
    showVisualizationError(message, details = '') {
        const chartContainer = this.visualizationSection.querySelector('.visualization-chart-container');
        chartContainer.classList.remove('loading');
        chartContainer.innerHTML = `
            <div class="visualization-error">
                <div class="visualization-error-icon">⚠️</div>
                <div class="visualization-error-message">${message}</div>
                ${details ? `<div class="visualization-error-details">${details}</div>` : ''}
            </div>
        `;
    }

    /**
     * Score the current structure and display visualization inline
     */
    async scoreAndVisualize() {
        try {
            // Validate current structure
            const validationErrors = this.validateHierarchy();
            if (validationErrors.length > 0) {
                const proceed = confirm(
                    `The current structure is invalid:\n${validationErrors.join('\n')}`
                );
                return;
            }
            this.showLoadingState('Preparing structure for scoring...');
            const exportData = this.exportForScoring();
            if (!exportData.structure || exportData.structure.length === 0) {
                this.hideLoadingState();
                alert('No indicators found in the current structure. Please add some indicators before scoring.');
                return;
            }
            // Check if we should save first, or save if no config ID exists yet
            let configId = null;
            if (this.unsavedChanges) {
                const shouldSave = confirm('You have unsaved changes. Would you like to save this configuration before scoring?');
                if (shouldSave) {
                    configId = await this.saveConfiguration();
                    exportData.hasUnsavedChanges = false;
                }
            } else {
                // Try to find existing config ID if this was loaded from a saved config
                const selector = document.querySelector('.config-selector select');
                if (selector && selector.value) {
                    configId = selector.value;
                }
            }
            // Show visualization section with loading state
            this.showVisualizationSection();
            this.showVisualizationLoading('Scoring structure...');
            this.hideLoadingState();
            // If no config ID, require saving first
            if (!configId) {
                this.showVisualizationError(
                    'Configuration Not Saved',
                    'Please save your configuration before scoring. Use the "Save" button in the toolbar.'
                );
                return;
            }
            this.currentConfigId = configId;
            this.showVisualizationLoading('Computing scores across years and countries...');
            const scoreResponse = await fetch(`/api/v1/customize/score-dynamic/${configId}`, {
                method: 'POST'
            });
            if (!scoreResponse.ok) {
                const errorData = await scoreResponse.json();
                throw new Error(errorData.error || `Scoring failed: ${scoreResponse.statusText}`);
            }
            const scoreResult = await scoreResponse.json();
            if (!scoreResult.success) {
                throw new Error(scoreResult.error || 'Scoring failed');
            }
            console.log(`Scored ${scoreResult.documents_scored} documents for ${scoreResult.countries_count} countries`);
            // Initialize chart with scored data
            this.showVisualizationLoading('Loading visualization...');
            await this.initializeInlineChart(configId, scoreResult);
            // Show success notification
            this.showNotification(
                '✓ Visualization loaded successfully!',
                'success',
                3000
            );
        } catch (error) {
            this.hideLoadingState();
            console.error('Error in scoreAndVisualize:', error);
            // Show error in visualization section if it's open
            if (this.isVisualizationOpen) {
                this.showVisualizationError(
                    'Scoring Error',
                    error.message || 'An unexpected error occurred while scoring the structure.'
                );
            } else {
                alert(`Error preparing visualization: ${error.message}`);
            }
        }
    }

    /**
     * Initialize the inline chart with scored data
     * @param {string} configId - The configuration ID
     * @param {object} scoreResult - The scoring result from the API
     */
    async initializeInlineChart(configId, scoreResult) {
        const chartContainer = this.visualizationSection.querySelector('.visualization-chart-container');
        chartContainer.classList.remove('loading');
        chartContainer.innerHTML = '';
        try {
            // Check if CustomSSPIPanelChart is available
            if (typeof CustomSSPIPanelChart === 'undefined') {
                throw new Error('CustomSSPIPanelChart class not loaded. Please ensure the script is included.');
            }

            // Destroy existing chart if present
            if (this.currentChart) {
                if (typeof this.currentChart.destroy === 'function') {
                    this.currentChart.destroy();
                }
                this.currentChart = null;
            }

            // Create a container div for the chart
            const chartDiv = document.createElement('div');
            chartDiv.id = `custom-sspi-chart-${configId}`;
            chartDiv.style.width = '100%';
            chartDiv.style.minHeight = '400px';
            chartContainer.appendChild(chartDiv);

            // Initialize the panel chart
            this.currentChart = new CustomSSPIPanelChart(chartDiv, {
                configId: configId,
                initialData: scoreResult.data || null,
                inlineMode: true,
                autoLoad: true
            });
            // Wait for chart to initialize
            await new Promise(resolve => setTimeout(resolve, 100));
            console.log('Inline chart initialized successfully');
        } catch (error) {
            console.error('Error initializing inline chart:', error);
            this.showVisualizationError(
                'Chart Initialization Error',
                error.message || 'Failed to load the visualization component.'
            );
            throw error;
        }
    }

    /**
     * Show a temporary notification to the user
     * @param {string} message - The message to display
     * @param {string} type - The notification type ('success', 'error', 'info')
     * @param {number} duration - Duration in milliseconds (default: 3000)
     */
    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
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
        document.body.appendChild(notification);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }
        }, duration);
        
        return notification;
    }

    // Helper methods for undo/redo
    getElementName(element) {
        if (!element) return 'Unknown';

        // Try to get name from indicator, category, or pillar
        const indicatorName = element.querySelector('.indicator-name');
        if (indicatorName) return indicatorName.textContent.trim() || 'Unnamed\u0020Indicator';

        const categoryName = element.querySelector('.customization-category-header-title');
        if (categoryName) return categoryName.textContent.trim() || 'Unnamed\u0020Category';

        const pillarName = element.querySelector('.pillar-name');
        if (pillarName) return pillarName.textContent.trim() || 'Unnamed\u0020Pillar';

        return 'Unnamed\u0020Item';
    }

    getLocationName(container) {
        if (!container) return 'Unknown\u0020Location';

        // Check if it's a pillar's categories container
        const pillarColumn = container.closest('.pillar-column');
        if (pillarColumn && container.classList.contains('categories-container')) {
            const pillarName = pillarColumn.querySelector('.pillar-name');
            return pillarName ? `"${pillarName.textContent.trim()}"\u0020pillar` : 'Pillar';
        }

        // Check if it's inside a category
        const categoryBox = container.closest('.category-box');
        if (categoryBox && container.classList.contains('indicators-container')) {
            const categoryName = categoryBox.querySelector('.customization-category-header-title');
            return categoryName ? `category\u0020"${categoryName.textContent.trim()}"` : 'Category';
        }

        return 'Container';
    }

    rigUnloadListener() {
        window.addEventListener('beforeunload', () => {
            let stateLookup = {};

            // Save indicator expansion states
            const indicators = this.container.querySelectorAll('.indicator-card');
            indicators.forEach((indicator) => {
                const collapsible = indicator.querySelector('.indicator-collapsible');
                const codeInput = indicator.querySelector('.indicator-code-input');
                const code = codeInput ? codeInput.value.trim() : '';

                if (code && collapsible) {
                    stateLookup[`ind_${code}`] = collapsible.dataset.expanded;
                }
            });

            // Save category expansion states
            const categories = this.container.querySelectorAll('.category-box');
            categories.forEach((category) => {
                const collapsible = category.querySelector('.category-collapsible');
                const codeInput = category.querySelector('.category-code-input');
                const code = codeInput ? codeInput.value.trim() : '';

                if (code && collapsible) {
                    stateLookup[`cat_${code}`] = collapsible.dataset.expanded;
                }
            });

            window.observableStorage.setItem('customizableSSPIExpansionState', stateLookup);
            // Save scroll position
            window.observableStorage.setItem('customizableSSPIScrollX', window.scrollX);
            window.observableStorage.setItem('customizableSSPIScrollY', window.scrollY);
        });
    }

    restoreExpansionState() {
        const cachedStateObject = window.observableStorage.getItem('customizableSSPIExpansionState');
        if (!cachedStateObject) return;
        // Restore indicator expansion states
        const indicators = this.container.querySelectorAll('.indicator-card');
        indicators.forEach((indicator) => {
            const collapsible = indicator.querySelector('.indicator-collapsible');
            const codeInput = indicator.querySelector('.indicator-code-input');
            const code = codeInput ? codeInput.value.trim() : '';
            if (code && collapsible) {
                const key = `ind_${code}`;
                if (cachedStateObject.hasOwnProperty(key)) {
                    const cachedState = cachedStateObject[key] === 'true';
                    this.applyExpansionState(collapsible, cachedState);
                }
            }
        });
        // Restore category expansion states
        const categories = this.container.querySelectorAll('.category-box');
        categories.forEach((category) => {
            const collapsible = category.querySelector('.category-collapsible');
            const codeInput = category.querySelector('.category-code-input');
            const code = codeInput ? codeInput.value.trim() : '';
            if (code && collapsible) {
                const key = `cat_${code}`;
                if (cachedStateObject.hasOwnProperty(key)) {
                    const cachedState = cachedStateObject[key] === 'true';
                    this.applyExpansionState(collapsible, cachedState);
                }
            }
        });
    }

    applyExpansionState(collapsible, isExpanded) {
        collapsible.dataset.expanded = isExpanded.toString();
        // Update visual state
        const content = collapsible.querySelector('.indicator-config, .category-content');
        if (content) {
            if (isExpanded) {
                content.style.display = '';
                content.style.maxHeight = '';
            } else {
                content.style.display = 'none';
            }
        }
        const toggleBtn = collapsible.querySelector('.collapse-toggle-btn');
        if (toggleBtn) {
            const icon = toggleBtn.querySelector('.collapse-icon');
            if (icon) {
                if (isExpanded) {
                    icon.style.transform = 'rotate(0deg)';
                } else {
                    icon.style.transform = 'rotate(-90deg)';
                }
            }
        }
    }

    restoreScrollPosition() {
        const scrollX = window.observableStorage.getItem('customizableSSPIScrollX');
        const scrollY = window.observableStorage.getItem('customizableSSPIScrollY');
        if (scrollX !== null && scrollY !== null) {
            requestAnimationFrame(() => {  // Use requestAnimationFrame to ensure DOM is fully rendered
                window.scrollTo(parseInt(scrollX), parseInt(scrollY));
            });
        }
    }

    handleToggle(toggleBtn) {
        // Find the collapsible section (indicator-collapsible or category-collapsible)
        const collapsible = toggleBtn.closest('.indicator-collapsible, .category-collapsible');
        if (!collapsible) return;
        const isCurrentlyExpanded = collapsible.dataset.expanded === 'true';
        const newExpandedState = !isCurrentlyExpanded;
        collapsible.dataset.expanded = newExpandedState.toString();
        this.applyExpansionState(collapsible, newExpandedState);
    }

    // Hierarchy management methods
    updateHierarchyOnAdd(element, elementType) {
        this.flagUnsaved();
        // Skip logging and validation during bulk import to reduce noise
        if (!this.isImporting) {
            console.log(`Added ${elementType}:`, element);
            const errors = this.validateHierarchy();
            if (errors.length > 0) {
                console.warn('Hierarchy validation errors after add:', errors);
            }
        }
        this.changeLog.push({ 
            changeType: "Added" + elementType,
            element: element,
        })
    }

    updateHierarchyOnRemove(element, elementType) {
        this.flagUnsaved();
        console.log(`Removed ${elementType}:`, element);

        // Skip validation during bulk import to avoid noisy warnings
        if (!this.isImporting) {
            const errors = this.validateHierarchy();
            if (errors.length > 0) {
                console.warn('Hierarchy validation errors after remove:', errors);
            }
        }
    }

    validateHierarchy() {
        const errors = [];
        const warnings = [];
        // Check that all pillars have at least one category
        this.container.querySelectorAll('.pillar-column').forEach(pillar => {
            const pillarName = pillar.querySelector('.pillar-name').textContent.trim();
            const pillarCode = pillar.querySelector('.pillar-code-input').value.trim();
            const categories = pillar.querySelectorAll('.category-box');
            if (categories.length === 0) {
                warnings.push('Pillar ' + pillarName + " (" + pillarCode + ") has no categories");
            }
        });
        
        // Check that all categories have at least one indicator
        this.container.querySelectorAll('.category-box').forEach(category => {
            const categoryName = category.querySelector('.customization-category-header-title').textContent.trim();
            const categoryCode = category.querySelector('.category-code-input').value.trim();
            const indicators = category.querySelectorAll('.indicator-card');
            
            if (indicators.length === 0) {
                warnings.push(`Category "${categoryName}" (${categoryCode}) has no indicators`);
            }
        });
        
        // Check that all indicators have at least one dataset
        this.container.querySelectorAll('.indicator-card').forEach(indicator => {
            const indicatorName = indicator.querySelector('.indicator-name').textContent.trim();
            const indicatorCode = indicator.querySelector('.indicator-code-input').value.trim();
            const datasets = indicator.querySelectorAll('.dataset-item');

            if (datasets.length === 0) {
                warnings.push(`Indicator "${indicatorName}" (${indicatorCode}) has no datasets`);
            }
        });

        // Check for nested categories (categories inside categories)
        this.container.querySelectorAll('.category-box').forEach(category => {
            const categoryName = category.querySelector('.customization-category-header-title').textContent.trim();
            const categoryCode = category.querySelector('.category-code-input').value.trim();
            const nestedCategories = category.querySelectorAll('.category-box');

            if (nestedCategories.length > 0) {
                errors.push(`Category "${categoryName}" (${categoryCode}) contains nested categories. Nested categories are not allowed.`);
            }
        });

        // Check for duplicate codes
        const pillarCodes = new Set();
        const categoryCodes = new Set();
        const indicatorCodes = new Set();
        
        this.container.querySelectorAll('.pillar-code-input').forEach(input => {
            const code = input.value.trim().toUpperCase();
            if (code) {
                if (pillarCodes.has(code)) {
                    errors.push(`Duplicate pillar code: ${code}`);
                } else {
                    pillarCodes.add(code);
                }
            }
        });
        
        this.container.querySelectorAll('.category-code-input').forEach(input => {
            const code = input.value.trim().toUpperCase();
            if (code) {
                if (categoryCodes.has(code)) {
                    errors.push(`Duplicate category code: ${code}`);
                } else {
                    categoryCodes.add(code);
                }
            }
        });
        
        this.container.querySelectorAll('.indicator-code-input').forEach(input => {
            const code = input.value.trim().toUpperCase();
            if (code) {
                if (indicatorCodes.has(code)) {
                    errors.push(`Duplicate indicator code: ${code}`);
                } else {
                    indicatorCodes.add(code);
                }
            }
        });
        
        // Log results
        if (warnings.length > 0) {
            console.warn('Hierarchy warnings:', warnings);
        }
        
        return { errors, warnings };
    }

    showHierarchyStatus() {
        const result = this.validateHierarchy();
        const stats = this.getMetadataStats();
        
        let message = `Metadata Stats:\n`;
        message += `- Pillars: ${stats.pillars}\n`;
        message += `- Categories: ${stats.categories}\n`;
        message += `- Indicators: ${stats.indicators}\n`;
        message += `- Total Datasets: ${stats.datasets}\n\n`;
        
        if (result.errors.length > 0) {
            message += `Errors (${result.errors.length}):\n`;
            result.errors.forEach(error => message += `- ${error}\n`);
            message += '\n';
        }
        
        if (result.warnings.length > 0) {
            message += `Warnings (${result.warnings.length}):\n`;
            result.warnings.forEach(warning => message += `- ${warning}\n`);
        }
        
        if (result.errors.length === 0 && result.warnings.length === 0) {
            message += 'Metadata is valid! ✓';
        }
        
        alert(message);
    }

    /**
     * Show the changes history modal
     */
    showChangesHistory() {
        if (!window.ChangesHistoryModal) {
            console.error('ChangesHistoryModal class not loaded');
            alert('Changes history feature is not available. Please refresh the page.');
            return;
        }

        // Create and show modal
        const modal = new ChangesHistoryModal({
            actionHistory: this.actionHistory,
            mode: 'modal'
        });

        modal.show();
    }

    getMetadataStats() {
        return {
            pillars: this.container.querySelectorAll('.pillar-column').length,
            categories: this.container.querySelectorAll('.category-box').length,
            indicators: this.container.querySelectorAll('.indicator-card').length,
            datasets: this.container.querySelectorAll('.dataset-item').length
        };
    }

    // Auto-loading functionality
    async loadInitialData() {
        // CRITICAL: Always load available datasets first (before metadata)
        // This ensures dataset selector has complete list, regardless of cache
        await this.loadAvailableDatasets();

        // Then check if we have cached modifications for structure
        if (this.hasCachedModifications()) {
            try {
                const loaded = await this.loadCachedState();
                if (loaded) {
                    this.showCacheRestoredIndicator();
                    this.restoreExpansionState();
                    this.restoreScrollPosition();
                    return;
                }
            } catch (error) {
                console.warn('Failed to load cached modifications, falling back to default:', error);
            }
        }

        // Fall back to loading default metadata
        await this.loadDefaultMetadata();
        this.restoreExpansionState();
        this.restoreScrollPosition();
    }
    
    showCacheRestoredIndicator() {
        // Create a temporary indicator showing cached data was restored
        const indicator = document.createElement('div');
        indicator.className = 'cache-restored-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--green-accent);
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
        `;
        indicator.textContent = '✓ Restored from previous session';
        
        document.body.appendChild(indicator);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => {
                    if (indicator.parentNode) {
                        indicator.parentNode.removeChild(indicator);
                    }
                }, 300);
            }
        }, 3000);
    }
    
    async discardChanges() {
        try {
            // Clear the cache first
            this.clearCache();
            
            // Show loading state briefly
            this.showLoadingState('Discarding changes...');
            
            // Clear unsaved state
            this.clearUnsavedState();
            
            // Brief delay to show the loading state, then hide it and reload
            setTimeout(() => {
                this.hideLoadingState();
                // Small additional delay to ensure UI updates are processed
                setTimeout(() => {
                    window.location.reload();
                }, 100);
            }, 400);
            
        } catch (error) {
            this.hideLoadingState();
            console.error('Error discarding changes:', error);
            alert('Error discarding changes. Please try again.');
        }
    }

    async loadDefaultMetadata() {
        if (this.isLoading) {
            console.log('Already loading metadata, skipping...');
            return;
        }

        try {
            this.showLoadingState('Loading default SSPI metadata...');

            const response = await this.fetch('/api/v1/customize/default-structure');

            if (response.success) {
                console.log('Auto-loading default SSPI metadata:', response.stats);

                // Fallback: Load dataset details if loadAvailableDatasets failed
                // (datasetDetails should already be populated from separate cache/API call)
                if (response.all_datasets && Array.isArray(response.all_datasets)) {
                    const currentCount = Object.keys(this.datasetDetails).length;
                    if (currentCount === 0 && response.all_datasets) {
                        console.log('Dataset details not yet loaded, building map from all_datasets as fallback');
                        response.all_datasets.forEach(ds => {
                            this.datasetDetails[ds.DatasetCode] = ds;
                        });
                        console.log(`Loaded ${response.all_datasets.length} dataset details for selection (fallback)`);
                    } else {
                        console.log(`Dataset details already loaded (${currentCount} datasets)`);
                    }
                }

                // Import the metadata efficiently
                await this.importDataAsync(response.metadata);

                // Capture baseline for action history tracking
                this.actionHistory.captureBaseline(response.metadata);

                this.hideLoadingState();

                // Don't flag as unsaved for auto-loaded default metadata
                this.clearUnsavedState();

                console.log('Default SSPI metadata loaded successfully');
            } else {
                this.handleLoadError('Failed to load default metadata: ' + response.error);
            }
        } catch (error) {
            console.error('Error auto-loading default metadata:', error);
            this.handleLoadError('Network error loading default metadata');
        }
    }

    showLoadingState(message = 'Loading...') {
        this.isLoading = true;
        
        // Create loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('sspi-loading');
        loadingDiv.textContent = message;
        loadingDiv.id = 'sspi-loading-indicator';
        
        // Hide the main container and show loading
        this.container.style.display = 'none';
        this.parentElement.appendChild(loadingDiv);
        
        // Disable toolbar buttons
        this.setToolbarDisabled(true);
    }

    hideLoadingState() {
        this.isLoading = false;
        
        // Remove loading indicator
        const loadingDiv = this.parentElement.querySelector('#sspi-loading-indicator');
        if (loadingDiv) {
            loadingDiv.remove();
        }
        
        // Show the main container
        this.container.style.display = '';
        
        // Enable toolbar buttons
        this.setToolbarDisabled(false);
    }

    handleLoadError(errorMessage) {
        this.isLoading = false;
        
        // Remove loading indicator
        const loadingDiv = this.parentElement.querySelector('#sspi-loading-indicator');
        if (loadingDiv) {
            loadingDiv.remove();
        }
        
        // Show error state
        const errorDiv = document.createElement('div');
        errorDiv.classList.add('sspi-error');
        errorDiv.id = 'sspi-error-indicator';
        
        const errorText = document.createElement('div');
        errorText.textContent = errorMessage;
        
        const retryBtn = document.createElement('button');
        retryBtn.textContent = 'Load Default Metadata';
        retryBtn.addEventListener('click', () => {
            errorDiv.remove();
            this.loadDefaultMetadata();
        });
        
        errorDiv.appendChild(errorText);
        errorDiv.appendChild(retryBtn);
        this.parentElement.appendChild(errorDiv);
        
        // Show the main container in case user wants to build manually
        this.container.style.display = '';
        this.setToolbarDisabled(false);
        
        console.error('SSPI metadata loading failed:', errorMessage);
    }

    setToolbarDisabled(disabled) {
        const toolbar = this.parentElement.querySelector('.sspi-toolbar');
        if (toolbar) {
            const buttons = toolbar.querySelectorAll('button');
            buttons.forEach(btn => {
                btn.disabled = disabled;
                if (disabled) {
                    btn.style.opacity = '0.5';
                    btn.style.cursor = 'not-allowed';
                } else {
                    btn.style.opacity = '';
                    btn.style.cursor = '';
                }
            });
        }
    }

    // Build hierarchy tree from metadata items
    buildHierarchyTree(metadataItems) {
        const itemsById = {};
        const hierarchy = {
            sspi: null,
            pillars: {},
            categories: {},
            indicators: {}
        };
        
        // Index all items by their ItemCode
        metadataItems.forEach(item => {
            itemsById[item.ItemCode] = item;
        });
        
        // Build hierarchy structure
        metadataItems.forEach(item => {
            switch (item.ItemType) {
                case 'SSPI':
                    hierarchy.sspi = item;
                    break;
                case 'Pillar':
                    hierarchy.pillars[item.ItemCode] = item;
                    break;
                case 'Category':
                    hierarchy.categories[item.ItemCode] = item;
                    break;
                case 'Indicator':
                    hierarchy.indicators[item.ItemCode] = item;
                    break;
            }
        });
        
        return { hierarchy, itemsById };
    }
    
    // Optimized async import method for metadata
    async importDataAsync(metadataItems) {
        console.log('Importing', metadataItems.length, 'metadata items asynchronously');
        console.log(`Using ${Object.keys(this.datasetDetails).length} dataset details from map`);

        // Set importing flag to suppress validation warnings during bulk import
        this.isImporting = true;

        // Clear existing content
        this.container.querySelectorAll('.category-box, .indicator-card').forEach(e => e.remove());

        // Build hierarchy tree
        const { hierarchy, itemsById } = this.buildHierarchyTree(metadataItems);
        
        if (!hierarchy.sspi) {
            console.error('No SSPI root item found in metadata');
            return;
        }
        
        // Process each pillar from the SSPI's Children list
        const pillarCodes = hierarchy.sspi.Children || [];
        
        for (let i = 0; i < pillarCodes.length; i++) {
            const pillarCode = pillarCodes[i];
            const pillarItem = hierarchy.pillars[pillarCode];
            
            if (pillarItem) {
                await this.processPillarFromMetadata(pillarItem, hierarchy);
            }
            
            // Yield control to browser between pillars
            if (i < pillarCodes.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 0));
            }
        }

        console.log('Async metadata import completed');

        // Clear importing flag
        this.isImporting = false;

        // Clear undo/redo history after initial import
        // This ensures dataset additions during load are not in history
        this.actionHistory.clear();
        console.log('Cleared undo/redo history after initial metadata import');

        // Mark any indicators that are outside categories
        this.markInvalidIndicatorPlacements();
        // Mark any nested categories
        this.markInvalidNestedCategories();

        // Validate hierarchy once at the end of import
        const validation = this.validateHierarchy();
        if (validation.errors && validation.errors.length > 0) {
            console.error('Hierarchy errors after import:', validation.errors);
        }
        if (validation.warnings && validation.warnings.length > 0) {
            console.warn('Hierarchy warnings after import:', validation.warnings);
        }
    }

    async processPillarFromMetadata(pillarItem, hierarchy) {
        // Find the corresponding pillar column in the UI
        const col = Array.from(this.container.querySelectorAll('.pillar-column'))
            .find(c => c.dataset.pillar === pillarItem.ItemName);
        
        if (!col) {
            console.warn(`No UI column found for pillar: ${pillarItem.ItemName}`);
            return;
        }
        
        // Update pillar code
        const pillarCodeInput = col.querySelector('.pillar-code-input');
        if (pillarCodeInput) {
            pillarCodeInput.value = pillarItem.ItemCode;
        }

        // Set data attributes for efficient querying
        col.dataset.pillarCode = pillarItem.ItemCode;
        col.dataset.itemCode = pillarItem.ItemCode;
        col.dataset.itemType = 'Pillar';

        // Update pillar name
        const pillarNameEl = col.querySelector('.pillar-name');
        if (pillarNameEl) {
            pillarNameEl.textContent = pillarItem.ItemName;
        }

        const categoriesContainer = col.querySelector('.categories-container');
        if (!categoriesContainer) return;
        
        // Create document fragment for efficient DOM building
        const fragment = document.createDocumentFragment();
        
        // Process categories from pillar's Children list
        const categoryCodes = pillarItem.Children || [];
        
        for (const categoryCode of categoryCodes) {
            const categoryItem = hierarchy.categories[categoryCode];
            
            if (categoryItem) {
                const catEl = this.createCategoryElement();

                // Set category details
                const categoryHeader = catEl.querySelector('.customization-category-header-title');
                const categoryCodeInput = catEl.querySelector('.category-code-input');

                if (categoryHeader) categoryHeader.textContent = categoryItem.ItemName;
                if (categoryCodeInput) categoryCodeInput.value = categoryItem.ItemCode;

                // Set data attributes for efficient querying
                catEl.dataset.categoryCode = categoryItem.ItemCode;
                catEl.dataset.itemCode = categoryItem.ItemCode;

                // Add indicators to this category
                const indicatorsContainer = catEl.querySelector('.indicators-container');
                const indicatorCodes = categoryItem.Children || [];
                
                indicatorCodes.forEach(indicatorCode => {
                    const indicatorItem = hierarchy.indicators[indicatorCode];
                    
                    if (indicatorItem) {
                        const indEl = this.createIndicatorElement();
                        
                        // Populate indicator fields
                        const indicatorName = indEl.querySelector('.indicator-name');
                        const indicatorCodeInput = indEl.querySelector('.indicator-code-input');
                        const lowerGoalpost = indEl.querySelector('.lower-goalpost');
                        const upperGoalpost = indEl.querySelector('.upper-goalpost');
                        const invertedCheckbox = indEl.querySelector('.inverted-checkbox');
                        const scoreFunctionEl = indEl.querySelector('.editable-score-function');

                        if (indicatorName) indicatorName.textContent = indicatorItem.ItemName || '';
                        if (indicatorCodeInput) indicatorCodeInput.value = indicatorItem.ItemCode || '';

                        // Set data attributes for efficient querying
                        indEl.dataset.indicatorCode = indicatorItem.ItemCode;
                        indEl.dataset.itemCode = indicatorItem.ItemCode;

                        // Populate score function if present
                        if (scoreFunctionEl) {
                            if (indicatorItem.ScoreFunction) {
                                scoreFunctionEl.textContent = indicatorItem.ScoreFunction;
                                if (!this.isImporting) {
                                    console.log(`Set score function for ${indicatorItem.ItemCode}:`, indicatorItem.ScoreFunction);
                                }
                            } else if (!this.isImporting) {
                                console.log(`No ScoreFunction for ${indicatorItem.ItemCode}`);
                            }
                        }

                        // Add datasets if present - lookup from DatasetCodes using the map
                        const datasetCodes = indicatorItem.DatasetCodes || [];
                        if (!this.isImporting) {
                            console.log(`Processing ${indicatorItem.ItemCode}: ${datasetCodes.length} dataset codes`);
                        }

                        if (datasetCodes.length > 0) {
                            const selectedDatasetsDiv = indEl.querySelector('.selected-datasets');

                            if (!selectedDatasetsDiv) {
                                console.error(`No .selected-datasets div found for indicator ${indicatorItem.ItemCode}`);
                            } else {
                                if (!this.isImporting) {
                                    console.log(`Found .selected-datasets div for ${indicatorItem.ItemCode}, adding ${datasetCodes.length} datasets`);
                                }

                                datasetCodes.forEach((datasetCode, idx) => {
                                    // Lookup dataset details from map
                                    const datasetDetail = this.datasetDetails[datasetCode];

                                    if (!datasetDetail) {
                                        console.warn(`Dataset ${datasetCode} not found in datasetDetails map for indicator ${indicatorItem.ItemCode}`);
                                        return;
                                    }

                                    if (!this.isImporting) {
                                        console.log(`Adding dataset ${datasetCode} to ${indicatorItem.ItemCode}`);
                                    }
                                    this.addDatasetToIndicatorSilent(
                                        selectedDatasetsDiv,
                                        datasetDetail,
                                        1.0  // Default weight
                                    );
                                });

                                // Verify datasets were added
                                if (!this.isImporting) {
                                    const addedDatasets = selectedDatasetsDiv.querySelectorAll('.dataset-item');
                                    console.log(`After adding: ${addedDatasets.length} dataset items in DOM for ${indicatorItem.ItemCode}`);
                                }
                            }
                        } else if (!this.isImporting) {
                            console.log(`No datasets to add for ${indicatorItem.ItemCode}`);
                        }
                        
                        indicatorsContainer.appendChild(indEl);
                    }
                });
                
                fragment.appendChild(catEl);
            }
        }
        
        // Single DOM append for all categories in this pillar
        categoriesContainer.appendChild(fragment);
        this.validate(categoriesContainer);
    }

    importData(data) {
        console.log('Importing data:', data);
        this.container.querySelectorAll('.category-box, .indicator-card').forEach(e => e.remove());

        const grouping = {};
        const pillarCodes = {};
        const categoryOrders = {};  // Track category ItemOrder for sorting

        data.forEach(item => {
            const { Pillar, Category, CategoryCode, PillarCode, ItemOrder, ItemType } = item;

            // Store pillar codes
            if (PillarCode) {
                pillarCodes[Pillar] = PillarCode;
            }

            grouping[Pillar] = grouping[Pillar] || {};
            grouping[Pillar][Category] = grouping[Pillar][Category] || {
                CategoryCode: CategoryCode || '',
                items: []
            };
            grouping[Pillar][Category].items.push(item);

            // Store category order (from Category items in metadata)
            if (ItemType === 'Category' && CategoryCode) {
                const key = `${Pillar}:${Category}`;
                categoryOrders[key] = ItemOrder || 999;
            }
        });
        
        this.pillars.forEach(p => {
            const col = Array.from(this.container.querySelectorAll('.pillar-column'))
                .find(c => c.dataset.pillar === p);
            if (!col) return;
            
            // Set pillar code if available
            const pillarCodeInput = col.querySelector('.pillar-code-input');
            if (pillarCodeInput && pillarCodes[p]) {
                pillarCodeInput.value = pillarCodes[p];
            }
            
            if (!grouping[p]) return;

            const zone = col.querySelector('.categories-container');

            // Sort categories by ItemOrder before creating them
            const categoriesArray = Object.entries(grouping[p]);
            categoriesArray.sort((a, b) => {
                const keyA = `${p}:${a[0]}`;
                const keyB = `${p}:${b[0]}`;
                const orderA = categoryOrders[keyA] || 999;
                const orderB = categoryOrders[keyB] || 999;
                return orderA - orderB;
            });

            categoriesArray.forEach(([catName, info]) => {
                const catEl = this.createCategoryElement();
                catEl.querySelector('.customization-category-header-title').textContent = catName;
                
                // Set category code
                const categoryCodeInput = catEl.querySelector('.category-code-input');
                if (categoryCodeInput && info.CategoryCode) {
                    categoryCodeInput.value = info.CategoryCode;
                }
                zone.appendChild(catEl);
                info.items.sort((a, b) => a.ItemOrder - b.ItemOrder).forEach(item => {
                    const indEl = this.createIndicatorElement();
                    indEl.querySelector('.indicator-name').textContent = item.Indicator || 'New Indicator';
                    const indicatorCodeInput = indEl.querySelector('.indicator-code-input');
                    if (indicatorCodeInput && item.IndicatorCode) {
                        indicatorCodeInput.value = item.IndicatorCode;
                    }
                    indEl.title = item.Description || '';
                    const scoreFunctionEl = indEl.querySelector('.editable-score-function');
                    if (scoreFunctionEl && item.ScoreFunction) {
                        scoreFunctionEl.textContent = item.ScoreFunction;
                    }
                    if (item.datasets && Array.isArray(item.datasets)) {
                        const selectedDatasetsDiv = indEl.querySelector('.selected-datasets');
                        item.datasets.forEach(dataset => {
                            this.addDatasetToIndicator(
                                selectedDatasetsDiv, 
                                dataset.dataset_code, 
                                dataset.weight || 1.0
                            );
                        });
                    }
                    catEl.querySelector('.indicators-container').appendChild(indEl);
                });
                this.validate(catEl.querySelector('.indicators-container'));
            });
        });
        this.markInvalidIndicatorPlacements();// Mark any indicators that are outside categories
        this.markInvalidNestedCategories();// Mark any nested categories
        this.restoreExpansionState(); // Restore expansion state and scroll position after import
        this.restoreScrollPosition();
    }

    autoGenerateMissingCodes() {
        // Auto-generate missing pillar codes
        this.container.querySelectorAll('.pillar-column').forEach(pillarCol => {
            const pillarCodeInput = pillarCol.querySelector('.pillar-code-input');
            const pillarName = pillarCol.querySelector('.pillar-name').textContent.trim();

            if (pillarCodeInput && !pillarCodeInput.value.trim() && pillarName) {
                let generatedCode = this.generateCodeFromName(pillarName, 'pillar');
                let attempt = 1;

                // If code is not unique, try adding numbers
                while (generatedCode && !this.isCodeUnique(generatedCode, 'pillar', pillarCodeInput) && attempt < 10) {
                    generatedCode = this.generateCodeFromName(pillarName, 'pillar').substring(0, 2) + attempt;
                    attempt++;
                }

                if (generatedCode && this.isCodeUnique(generatedCode, 'pillar', pillarCodeInput)) {
                    pillarCodeInput.value = generatedCode;
                }
            }
        });

        // Auto-generate missing category codes
        this.container.querySelectorAll('.category-box').forEach(catBox => {
            const categoryCodeInput = catBox.querySelector('.category-code-input');
            const categoryName = catBox.querySelector('.customization-category-header-title').textContent.trim();

            if (categoryCodeInput && !categoryCodeInput.value.trim() && categoryName) {
                let generatedCode = this.generateCodeFromName(categoryName, 'category');
                let attempt = 1;

                // If code is not unique, try adding numbers
                while (generatedCode && !this.isCodeUnique(generatedCode, 'category', categoryCodeInput) && attempt < 10) {
                    generatedCode = this.generateCodeFromName(categoryName, 'category').substring(0, 2) + attempt;
                    attempt++;
                }

                if (generatedCode && this.isCodeUnique(generatedCode, 'category', categoryCodeInput)) {
                    categoryCodeInput.value = generatedCode;
                }
            }
        });

        // Auto-generate missing indicator codes
        this.container.querySelectorAll('.indicator-card').forEach(indCard => {
            const indicatorCodeInput = indCard.querySelector('.indicator-code-input');
            const indicatorName = indCard.querySelector('.indicator-name').textContent.trim();

            if (indicatorCodeInput && !indicatorCodeInput.value.trim() && indicatorName) {
                let generatedCode = this.generateCodeFromName(indicatorName, 'indicator');
                let attempt = 1;

                // If code is not unique, try adding numbers
                while (generatedCode && !this.isCodeUnique(generatedCode, 'indicator', indicatorCodeInput) && attempt < 100) {
                    const baseCode = this.generateCodeFromName(indicatorName, 'indicator').substring(0, 4);
                    generatedCode = baseCode + ('0' + attempt).slice(-2);
                    attempt++;
                }

                if (generatedCode && this.isCodeUnique(generatedCode, 'indicator', indicatorCodeInput)) {
                    indicatorCodeInput.value = generatedCode;
                }
            }
        });
    }

    async saveConfiguration() {
        try {
            // Auto-generate missing codes before saving
            this.autoGenerateMissingCodes();

            // Validate before saving
            const validation = this.validateHierarchy();
            if (validation.errors.length > 0) {
                let errorMessage = 'Cannot save configuration due to validation errors:\n\n';
                validation.errors.forEach(error => errorMessage += `• ${error}\n`);
                alert(errorMessage);
                return;
            }

            const name = prompt('Enter a name for this configuration:');
            if (!name) return;

            const metadata = this.exportMetadata();

            const response = await this.fetch('/api/v1/customize/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    metadata: metadata
                })
            });

            if (response.success) {
                this.clearUnsavedState();

                // Update cache with saved state instead of clearing it
                this.cacheCurrentState();

                this.showNotification('Configuration "' + name + '" saved successfully!', 'success', 3000);
                this.loadConfigurationsList(); // Refresh the list
            } else {
                this.showNotification('Error saving configuration: ' + response.error, 'error', 5000);
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showNotification('Error saving configuration. Please try again.', 'error', 5000);
        }
    }

    async loadConfigurationsList() {
        try {
            const response = await this.fetch('/api/v1/customize/list');
            if (response.success && response.configurations) {
                this.updateConfigurationsDropdown(response.configurations);
            }
        } catch (error) {
            console.error('Error loading configurations list:', error);
        }
    }

    updateConfigurationsDropdown(configurations) {
        // Remove existing dropdown if it exists
        const existingDropdown = this.parentElement.querySelector('.config-selector');
        if (existingDropdown) {
            existingDropdown.remove();
        }

        if (configurations.length === 0) return;

        // Create configuration selector dropdown
        const selectorContainer = document.createElement('div');
        selectorContainer.classList.add('config-selector');
        selectorContainer.style.marginBottom = '1rem';

        const label = document.createElement('label');
        label.textContent = 'Load Configuration: ';
        label.style.marginRight = '0.5rem';

        const select = document.createElement('select');
        select.style.marginRight = '0.5rem';

        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select a configuration...';
        select.appendChild(defaultOption);

        // Add configuration options
        configurations.forEach(config => {
            const option = document.createElement('option');
            option.value = config.config_id;
            option.textContent = config.name;
            select.appendChild(option);
        });

        const loadButton = document.createElement('button');
        loadButton.textContent = 'Load';
        loadButton.addEventListener('click', async () => {
            const configId = select.value;
            if (configId) {
                await this.loadConfiguration(configId);
            }
        });

        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'Delete';
        deleteButton.style.marginLeft = '0.5rem';
        deleteButton.addEventListener('click', async () => {
            const configId = select.value;
            if (configId) {
                const selectedOption = select.options[select.selectedIndex];
                const configName = selectedOption.textContent;
                if (confirm(`Are you sure you want to delete "${configName}"?`)) {
                    await this.deleteConfiguration(configId);
                }
            }
        });

        selectorContainer.append(label, select, loadButton, deleteButton);
        this.parentElement.insertBefore(selectorContainer, this.parentElement.firstChild);
    }

    async loadConfiguration(configId) {
        try {
            const response = await this.fetch('/api/v1/customize/load/' + configId);

            if (response.success && response.configuration) {
                // Clear cache before loading saved configuration
                this.clearCache();

                this.importData(response.configuration.metadata);
                this.clearUnsavedState();
                this.showNotification('Configuration "' + response.configuration.name + '" loaded successfully!', 'success', 3000);
            } else {
                this.showNotification('Error loading configuration: ' + response.error, 'error', 5000);
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
            this.showNotification('Error loading configuration. Please try again.', 'error', 5000);
        }
    }

    async deleteConfiguration(configId) {
        try {
            const response = await this.fetch('/api/v1/customize/delete/' + configId, {
                method: 'DELETE'
            });

            if (response.success) {
                this.showNotification('Configuration deleted successfully!', 'success', 3000);
                this.loadConfigurationsList(); // Refresh the list
            } else {
                this.showNotification('Error deleting configuration: ' + response.error, 'error', 5000);
            }
        } catch (error) {
            console.error('Error deleting configuration:', error);
            this.showNotification('Error deleting configuration. Please try again.', 'error', 5000);
        }
    }

    setupCodeValidation(input, type) {
        if (!input) return;
        // Find validation message - structure differs between types
        // Indicators: inside parent's previous sibling | Categories/Pillars: next sibling
        const validationMessage = input.closest('.category-code-section, .indicator-code-section, .customization-pillar-header')
            ?.querySelector('.code-validation-message');
        input.addEventListener('input', (e) => {
            let value = e.target.value.toUpperCase();
            e.target.value = value;
            const isValid = this.validateCode(value, type);
            const isUnique = this.isCodeUnique(value, type, input);
            if (!value) {
                this.flashValidationMessage(validationMessage, input, '', '');
            } else if (!isValid) {
                this.flashValidationMessage(validationMessage, input, 'Invalid format', 'error');
            } else if (!isUnique) {
                this.flashValidationMessage(validationMessage, input, 'Code reserved', 'error');
            } else {
                this.flashValidationMessage(validationMessage, input, 'Valid', 'success');
            }
            this.flagUnsaved();
        });
        
        input.addEventListener('blur', () => {
            const newCode = input.value.trim();

            // If no code entered, try to generate one from name
            if (!newCode) {
                const name = this.getNameForCodeInput(input, type);
                if (name) {
                    const generatedCode = this.generateCodeFromName(name, type);
                    if (this.isCodeUnique(generatedCode, type, input)) {
                        input.value = generatedCode;
                        this.flashValidationMessage(validationMessage, input, 'Generated', 'success');
                        // Continue to process the generated code
                        this.processCodeChange(input, generatedCode, type);
                    }
                }
                return;
            }

            // Validate the entered code
            if (!this.validateCode(newCode, type)) {
                return; // Validation message already shown by input handler
            }

            if (!this.isCodeUnique(newCode, type, input)) {
                return; // Validation message already shown by input handler
            }

            // Process the code change
            this.processCodeChange(input, newCode, type);
        });
    }

    /**
     * Process a code change from an input field
     * Calls the appropriate API method to update the code and record the action
     * @param {HTMLInputElement} input - The code input element
     * @param {string} newCode - The new code value
     * @param {string} type - Item type ('indicator', 'category', or 'pillar')
     */
    processCodeChange(input, newCode, type) {
        // Find the parent element (indicator card, category box, or pillar column)
        let element;
        if (type === 'indicator') {
            element = input.closest('.indicator-card');
        } else if (type === 'category') {
            element = input.closest('.category-box');
        } else if (type === 'pillar') {
            element = input.closest('[data-pillar-code]');
        }

        if (!element) {
            console.warn(`Could not find ${type} element for code input`);
            return;
        }

        // Get the old code from data attribute
        const oldCode = type === 'indicator' ? element.dataset.indicatorCode :
                       type === 'category' ? element.dataset.categoryCode :
                       element.dataset.pillarCode;

        // Don't process if code hasn't changed
        if (oldCode === newCode) {
            return;
        }

        // Call the appropriate API method
        let result;
        try {
            if (type === 'indicator') {
                result = this.setIndicatorCode(element, { newCode });
            } else if (type === 'category') {
                result = this.setCategoryCode(element, { newCode });
            } else if (type === 'pillar') {
                result = this.setPillarCode(element, { newCode });
            }

            if (result && !result.success) {
                console.error(`Failed to set ${type} code:`, result.error);
                this.showNotification(`Error: ${result.error}`, 'error', 3000);
                // Revert input to old code
                input.value = oldCode || '';
            }
        } catch (error) {
            console.error(`Error setting ${type} code:`, error);
            this.showNotification(`Error updating code`, 'error', 3000);
            // Revert input to old code
            input.value = oldCode || '';
        }
    }

    validateCode(code, type) {
        if (!code) return false;
        
        switch (type) {
            case 'pillar':
                return /^[A-Z]{2,3}$/.test(code);
            case 'category':
                return /^[A-Z]{3}$/.test(code);
            case 'indicator':
                return /^[A-Z0-9]{6}$/.test(code);
            default:
                return false;
        }
    }

    isCodeUnique(code, type, currentInput) {
        if (!code) return true;
        
        const selector = type === 'pillar' ? '.pillar-code-input' : 
                        type === 'category' ? '.category-code-input' : 
                        '.indicator-code-input';
        
        const allInputs = this.container.querySelectorAll(selector);
        
        for (const input of allInputs) {
            if (input !== currentInput && input.value === code) {
                return false;
            }
        }
        
        return true;
    }

    flashValidationMessage(element, input, message, type) {
        if (!element) return;
        element.textContent = message;
        element.className = 'code-validation-message';
        if (type === 'error') {
            element.classList.add('error');
        } else if (type === 'success') {
            element.classList.add('success');
        }
        input.addEventListener('blur', (event) => {
            if (type) {
                input.classList.add('input-error')
            } else {
                input.classList.remove('input-error')
            }
            element.textContent = '';
            element.classList.remove('error', 'success');
        })
    }

    getNameForCodeInput(input, type) {
        const container = input.closest(type === 'pillar' ? '.customization-pillar-header' : 
                                      type === 'category' ? '.category-box' : 
                                      '.indicator-card');
        
        if (type === 'pillar') {
            return container.querySelector('.pillar-name').textContent.trim();
        } else if (type === 'category') {
            return container.querySelector('.customization-category-header-title').textContent.trim();
        } else if (type === 'indicator') {
            return container.querySelector('.indicator-name').textContent.trim();
        }
        
        return '';
    }

    generateCodeFromName(name, type) {
        if (!name) return '';
        
        // Remove common words and clean the name
        const cleanName = name.toUpperCase()
            .replace(/\b(THE|AND|OR|OF|FOR|IN|ON|AT|TO|A|AN)\b/g, '')
            .replace(/[^A-Z0-9]/g, '');
        
        const maxLength = type === 'indicator' ? 6 : 3;
        
        if (cleanName.length <= maxLength) {
            return cleanName.padEnd(maxLength, '1');
        }
        
        // Take first letters of words, then fill with characters
        const words = name.split(/\s+/);
        let code = '';
        
        // Get first letter of each word
        for (const word of words) {
            if (code.length < maxLength) {
                const firstChar = word.replace(/[^A-Z0-9]/gi, '').charAt(0).toUpperCase();
                if (firstChar && /[A-Z0-9]/.test(firstChar)) {
                    code += firstChar;
                }
            }
        }
        
        // Fill remaining with characters from the original name
        if (code.length < maxLength) {
            for (const char of cleanName) {
                if (code.length >= maxLength) break;
                if (!code.includes(char) && /[A-Z0-9]/.test(char)) {
                    code += char;
                }
            }
        }
        
        // Pad with numbers if still too short
        while (code.length < maxLength) {
            code += '1';
        }
        
        return code.substring(0, maxLength);
    }

    setupDatasetSelection(indicatorElement) {
        const addDatasetBtn = indicatorElement.querySelector('.add-dataset-btn');
        const selectedDatasetsDiv = indicatorElement.querySelector('.selected-datasets');
        
        addDatasetBtn.addEventListener('click', async () => {
            await this.showDatasetSelector(selectedDatasetsDiv);
        });
    }

    async showDatasetSelector(selectedDatasetsDiv) {
        try {
            // Check if we've already reached the limit
            const currentDatasets = selectedDatasetsDiv.querySelectorAll('.dataset-item');
            if (currentDatasets.length >= 10) {
                alert('Maximum of 10 datasets allowed per indicator');
                return;
            }

            // Show dataset selection modal
            this.showDatasetSelectionModal(selectedDatasetsDiv);
        } catch (error) {
            console.error('Error showing dataset selector:', error);
            alert('Error loading datasets. Please try again.');
        }
    }

    async showDatasetSelectionModal(selectedDatasetsDiv) {
        // Get currently selected datasets
        const currentSelections = Array.from(selectedDatasetsDiv.querySelectorAll('.dataset-item'))
            .map(item => item.dataset.datasetCode);

        // Pass dataset details directly - no mapping needed
        const preloadedDatasets = Object.values(this.datasetDetails);

        // Create and configure enhanced dataset selector with preloaded data
        const selector = new DatasetSelector({
            maxSelections: 10,
            multiSelect: true,
            enableSearch: true,
            enableFilters: true,
            showOrganizations: true,
            showTypes: true,
            preloadedDatasets: preloadedDatasets.length > 0 ? preloadedDatasets : null,
            onSelectionChange: (selectedDatasets) => {
                this.updateDatasetSelection(selectedDatasetsDiv, selectedDatasets);
            }
        });

        // Show the enhanced selector
        await selector.show(currentSelections);
    }
    
    updateDatasetSelection(selectedDatasetsDiv, selectedDatasets) {
        // Clear existing selections
        selectedDatasetsDiv.innerHTML = '';

        // Add new selections using full dataset objects
        // Datasets are already in the backend format - no conversion needed
        selectedDatasets.forEach(dataset => {
            // Use addDatasetToIndicatorWithDetails to pass full details directly
            this.addDatasetToIndicatorWithDetails(selectedDatasetsDiv, dataset);
        });

        // IMPORTANT: Always flag unsaved and update cache after dataset selection changes
        // This ensures changes are cached even when removing all datasets
        this.flagUnsaved();
        this.debouncedCacheState();
    }


    findSelectedDatasetsDiv(modal) {
        // This is a bit hacky but works for finding the selected datasets div
        // In a real implementation, we'd pass this more cleanly
        const indicators = document.querySelectorAll('.indicator-card');
        return indicators[indicators.length - 1]?.querySelector('.selected-datasets');
    }

    addDatasetToIndicator(selectedDatasetsDiv, datasetCode) {
        // Check for duplicates
        const existing = selectedDatasetsDiv.querySelector(`[data-dataset-code="${datasetCode}"]`);
        if (existing) {
            alert('Dataset already added');
            return;
        }

        // Get dataset details from the loaded dataset map
        const datasetDetail = this.datasetDetails[datasetCode];
        const datasetName = datasetDetail ? datasetDetail.name : 'Unknown Dataset';
        const datasetTitle = datasetDetail ? `${datasetDetail.description}` : datasetCode;

        // Debug: Log dataset details
        if (!datasetDetail) {
            console.warn(`No dataset details found for ${datasetCode}. Available datasets:`, Object.keys(this.datasetDetails).length);
        }

        const datasetItem = document.createElement('div');
        datasetItem.classList.add('dataset-item');
        datasetItem.dataset.datasetCode = datasetCode;

        const datasetDescription = datasetDetail?.description || 'No description available';
        const datasetOrg = datasetDetail?.organization || 'N/A';
        const datasetOrgCode = datasetDetail?.organizationCode || '';
        const datasetType = datasetDetail?.type || 'N/A';

        datasetItem.dataset.expanded = 'false';
        datasetItem.innerHTML = `
            <div class="dataset-item-header">
                <div class="dataset-info">
                    <span class="dataset-name">${datasetName}</span>
                    <span class="dataset-code">${datasetCode}</span>
                </div>
                <div class="dataset-actions">
                    <button class="remove-dataset" type="button" title="Remove dataset">×</button>
                </div>
            </div>
            <div class="dataset-details-slideout">
                <div class="detail-row">
                    <span class="detail-label">Description:</span>
                    <span class="detail-value">${datasetDescription}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Organization:</span>
                    <span class="detail-value">${datasetOrg}${datasetOrgCode ? ' (' + datasetOrgCode + ')' : ''}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Type:</span>
                    <span class="detail-value">${datasetType}</span>
                </div>
            </div>
        `;

        // Add click handler to entire dataset-item for expand/collapse
        datasetItem.addEventListener('click', (e) => {
            const isExpanded = datasetItem.dataset.expanded === 'true';
            datasetItem.dataset.expanded = (!isExpanded).toString();

            const slideout = datasetItem.querySelector('.dataset-details-slideout');
            if (!isExpanded) {
                slideout.style.maxHeight = slideout.scrollHeight + 'px';
            } else {
                slideout.style.maxHeight = '0';
            }
        });

        datasetItem.querySelector('.remove-dataset').addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent toggle when clicking remove button
            // Record removal action with proper delta structure
            const indicatorCard = selectedDatasetsDiv.closest('.indicator-card');
            const indicatorName = this.getElementName(indicatorCard);
            const indicatorCode = indicatorCard?.dataset.indicatorCode;

            // Get position in dataset list
            const position = Array.from(selectedDatasetsDiv.children).indexOf(datasetItem);

            this.actionHistory.recordAction({
                type: 'remove-dataset',
                message: `Removed\u0020dataset\u0020"${datasetCode}"\u0020from\u0020indicator\u0020"${indicatorName}"`,
                delta: {
                    type: 'remove-dataset',
                    indicatorCode: indicatorCode,
                    datasetCode: datasetCode,
                    datasetDetails: datasetDetail || this.datasetDetails[datasetCode],
                    position: position
                },
                undo: () => {
                    // Re-add the dataset
                    selectedDatasetsDiv.appendChild(datasetItem);
                    this.updateHierarchyOnAdd(datasetItem, 'dataset');
                },
                redo: () => {
                    // Remove it again
                    datasetItem.remove();
                    this.updateHierarchyOnRemove(datasetItem, 'dataset');
                }
            });

            datasetItem.remove();
            this.updateHierarchyOnRemove(datasetItem, 'dataset');
        });

        selectedDatasetsDiv.appendChild(datasetItem);
        this.updateHierarchyOnAdd(datasetItem, 'dataset');

        // Record add action with proper delta structure
        const indicatorCard = selectedDatasetsDiv.closest('.indicator-card');
        const indicatorName = this.getElementName(indicatorCard);
        const indicatorCode = indicatorCard?.dataset.indicatorCode;

        // Get position in dataset list
        const position = Array.from(selectedDatasetsDiv.children).indexOf(datasetItem);

        this.actionHistory.recordAction({
            type: 'add-dataset',
            message: `Added\u0020dataset\u0020"${datasetCode}"\u0020to\u0020indicator\u0020"${indicatorName}"`,
            delta: {
                type: 'add-dataset',
                indicatorCode: indicatorCode,
                datasetCode: datasetCode,
                datasetDetails: datasetDetail || this.datasetDetails[datasetCode],
                position: position
            },
            undo: () => {
                // Remove the dataset
                datasetItem.remove();
                this.updateHierarchyOnRemove(datasetItem, 'dataset');
            },
            redo: () => {
                // Re-add the dataset
                selectedDatasetsDiv.appendChild(datasetItem);
                this.updateHierarchyOnAdd(datasetItem, 'dataset');
            }
        });
    }

    addDatasetToIndicatorWithDetails(selectedDatasetsDiv, datasetDetail) {
        // Add dataset using full details passed directly (no lookup needed)
        const datasetCode = datasetDetail.DatasetCode;

        // Check for duplicates
        const existing = selectedDatasetsDiv.querySelector(`[data-dataset-code="${datasetCode}"]`);
        if (existing) {
            alert('Dataset already added');
            return;
        }

        const datasetName = datasetDetail.DatasetName || 'Unknown Dataset';
        const datasetTitle = datasetDetail.Description || datasetCode;

        const datasetItem = document.createElement('div');
        datasetItem.classList.add('dataset-item');
        datasetItem.dataset.datasetCode = datasetCode;

        // Use exact backend field names
        const datasetDescription = datasetDetail.Description || 'No description available';
        const datasetOrg = datasetDetail.Source?.OrganizationName || 'N/A';
        const datasetOrgCode = datasetDetail.Source?.OrganizationCode || '';
        const formatNumber = (num) => {
            return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        };
        const unitHtml = datasetDetail.Unit ? `
                <div class="detail-row">
                    <span class="detail-label">Unit</span>
                    <span class="detail-value">${datasetDetail.Unit}</span>
                </div>` : '';
        const rangeHtml = datasetDetail.Range ? `
                <div class="detail-row">
                    <span class="detail-label">Range</span>
                    <span class="detail-value">${formatNumber(datasetDetail.Range.yMin)} – ${formatNumber(datasetDetail.Range.yMax)}</span>
                </div>` : '';

        datasetItem.dataset.expanded = 'false';
        datasetItem.innerHTML = `
            <div class="dataset-item-header">
                <div class="dataset-info">
                    <span class="dataset-name">${datasetName}</span>
                    <span class="dataset-code">${datasetCode}</span>
                </div>
                <div class="dataset-actions">
                    <button class="remove-dataset" type="button" title="Remove dataset">×</button>
                </div>
            </div>
            <div class="dataset-details-slideout">
                <div class="detail-row">
                    <span class="detail-label">Description</span>
                    <span class="detail-value">${datasetDescription}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Organization</span>
                    <span class="detail-value">${datasetOrg}${datasetOrgCode ? ' (' + datasetOrgCode + ')' : ''}</span>
                </div>${unitHtml}${rangeHtml}
            </div>
        `;

        // Add click handler to entire dataset-item for expand/collapse
        datasetItem.addEventListener('click', (e) => {
            const isExpanded = datasetItem.dataset.expanded === 'true';
            datasetItem.dataset.expanded = (!isExpanded).toString();

            const slideout = datasetItem.querySelector('.dataset-details-slideout');
            if (!isExpanded) {
                slideout.style.maxHeight = slideout.scrollHeight + 'px';
            } else {
                slideout.style.maxHeight = '0';
            }
        });

        datasetItem.querySelector('.remove-dataset').addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent toggle when clicking remove button
            // Record removal action with proper delta structure
            const indicatorCard = selectedDatasetsDiv.closest('.indicator-card');
            const indicatorName = this.getElementName(indicatorCard);
            const indicatorCode = indicatorCard?.dataset.indicatorCode;

            // Get position in dataset list
            const position = Array.from(selectedDatasetsDiv.children).indexOf(datasetItem);

            this.actionHistory.recordAction({
                type: 'remove-dataset',
                message: `Removed\u0020dataset\u0020"${datasetCode}"\u0020from\u0020indicator\u0020"${indicatorName}"`,
                delta: {
                    type: 'remove-dataset',
                    indicatorCode: indicatorCode,
                    datasetCode: datasetCode,
                    datasetDetails: datasetDetail || this.datasetDetails[datasetCode],
                    position: position
                },
                undo: () => {
                    // Re-add the dataset
                    selectedDatasetsDiv.appendChild(datasetItem);
                    this.updateHierarchyOnAdd(datasetItem, 'dataset');
                },
                redo: () => {
                    // Remove it again
                    datasetItem.remove();
                    this.updateHierarchyOnRemove(datasetItem, 'dataset');
                }
            });

            datasetItem.remove();
            this.updateHierarchyOnRemove(datasetItem, 'dataset');
        });

        selectedDatasetsDiv.appendChild(datasetItem);
        this.updateHierarchyOnAdd(datasetItem, 'dataset');

        // Record add action with proper delta structure
        const indicatorCard = selectedDatasetsDiv.closest('.indicator-card');
        const indicatorName = this.getElementName(indicatorCard);
        const indicatorCode = indicatorCard?.dataset.indicatorCode;

        // Get position in dataset list
        const position = Array.from(selectedDatasetsDiv.children).indexOf(datasetItem);

        this.actionHistory.recordAction({
            type: 'add-dataset',
            message: `Added\u0020dataset\u0020"${datasetCode}"\u0020to\u0020indicator\u0020"${indicatorName}"`,
            delta: {
                type: 'add-dataset',
                indicatorCode: indicatorCode,
                datasetCode: datasetCode,
                datasetDetails: datasetDetail || this.datasetDetails[datasetCode],
                position: position
            },
            undo: () => {
                // Remove the dataset
                datasetItem.remove();
                this.updateHierarchyOnRemove(datasetItem, 'dataset');
            },
            redo: () => {
                // Re-add the dataset
                selectedDatasetsDiv.appendChild(datasetItem);
                this.updateHierarchyOnAdd(datasetItem, 'dataset');
            }
        });
    }

    /**
     * Add a dataset to an indicator without recording undo/redo history for the addition.
     * Used during initial metadata import to avoid polluting history.
     * Dataset removal by user will still be tracked in undo/redo.
     *
     * @param {HTMLElement} selectedDatasetsDiv - Container for datasets
     * @param {Object} datasetDetail - Dataset detail object from backend
     */
    addDatasetToIndicatorSilent(selectedDatasetsDiv, datasetDetail) {
        const datasetCode = datasetDetail.DatasetCode;

        // Check for duplicates
        const existing = selectedDatasetsDiv.querySelector(`[data-dataset-code="${datasetCode}"]`);
        if (existing) {
            console.warn('Dataset already added:', datasetCode);
            return;
        }

        const datasetName = datasetDetail.DatasetName || 'Unknown Dataset';
        const datasetTitle = datasetDetail.Description || datasetCode;

        const datasetItem = document.createElement('div');
        datasetItem.classList.add('dataset-item');
        datasetItem.dataset.datasetCode = datasetCode;

        // Use exact backend field names
        const datasetDescription = datasetDetail.Description || 'No description available';
        const datasetOrg = datasetDetail.Source?.OrganizationName || 'N/A';
        const datasetOrgCode = datasetDetail.Source?.OrganizationCode || '';
        const formatNumber = (num) => {
            return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        };
        const unitHtml = datasetDetail.Unit ? `
                <div class="detail-row">
                    <span class="detail-label">Unit</span>
                    <span class="detail-value">${datasetDetail.Unit}</span>
                </div>` : '';
        const rangeHtml = datasetDetail.Range ? `
                <div class="detail-row">
                    <span class="detail-label">Range</span>
                    <span class="detail-value">${formatNumber(datasetDetail.Range.yMin)} – ${formatNumber(datasetDetail.Range.yMax)}</span>
                </div>` : '';

        datasetItem.dataset.expanded = 'false';
        datasetItem.innerHTML = `
            <div class="dataset-item-header">
                <div class="dataset-info">
                    <span class="dataset-name">${datasetName}</span>
                    <span class="dataset-code">${datasetCode}</span>
                </div>
                <div class="dataset-actions">
                    <button class="remove-dataset" type="button" title="Remove dataset">×</button>
                </div>
            </div>
            <div class="dataset-details-slideout">
                <div class="detail-row">
                    <span class="detail-label">Description</span>
                    <span class="detail-value">${datasetDescription}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Organization</span>
                    <span class="detail-value">${datasetOrg}${datasetOrgCode ? ' (' + datasetOrgCode + ')' : ''}</span>
                </div>${unitHtml}${rangeHtml}
            </div>
        `;

        // Add click handler to entire dataset-item for expand/collapse
        datasetItem.addEventListener('click', (e) => {
            const isExpanded = datasetItem.dataset.expanded === 'true';
            datasetItem.dataset.expanded = (!isExpanded).toString();

            const slideout = datasetItem.querySelector('.dataset-details-slideout');
            if (!isExpanded) {
                slideout.style.maxHeight = slideout.scrollHeight + 'px';
            } else {
                slideout.style.maxHeight = '0';
            }
        });

        datasetItem.querySelector('.remove-dataset').addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent toggle when clicking remove button
            // Record removal action for undo/redo (user action)
            const indicatorCard = selectedDatasetsDiv.closest('.indicator-card');
            const indicatorName = this.getElementName(indicatorCard);

            this.actionHistory.recordAction({
                type: 'remove-dataset',
                message: `Removed\u0020dataset\u0020"${datasetCode}"\u0020from\u0020indicator\u0020"${indicatorName}"`,
                undo: () => {
                    // Re-add the dataset
                    selectedDatasetsDiv.appendChild(datasetItem);
                    this.updateHierarchyOnAdd(datasetItem, 'dataset');
                },
                redo: () => {
                    // Remove it again
                    datasetItem.remove();
                    this.updateHierarchyOnRemove(datasetItem, 'dataset');
                }
            });

            datasetItem.remove();
            this.updateHierarchyOnRemove(datasetItem, 'dataset');
        });

        selectedDatasetsDiv.appendChild(datasetItem);
        this.updateHierarchyOnAdd(datasetItem, 'dataset');

        // NOTE: We do NOT record the add action in undo/redo history
        // This method is only used during initial metadata import
    }

    showDatasetOptionsMenu(buttonElement, datasetCode) {
        // Remove any existing menu
        const existingMenu = document.querySelector('.dataset-options-menu');
        if (existingMenu) {
            existingMenu.remove();
        }

        // Create menu
        const menu = document.createElement('div');
        menu.className = 'dataset-options-menu';
        menu.innerHTML = `
            <div class="menu-item" data-action="rename">
                <span>Rename</span>
            </div>
            <div class="menu-item" data-action="duplicate">
                <span>Duplicate</span>
            </div>
            <div class="menu-item" data-action="info">
                <span>View Info</span>
            </div>
        `;

        // Position menu
        const rect = buttonElement.getBoundingClientRect();
        menu.style.position = 'fixed';
        menu.style.top = rect.bottom + 5 + 'px';
        menu.style.left = rect.left + 'px';
        menu.style.zIndex = '1000';

        // Add menu to document
        document.body.appendChild(menu);

        // Handle menu clicks
        menu.addEventListener('click', (e) => {
            const action = e.target.closest('.menu-item')?.dataset.action;
            if (action) {
                this.handleDatasetMenuAction(action, datasetCode);
                menu.remove();
            }
        });

        // Close menu when clicking outside
        const closeMenu = (e) => {
            if (!menu.contains(e.target) && e.target !== buttonElement) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        };
        setTimeout(() => document.addEventListener('click', closeMenu), 0);
    }

    handleDatasetMenuAction(action, datasetCode) {
        switch (action) {
            case 'rename':
                alert('Rename functionality - placeholder');
                break;
            case 'duplicate':
                alert('Duplicate functionality - placeholder');
                break;
            case 'info':
                alert('Dataset info functionality - placeholder');
                break;
        }
    }

    // Cache management methods

    /**
     * Enrich metadata with full dataset details for caching.
     * This ensures dataset assignments can be fully restored from cache.
     * Uses Dataset Codes as keys to lookup full details from this.datasetDetails.
     *
     * @param {Array} metadata - SSPI metadata items with DatasetCodes arrays
     * @returns {Array} - Enriched metadata with DatasetDetails arrays
     */
    cacheCurrentState() {
        try {
            const metadata = this.exportMetadata();
            // No enrichment! Store only DatasetCodes in metadata
            const cacheData = {
                hasModifications: this.unsavedChanges,
                lastModified: Date.now(),
                metadata: metadata,  // Only DatasetCodes, no DatasetDetails
                datasetDetailsMap: this.datasetDetails,  // Store map separately
                version: this.CACHE_VERSION
            };

            // Check cache size (rough estimate)
            const cacheSize = JSON.stringify(cacheData).length;
            if (cacheSize > 5 * 1024 * 1024) { // 5MB limit
                console.warn('Cache data is too large (>5MB), skipping cache');
                return;
            }

            window.observableStorage.setItem("sspi-custom-modifications", cacheData);
            console.log('SSPI modifications cached successfully with dataset details');
        } catch (error) {
            console.warn('Failed to cache SSPI modifications:', error);

            // Handle specific localStorage errors
            if (error.name === 'QuotaExceededError' || error.name === 'NS_ERROR_DOM_QUOTA_REACHED') {
                this.handleStorageQuotaExceeded();
            }
        }
    }
    
    handleStorageQuotaExceeded() {
        console.warn('localStorage quota exceeded, attempting to free space');
        
        try {
            // Clear any old cache data
            const allKeys = [];
            for (let i = 0; i < localStorage.length; i++) {
                allKeys.push(localStorage.key(i));
            }
            
            // Remove old SSPI cache entries if any exist
            allKeys.forEach(key => {
                if (key && key.startsWith('sspi-') && key !== 'sspi-custom-modifications') {
                    try {
                        localStorage.removeItem(key);
                        console.log('Removed old cache entry:', key);
                    } catch (e) {
                        // Ignore errors when removing individual items
                    }
                }
            });
            
            // Show user notification
            const indicator = document.createElement('div');
            indicator.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #ff9500;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                z-index: 1000;
                max-width: 300px;
                animation: slideInRight 0.3s ease-out;
            `;
            indicator.textContent = '⚠ Storage limit reached. Changes may not be cached across sessions.';
            
            document.body.appendChild(indicator);
            
            setTimeout(() => {
                if (indicator.parentNode) {
                    indicator.style.animation = 'slideOutRight 0.3s ease-in';
                    setTimeout(() => {
                        if (indicator.parentNode) {
                            indicator.parentNode.removeChild(indicator);
                        }
                    }, 300);
                }
            }, 5000);
            
        } catch (e) {
            console.error('Error handling storage quota exceeded:', e);
        }
    }
    
    async loadCachedState() {
        try {
            const cacheData = window.observableStorage.getItem("sspi-custom-modifications");
            if (!cacheData || !this.isValidCacheData(cacheData)) {
                return false;
            }
            console.log('Loading cached SSPI modifications from:', new Date(cacheData.lastModified));

            // Restore dataset details map
            if (cacheData.datasetDetailsMap) {
                this.datasetDetails = cacheData.datasetDetailsMap;
                console.log(`Restored ${Object.keys(this.datasetDetails).length} dataset details from cache map`);
            }

            // Import the cached metadata using async method
            await this.importDataAsync(cacheData.metadata);
            // Set unsaved state based on cache
            this.setUnsavedState(cacheData.hasModifications);
            return true;
        } catch (error) {
            console.warn('Failed to load cached SSPI modifications:', error);
            this.clearCache(); // Clear corrupted cache
            return false;
        }
    }
    
    clearCache() {
        try {
            window.observableStorage.removeItem("sspi-custom-modifications");
            window.observableStorage.removeItem("sspi-available-datasets");
            console.log('SSPI modifications and dataset cache cleared');
        } catch (error) {
            console.warn('Failed to clear SSPI cache:', error);
        }
    }
    
    hasCachedModifications() {
        try {
            const cacheData = window.observableStorage.getItem("sspi-custom-modifications");
            return cacheData && this.isValidCacheData(cacheData) && cacheData.hasModifications;
        } catch (error) {
            console.warn('Error checking for cached modifications:', error);
            return false;
        }
    }
    
    isValidCacheData(cacheData) {
        if (!cacheData || typeof cacheData !== 'object') {
            return false;
        }
        // Check required fields
        const requiredFields = ['hasModifications', 'lastModified', 'metadata', 'version'];
        for (const field of requiredFields) {
            if (!(field in cacheData)) {
                console.warn(`Invalid cache data: missing field '${field}'`);
                return false;
            }
        }
        // Validate cache field types
        if (typeof cacheData.hasModifications !== 'boolean') {
            console.warn('Invalid cache data: hasModifications must be boolean');
            return false;
        }
        if (typeof cacheData.lastModified !== 'number' || cacheData.lastModified <= 0) {
            console.warn('Invalid cache data: lastModified must be a positive number');
            return false;
        }
        if (!Array.isArray(cacheData.metadata)) {
            console.warn('Invalid cache data: metadata must be an array');
            return false;
        }
        if (typeof cacheData.version !== 'string') {
            console.warn('Invalid cache data: version must be a string');
            return false;
        }

        // Check cache version matches current version
        if (cacheData.version !== this.CACHE_VERSION) {
            console.warn(`Cache version mismatch: cache=${cacheData.version}, current=${this.CACHE_VERSION}. Invalidating cache.`);
            return false;
        }

        // Check if cache is not too old (30 days max)
        const maxAge = 30 * 24 * 60 * 60 * 1000; // 30 days in milliseconds
        const age = Date.now() - cacheData.lastModified;
        if (age > maxAge) {
            console.warn('Cache data is too old (>7 days), discarding');
            return false;
        }
        // Basic metadata validation
        if (cacheData.metadata.length > 0) {
            const firstItem = cacheData.metadata[0];
            if (!firstItem || typeof firstItem !== 'object' || !firstItem.ItemType) {
                console.warn('Invalid cache data: metadata items have invalid structure');
                return false;
            }
        }
        return true;
    }

    // Available Datasets Cache Management
    // Separate from metadata cache to ensure dataset selector always has fresh options

    /**
     * Load available datasets from cache or backend.
     * Uses separate cache with 24-hour TTL to ensure dataset selector has fresh data.
     */
    async loadAvailableDatasets() {
        // Try to load from cache first
        const cached = this.getCachedAvailableDatasets();
        if (cached) {
            cached.forEach(ds => {
                this.datasetDetails[ds.DatasetCode] = ds;
            });
            console.log(`Loaded ${cached.length} available datasets from cache`);
            return;
        }

        // Cache miss or stale - fetch from backend
        try {
            const response = await this.fetch('/api/v1/customize/datasets?limit=0');
            if (response.success && response.datasets) {
                response.datasets.forEach(ds => {
                    this.datasetDetails[ds.DatasetCode] = ds;
                });
                this.cacheAvailableDatasets(response.datasets);
                console.log(`Loaded ${response.datasets.length} available datasets from backend`);
            } else {
                console.warn('Failed to load available datasets from backend');
            }
        } catch (error) {
            console.error('Error loading available datasets:', error);
        }
    }

    /**
     * Cache available datasets separately from metadata
     */
    cacheAvailableDatasets(datasets) {
        try {
            const cacheData = {
                datasets: datasets,
                cachedAt: Date.now(),
                version: this.CACHE_VERSION
            };
            window.observableStorage.setItem('sspi-available-datasets', cacheData);
            console.log('Cached available datasets');
        } catch (error) {
            console.warn('Failed to cache available datasets:', error);
        }
    }

    /**
     * Get cached available datasets if valid (not stale)
     * @returns {Array|null} - Cached datasets or null if invalid/stale
     */
    getCachedAvailableDatasets() {
        try {
            const cacheData = window.observableStorage.getItem('sspi-available-datasets');
            if (!cacheData || typeof cacheData !== 'object') {
                return null;
            }

            // Validate structure
            if (!Array.isArray(cacheData.datasets) || typeof cacheData.cachedAt !== 'number') {
                console.warn('Invalid available datasets cache structure');
                return null;
            }

            // Check version
            if (cacheData.version !== this.CACHE_VERSION) {
                console.warn('Available datasets cache version mismatch');
                return null;
            }

            // Check freshness (24 hours)
            const maxAge = 24 * 60 * 60 * 1000; // 24 hours
            const age = Date.now() - cacheData.cachedAt;
            if (age > maxAge) {
                console.log('Available datasets cache is stale (>24 hours), will refresh');
                return null;
            }

            return cacheData.datasets;
        } catch (error) {
            console.warn('Error reading available datasets cache:', error);
            return null;
        }
    }

    debouncedCacheState() {
        // Clear existing timeout
        if (this.cacheTimeout) {
            clearTimeout(this.cacheTimeout);
        }
        // Set new timeout for debounced caching
        this.cacheTimeout = setTimeout(() => {
            this.cacheCurrentState();
        }, 500); // 500ms debounce
    }
    
    setupCacheSync() {
        // Listen for cache changes from other tabs
        window.observableStorage.onChange("sspi-custom-modifications", async (oldValue, newValue) => {
            console.log('Cache change detected from another tab');
            // Only sync if we don't have unsaved changes in current tab
            if (!this.unsavedChanges) {
                if (newValue && this.isValidCacheData(newValue) && newValue.hasModifications) {
                    console.log('Syncing modifications from another tab');
                    await this.importDataAsync(newValue.metadata);
                    this.setUnsavedState(newValue.hasModifications);
                    
                    // Show indicator
                    this.showSyncIndicator();
                } else if (!newValue) {
                    // Cache was cleared in another tab, reload default if no local changes
                    console.log('Cache cleared in another tab, reloading default');
                    await this.loadDefaultMetadata();
                }
            }
        });
    }
    
    showSyncIndicator() {
        const indicator = document.createElement('div');
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--ms-color);
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
        `;
        indicator.textContent = '⟲ Synced from another tab';
        document.body.appendChild(indicator);
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => {
                    if (indicator.parentNode) {
                        indicator.parentNode.removeChild(indicator);
                    }
                }, 300);
            }
        }, 2000);
    }
    
    // Changelog and Diff System
    
    captureBaseline() {
        try {
            this.baselineMetadata = this.exportMetadata();
            this.diffCache = null; // Clear diff cache
            console.log('Baseline captured with', this.baselineMetadata.length, 'items');
        } catch (error) {
            console.warn('Failed to capture baseline:', error);
        }
    }
    
    generateDiff() {
        if (!this.baselineMetadata) {
            return { error: 'No baseline available for comparison' };
        }
        try {
            const currentMetadata = this.exportMetadata();
            // Use cached diff if current state hasn't changed
            if (this.diffCache && this.areMetadataEqual(this.diffCache.currentSnapshot, currentMetadata)) {
                return this.diffCache.diff;
            }
            const diff = this.compareMetadata(this.baselineMetadata, currentMetadata);
            // Cache the diff result
            this.diffCache = {
                currentSnapshot: JSON.parse(JSON.stringify(currentMetadata)),
                diff: diff
            };
            return diff;
        } catch (error) {
            console.error('Error generating diff:', error);
            return { error: 'Failed to generate diff: ' + error.message };
        }
    }
    
    compareMetadata(baseline, current) {
        const baselineMap = this.createItemMap(baseline);
        const currentMap = this.createItemMap(current);
        const changes = {
            summary: {
                totalChanges: 0,
                pillarsAffected: 0,
                categoriesAffected: 0,
                indicatorsAffected: 0
            },
            added: [],
            removed: [],
            modified: [],
            moved: [],
            unchanged: []
        };
        // Find removed items (in baseline but not in current)
        for (const [code, baselineItem] of baselineMap) {
            if (!currentMap.has(code)) {
                changes.removed.push({
                    type: baselineItem.ItemType,
                    code: code,
                    name: baselineItem.ItemName,
                    item: baselineItem
                });
            }
        }
        // Find added and modified items
        for (const [code, currentItem] of currentMap) {
            if (!baselineMap.has(code)) {
                // Item was added
                changes.added.push({
                    type: currentItem.ItemType,
                    code: code,
                    name: currentItem.ItemName,
                    item: currentItem
                });
            } else {
                // Item exists in both, check for modifications
                const baselineItem = baselineMap.get(code);
                const itemChanges = this.compareItems(baselineItem, currentItem);
                
                if (itemChanges) {
                    changes.modified.push({
                        type: currentItem.ItemType,
                        code: code,
                        name: currentItem.ItemName,
                        changes: itemChanges,
                        before: baselineItem,
                        after: currentItem
                    });
                } else {
                    changes.unchanged.push({
                        type: currentItem.ItemType,
                        code: code,
                        name: currentItem.ItemName
                    });
                }
            }
        }
        // Calculate summary statistics
        changes.summary.totalChanges = changes.added.length + changes.removed.length + changes.modified.length + changes.moved.length;
        // Count affected items by type
        const affectedTypes = new Set();
        [...changes.added, ...changes.removed, ...changes.modified, ...changes.moved].forEach(change => {
            affectedTypes.add(change.type);
            switch (change.type) {
                case 'Pillar':
                    changes.summary.pillarsAffected++;
                    break;
                case 'Category':
                    changes.summary.categoriesAffected++;
                    break;
                case 'Indicator':
                    changes.summary.indicatorsAffected++;
                    break;
            }
        });
        return changes;
    }
    
    createItemMap(metadata) {
        const map = new Map();
        metadata.forEach(item => {
            map.set(item.ItemCode, item);
        });
        return map;
    }
    
    compareItems(baselineItem, currentItem) {
        const changes = {};
        // Compare basic properties
        // Compare indicator-specific properties
        if (baselineItem.ItemType === 'Indicator') {
            if (!this.arraysEqual(baselineItem.DatasetCodes || [], currentItem.DatasetCodes || [])) {
                changes.datasets = {
                    from: baselineItem.DatasetCodes || [],
                    to: currentItem.DatasetCodes || []
                };
            }
            
            if (baselineItem.ScoreFunction !== currentItem.ScoreFunction) {
                changes.ScoreFunction = { 
                    from: baselineItem.ScoreFunction, 
                    to: currentItem.ScoreFunction 
                };
            }
        }
        if (baselineItem.ItemName !== currentItem.ItemName) {
            changes.name = { from: baselineItem.ItemName, to: currentItem.ItemName };
        }
        // Compare children arrays
        if (!this.arraysEqual(baselineItem.Children || [], currentItem.Children || [])) {
            changes.children = { 
                from: baselineItem.Children || [], 
                to: currentItem.Children || [] 
            };
        }
        if (baselineItem.PillarCode !== currentItem.PillarCode) {
            changes.pillar = { 
                from: baselineItem.PillarCode, 
                to: currentItem.PillarCode 
            };
        }
        if (baselineItem.CategoryCode !== currentItem.CategoryCode) {
            changes.category = { 
                from: baselineItem.CategoryCode, 
                to: currentItem.CategoryCode 
            };
        }
        return Object.keys(changes).length > 0 ? changes : null;
    }
    
    arraysEqual(arr1, arr2) {
        if (arr1.length !== arr2.length) return false;
        return arr1.every((item, index) => item === arr2[index]);
    }
    
    areMetadataEqual(metadata1, metadata2) {
        if (!metadata1 || !metadata2) return false;
        if (metadata1.length !== metadata2.length) return false;
        
        return JSON.stringify(metadata1) === JSON.stringify(metadata2);
    }
    
    hasChangesFromBaseline() {
        if (!this.baselineMetadata) return false;
        
        const diff = this.generateDiff();
        return diff.summary && diff.summary.totalChanges > 0;
    }
    
    getChangeCount() {
        if (!this.baselineMetadata) return 0;
        
        const diff = this.generateDiff();
        return diff.summary ? diff.summary.totalChanges : 0;
    }

    async fetch(url, options = {}) {
        const response = await window.fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }
}

// Usage example:
// const root = document.getElementById('sspi-root');
// new CustomizableSSPIStructure(root);
