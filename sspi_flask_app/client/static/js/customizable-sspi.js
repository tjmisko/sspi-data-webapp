// customizable-sspi.js
// SSPI Tree UI implementing full specification (three-column layout)
class CustomizableSSPIStructure {
    constructor(parentElement, options = {}) {
        const {
            pillars = [
                { ItemName: 'Sustainability', ItemCode: 'SUS' },
                { ItemName: 'Market Structure', ItemCode: 'MS' },
                { ItemName: 'Public Goods', ItemCode: 'PG' }
            ],
            loadingDelay = 100,
            username = '',
            baseConfig = 'sspi',  // NEW: base config from URL
            readOnly = false
        } = options;
        this.readOnly = readOnly
        this.baseConfig = baseConfig;
        this.parentElement = parentElement;
        this.pillars = pillars;
        this.loadingDelay = loadingDelay;
        this.username = username || window.sspiUsername || '';
        this.unsavedChanges = false;
        this.isImporting = false; // Flag to suppress validation during bulk import
        this.draggedEl = null;
        this.origin = null;
        this.dropped = false;
        this.isLoading = false;
        this.cacheTimeout = null;
        this.datasetDetails = {};// Dataset details storage (maps dataset code to full details)
        this.actionHistory = new CustomizableActionHistory(this);
        // Configuration tracking for save/load
        this.currentConfigId = null;
        this.currentConfigName = null;
        this.initToolbar();
        this.initRoot();
        this.rigPillarRename();
        // Progress tracking - initialize AFTER initRoot() creates this.container
        this.rigCategoryIndicatorListeners();
        this.rigDragStructureListeners();
        this.setupKeyboardShortcuts();
        // NOTE: Dataset details are loaded as part of default-structure API response (datasetDetailsMap field)
        // This eliminates the need for a separate API call to /api/v1/customize/datasets
        this.setupCacheSync();
        this.rigUnloadListener();
        // Setup unsaved changes warning (uses client-side flag)
        this.setupUnsavedChangesWarning();
        // Auto-load cached modifications or default metadata if enabled
        setTimeout(() => { // delay ensures DOM is ready
            this.loadInitialData();
        }, this.loadingDelay);
    }

    initToolbar() {
        this.toolbarLeft = document.createElement('div');
        this.toolbarLeft.classList.add('sspi-toolbar-button-group');
        this.toolbarRight = document.createElement('div');
        this.toolbarRight.classList.add('sspi-toolbar-button-group');
        this.saveButton = document.createElement('button');
        this.saveButton.textContent = 'Save';
        this.saveButton.addEventListener('click', async () => {
            await this.handleSave();
        });
        const resetViewBtn = document.createElement('button');
        resetViewBtn.textContent = 'Default View';
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
        this.discardButton.disabled = true;
        this.discardButton.addEventListener('click', async () => {
            if (this.unsavedChanges && confirm('Are you sure you want to discard all unsaved changes? This action cannot be undone.')) {
                await this.discardChanges();
            }
        });
        const scoreVisualizeBtn = document.createElement('button');
        this.toolbarLeft.append(this.saveButton, validateBtn, viewChangesBtn, this.discardButton);
        this.toolbarRight.append(resetViewBtn, expandAllBtn, collapseAllBtn)
        this.toolbar = document.createElement('div')
        this.toolbar.classList.add('sspi-toolbar')
        this.toolbar.appendChild(this.toolbarLeft);
        this.toolbar.appendChild(this.toolbarRight);
        this.parentElement.appendChild(this.toolbar);
        this.updateSaveButtonState();
    }

    async fetch(url, options = {}) {
        // Add CSRF token for state-changing requests
        if (options.method && options.method !== 'GET') {
            // Add CSRF token to headers
            const headers = options.headers || {};
            if (window.csrfToken) {
                headers['X-CSRFToken'] = window.csrfToken;
            }
            options.headers = headers;
        }

        const res = await window.fetch(url, options);
        if (!res.ok) {
            const errorText = await res.text();
            throw new Error(`HTTP ${res.status}: ${errorText}`);
        }
        return await res.json();
    }

    // ========== Save & Load Methods ==========

    async handleSave() {
        try {
            // Check if user is authenticated
            if (!window.sspiUsername) {
                notifications.error('Please log in to save configurations');
                window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname + window.location.search);
                return;
            }

            // Protected configs cannot be overwritten
            const protectedConfigs = ['sspi', 'blank', 'default'];

            if (protectedConfigs.includes(this.baseConfig)) {
                // Always save as new when editing protected configs
                await this.saveNewConfiguration();
            } else {
                // Can update existing saved config
                if (this.currentConfigId === this.baseConfig) {
                    await this.updateConfiguration(this.baseConfig);
                } else {
                    await this.saveNewConfiguration();
                }
            }
        } catch (error) {
            console.error('Error in handleSave:', error);
            notifications.error('Failed to save configuration: ' + error.message);
        }
    }

    async saveNewConfiguration() {
        // Prompt for configuration name
        const name = await this.promptConfigName();
        if (!name) return; // User cancelled

        try {
            this.showLoadingState('Saving configuration...');

            // Prepare save payload
            const metadata = this.exportMetadata();
            const actions = this.actionHistory.exportActionLog();

            const payload = {
                name: name,
                metadata: metadata,
                actions: actions
            };

            console.log('Saving configuration:', {
                name: name,
                metadataCount: metadata.length,
                actionsCount: actions.length,
                payloadSize: JSON.stringify(payload).length
            });

            // Call API endpoint
            const response = await this.fetch('/api/v1/customize/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            this.hideLoadingState();

            if (response.success) {
                // Update current config tracking
                this.currentConfigId = response.config_id;
                this.currentConfigName = name;

                // Clear unsaved state and cache
                this.clearUnsavedState();
                this.clearCache();

                // Update UI
                this.updateSaveButtonState();

                // Show success with link to edit the newly saved config
                const editLink = `/customize/builder?base_config=${response.config_id}`;
                notifications.success(
                    `Configuration saved successfully! <a href="${editLink}" style="color: white; text-decoration: underline;">Edit this config</a>`,
                    8000
                );
            } else {
                throw new Error(response.error || 'Unknown error');
            }
        } catch (error) {
            this.hideLoadingState();
            throw error; // Re-throw to be handled by handleSave
        }
    }

    async updateConfiguration(configId) {
        try {
            this.showLoadingState('Updating configuration...');

            const payload = {
                name: this.currentConfigName || 'Custom SSPI',
                metadata: this.exportMetadata(),
                actions: this.actionHistory.exportActionLog()
            };

            const response = await this.fetch(`/api/v1/customize/update/${configId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            this.hideLoadingState();

            if (response.success) {
                this.clearUnsavedState();
                this.clearCache();
                this.updateSaveButtonState();
                notifications.success('Configuration updated successfully');
            } else {
                throw new Error(response.error || 'Update failed');
            }
        } catch (error) {
            this.hideLoadingState();
            throw error;
        }
    }

    async promptConfigName(defaultName = '') {
        return new Promise((resolve) => {
            // Create modal elements
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
            `;

            const dialog = document.createElement('div');
            dialog.className = 'modal-dialog';
            dialog.style.cssText = `
                background: var(--box-background-color);
                border-radius: 8px;
                padding: 24px;
                max-width: 400px;
                width: 90%;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            `;

            dialog.innerHTML = `
                <h3 style="margin: 0 0 16px 0;">Save Configuration</h3>
                <label style="display: block; margin-bottom: 8px;">Configuration Name:</label>
                <input type="text" id="config-name-input"
                    value="${defaultName || 'My Custom SSPI'}"
                    style="width: 100%; padding: 8px; margin-bottom: 16px; border: 1px solid var(--border-color); border-radius: 4px;"
                    maxlength="200">
                <div style="display: flex; gap: 8px; justify-content: flex-end;">
                    <button id="cancel-btn" style="padding: 8px 16px; border: 1px solid var(--border-color); background: transparent; border-radius: 4px; cursor: pointer;">Cancel</button>
                    <button id="save-btn" style="padding: 8px 16px; background: var(--primary-color); color: white; border: none; border-radius: 4px; cursor: pointer;">Save</button>
                </div>
            `;

            modal.appendChild(dialog);
            document.body.appendChild(modal);

            const input = dialog.querySelector('#config-name-input');
            const saveBtn = dialog.querySelector('#save-btn');
            const cancelBtn = dialog.querySelector('#cancel-btn');

            // Focus and select input text
            input.focus();
            input.select();

            const cleanup = () => {
                modal.remove();
            };

            const handleSave = () => {
                const name = input.value.trim();
                if (!name) {
                    input.style.borderColor = 'red';
                    return;
                }
                cleanup();
                resolve(name);
            };

            const handleCancel = () => {
                cleanup();
                resolve(null);
            };

            // Event listeners
            saveBtn.addEventListener('click', handleSave);
            cancelBtn.addEventListener('click', handleCancel);
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') handleSave();
                if (e.key === 'Escape') handleCancel();
            });
            modal.addEventListener('click', (e) => {
                if (e.target === modal) handleCancel();
            });
        });
    }

    updateSaveButtonState() {
        // Check if user is logged in (handle both undefined and empty string)
        const isLoggedIn = !!(window.sspiUsername && window.sspiUsername.trim());

        if (!isLoggedIn) {
            // Use same styling as Discard button when disabled
            this.saveButton.classList.remove('unsaved-changes');
            this.saveButton.textContent = 'Save';
            this.saveButton.disabled = true;
            this.saveButton.style.opacity = '0.5';
            this.saveButton.style.cursor = 'not-allowed';
            this.saveButton.title = 'You must be logged in to save configurations';
            return;
        }

        // User is logged in - enable save functionality
        if (this.unsavedChanges) {
            this.saveButton.classList.add('unsaved-changes');
            this.saveButton.textContent = this.currentConfigId ? 'Update' : 'Save';
            this.saveButton.disabled = false;
            this.saveButton.style.opacity = '1';
            this.saveButton.style.cursor = 'pointer';
            this.saveButton.title = this.currentConfigId ? 'Update the current configuration' : 'Save as new configuration';
        } else {
            this.saveButton.classList.remove('unsaved-changes');
            this.saveButton.textContent = 'Saved';
            this.saveButton.disabled = false;
            this.saveButton.style.opacity = '1';
            this.saveButton.style.cursor = 'pointer';
            this.saveButton.title = 'No unsaved changes';
        }
    }

    initRoot() {
        this.container = document.createElement('div');
        this.container.classList.add('pillars-container', 'pillars-grid');
        this.container.setAttribute('role', 'tree');
        this.pillars.forEach((item, index) => {
            const col = document.createElement('div');
            col.classList.add('pillar-column');
            col.dataset.pillar = item.ItemName;
            col.setAttribute('aria-label', item.ItemName + ' pillar');
            col.innerHTML = `
<div role="treeitem" class="customization-pillar-header draggable-item" dataset-type="pillar">
    <div class="customization-pillar-header-content">
        <div class="pillar-name" contenteditable="true" spellcheck="false" tabindex="0">${name}</div>
        <div class="pillar-code-section">
            <label class="code-label">Code:</label>
            <input type="text" class="pillar-code-input" maxlength="3" placeholder="${item.ItemCode}"
                   pattern="[A-Z]{2,3}" title="2-3 uppercase letters required" value="${item.ItemCode}">
            <span class="code-validation-message"></span>
        </div>
    </div>
</div>
            `;
            this.setupCodeValidation(col.querySelector('.pillar-code-input'), 'pillar');
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

    rigPillarRename() {
        // Pillar rename
        this.container.querySelectorAll('.customization-pillar-header').forEach(h =>
            h.addEventListener('keydown', e => {
                if (e.key === 'Enter') { e.preventDefault(); h.blur(); }
            })
        );
    }

    rigCategoryIndicatorListeners() {
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
    }

    rigDragStructureListeners() {
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
            this.clearDraggingVisuals();
        });
        this.container.addEventListener('dragover', e => {
            const z = e.target.closest('.drop-zone');
            if (!z || !this.draggedEl) return;
            e.preventDefault();
            z.classList.add('drag-over');
            this.clearDraggingVisuals(z);
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
                this.clearDraggingVisuals(z);
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
    }

    flagUnsaved() {
        this.unsavedChanges = true;
        this.discardButton.disabled = false;
        this.discardButton.style.opacity = '1';
        this.discardButton.style.cursor = 'pointer';
        this.updateSaveButtonState();
        this.debouncedCacheState();
    }
    
    clearUnsavedState() {
        this.unsavedChanges = false;
        this.discardButton.disabled = true;
        this.discardButton.style.opacity = '0.5';
        this.discardButton.style.cursor = 'not-allowed';
        this.updateSaveButtonState();
    }
    
    setUnsavedState(hasChanges) {
        if (hasChanges) {
            this.markUnsaved();
            this.saveButton.classList.add('unsaved-changes');
            this.discardButton.disabled = false;
            this.discardButton.style.opacity = '1';
            this.discardButton.style.cursor = 'pointer';
        } else {
            this.markSaved();
            this.clearUnsavedState();
        }
    }

    clearDraggingVisuals(scope) {
        const parent = scope || this.container;
        parent.querySelectorAll('.insertion-indicator').forEach(node => node.remove());
    }

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
        if (element.dataset.itemType === 'Category') {
            return 'Pillar';
        }
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

    /**
     * Private helper: Setup event handlers for a dataset element
     * Used when restoring dataset elements during undo/redo
     * @param {HTMLElement} datasetItem - The dataset item element
     * @param {HTMLElement} selectedDatasetsDiv - The container for datasets
     * @param {string} indicatorCode - The parent indicator code
     * @param {boolean} recordRemovalAction - Whether to record action when removing
     * @private
     */
    _setupDatasetHandlers(datasetItem, selectedDatasetsDiv, indicatorCode, recordRemovalAction) {
        const datasetCode = datasetItem.dataset.datasetCode;

        // Expansion toggle
        const existingExpandHandler = datasetItem._expandHandler;
        if (!existingExpandHandler) {
            const expandHandler = (e) => {
                const isExpanded = datasetItem.dataset.expanded === 'true';
                datasetItem.dataset.expanded = (!isExpanded).toString();
                const slideout = datasetItem.querySelector('.dataset-details-slideout');
                if (!isExpanded && slideout) {
                    slideout.style.maxHeight = slideout.scrollHeight + 'px';
                } else if (slideout) {
                    slideout.style.maxHeight = '0';
                }
            };
            datasetItem.addEventListener('click', expandHandler);
            datasetItem._expandHandler = expandHandler; // Store reference to prevent duplicate listeners
        }

        // Remove button
        const removeBtn = datasetItem.querySelector('.remove-dataset');
        if (removeBtn) {
            // Remove any existing listeners
            const oldBtn = removeBtn.cloneNode(true);
            removeBtn.parentNode.replaceChild(oldBtn, removeBtn);

            oldBtn.addEventListener('click', (e) => {
                e.stopPropagation();

                if (recordRemovalAction) {
                    const position = Array.from(selectedDatasetsDiv.children).indexOf(datasetItem);
                    const datasetDetails = this.datasetDetails[datasetCode];

                    this.actionHistory.recordAction({
                        type: 'remove-dataset',
                        message: `Removed dataset "${datasetCode}" from indicator "${indicatorCode}"`,
                        delta: {
                            type: 'remove-dataset',
                            indicatorCode,
                            datasetCode,
                            datasetDetails,
                            position
                        },
                        undo: () => {
                            const items = Array.from(selectedDatasetsDiv.children);
                            if (position >= items.length) {
                                selectedDatasetsDiv.appendChild(datasetItem);
                            } else {
                                selectedDatasetsDiv.insertBefore(datasetItem, items[position]);
                            }
                            this._setupDatasetHandlers(datasetItem, selectedDatasetsDiv, indicatorCode, true);
                            this.flagUnsaved();
                            this.validate();
                        },
                        redo: () => {
                            datasetItem.remove();
                            this.flagUnsaved();
                            this.validate();
                        }
                    });
                }

                datasetItem.remove();
                this.flagUnsaved();
                this.validate();
            });
        }
    }

    // ========== SECTION 4: API Methods - Indicators ==========

    /**
     * Private method: Add dataset to an indicator element (may or may not be in DOM yet)
     * @private
     * @param {string} datasetCode - The dataset code to add
     * @param {HTMLElement} indicatorElement - The indicator element
     * @param {string} indicatorCode - The indicator code (for action history messages)
     * @param {Object} options - Options
     * @param {boolean} [options.record=true] - Whether to record this action in undo/redo history
     * @returns {Object} Result with success status, action, and element
     */
    _addDatasetToIndicatorElement(datasetCode, indicatorElement, indicatorCode, { record = true } = {}) {
        const selectedDatasetsDiv = indicatorElement.querySelector('.selected-datasets');
        if (!selectedDatasetsDiv) {
            return { success: false, error: 'Selected datasets container not found' };
        }

        // Check for duplicates
        const existing = selectedDatasetsDiv.querySelector(`[data-dataset-code="${datasetCode}"]`);
        if (existing) {
            return { success: false, error: 'Dataset already added to this indicator' };
        }

        // Lookup dataset details (always from this.datasetDetails)
        const details = this.datasetDetails[datasetCode];
        if (!details) {
            return { success: false, error: `Dataset ${datasetCode} not found in datasetDetails` };
        }

        // Create dataset item element
        const formatNumber = (num) => num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');

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
                    <span class="dataset-name">${details.DatasetName || 'Unknown Dataset'}</span>
                    <span class="dataset-code">${datasetCode}</span>
                </div>
                <div class="dataset-actions">
                    <button class="remove-dataset" type="button" title="Remove dataset">×</button>
                </div>
            </div>
            <div class="dataset-details-slideout">
                <div class="detail-row">
                    <span class="detail-label">Description</span>
                    <span class="detail-value">${details.Description || 'No description available'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Organization</span>
                    <span class="detail-value">${details.Source?.OrganizationName || 'N/A'}${details.Source?.OrganizationCode ? ' (' + details.Source.OrganizationCode + ')' : ''}</span>
                </div>
                ${unitHtml}
                ${rangeHtml}
            </div>
        `;

        // Setup event handlers
        this._setupDatasetHandlers(datasetItem, selectedDatasetsDiv, indicatorCode, record);

        // Get position before adding
        const position = selectedDatasetsDiv.querySelectorAll('.dataset-item').length;

        // Add to DOM
        selectedDatasetsDiv.appendChild(datasetItem);

        // Record action conditionally
        let action = null;
        if (record) {
            action = this.actionHistory.recordAction({
                type: 'add-dataset',
                message: `Added dataset "${datasetCode}" to indicator "${indicatorCode}"`,
                delta: {
                    type: 'add-dataset',
                    indicatorCode: indicatorCode,
                    datasetCode: datasetCode,
                    position: position
                },
                undo: () => {
                    datasetItem.remove();
                    this.flagUnsaved();
                    this.validate();
                },
                redo: () => {
                    const items = Array.from(selectedDatasetsDiv.children);
                    if (position >= items.length) {
                        selectedDatasetsDiv.appendChild(datasetItem);
                    } else {
                        selectedDatasetsDiv.insertBefore(datasetItem, items[position]);
                    }
                    this.flagUnsaved();
                    this.validate();
                }
            });
        }

        // Update state (only flag unsaved if recording this action)
        if (record) {
            this.flagUnsaved();
        }
        this.validate();

        return { success: true, action, element: datasetItem };
    }

    /**
     * Add dataset to an indicator (code-based public API)
     * @param {string} datasetCode - The dataset code to add
     * @param {string} indicatorCode - The indicator code
     * @param {Object} options - Options
     * @param {boolean} [options.record=true] - Whether to record this action in undo/redo history
     * @returns {Object} Result with success status, action, and element
     */
    addDataset(datasetCode, indicatorCode, { record = true } = {}) {
        // Validate inputs
        if (!datasetCode) {
            return { success: false, error: 'Dataset code is required' };
        }
        if (!indicatorCode) {
            return { success: false, error: 'Indicator code is required' };
        }

        // Find indicator element in DOM
        const indicatorEl = this.findElementByCode(indicatorCode, 'Indicator');
        if (!indicatorEl) {
            return { success: false, error: `Indicator ${indicatorCode} not found` };
        }

        // Delegate to private method
        return this._addDatasetToIndicatorElement(datasetCode, indicatorEl, indicatorCode, { record });
    }

    /**
     * Remove dataset from an indicator
     * @param {string} indicatorCode - The indicator code
     * @param {Object} options - Options object
     * @param {string} options.datasetCode - The dataset code to remove
     * @returns {Object} Result with success status and action
     */
    removeDataset(datasetCode, indicatorCode) {
        if (!indicatorCode) {
            return { success: false, error: 'Indicator code is required' };
        }
        if (!datasetCode) {
            return { success: false, error: 'Dataset code is required' };
        }
        const indicatorEl = this.findElementByCode(indicatorCode, 'Indicator');
        if (!indicatorEl) {
            return { success: false, error: `Indicator ${indicatorCode} not found` };
        }
        const selectedDatasetsDiv = indicatorEl.querySelector('.selected-datasets');
        if (!selectedDatasetsDiv) {
            return { success: false, error: 'Selected datasets container not found' };
        }
        const datasetItem = selectedDatasetsDiv.querySelector(`[data-dataset-code="${datasetCode}"]`);
        if (!datasetItem) {
            return { success: false, error: `Dataset ${datasetCode} not found in indicator` };
        }
        const position = Array.from(selectedDatasetsDiv.children).indexOf(datasetItem);
        const details = this.datasetDetails[datasetCode];
        datasetItem.remove();
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
    addIndicator(parentCode, { indicatorCode = "", indicatorName = 'New Indicator', datasetCodes = [], scoreFunction = 'Score = ' } = {}) {
        if (!parentCode) {
            return { success: false, error: 'Parent code is required' };
        }
        let parentEl = this.findElementByCode(parentCode, 'Category');
        if (!parentEl) {
            parentEl = this.findElementByCode(parentCode, 'Pillar');
        }
        if (!parentEl) {
            return { success: false, error: `Parent ${parentCode} not found` };
        }
        const parentType = this.getItemType(parentEl);
        const indicatorsContainer = parentEl.querySelector('.indicators-container');
        if (!indicatorsContainer) {
            return { success: false, error: 'Indicators container not found in parent' };
        }
        const existing = this.findElementByCode(indicatorCode, 'Indicator');
        if (existing) {
            return { success: false, error: `Indicator code ${indicatorCode} already exists` };
        }
        const position = indicatorsContainer.querySelectorAll('.indicator-card').length;
        const indEl = this.createIndicatorElement();
        const indicatorNameEl = indEl.querySelector('.indicator-name');
        const indicatorCodeInput = indEl.querySelector('.indicator-code-input');
        const scoreFunctionEl = indEl.querySelector('.editable-score-function');
        if (indicatorNameEl) indicatorNameEl.textContent = indicatorName;
        if (indicatorCodeInput) indicatorCodeInput.value = indicatorCode;
        if (scoreFunctionEl) scoreFunctionEl.textContent = scoreFunction;
        indEl.dataset.indicatorCode = indicatorCode;
        indEl.dataset.itemCode = indicatorCode;
        if (datasetCodes.length > 0) {
            const selectedDatasetsDiv = indEl.querySelector('.selected-datasets');
            if (selectedDatasetsDiv) {
                datasetCodes.forEach(datasetCode => {
                    const details = this.datasetDetails[datasetCode];
                    if (details) {
                        this.addDataset(datasetCode, indicatorCode, {datasetDetails: details });
                    }
                });
            }
        }
        indicatorsContainer.appendChild(indEl);
        const indicatorMetadata = {
            ItemType: 'Indicator',
            ItemCode: indicatorCode,
            ItemName: indicatorName,
            DatasetCodes: datasetCodes,
            ScoreFunction: scoreFunction,
            Children: []
        };
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
        if (!indicatorCode) {
            return { success: false, error: 'Indicator code is required' };
        }
        const indEl = this.findElementByCode(indicatorCode, 'Indicator');
        if (!indEl) {
            return { success: false, error: `Indicator ${indicatorCode} not found` };
        }
        const parentCode = this.getParentCode(indEl);
        const parentType = this.getParentType(indEl);
        const position = this.getPositionInParent(indEl);
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
        const parentEl = indEl.parentElement;
        indEl.remove();
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
        if (!indicatorCode) {
            return { success: false, error: 'Indicator code is required' };
        }
        if (!targetParentCode) {
            return { success: false, error: 'Target parent code is required' };
        }
        const indEl = this.findElementByCode(indicatorCode, 'Indicator');
        if (!indEl) {
            return { success: false, error: `Indicator ${indicatorCode} not found` };
        }
        const fromParentCode = this.getParentCode(indEl);
        const fromParentType = this.getParentType(indEl);
        const fromPosition = this.getPositionInParent(indEl);
        let targetParentEl = this.findElementByCode(targetParentCode, 'Category');
        if (!targetParentEl) {
            targetParentEl = this.findElementByCode(targetParentCode, 'Pillar');
        }
        if (!targetParentEl) {
            return { success: false, error: `Target parent ${targetParentCode} not found` };
        }
        const toParentType = this.getItemType(targetParentEl);
        if (fromParentCode === targetParentCode) {
            return { success: false, error: 'Indicator is already in target parent' };
        }
        const targetContainer = targetParentEl.querySelector('.indicators-container');
        if (!targetContainer) {
            return { success: false, error: 'Indicators container not found in target parent' };
        }
        const toPosition = targetContainer.querySelectorAll('.indicator-card').length;
        const fromParentEl = indEl.parentElement;
        targetContainer.appendChild(indEl);
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
    /**
     * Modify multiple properties of an indicator in a single call
     * Records separate actions for each property changed (granular undo/redo)
     * @param {string} indicatorCode - The indicator code to modify
     * @param {Object} changes - Object containing properties to change
     * @param {string} [changes.newIndicatorCode] - New indicator code
     * @param {string} [changes.indicatorName] - New indicator name
     * @param {string} [changes.scoreFunction] - New score function
     * @param {Array<string>} [changes.datasetCodes] - Array of dataset codes (replaces all existing)
     * @param {boolean} [changes.record=true] - Whether to record actions
     * @returns {Object} Result with success status, actions array, and error if applicable
     */
    modifyIndicator(indicatorCode, { newIndicatorCode, indicatorName, scoreFunction, datasetCodes, record = true } = {}) {
        // Validate at least one change is specified
        if (newIndicatorCode === undefined && indicatorName === undefined &&
            scoreFunction === undefined && datasetCodes === undefined) {
            return { success: false, error: 'No changes specified' };
        }

        // Find indicator element
        const indicatorEl = this.findElementByCode(indicatorCode, 'Indicator');
        if (!indicatorEl) {
            return { success: false, error: `Indicator ${indicatorCode} not found` };
        }

        // Ensure element has stable ID for undo/redo
        if (!indicatorEl.id) {
            indicatorEl.id = `indicator-${Math.random().toString(36).substr(2,9)}`;
        }
        const elementId = indicatorEl.id;

        const actions = [];
        let currentCode = indicatorCode; // Track code changes for subsequent operations

        // 1. Handle indicator code change
        if (newIndicatorCode !== undefined) {
            // Validate new code
            if (!this.validateCode(newIndicatorCode, 'indicator')) {
                return { success: false, error: `Invalid indicator code format: ${newIndicatorCode} (must be 6 uppercase letters/numbers)` };
            }

            const codeInput = indicatorEl.querySelector('.indicator-code-input');
            if (!this.isCodeUnique(newIndicatorCode, 'indicator', codeInput)) {
                return { success: false, error: `Code "${newIndicatorCode}" is already in use` };
            }

            const oldCode = indicatorEl.dataset.indicatorCode || '';

            if (oldCode !== newIndicatorCode) {
                // Update DOM
                this.updateElementCode(indicatorEl, newIndicatorCode);
                if (codeInput) {
                    codeInput.value = newIndicatorCode;
                }

                // Record action
                if (record) {
                    const action = this.actionHistory.recordAction({
                        type: 'modify-indicator',
                        subtype: 'set-code',
                        message: oldCode
                            ? `Changed indicator code from "${oldCode}" to "${newIndicatorCode}"`
                            : `Set indicator code to "${newIndicatorCode}"`,
                        delta: {
                            type: 'set-code',
                            indicatorCode: newIndicatorCode,
                            from: oldCode,
                            to: newIndicatorCode
                        },
                        undo: () => {
                            const el = document.getElementById(elementId);
                            if (el) {
                                this.updateElementCode(el, oldCode);
                                const input = el.querySelector('.indicator-code-input');
                                if (input) input.value = oldCode;
                                this.validate();
                            }
                        },
                        redo: () => {
                            const el = document.getElementById(elementId);
                            if (el) {
                                this.updateElementCode(el, newIndicatorCode);
                                const input = el.querySelector('.indicator-code-input');
                                if (input) input.value = newIndicatorCode;
                                this.validate();
                            }
                        }
                    });
                    actions.push(action);
                }

                currentCode = newIndicatorCode; // Update for subsequent operations
            }
        }

        // 2. Handle indicator name change
        if (indicatorName !== undefined) {
            const indicatorNameEl = indicatorEl.querySelector('.indicator-name');
            if (!indicatorNameEl) {
                return { success: false, error: 'Indicator name element not found' };
            }

            const oldName = indicatorNameEl.textContent.trim();

            if (oldName !== indicatorName) {
                // Update DOM
                indicatorNameEl.textContent = indicatorName;

                // Record action
                if (record) {
                    const action = this.actionHistory.recordAction({
                        type: 'modify-indicator',
                        subtype: 'set-name',
                        message: `Changed indicator name from "${oldName}" to "${indicatorName}"`,
                        delta: {
                            type: 'set-name',
                            indicatorCode: currentCode,
                            from: oldName,
                            to: indicatorName
                        },
                        undo: () => {
                            const el = document.getElementById(elementId);
                            if (el) {
                                const nameEl = el.querySelector('.indicator-name');
                                if (nameEl) nameEl.textContent = oldName;
                            }
                        },
                        redo: () => {
                            const el = document.getElementById(elementId);
                            if (el) {
                                const nameEl = el.querySelector('.indicator-name');
                                if (nameEl) nameEl.textContent = indicatorName;
                            }
                        }
                    });
                    actions.push(action);
                }
            }
        }

        // 3. Handle score function change
        if (scoreFunction !== undefined) {
            const scoreFunctionEl = indicatorEl.querySelector('.editable-score-function');
            if (!scoreFunctionEl) {
                return { success: false, error: 'Score function element not found' };
            }

            const oldScoreFunction = scoreFunctionEl.textContent.trim();

            if (oldScoreFunction !== scoreFunction) {
                // Update DOM
                scoreFunctionEl.textContent = scoreFunction;

                // Record action
                if (record) {
                    const action = this.actionHistory.recordAction({
                        type: 'modify-indicator',
                        subtype: 'set-score-function',
                        message: `Updated score function for indicator "${currentCode}"`,
                        delta: {
                            type: 'set-score-function',
                            indicatorCode: currentCode,
                            from: oldScoreFunction,
                            to: scoreFunction
                        },
                        undo: () => {
                            const el = document.getElementById(elementId);
                            if (el) {
                                const sfEl = el.querySelector('.editable-score-function');
                                if (sfEl) sfEl.textContent = oldScoreFunction;
                                this.validate();
                            }
                        },
                        redo: () => {
                            const el = document.getElementById(elementId);
                            if (el) {
                                const sfEl = el.querySelector('.editable-score-function');
                                if (sfEl) sfEl.textContent = scoreFunction;
                                this.validate();
                            }
                        }
                    });
                    actions.push(action);
                }
            }
        }

        // 4. Handle dataset replacement
        if (datasetCodes !== undefined) {
            if (!Array.isArray(datasetCodes)) {
                return { success: false, error: 'datasetCodes must be an array' };
            }

            const selectedDatasetsDiv = indicatorEl.querySelector('.selected-datasets');
            if (!selectedDatasetsDiv) {
                return { success: false, error: 'Selected datasets container not found' };
            }

            // Get current datasets
            const currentDatasetItems = Array.from(selectedDatasetsDiv.querySelectorAll('.dataset-item'));
            const currentDatasetCodes = currentDatasetItems.map(item => item.dataset.datasetCode);

            // Only proceed if there's a difference
            const hasChanged = JSON.stringify(currentDatasetCodes.sort()) !== JSON.stringify([...datasetCodes].sort());

            if (hasChanged) {
                // Store current datasets HTML for undo
                const oldDatasetsHTML = selectedDatasetsDiv.innerHTML;

                // Remove all existing datasets
                currentDatasetItems.forEach(item => item.remove());

                // Add new datasets
                const newDatasetElements = [];
                for (const datasetCode of datasetCodes) {
                    const datasetDetails = this.datasetDetails[datasetCode];
                    if (!datasetDetails) {
                        console.warn(`Dataset ${datasetCode} not found in datasetDetails`);
                        continue;
                    }

                    // Use existing method to add dataset without recording individual actions
                    const result = this.addDataset(datasetCode, currentCode, {
                        datasetDetails,
                        record: false // Don't record individual add actions
                    });

                    if (result.success && result.element) {
                        newDatasetElements.push(result.element);
                    }
                }

                // Record single action for dataset replacement
                if (record) {
                    const action = this.actionHistory.recordAction({
                        type: 'modify-indicator',
                        subtype: 'replace-datasets',
                        message: `Replaced datasets for indicator "${currentCode}" (${datasetCodes.length} datasets)`,
                        delta: {
                            type: 'replace-datasets',
                            indicatorCode: currentCode,
                            from: currentDatasetCodes,
                            to: datasetCodes
                        },
                        undo: () => {
                            const el = document.getElementById(elementId);
                            if (el) {
                                const dsDiv = el.querySelector('.selected-datasets');
                                if (dsDiv) {
                                    dsDiv.innerHTML = oldDatasetsHTML;
                                    // Re-attach event handlers
                                    dsDiv.querySelectorAll('.dataset-item').forEach(item => {
                                        this._setupDatasetHandlers(item, dsDiv, currentCode, true);
                                    });
                                }
                                this.validate();
                            }
                        },
                        redo: () => {
                            const el = document.getElementById(elementId);
                            if (el) {
                                const dsDiv = el.querySelector('.selected-datasets');
                                if (dsDiv) {
                                    // Clear and re-add
                                    Array.from(dsDiv.children).forEach(child => child.remove());
                                    newDatasetElements.forEach(dsEl => {
                                        dsDiv.appendChild(dsEl.cloneNode(true));
                                    });
                                    // Re-attach event handlers
                                    dsDiv.querySelectorAll('.dataset-item').forEach(item => {
                                        this._setupDatasetHandlers(item, dsDiv, currentCode, true);
                                    });
                                }
                                this.validate();
                            }
                        }
                    });
                    actions.push(action);
                }
            }
        }

        // Flag unsaved and validate if any changes were made
        if (actions.length > 0 || !record) {
            this.flagUnsaved();
            this.validate();
        }

        return {
            success: true,
            actions: actions,
            message: actions.length === 0 ? 'No changes made' : `Made ${actions.length} change(s) to indicator "${currentCode}"`
        };
    }

    // ========== SECTION 5: API Methods - Categories ==========

    /**
     * Add a new category to a pillar
     * @param {string} pillarCode - Parent pillar code
     * @param {Object} options
     * @param {string} options.categoryCode - Category code (3 chars)
     * @param {string} options.categoryName - Category name (optional)
     * @returns {Object} Result with success status and action
     */
    addCategory(categoryCode, pillarCode, { categoryName = "", logAction = true } = {}) {
        // Validate inputs
        if (!pillarCode || typeof pillarCode !== 'string') {
            return { success: false, error: 'Invalid pillarCode' };
        }
        if (!categoryCode || !/^[A-Z]{3}$/.test(categoryCode)) {
            return { success: false, error: 'categoryCode must be 3 uppercase letters' };
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
        this.setupCategoryHandlers(categoryEl);
        let action;
        if (logAction) {
            action = this.actionHistory.recordAction({
                type: 'add-category',
                message: `Added category "${categoryName}" (${categoryCode}) to pillar ${pillarCode}`,
                delta: {
                    type: 'add-category',
                    categoryCode: categoryCode,
                    pillarCode: pillarCode,
                    categoryName: categoryName ?? ""
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
        }
        this.hasUnsavedChanges = true;
        this.validate();
        return { success: true, action: action ?? "Action not recorded" };
    }

    /**
     * Set code for a category
     * @param {HTMLElement} categoryElement - The category element
     * @param {Object} options - Options object
     * @param {string} options.newCode - The new code value
     * @returns {Object} Result with success status and action
     */
    setCategoryCode(categoryElement, { newCode } = {}) {
        if (!(categoryElement instanceof HTMLElement)) {
            return { success: false, error: 'Category element is required' };
        }
        if (!newCode) {
            return { success: false, error: 'New code is required' };
        }
        if (!this.validateCode(newCode, 'category')) {
            return { success: false, error: 'Invalid category code format (must be 3 uppercase letters)' };
        }
        if (!categoryElement.id) {
            categoryElement.id = `category-${Math.random().toString(36).substr(2,9)}`;
        }
        const elementId = categoryElement.id;
        const oldCode = categoryElement.dataset.categoryCode || '';
        const codeInput = categoryElement.querySelector('.category-code-input');
        if (!this.isCodeUnique(newCode, 'category', codeInput)) {
            return { success: false, error: 'Code already in use' };
        }
        if (oldCode === newCode) {
            return { success: true, message: 'No change needed' };
        }
        this.updateElementCode(categoryElement, newCode);
        if (codeInput) {
            codeInput.value = newCode;
        }
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
    setCategoryName(categoryCode, categoryName) {
        if (!categoryCode || typeof categoryCode !== 'string') {
            return { success: false, error: 'Invalid categoryCode' };
        }
        if (!categoryName || typeof categoryName !== 'string') {
            return { success: false, error: 'Invalid categoryName' };
        }
        const categoryEl = this.findElementByCode(categoryCode, 'Category');
        if (!categoryEl) {
            return { success: false, error: `Category ${categoryCode} not found` };
        }
        const nameEl = categoryEl.querySelector('.customization-category-header-title');
        if (!nameEl) {
            return { success: false, error: 'Category name element not found' };
        }
        const oldName = nameEl.textContent;
        if (oldName === categoryName) {
            return { success: false, error: 'New name is same as current name' };
        }
        nameEl.textContent = categoryName;
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
    setPillarName(pillarCode, pillarName ) {
        if (!pillarCode || typeof pillarCode !== 'string') {
            return { success: false, error: 'Invalid pillarCode' };
        }
        if (!pillarName || typeof pillarName !== 'string') {
            return { success: false, error: 'Invalid pillarName' };
        }
        const pillarCol = this.findElementByCode(pillarCode, 'Pillar');
        if (!pillarCol) {
            return { success: false, error: `Pillar ${pillarCode} not found` };
        }
        const nameEl = pillarCol.querySelector('.pillar-name');
        if (!nameEl) {
            return { success: false, error: 'Pillar name element not found' };
        }
        const oldName = nameEl.textContent;
        if (oldName === pillarName) {
            return { success: false, error: 'New name is same as current name' };
        }
        nameEl.textContent = pillarName;
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
    setPillarCode(pillarElement, newCode ) {
        if (!(pillarElement instanceof HTMLElement)) {
            return { success: false, error: 'Pillar element is required' };
        }
        if (!newCode) {
            return { success: false, error: 'New code is required' };
        }
        if (!this.validateCode(newCode, 'pillar')) {
            return { success: false, error: 'Invalid pillar code format (must be 2-3 uppercase letters)' };
        }
        if (!pillarElement.id) {
            pillarElement.id = `pillar-${Math.random().toString(36).substr(2,9)}`;
        }
        const elementId = pillarElement.id;
        const oldCode = pillarElement.dataset.pillarCode || '';
        const codeInput = pillarElement.querySelector('.pillar-code-input');
        if (!this.isCodeUnique(newCode, 'pillar', codeInput)) {
            return { success: false, error: 'Code already in use' };
        }
        if (oldCode === newCode) {
            return { success: true, message: 'No change needed' };
        }
        this.updateElementCode(pillarElement, newCode);
        if (codeInput) {
            codeInput.value = newCode;
        }
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
            const indicatorCode = indicator.IndicatorCode || '';
            indicator.DatasetCodes.forEach(datasetCode => {
                // Use private method - element not in DOM yet
                this._addDatasetToIndicatorElement(datasetCode, ind, indicatorCode, { record: false });
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
                        notifications.error('Error:\u0020Could\u0020not\u0020find\u0020categories\u0020container\u0020in\u0020the\u0020target\u0020pillar');
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
                        notifications.error('Error:\u0020Could\u0020not\u0020find\u0020indicators\u0020container\u0020in\u0020the\u0020target\u0020category');
                    }
                }
            } else {
                notifications.warning(`${destinationType.charAt(0).toUpperCase() + destinationType.slice(1)}\u0020"${userInput}"\u0020not\u0020found.\u0020Please\u0020use\u0020a\u0020valid\u0020${destinationType}\u0020name\u0020or\u0020code.`);
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
        if (!itemCode) {
            notifications.warning('Cannot\u0020preview:\u0020No\u0020code\u0020assigned\u0020to\u0020this\u0020item\u0020yet.');
            return;
        }
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
        let chartInstance = null;
        try {
            if (itemType === 'indicator') {
                chartInstance = new IndicatorPanelChart(chartContainer, itemCode);
            } else {
                chartInstance = new ScorePanelChart(chartContainer, itemCode);
            }
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
        const closeModal = () => {
            if (chartInstance && typeof chartInstance.destroy === 'function') {
                try {
                    chartInstance.destroy();
                } catch (error) {
                    console.error('Error destroying chart:', error);
                }
            }
            if (window.SSPICharts && chartInstance) {
                const index = window.SSPICharts.indexOf(chartInstance);
                if (index > -1) {
                    window.SSPICharts.splice(index, 1);
                }
            }
            overlay.remove();
        };
        closeBtn.addEventListener('click', closeModal);
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
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
            notifications.warning('Cannot\u0020preview:\u0020No\u0020dataset\u0020code\u0020found.');
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
                TreeIndex: [0, category.pillarIdx, category.catIdx, -1],
                TreePath: `sspi/${category.pillarCode.toLowerCase()}/${category.code.toLowerCase()}`,
                ItemOrder: category.itemOrder
            });
        });
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
                ScoreFunction: indicator.scoreFunction,
                TreeIndex: [0, indicator.pillarIdx, indicator.catIdx, indicator.indIdx],
                TreePath: `sspi/${indicator.pillarCode.toLowerCase()}/${indicator.categoryCode.toLowerCase()}/${indicator.code.toLowerCase()}`,
                ItemOrder: indicator.itemOrder
            });
        });
        return metadataItems;
    }

    /**
     * Export data in format suitable for scoring pipeline
     * @returns {Object} Structure data with metadata for scoring
     */
    async exportForScoring() {
        let res = await this.fetch("/api/v1/customize/score", {
            method: "POST",
            body: JSON.stringify({
                metadata: this.exportMetadata(),
                changes: this.actionHistory.exportActionLog()
            }),
            headers: {
                "Content-type": "application/json; charset=UTF-8"
            }
        })
        console.log(res)
    }

    /**
     * Show a temporary notification to the user
     * @param {string} message - The message to display
     * @param {string} type - The notification type ('success', 'error', 'info')
     * @param {number} duration - Duration in milliseconds (default: 3000)
     */
    showNotification(message, type = 'info', duration = 3000) {
        // Delegate to global notification manager
        return notifications.show(message, type, duration);
    }

    // Cache Management Helper Methods
    /**
     * Get the cache key for the current base configuration
     * Single cache key per user per base config
     */
    getCacheKey() {
        const username = this.username || 'anonymous';
        return `customSSPI_${username}_${this.baseConfig}`;
    }

    /**
     * Save data to cache
     */
    setCache(data) {
        const cacheKey = this.getCacheKey();
        try {
            localStorage.setItem(cacheKey, JSON.stringify(data));
        } catch (error) {
            console.error('Error saving cache:', error);
        }
    }

    /**
     * Load data from cache
     */
    getCache() {
        const cacheKey = this.getCacheKey();
        try {
            const data = localStorage.getItem(cacheKey);
            return data ? JSON.parse(data) : null;
        } catch (error) {
            console.error('Error loading cache:', error);
            return null;
        }
    }

    /**
     * Clear cache for current base config
     */
    clearCache() {
        const cacheKey = this.getCacheKey();
        try {
            localStorage.removeItem(cacheKey);
            console.log(`Cleared cache for ${this.baseConfig}`);
        } catch (error) {
            console.error('Error clearing cache:', error);
        }
    }

    // Legacy storage methods (kept for backwards compatibility during migration)
    getStorageKey(key) {
        // OLD: Namespace storage keys with username for user isolation
        return `customSSPI_${this.username}_${key}`;
    }

    setStorage(key, value) {
        const namespacedKey = this.getStorageKey(key);
        window.observableStorage.setItem(namespacedKey, value);
    }

    getStorage(key) {
        const namespacedKey = this.getStorageKey(key);
        return window.observableStorage.getItem(namespacedKey);
    }

    markUnsaved() {
        this.unsavedChanges = true;
        // Legacy: still set old storage flag for backwards compatibility
        this.setStorage('hasUnsaved', true);
    }

    markSaved() {
        this.unsavedChanges = false;
        // Legacy: still clear old storage flag for backwards compatibility
        this.setStorage('hasUnsaved', false);
    }

    setupUnsavedChangesWarning() {
        // Warn before leaving page with unsaved changes
        window.addEventListener('beforeunload', (e) => {
            if (this.unsavedChanges) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
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
            this.setStorage('expansionState', stateLookup);
            // Save scroll position
            this.setStorage('scrollX', window.scrollX);
            this.setStorage('scrollY', window.scrollY);
        });
    }

    restoreExpansionState() {
        const cachedStateObject = this.getStorage('expansionState');
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
        const scrollX = this.getStorage('scrollX');
        const scrollY = this.getStorage('scrollY');
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
                warnings.push('Category '+ categoryName + ' (' + categoryCode + ') has no indicators');
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
                errors.push(`Category\u0020${categoryName}\u0020(${categoryCode})\u0020contains\u0020nested\u0020categories.\u0020Nested\u0020categories\u0020are\u0020not\u0020allowed.`);
            }
        });
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

        // Show appropriate notification based on validation results
        if (result.errors.length > 0) {
            notifications.error(message, 10000); // Longer duration for errors
        } else if (result.warnings.length > 0) {
            notifications.warning(message, 8000);
        } else {
            notifications.success(message);
        }
    }

    /**
     * Show the changes history modal
     */
    showChangesHistory() {
        if (!window.ChangesHistoryModal) {
            console.error('ChangesHistoryModal class not loaded');
            notifications.error('Changes history feature is not available. Please refresh the page.');
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
        console.log(`Loading initial data for base_config: ${this.baseConfig}`);

        // Check and migrate legacy data first
        await this.checkLegacyData();

        // STEP 1: Try to load from cache
        const cachedState = this.getCache();
        if (cachedState && cachedState.hasModifications) {
            console.log('Restoring from cached state');
            try {
                await this.restoreFromCache(cachedState);
                this.showNotification("✓ Restored from previous session");
                this.restoreExpansionState();
                this.restoreScrollPosition();
                return;
            } catch (error) {
                console.warn('Failed to restore cache, loading from server:', error);
                this.clearCache();
            }
        }

        // STEP 2: Load fresh from server based on base_config
        await this.loadFromServer();
        this.restoreExpansionState();
        this.restoreScrollPosition();
    }

    /**
     * Load configuration from server based on base_config
     */
    async loadFromServer() {
        try {
            this.showLoadingState('Loading configuration...');

            let endpoint;
            let configName;

            // Determine endpoint based on base_config
            if (this.baseConfig === 'sspi' || this.baseConfig === 'default') {
                endpoint = '/api/v1/customize/default-structure';
                configName = 'Standard SSPI';
            } else if (this.baseConfig === 'blank') {
                endpoint = '/api/v1/customize/empty-structure';
                configName = 'Blank Configuration';
            } else {
                // Assume it's a saved config ID
                endpoint = `/api/v1/customize/load/${this.baseConfig}`;
                configName = null; // Will be set from response
            }

            const response = await this.fetch(endpoint);

            if (response.success) {
                // Store dataset details
                if (response.datasetDetailsMap) {
                    this.datasetDetails = response.datasetDetailsMap;
                }

                // Import metadata
                await this.importDataAsync(response.metadata);

                // Restore action history if available
                if (response.actions && Array.isArray(response.actions)) {
                    console.log('Restoring action history with', response.actions.length, 'actions');
                    this.actionHistory.clear();
                    response.actions.forEach(action => {
                        this.actionHistory.actions.push({
                            ...action,
                            undo: () => {},
                            redo: () => {}
                        });
                    });
                    this.actionHistory.currentIndex = this.actionHistory.actions.length - 1;
                }

                // Set config name
                if (response.name) {
                    configName = response.name;
                }
                this.currentConfigName = configName;

                // Clear unsaved state for freshly loaded config
                this.clearUnsavedState();

                this.hideLoadingState();
                console.log(`Loaded ${configName} successfully`);
            } else {
                this.handleLoadError('Failed to load configuration: ' + (response.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error loading from server:', error);
            this.handleLoadError('Network error loading configuration');
        }
    }

    /**
     * Restore configuration from cached state
     */
    async restoreFromCache(cachedState) {
        console.log('Restoring from cache:', cachedState);

        // Restore dataset details
        if (cachedState.datasetDetailsMap) {
            this.datasetDetails = cachedState.datasetDetailsMap;
        }

        // Import metadata
        if (cachedState.metadata) {
            await this.importDataAsync(cachedState.metadata);
        }

        // Restore action history
        if (cachedState.actions && Array.isArray(cachedState.actions)) {
            this.actionHistory.clear();
            cachedState.actions.forEach(action => {
                this.actionHistory.actions.push({
                    ...action,
                    undo: () => {},
                    redo: () => {}
                });
            });
            this.actionHistory.currentIndex = this.actionHistory.actions.length - 1;
        }

        // Mark as having unsaved changes
        this.flagUnsaved();
    }

    /**
     * Check for and migrate legacy session/cache data
     */
    async checkLegacyData() {
        // Check for old sspi_active_session
        const oldSession = window.observableStorage?.getItem('sspi_active_session');
        if (oldSession) {
            console.log('Found legacy session, cleaning up...');
            window.observableStorage.removeItem('sspi_active_session');
            window.observableStorage.removeItem('sspi_pending_config');
        }

        // Migrate old cache if exists
        const oldCacheKey = `customSSPI_${this.username}_cachedModifications`;
        const oldCache = localStorage.getItem(oldCacheKey);

        if (oldCache && this.baseConfig === 'sspi') {
            console.log('Migrating legacy cache to new format');
            try {
                const data = JSON.parse(oldCache);
                const newCacheKey = this.getCacheKey();
                localStorage.setItem(newCacheKey, oldCache);
                localStorage.removeItem(oldCacheKey);
                // Also remove old hasUnsaved flag
                localStorage.removeItem(`customSSPI_${this.username}_hasUnsaved`);
                console.log('Migration complete');
            } catch (error) {
                console.error('Failed to migrate cache:', error);
            }
        }
    }
    
    async discardChanges() {
        try {
            this.clearCache();
            this.showLoadingState('Discarding changes...');
            this.clearUnsavedState();
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
            notifications.error('Error discarding changes. Please try again.');
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
                if (response.datasetDetailsMap) {
                    const currentCount = Object.keys(this.datasetDetails).length;
                    if (currentCount === 0) {
                        console.log('Dataset details not yet loaded, loading from datasetDetailsMap');
                        this.datasetDetails = response.datasetDetailsMap;
                        console.log(`Loaded ${Object.keys(this.datasetDetails).length} dataset details for selection`);
                    } else {
                        console.log(`Dataset details already loaded (${currentCount} datasets)`);
                    }
                }
                await this.importDataAsync(response.metadata);
                this.hideLoadingState();
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
        const loadingDiv = this.parentElement.querySelector('#sspi-loading-indicator');
        if (loadingDiv) {
            loadingDiv.remove();
        }
        this.container.style.display = '';
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
        console.log('Using', Object.keys(this.datasetDetails).length, 'dataset details from datasetDetailsMap');
        this.isImporting = true;
        this.container.querySelectorAll('.category-box, .indicator-card').forEach(e => e.remove());
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
        this.isImporting = false;
        this.actionHistory.clear();
        console.log('Cleared undo/redo history after initial metadata import');
        this.markInvalidIndicatorPlacements();
        this.markInvalidNestedCategories();
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
                        // Add datasets if present - use private method since element isn't in DOM yet
                        const datasetCodes = indicatorItem.DatasetCodes || [];
                        if (!this.isImporting) {
                            console.log(`Processing ${indicatorItem.ItemCode}: ${datasetCodes.length} dataset codes`);
                        }
                        if (datasetCodes.length > 0) {
                            datasetCodes.forEach((datasetCode, idx) => {
                                if (!this.isImporting) {
                                    console.log(`Adding dataset ${datasetCode} to ${indicatorItem.ItemCode}`);
                                }
                                // Use private method - element not in DOM yet, can't use code-based addDataset()
                                const result = this._addDatasetToIndicatorElement(
                                    datasetCode,
                                    indEl,
                                    indicatorItem.ItemCode,
                                    { record: false }
                                );
                                if (!result.success) {
                                    console.warn(`Failed to add dataset ${datasetCode}: ${result.error}`);
                                }
                            });
                            // Verify datasets were added
                            if (!this.isImporting) {
                                const selectedDatasetsDiv = indEl.querySelector('.selected-datasets');
                                const addedDatasets = selectedDatasetsDiv?.querySelectorAll('.dataset-item') || [];
                                console.log(`After adding: ${addedDatasets.length} dataset items in DOM for ${indicatorItem.ItemCode}`);
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

    exportData() {
        // Export current SSPI structure as metadata array
        const metadataItems = [];

        // Add SSPI root item
        const pillarCodes = [];
        const pillarColumns = this.container.querySelectorAll('.pillar-column');

        pillarColumns.forEach(col => {
            const pillarCode = col.dataset.pillarCode || col.dataset.itemCode;
            if (pillarCode) {
                pillarCodes.push(pillarCode);
            }
        });

        metadataItems.push({
            ItemType: 'SSPI',
            ItemCode: 'sspi',
            ItemName: 'Sustainable and Shared Prosperity Policy Index',
            Children: pillarCodes,
            DocumentType: 'ItemDetail'
        });

        // Process each pillar
        pillarColumns.forEach(col => {
            const pillarCode = col.dataset.pillarCode || col.dataset.itemCode;
            const pillarName = col.querySelector('.pillar-name')?.textContent || '';
            const categoryCodes = [];

            // Get all categories in this pillar
            const categories = col.querySelectorAll('.category-box');
            categories.forEach(catEl => {
                const categoryCode = catEl.dataset.categoryCode || catEl.dataset.itemCode;
                if (categoryCode) {
                    categoryCodes.push(categoryCode);
                }
            });

            // Add pillar item
            metadataItems.push({
                ItemType: 'Pillar',
                ItemCode: pillarCode,
                ItemName: pillarName,
                PillarCode: pillarCode,
                Children: categoryCodes,
                CategoryCodes: categoryCodes,
                DocumentType: 'PillarDetail',
                TreePath: `sspi/${pillarCode.toLowerCase()}`
            });

            // Process each category
            categories.forEach(catEl => {
                const categoryCode = catEl.dataset.categoryCode || catEl.dataset.itemCode;
                const categoryName = catEl.querySelector('.customization-category-header-title')?.textContent || '';
                const indicatorCodes = [];

                // Get all indicators in this category
                const indicators = catEl.querySelectorAll('.indicator-card');
                indicators.forEach(indEl => {
                    const indicatorCode = indEl.dataset.indicatorCode || indEl.dataset.itemCode;
                    if (indicatorCode) {
                        indicatorCodes.push(indicatorCode);
                    }
                });

                // Add category item
                metadataItems.push({
                    ItemType: 'Category',
                    ItemCode: categoryCode,
                    ItemName: categoryName,
                    CategoryCode: categoryCode,
                    PillarCode: pillarCode,
                    Children: indicatorCodes,
                    IndicatorCodes: indicatorCodes,
                    DocumentType: 'CategoryDetail',
                    TreePath: `sspi/${pillarCode.toLowerCase()}/${categoryCode.toLowerCase()}`
                });

                // Process each indicator
                indicators.forEach(indEl => {
                    const indicatorCode = indEl.dataset.indicatorCode || indEl.dataset.itemCode;
                    const indicatorName = indEl.querySelector('.indicator-name')?.textContent || '';
                    const scoreFunction = indEl.querySelector('.editable-score-function')?.textContent || 'Score = 0';

                    // Get dataset codes
                    const datasetCodes = [];
                    const datasetItems = indEl.querySelectorAll('.dataset-item');
                    datasetItems.forEach(dsEl => {
                        const datasetCode = dsEl.dataset.datasetCode;
                        if (datasetCode) {
                            datasetCodes.push(datasetCode);
                        }
                    });

                    // Add indicator item
                    metadataItems.push({
                        ItemType: 'Indicator',
                        ItemCode: indicatorCode,
                        ItemName: indicatorName,
                        IndicatorCode: indicatorCode,
                        CategoryCode: categoryCode,
                        PillarCode: pillarCode,
                        ScoreFunction: scoreFunction,
                        DatasetCodes: datasetCodes,
                        Children: [],
                        DocumentType: 'IndicatorDetail',
                        TreePath: `sspi/${pillarCode.toLowerCase()}/${categoryCode.toLowerCase()}/${indicatorCode.toLowerCase()}`
                    });
                });
            });
        });

        return metadataItems;
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
            if (!this.validateCode(newCode, type)) {
                return; // Validation message already shown by input handler
            }
            if (!this.isCodeUnique(newCode, type, input)) {
                return; // Validation message already shown by input handler
            }
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
        const oldCode = type === 'indicator' ? element.dataset.indicatorCode :
                       type === 'category' ? element.dataset.categoryCode :
                       element.dataset.pillarCode; // it's an older code, sir, but it checks out
        if (oldCode === newCode) {
            return; // it's an older code, sir, but it checks out
        }
        // Call the appropriate API method
        let result;
        try {
            if (type === 'indicator') {
                // Use new modifyIndicator() method
                result = this.modifyIndicator(oldCode, { newIndicatorCode: newCode });
            } else if (type === 'category') {
                result = this.setCategoryCode(element, newCode);
            } else if (type === 'pillar') {
                result = this.setPillarCode(element, newCode);
            }
            if (result && !result.success) {
                console.error(`Failed to set ${type} code:`, result.error);
                this.showNotification(`Error: ${result.error}`, 'error', 3000);
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
            input.classList.remove('input-error')
        }
        input.addEventListener('blur', (event) => {
            if (type !== 'success') {
                input.classList.add('input-error')
            } else {
                input.classList.remove('input-error')
            }
            element.textContent = '';
            element.classList.remove('error', 'success');
        })
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
                notifications.warning('Maximum of 10 datasets allowed per indicator');
                return;
            }
            // Show dataset selection modal
            this.showDatasetSelectionModal(selectedDatasetsDiv);
        } catch (error) {
            console.error('Error showing dataset selector:', error);
            notifications.error('Error loading datasets. Please try again.');
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
        await selector.show(currentSelections);
    }
    
    updateDatasetSelection(selectedDatasetsDiv, selectedDatasets) {
        // Get indicator code from parent indicator card
        const indicatorCard = selectedDatasetsDiv.closest('.indicator-card');
        const indicatorCode = indicatorCard ? indicatorCard.dataset.indicatorCode : null;

        if (!indicatorCode) {
            console.error('Could not find indicator code for dataset selection');
            return;
        }

        // Clear existing selections
        selectedDatasetsDiv.innerHTML = '';

        // Add new selections using unified addDataset method
        // Datasets are already in the backend format - no conversion needed
        selectedDatasets.forEach(dataset => {
            const result = this.addDataset(dataset.DatasetCode, indicatorCode);
            if (!result.success) {
                console.warn(`Failed to add dataset ${dataset.DatasetCode}: ${result.error}`);
            }
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
            const actionHistory = {
                actions: this.actionHistory.actions.map(action => ({
                    actionId: action.actionId,
                    timestamp: action.timestamp,
                    type: action.type,
                    message: action.message,
                    delta: action.delta
                    // Exclude undo/redo functions - can't serialize functions
                })),
                currentIndex: this.actionHistory.currentIndex,
                baseline: this.actionHistory.baseline
            };
            const cacheData = {
                hasModifications: this.unsavedChanges,
                timestamp: Date.now(),
                metadata: metadata,
                datasetDetailsMap: this.datasetDetails,
                actions: actionHistory.actions,
                baseConfig: this.baseConfig
            };
            const cacheSize = JSON.stringify(cacheData).length;
            console.log('Approximate cache size:', parseFloat((cacheSize / 1024 / 1024).toFixed(2)), 'MB');
            if (cacheSize > 5 * 1024 * 1024) { // 5MB limit
                console.warn('Cache data is too large (>5MB), skipping cache');
                notifications.warning('Configuration too large to cache locally. Please save to server.');
                return;
            }
            this.setCache(cacheData);
            console.log('SSPI modifications cached successfully');
        } catch (error) {
            console.warn('Failed to cache SSPI modifications:', error);
        }
    }

    async loadCachedState() {
        try {
            const cacheData = this.getStorage("cachedModifications");
            if (!cacheData || !this.isValidCacheData(cacheData)) {
                return false;
            }
            console.log('Loading cached SSPI modifications from:', new Date(cacheData.lastModified));
            if (cacheData.datasetDetailsMap) { // Restore dataset details map
                this.datasetDetails = cacheData.datasetDetailsMap;
                console.log('Restored', Object.keys(this.datasetDetails).length, 'dataset details from cache map');
            }
            await this.importDataAsync(cacheData.metadata);
            if (cacheData.actionHistory) { // Restore action history
                this.actionHistory.actions = cacheData.actionHistory.actions || [];
                this.actionHistory.currentIndex = cacheData.actionHistory.currentIndex ?? -1;
                this.actionHistory.baseline = cacheData.actionHistory.baseline || null;
                console.log('Restored', this.actionHistory.actions.length, 'actions from cache');
            }
            this.setUnsavedState(cacheData.hasModifications); // Set unsaved state based on cache
            return true;
        } catch (error) {
            console.warn('Failed to load cached SSPI modifications:', error);
            this.clearCache(); // Clear corrupted cache
            return false;
        }
    }
    
    clearCache() {
        try {
            const cacheKey = this.getStorageKey("cachedModifications");
            window.observableStorage.removeItem(cacheKey);
            console.log('SSPI modifications and dataset cache cleared');
        } catch (error) {
            console.warn('Failed to clear SSPI cache:', error);
        }
    }
    
    hasCachedModifications() {
        try {
            const cacheData = this.getStorage("cachedModifications");
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
        const requiredFields = ['hasModifications', 'lastModified', 'metadata'];
        for (const field of requiredFields) {
            if (!(field in cacheData)) {
                console.warn(`Invalid cache data: missing field '${field}'`);
                return false;
            }
        }
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
        const maxAge = 7 * 24 * 60 * 60 * 1000;
        const age = Date.now() - cacheData.lastModified;
        if (age > maxAge) {
            console.warn('Cache data is too old (>7 days), discarding');
            return false;
        }
        if (cacheData.metadata.length > 0) {
            const firstItem = cacheData.metadata[0];
            if (!firstItem || typeof firstItem !== 'object' || !firstItem.ItemType) {
                console.warn('Invalid cache data: metadata items have invalid structure');
                return false;
            }
        }
        return true;
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
        // Listen for storage events from other tabs
        window.addEventListener('storage', (e) => {
            const myCacheKey = this.getCacheKey();
            if (e.key === myCacheKey && e.newValue !== e.oldValue) {
                console.log('Cache updated in another tab');
                if (confirm('Configuration updated in another tab. Reload to see changes?')) {
                    window.location.reload();
                }
            }
        });
    }
    
}
// Usage example:
// const root = document.getElementById('sspi-root');
// new CustomizableSSPIStructure(root);
