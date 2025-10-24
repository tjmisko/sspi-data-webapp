// customizable-sspi.js
// SSPI Tree UI implementing full specification (three-column layout)

class CustomizableSSPIStructure {
    constructor(parentElement, options = {}) {
        const {
            pillars = ['Sustainability', 'Market Structure', 'Public Goods'],
            autoLoad = true,
            loadingDelay = 100
        } = options;
        
        this.parentElement = parentElement;
        this.pillars = pillars;
        this.autoLoad = autoLoad;
        this.loadingDelay = loadingDelay;
        this.unsavedChanges = false;
        this.draggedEl = null;
        this.origin = null;
        this.dropped = false;
        this.isLoading = false;
        this.cacheTimeout = null;
        
        // Initialize changelog system
        this.baselineMetadata = null;
        this.diffCache = null;
        
        this.injectStyles();
        this.initToolbar();
        this.initRoot();
        this.addEventListeners();
        this.loadConfigurationsList();
        this.setupCacheSync();
        
        // Auto-load cached modifications or default metadata if enabled
        if (this.autoLoad) {
            // Small delay to ensure DOM is ready
            setTimeout(() => {
                this.loadInitialData();
            }, this.loadingDelay);
        }
    }

    injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
.insertion-indicator {
    height: 5px;
    background: var(--green-accent);
    margin: 4px 0;
}
.drag-over {
    outline: 2px dashed var(--green-accent);
}
.unsaved-changes {
    background: var(--ms-color);
    color: white;
}
.draggable-item {
    cursor: grab;
}
.draggable-item.dragging {
    visibility: hidden;
}
.sspi-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    color: var(--text-color);
    font-size: 1.1rem;
}
.sspi-loading::before {
    content: '';
    width: 20px;
    height: 20px;
    margin-right: 10px;
    border: 2px solid var(--subtle-line-color);
    border-top-color: var(--green-accent);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}
@keyframes slideInRight {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
@keyframes slideOutRight {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
}
.sspi-error {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    color: var(--sus-color);
    font-size: 1rem;
    flex-direction: column;
    gap: 1rem;
}
`;
        document.head.appendChild(style);
    }

    initToolbar() {
        const toolbar = document.createElement('div');
        toolbar.classList.add('sspi-toolbar');

        const importBtn = document.createElement('button');
        importBtn.textContent = 'Load Default SSPI';
        importBtn.addEventListener('click', async () => {
            try {
                this.showLoadingState('Loading default SSPI metadata...');
                
                // Clear cache when explicitly loading default metadata
                this.clearCache();
                
                const response = await this.fetch('/api/v1/customize/default-structure');
                if (response.success) {
                    console.log('Loading default SSPI metadata with', response.stats);
                    
                    // Use async import for better performance with large metadata
                    await this.importDataAsync(response.metadata);
                    
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

        const exportBtn = document.createElement('button');
        exportBtn.textContent = 'Export Metadata';
        exportBtn.addEventListener('click', () => {
            const json = JSON.stringify(this.exportData(), null, 2);
            console.log('SSPI Metadata Format:', json);
            alert('Metadata JSON copied to console.');
        });

        this.saveButton = document.createElement('button');
        this.saveButton.textContent = 'Save';
        this.saveButton.addEventListener('click', async () => {
            await this.saveConfiguration();
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

        toolbar.append(importBtn, exportBtn, this.saveButton, scoreVisualizeBtn, validateBtn, this.discardButton, expandAllBtn, collapseAllBtn);
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
            header.classList.add('customization-pillar-header');
            header.setAttribute('role', 'treeitem');
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

    addEventListeners() {
        // Pillar rename
        this.container.querySelectorAll('.customization-pillar-header').forEach(h =>
            h.addEventListener('keydown', e => {
                if (e.key === 'Enter') { e.preventDefault(); h.blur(); }
            })
        );

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
            const el = e.target.closest('.draggable-item');
            if (!el) return;
            this.draggedEl = el;
            this.origin = { parent: el.parentNode, next: el.nextSibling };
            this.dropped = false;
            el.classList.add('dragging');
            const clone = el.cloneNode(true);
            clone.style.position = 'absolute'
            document.body.appendChild(clone);
            const rect = el.getBoundingClientRect();
            e.dataTransfer.setDragImage(clone, rect.width/2, rect.height/2);
            setTimeout(() => document.body.removeChild(clone), 0);
            if (!el.id) el.id = `id-${Math.random().toString(36).substr(2,9)}`;
            e.dataTransfer.setData('text/plain', el.id);
            e.dataTransfer.effectAllowed = 'move';
        });

        this.container.addEventListener('dragend', () => {
            if (!this.dropped && this.origin && this.draggedEl) {
                this.origin.parent.insertBefore(this.draggedEl, this.origin.next);
            }
            if (this.draggedEl) this.draggedEl.classList.remove('dragging');
            this.draggedEl = null;
            this.origin = null;
            this.dropped = false;
            this.clearIndicators();
        });

        this.container.addEventListener('dragover', e => {
            const z = e.target.closest('.drop-zone');
            if (!z || !this.draggedEl) return;
            e.preventDefault();
            z.classList.add('drag-over');
            this.clearIndicators(z);
            const overItem = e.target.closest('.draggable-item');
            if (overItem && overItem.parentNode === z) {
                const { top, height } = overItem.getBoundingClientRect();
                const before = (e.clientY - top) < (height / 2);
                const indicator = document.createElement('div');
                indicator.className = 'insertion-indicator';
                z.insertBefore(indicator, before ? overItem : overItem.nextSibling);
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
            const indicator = z.querySelector('.insertion-indicator');
            if (indicator) {
                z.insertBefore(this.draggedEl, indicator);
                indicator.remove();
            } else if (z.dataset.accept === this.draggedEl.dataset.type) {
                z.appendChild(this.draggedEl);
            }
            this.dropped = true;
            this.draggedEl.classList.remove('dragging');
            this.validate(z);
            this.flagUnsaved();
            this.markInvalidIndicatorPlacements();
            const order = Array.from(z.children).map(c => c.id);
            console.log('New order:', order);
        });

        // Context menu & keyboard
        this.container.addEventListener('contextmenu', e => {
            const t = e.target.closest('.draggable-item'); if (!t) return; e.preventDefault();
            this.showContextMenu(e.pageX, e.pageY, t);
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

        // Custom collapse button handling
        this.container.addEventListener('click', e => {
            // Handle collapse toggle button clicks
            if (e.target.closest('.collapse-toggle-btn')) {
                const toggleBtn = e.target.closest('.collapse-toggle-btn');
                const collapsible = toggleBtn.closest('[data-expanded]');
                if (collapsible) {
                    const isExpanded = collapsible.dataset.expanded === 'true';
                    collapsible.dataset.expanded = (!isExpanded).toString();
                    console.log('Toggled collapsible:', collapsible, 'new state:', collapsible.dataset.expanded);
                }
            }
        });
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

    createCategoryElement() {
        const cat = document.createElement('div');
        cat.classList.add('category-box','draggable-item');
        cat.setAttribute('draggable','true');
        cat.setAttribute('role','group');
        cat.dataset.type='category';
        cat.innerHTML = `
<div class="category-collapsible" data-expanded="true">
    <div class="customization-category-header">
        <button class="collapse-toggle-btn category-toggle" type="button">
            <span class="collapse-icon">▼</span>
        </button>
        <h4 class="customization-category-header-title" contenteditable="true">New Category</h4>
        <div class="category-code-section">
            <label class="code-label">Code:</label>
            <input type="text" class="category-code-input" maxlength="3" placeholder="CAT" 
                   pattern="[A-Z]{3}" title="Exactly 3 uppercase letters required">
            <span class="code-validation-message"></span>
        </div>
    </div>
    <div class="category-content">
        <div class="indicators-container drop-zone" data-accept="indicator" role="group"></div>
        <button class="add-indicator" aria-label="Add Indicator">+ Add Indicator</button>
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
        ind.setAttribute('draggable','true');
        ind.setAttribute('role','treeitem');
        ind.dataset.type='indicator';
        ind.innerHTML = `
<div class="indicator-collapsible" data-expanded="false">
    <div class="customization-indicator-header">
        <button class="collapse-toggle-btn indicator-toggle" type="button">
            <span class="collapse-icon">▼</span>
        </button>
        <h5 class="indicator-name" contenteditable="true">New Indicator</h5>
        <div class="indicator-code-section">
            <label class="code-label">Code:</label>
            <input type="text" class="indicator-code-input" maxlength="6" placeholder="INDIC1" 
                   pattern="[A-Z0-9]{6}" title="Exactly 6 uppercase letters/numbers required">
            <span class="code-validation-message"></span>
        </div>
    </div>
    <div class="indicator-config">
    <div class="dataset-selection">
        <label>Datasets (max 5):</label>
        <div class="selected-datasets"></div>
        <button class="add-dataset-btn" type="button">+ Add Dataset</button>
    </div>
    <div class="scoring-function">
        <label>Scoring Function:</label>
        <select class="scoring-function-select">
            <option value="average">Average</option>
            <option value="weighted_average">Weighted Average</option>
            <option value="sum">Sum</option>
            <option value="min">Minimum</option>
            <option value="max">Maximum</option>
        </select>
    </div>
    <div class="goalposts-section">
        <div class="goalpost-input">
            <label>Lower Goalpost:</label>
            <input type="number" class="lower-goalpost" value="0" step="0.1">
        </div>
        <div class="goalpost-input">
            <label>Upper Goalpost:</label>
            <input type="number" class="upper-goalpost" value="100" step="0.1">
        </div>
        <div class="indicator-options">
            <label>
                <input type="checkbox" class="inverted-checkbox"> Inverted (lower is better)
            </label>
        </div>
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

    expandAll() {
        const allCollapsibles = this.container.querySelectorAll('[data-expanded]');
        allCollapsibles.forEach(collapsible => {
            collapsible.dataset.expanded = 'true';
        });
    }

    collapseAll() {
        const allCollapsibles = this.container.querySelectorAll('[data-expanded]');
        allCollapsibles.forEach(collapsible => {
            collapsible.dataset.expanded = 'false';
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
        
        // Fill in the indicator data
        const indicatorName = ind.querySelector('.indicator-name');
        const indicatorCodeInput = ind.querySelector('.indicator-code-input');
        const lowerGoalpost = ind.querySelector('.lower-goalpost');
        const upperGoalpost = ind.querySelector('.upper-goalpost');
        const invertedCheckbox = ind.querySelector('.inverted-checkbox');
        
        if (indicatorName) indicatorName.textContent = indicator.indicator_name || '';
        if (indicatorCodeInput) indicatorCodeInput.value = indicator.indicator_code || '';
        if (lowerGoalpost) lowerGoalpost.value = indicator.lower_goalpost || 0;
        if (upperGoalpost) upperGoalpost.value = indicator.upper_goalpost || 100;
        if (invertedCheckbox) invertedCheckbox.checked = indicator.inverted || false;
        
        // Add datasets if present
        if (indicator.dataset_codes && indicator.dataset_codes.length > 0) {
            const selectedDatasetsDiv = ind.querySelector('.selected-datasets');
            indicator.dataset_codes.forEach(datasetCode => {
                this.addDatasetToIndicator(selectedDatasetsDiv, datasetCode, 1.0);
            });
        }
        
        indicatorsContainer.appendChild(ind);
        this.validate(indicatorsContainer);
        this.updateHierarchyOnAdd(ind, 'indicator');
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
        [
            { name: 'Move to Pillar', handler: () => this.promptMove(target) },
            { name: 'Rename', handler: () => this.renameItem(target) },
            { name: 'Delete', handler: () => this.deleteItem(target) },
            { name: 'Set Goalposts', handler: () => this.editGoalposts(target) }
        ].forEach(a => {
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
        // Create styled modal instead of native prompt
        const modal = this.createMoveToPillarModal(el);
        document.body.appendChild(modal);

        // Focus on the input
        setTimeout(() => {
            const input = modal.querySelector('.move-pillar-input');
            if (input) input.focus();
        }, 100);
    }

    createMoveToPillarModal(element) {
        const overlay = document.createElement('div');
        overlay.className = 'move-pillar-overlay';

        // Get pillar info for display
        const pillarInfo = this.container.querySelectorAll('.pillar-column');
        const pillarOptions = Array.from(pillarInfo).map(col => {
            const name = col.dataset.pillar;
            const codeInput = col.querySelector('.pillar-code-input');
            const code = codeInput ? codeInput.value.trim() : '';
            return { name, code };
        }).filter(p => p.name && p.code);

        const optionsHtml = pillarOptions.map(p =>
            `<button class="pillar-option clickable" type="button" data-pillar-name="${p.name}" data-pillar-code="${p.code}">
                <strong>${p.code}</strong> - ${p.name}
            </button>`
        ).join('');

        const elementType = element.dataset.type;
        const isIndicator = elementType === 'indicator';
        const instructionText = isIndicator
            ? 'Select destination pillar (indicator will be moved to pillar bottom):'
            : 'Select destination pillar or enter pillar name/code:';

        // Create dynamic placeholder from available pillar codes
        const placeholderCodes = pillarOptions.slice(0, 3).map(p => p.code).join(', ');
        const placeholder = placeholderCodes ? `Enter pillar name or code (e.g., ${placeholderCodes})` : 'Enter pillar name or code';

        overlay.innerHTML = `
            <div class="move-pillar-modal">
                <div class="move-pillar-header">
                    <h3>Move ${elementType === 'category' ? 'Category' : 'Indicator'} to Pillar</h3>
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
        const pillarOptionButtons = overlay.querySelectorAll('.pillar-option.clickable');

        // Add click handlers to pillar option buttons
        pillarOptionButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const pillarCode = btn.dataset.pillarCode;
                input.value = pillarCode;
                input.focus();
            });
        });

        const handleMove = () => {
            const userInput = input.value.trim();
            if (!userInput) {
                overlay.remove();
                return;
            }

            // Find pillar column by name or code (case-insensitive)
            const col = Array.from(this.container.querySelectorAll('.pillar-column'))
                .find(c => {
                    const pillarName = c.dataset.pillar;
                    const codeInput = c.querySelector('.pillar-code-input');
                    const pillarCode = codeInput ? codeInput.value.trim() : '';

                    return pillarName.toLowerCase() === userInput.toLowerCase() ||
                           pillarCode.toLowerCase() === userInput.toLowerCase();
                });

            if (col) {
                const elementType = element.dataset.type;

                if (elementType === 'category') {
                    // Move category to pillar's categories-container
                    const targetContainer = col.querySelector('.categories-container');
                    if (targetContainer) {
                        targetContainer.appendChild(element);
                        this.flagUnsaved();
                        overlay.remove();
                        console.log(`Category moved to pillar: ${userInput}`);
                    } else {
                        alert('Error: Could not find categories container in the target pillar');
                    }
                } else if (elementType === 'indicator') {
                    // Move indicator to bottom of categories-container (outside any specific category)
                    // This creates an invalid state but keeps it in the proper drop zone
                    // This allows users to temporarily move indicators between pillars
                    // before assigning them to a specific category

                    // Append to the categories-container at the bottom
                    const categoriesContainer = col.querySelector('.categories-container');
                    if (categoriesContainer) {
                        categoriesContainer.appendChild(element);
                    } else {
                        // Fallback: insert before Add Category button
                        const addCategoryBtn = col.querySelector('.add-category');
                        if (addCategoryBtn) {
                            col.insertBefore(element, addCategoryBtn);
                        } else {
                            col.appendChild(element);
                        }
                    }

                    this.flagUnsaved();
                    overlay.remove();
                    console.log(`Indicator moved to categories-container bottom (invalid state): ${userInput}`);

                    // Add visual indicator that this is an invalid state
                    element.classList.add('temporary-invalid-placement');
                    element.title = 'This indicator needs to be moved into a category';
                } else {
                    alert(`Cannot move this ${elementType} to a pillar`);
                }
            } else {
                alert(`Pillar "${userInput}" not found. Please use a valid pillar name or code.`);
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
        if (confirm('Delete this item?')) el.remove();
    }

    editGoalposts(t) {
        const l = prompt('Lower Goalpost:', '0');
        const u = prompt('Upper Goalpost:', '100');
        const s = t.querySelector('.goal-slider');
        if (s) {
            s.min = l;
            s.max = u;
            s.value = Math.min(Math.max(s.value, l), u);
        }
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

    validate(z) {
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

    exportData() {
        return this.exportMetadataFormat();
    }


    exportMetadataFormat() {
        const metadataItems = [];
        
        // Get all pillars
        const pillars = {};
        const categories = {};
        const indicators = {};
        
        // Collect all items from the DOM
        this.container.querySelectorAll('.pillar-column').forEach(pillarCol => {
            const pillarName = pillarCol.querySelector('.pillar-name').textContent.trim();
            const pillarCode = pillarCol.querySelector('.pillar-code-input').value.trim();
            
            if (pillarCode) {
                pillars[pillarCode] = {
                    code: pillarCode,
                    name: pillarName,
                    categories: []
                };
                
                // Get categories in this pillar
                pillarCol.querySelectorAll('.category-box').forEach(catBox => {
                    const categoryName = catBox.querySelector('.customization-category-header-title').textContent.trim();
                    const categoryCode = catBox.querySelector('.category-code-input').value.trim();
                    
                    if (categoryCode) {
                        pillars[pillarCode].categories.push(categoryCode);
                        categories[categoryCode] = {
                            code: categoryCode,
                            name: categoryName,
                            pillarCode: pillarCode,
                            indicators: []
                        };
                        
                        // Get indicators in this category
                        catBox.querySelectorAll('.indicator-card').forEach((indCard, idx) => {
                            const indicatorName = indCard.querySelector('.indicator-name').textContent.trim();
                            const indicatorCode = indCard.querySelector('.indicator-code-input').value.trim();
                            
                            if (indicatorCode) {
                                categories[categoryCode].indicators.push(indicatorCode);
                                
                                // Get datasets
                                const datasetCodes = [];
                                indCard.querySelectorAll('.dataset-item').forEach(item => {
                                    const datasetCode = item.dataset.datasetCode;
                                    if (datasetCode) {
                                        datasetCodes.push(datasetCode);
                                    }
                                });
                                
                                // Get other indicator properties
                                const lowerGoalpost = parseFloat(indCard.querySelector('.lower-goalpost').value) || null;
                                const upperGoalpost = parseFloat(indCard.querySelector('.upper-goalpost').value) || null;
                                const inverted = indCard.querySelector('.inverted-checkbox').checked;
                                
                                indicators[indicatorCode] = {
                                    code: indicatorCode,
                                    name: indicatorName,
                                    categoryCode: categoryCode,
                                    pillarCode: pillarCode,
                                    datasetCodes: datasetCodes,
                                    lowerGoalpost: lowerGoalpost,
                                    upperGoalpost: upperGoalpost,
                                    inverted: inverted,
                                    itemOrder: idx
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
                ItemType: "SSPI",
                ItemCode: "SSPI",
                ItemName: "Custom SSPI",
                Children: pillarCodes,
                Description: "Custom SSPI metadata created through the customization interface"
            });
        }
        
        // Create pillar items
        Object.values(pillars).forEach(pillar => {
            metadataItems.push({
                ItemType: "Pillar",
                ItemCode: pillar.code,
                ItemName: pillar.name,
                Children: pillar.categories,
                Pillar: pillar.name,
                PillarCode: pillar.code
            });
        });
        
        // Create category items
        Object.values(categories).forEach(category => {
            metadataItems.push({
                ItemType: "Category",
                ItemCode: category.code,
                ItemName: category.name,
                Children: category.indicators,
                Category: category.name,
                CategoryCode: category.code,
                Pillar: pillars[category.pillarCode].name,
                PillarCode: category.pillarCode
            });
        });
        
        // Create indicator items
        Object.values(indicators).forEach(indicator => {
            metadataItems.push({
                ItemType: "Indicator",
                ItemCode: indicator.code,
                ItemName: indicator.name,
                Children: [],
                DatasetCodes: indicator.datasetCodes,
                Indicator: indicator.name,
                IndicatorCode: indicator.code,
                Category: categories[indicator.categoryCode].name,
                CategoryCode: indicator.categoryCode,
                Pillar: pillars[indicator.pillarCode].name,
                PillarCode: indicator.pillarCode,
                LowerGoalpost: indicator.lowerGoalpost,
                UpperGoalpost: indicator.upperGoalpost,
                Inverted: indicator.inverted,
                ItemOrder: indicator.itemOrder
            });
        });
        
        return metadataItems;
    }

    /**
     * Export data in format suitable for scoring pipeline
     * @returns {Object} Structure data with metadata for scoring
     */
    exportForScoring() {
        const metadata = this.exportData();
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
                code: code,
                weight: 1.0 // Default weight
            }));
            
            structure.push({
                Indicator: indicator.ItemName || indicator.Indicator || indicator.ItemCode,
                IndicatorCode: indicator.ItemCode,
                Category: category ? (category.ItemName || category.Category || category.ItemCode) : 'Unknown',
                CategoryCode: indicator.CategoryCode,
                Pillar: pillar ? (pillar.ItemName || pillar.Pillar || pillar.ItemCode) : 'Unknown', 
                PillarCode: indicator.PillarCode,
                LowerGoalpost: indicator.LowerGoalpost,
                UpperGoalpost: indicator.UpperGoalpost,
                Inverted: indicator.Inverted || false,
                ItemOrder: indicator.ItemOrder || 0,
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
     * Score the current structure and open visualization
     */
    async scoreAndVisualize() {
        try {
            // Validate current structure
            const validationErrors = this.validateHierarchy();
            if (validationErrors.length > 0) {
                const proceed = confirm(
                    `The current structure has validation issues:\n${validationErrors.join('\n')}\n\nDo you want to continue with scoring anyway?`
                );
                if (!proceed) {
                    return;
                }
            }

            // Show loading indicator
            this.showLoadingState('Preparing structure for scoring...');

            // Export current structure
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

            // Update loading message
            this.showLoadingState('Initiating scoring process...');

            let visualizationUrl;
            if (configId) {
                // Use the production visualization page with saved config
                visualizationUrl = `/customize/visualize/${configId}`;
            } else {
                // Fall back to test page with structure data
                visualizationUrl = `/customize/test-chart?structure=${encodeURIComponent(JSON.stringify(exportData.structure))}`;
                
                // Show message about saving
                this.showNotification(
                    'Using test mode - save your configuration for full features!', 
                    'warning', 
                    7000
                );
            }
            
            this.hideLoadingState();
            
            // Open in new tab/window
            const visualizationWindow = window.open(visualizationUrl, '_blank', 'width=1200,height=800');
            
            if (!visualizationWindow) {
                alert('Popup blocked. Please allow popups for this site and try again.');
            } else {
                // Show success message
                const notification = this.showNotification(
                    '🎉 Scoring visualization opened in new window!', 
                    'success', 
                    5000
                );
            }

        } catch (error) {
            this.hideLoadingState();
            console.error('Error in scoreAndVisualize:', error);
            alert(`Error preparing visualization: ${error.message}`);
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
            font-weight: bold;
            z-index: 10000;
            max-width: 300px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            animation: slideInRight 0.3s ease-out;
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

    // Hierarchy management methods
    updateHierarchyOnAdd(element, elementType) {
        this.flagUnsaved();
        console.log(`Added ${elementType}:`, element);
        
        // Validate hierarchy after addition
        const errors = this.validateHierarchy();
        if (errors.length > 0) {
            console.warn('Hierarchy validation errors after add:', errors);
        }
    }

    updateHierarchyOnRemove(element, elementType) {
        this.flagUnsaved();
        console.log(`Removed ${elementType}:`, element);
        
        // Validate hierarchy after removal
        const errors = this.validateHierarchy();
        if (errors.length > 0) {
            console.warn('Hierarchy validation errors after remove:', errors);
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
                warnings.push(`Pillar "${pillarName}" (${pillarCode}) has no categories`);
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
        // First, check if we have cached modifications
        if (this.hasCachedModifications()) {
            try {
                const loaded = await this.loadCachedState();
                if (loaded) {
                    this.showCacheRestoredIndicator();
                    return;
                }
            } catch (error) {
                console.warn('Failed to load cached modifications, falling back to default:', error);
            }
        }
        
        // Fall back to loading default metadata
        await this.loadDefaultMetadata();
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
                
                // Import the metadata efficiently
                await this.importDataAsync(response.metadata);
                
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

        // Mark any indicators that are outside categories
        this.markInvalidIndicatorPlacements();
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
                        
                        if (indicatorName) indicatorName.textContent = indicatorItem.ItemName || '';
                        if (indicatorCodeInput) indicatorCodeInput.value = indicatorItem.ItemCode || '';
                        if (lowerGoalpost) lowerGoalpost.value = indicatorItem.LowerGoalpost || 0;
                        if (upperGoalpost) upperGoalpost.value = indicatorItem.UpperGoalpost || 100;
                        if (invertedCheckbox) invertedCheckbox.checked = indicatorItem.Inverted || false;
                        
                        // Add datasets if present
                        const datasetCodes = indicatorItem.DatasetCodes || [];
                        if (datasetCodes.length > 0) {
                            const selectedDatasetsDiv = indEl.querySelector('.selected-datasets');
                            datasetCodes.forEach(datasetCode => {
                                this.addDatasetToIndicator(
                                    selectedDatasetsDiv, 
                                    datasetCode, 
                                    1.0  // Default weight
                                );
                            });
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
        
        data.forEach(item => {
            const { Pillar, Category, CategoryCode, PillarCode, ItemOrder } = item;
            
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
            Object.entries(grouping[p]).forEach(([catName, info]) => {
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
                    
                    // Set indicator name and code
                    indEl.querySelector('.indicator-name').textContent = item.Indicator || 'New Indicator';
                    const indicatorCodeInput = indEl.querySelector('.indicator-code-input');
                    if (indicatorCodeInput && item.IndicatorCode) {
                        indicatorCodeInput.value = item.IndicatorCode;
                    }
                    
                    // Set description
                    indEl.title = item.Description || '';
                    
                    // Set goalposts
                    const lowerGoalpostInput = indEl.querySelector('.lower-goalpost');
                    const upperGoalpostInput = indEl.querySelector('.upper-goalpost');
                    if (lowerGoalpostInput && item.LowerGoalpost != null) {
                        lowerGoalpostInput.value = item.LowerGoalpost;
                    }
                    if (upperGoalpostInput && item.UpperGoalpost != null) {
                        upperGoalpostInput.value = item.UpperGoalpost;
                    }
                    
                    // Set inverted flag
                    const invertedCheckbox = indEl.querySelector('.inverted-checkbox');
                    if (invertedCheckbox) {
                        invertedCheckbox.checked = item.Inverted || false;
                    }
                    
                    // Set scoring function
                    const scoringSelect = indEl.querySelector('.scoring-function-select');
                    if (scoringSelect && item.scoring_function && item.scoring_function.type) {
                        scoringSelect.value = item.scoring_function.type;
                    }
                    
                    // Set datasets if available
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

        // Mark any indicators that are outside categories
        this.markInvalidIndicatorPlacements();
    }

    async saveConfiguration() {
        try {
            const name = prompt('Enter a name for this configuration:');
            if (!name) return;

            const metadata = this.exportData();
            
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
                
                // Clear cache since the configuration is now saved
                this.clearCache();
                
                alert(`Configuration "${name}" saved successfully!`);
                this.loadConfigurationsList(); // Refresh the list
            } else {
                alert(`Error saving configuration: ${response.error}`);
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            alert('Error saving configuration. Please try again.');
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
            const response = await this.fetch(`/api/v1/customize/load/${configId}`);
            
            if (response.success && response.configuration) {
                // Clear cache before loading saved configuration
                this.clearCache();
                
                this.importData(response.configuration.metadata);
                this.clearUnsavedState();
                alert(`Configuration "${response.configuration.name}" loaded successfully!`);
            } else {
                alert(`Error loading configuration: ${response.error}`);
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
            alert('Error loading configuration. Please try again.');
        }
    }

    async deleteConfiguration(configId) {
        try {
            const response = await this.fetch(`/api/v1/customize/delete/${configId}`, {
                method: 'DELETE'
            });

            if (response.success) {
                alert('Configuration deleted successfully!');
                this.loadConfigurationsList(); // Refresh the list
            } else {
                alert(`Error deleting configuration: ${response.error}`);
            }
        } catch (error) {
            console.error('Error deleting configuration:', error);
            alert('Error deleting configuration. Please try again.');
        }
    }

    setupCodeValidation(input, type) {
        if (!input) return;
        
        const validationMessage = input.nextElementSibling;
        
        input.addEventListener('input', (e) => {
            let value = e.target.value.toUpperCase();
            e.target.value = value;
            
            const isValid = this.validateCode(value, type);
            const isUnique = this.isCodeUnique(value, type, input);
            
            if (!value) {
                this.showValidationMessage(validationMessage, '', '');
            } else if (!isValid) {
                this.showValidationMessage(validationMessage, 'Invalid format', 'error');
            } else if (!isUnique) {
                this.showValidationMessage(validationMessage, 'Code already used', 'error');
            } else {
                this.showValidationMessage(validationMessage, 'Valid', 'success');
            }
            
            this.flagUnsaved();
        });
        
        input.addEventListener('blur', () => {
            if (input.value && this.validateCode(input.value, type) && this.isCodeUnique(input.value, type, input)) {
                // Generate code from name if empty
                if (!input.value) {
                    const name = this.getNameForCodeInput(input, type);
                    if (name) {
                        const generatedCode = this.generateCodeFromName(name, type);
                        if (this.isCodeUnique(generatedCode, type, input)) {
                            input.value = generatedCode;
                            this.showValidationMessage(validationMessage, 'Generated', 'success');
                        }
                    }
                }
            }
        });
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

    showValidationMessage(element, message, type) {
        if (!element) return;
        
        element.textContent = message;
        element.className = 'code-validation-message';
        
        if (type === 'error') {
            element.classList.add('error');
        } else if (type === 'success') {
            element.classList.add('success');
        }
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
            if (currentDatasets.length >= 5) {
                alert('Maximum of 5 datasets allowed per indicator');
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
        
        // Create and configure enhanced dataset selector
        const selector = new DatasetSelector({
            maxSelections: 5,
            multiSelect: true,
            enableSearch: true,
            enableFilters: true,
            showOrganizations: true,
            showTypes: true,
            onSelectionChange: (selectedCodes) => {
                this.updateDatasetSelection(selectedDatasetsDiv, selectedCodes);
            }
        });
        
        // Show the enhanced selector
        await selector.show(currentSelections);
    }
    
    updateDatasetSelection(selectedDatasetsDiv, selectedCodes) {
        // Clear existing selections
        selectedDatasetsDiv.innerHTML = '';
        
        // Add new selections
        selectedCodes.forEach(datasetCode => {
            this.addDatasetToIndicator(selectedDatasetsDiv, datasetCode, 1.0);
        });
    }


    findSelectedDatasetsDiv(modal) {
        // This is a bit hacky but works for finding the selected datasets div
        // In a real implementation, we'd pass this more cleanly
        const indicators = document.querySelectorAll('.indicator-card');
        return indicators[indicators.length - 1]?.querySelector('.selected-datasets');
    }

    addDatasetToIndicator(selectedDatasetsDiv, datasetCode, weight = 1.0) {
        // Check for duplicates
        const existing = selectedDatasetsDiv.querySelector(`[data-dataset-code="${datasetCode}"]`);
        if (existing) {
            alert('Dataset already added');
            return;
        }

        const datasetItem = document.createElement('div');
        datasetItem.classList.add('dataset-item');
        datasetItem.dataset.datasetCode = datasetCode;
        datasetItem.dataset.weight = weight;
        
        datasetItem.innerHTML = `
            <span class="dataset-code">${datasetCode}</span>
            <div class="dataset-actions">
                <button class="dataset-menu-btn" type="button" title="Dataset options">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <circle cx="8" cy="2" r="1.5"/>
                        <circle cx="8" cy="8" r="1.5"/>
                        <circle cx="8" cy="14" r="1.5"/>
                    </svg>
                </button>
                <button class="remove-dataset" type="button" title="Remove dataset">×</button>
            </div>
        `;

        const menuBtn = datasetItem.querySelector('.dataset-menu-btn');
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showDatasetOptionsMenu(menuBtn, datasetCode);
        });

        datasetItem.querySelector('.remove-dataset').addEventListener('click', () => {
            datasetItem.remove();
            this.updateHierarchyOnRemove(datasetItem, 'dataset');
        });

        selectedDatasetsDiv.appendChild(datasetItem);
        this.updateHierarchyOnAdd(datasetItem, 'dataset');
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
            <div class="menu-item" data-action="weight">
                <span>Set Weight</span>
            </div>
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
            case 'weight':
                const currentWeight = document.querySelector(`[data-dataset-code="${datasetCode}"]`)?.dataset.weight || '1.0';
                const newWeight = prompt('Enter weight (0-10):', currentWeight);
                if (newWeight !== null && !isNaN(newWeight) && newWeight >= 0 && newWeight <= 10) {
                    document.querySelector(`[data-dataset-code="${datasetCode}"]`).dataset.weight = newWeight;
                    this.flagUnsaved();
                }
                break;
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
    
    cacheCurrentState() {
        try {
            const cacheData = {
                hasModifications: this.unsavedChanges,
                lastModified: Date.now(),
                metadata: this.exportData(),
                version: "1.0"
            };
            
            // Check cache size (rough estimate)
            const cacheSize = JSON.stringify(cacheData).length;
            if (cacheSize > 5 * 1024 * 1024) { // 5MB limit
                console.warn('Cache data is too large (>5MB), skipping cache');
                return;
            }
            
            window.observableStorage.setItem("sspi-custom-modifications", cacheData);
            console.log('SSPI modifications cached successfully');
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
            console.log('SSPI modifications cache cleared');
        } catch (error) {
            console.warn('Failed to clear SSPI modifications cache:', error);
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
        
        // Validate field types
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
        
        // Check if cache is not too old (7 days max)
        const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 days in milliseconds
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
            this.baselineMetadata = this.exportData();
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
            const currentMetadata = this.exportData();
            
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
        
        // Compare indicator-specific properties
        if (baselineItem.ItemType === 'Indicator') {
            if (!this.arraysEqual(baselineItem.DatasetCodes || [], currentItem.DatasetCodes || [])) {
                changes.datasets = {
                    from: baselineItem.DatasetCodes || [],
                    to: currentItem.DatasetCodes || []
                };
            }
            
            if (baselineItem.LowerGoalpost !== currentItem.LowerGoalpost) {
                changes.lowerGoalpost = { 
                    from: baselineItem.LowerGoalpost, 
                    to: currentItem.LowerGoalpost 
                };
            }
            
            if (baselineItem.UpperGoalpost !== currentItem.UpperGoalpost) {
                changes.upperGoalpost = { 
                    from: baselineItem.UpperGoalpost, 
                    to: currentItem.UpperGoalpost 
                };
            }
            
            if (baselineItem.Inverted !== currentItem.Inverted) {
                changes.inverted = { 
                    from: baselineItem.Inverted, 
                    to: currentItem.Inverted 
                };
            }
        }
        
        // Compare hierarchy relationships
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
