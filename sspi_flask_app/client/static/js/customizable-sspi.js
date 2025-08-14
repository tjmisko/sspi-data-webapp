// customizable-sspi.js
// SSPI Tree UI implementing full specification (three-column layout)

class CustomizableSSPIStructure {
    constructor(parentElement, { pillars = ['Sustainability', 'Market Structure', 'Public Goods'] } = {}) {
        this.parentElement = parentElement;
        this.pillars = pillars;
        this.unsavedChanges = false;
        this.draggedEl = null;
        this.origin = null;
        this.dropped = false;
        this.injectStyles();
        this.initToolbar();
        this.initRoot();
        this.addEventListeners();
        this.loadConfigurationsList();
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
`;
        document.head.appendChild(style);
    }

    initToolbar() {
        const toolbar = document.createElement('div');
        toolbar.classList.add('sspi-toolbar');

        const importBtn = document.createElement('button');
        importBtn.textContent = 'Default SSPI';
        importBtn.addEventListener('click', async () => {
            try {
                const data = await this.fetch('/api/v1/metadata/indicator_details');
                this.importData(data);
                this.flagUnsaved();
            } catch (err) {
                console.error(err);
            }
        });

        const exportBtn = document.createElement('button');
        exportBtn.textContent = 'Export';
        exportBtn.addEventListener('click', () => {
            const json = JSON.stringify(this.exportData(), null, 2);
            console.log(json);
            alert('Exported JSON copied to console.');
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

        toolbar.append(importBtn, exportBtn, this.saveButton, expandAllBtn, collapseAllBtn);
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
        this.pillars.forEach(name => {
            const col = document.createElement('div');
            col.classList.add('pillar-column');
            col.dataset.pillar = name;
            col.setAttribute('aria-label', name + ' pillar');

            const header = document.createElement('div');
            header.classList.add('pillar-header');
            header.setAttribute('role', 'treeitem');
            header.innerHTML = `
                <div class="pillar-header-content">
                    <div class="pillar-name" contenteditable="true" spellcheck="false" tabindex="0">${name}</div>
                    <div class="pillar-code-section">
                        <label class="code-label">Code:</label>
                        <input type="text" class="pillar-code-input" maxlength="3" placeholder="SUS" 
                               pattern="[A-Z]{2,3}" title="2-3 uppercase letters required">
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
        this.container.querySelectorAll('.pillar-header').forEach(h =>
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
                this.flagUnsaved();
            }
            if (e.target.classList.contains('add-indicator')) {
                // Find the indicators container (either directly previous sibling or within category-content)
                let list = e.target.previousElementSibling;
                if (!list || !list.classList.contains('indicators-container')) {
                    list = e.target.parentElement.querySelector('.indicators-container');
                }
                if (list) {
                    const ind = this.createIndicatorElement();
                    list.appendChild(ind);
                    this.validate(list);
                    this.flagUnsaved();
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
    }

    flagUnsaved() {
        this.saveButton.classList.add('unsaved-changes');
        this.unsavedChanges = true;
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
<details class="category-details" open>
    <summary class="category-summary" role="treeitem">
        <div class="category-header-content">
            <div class="category-collapse-icon">▼</div>
            <h4 class="category-header" contenteditable="true">New Category</h4>
            <div class="category-code-section">
                <label class="code-label">Code:</label>
                <input type="text" class="category-code-input" maxlength="3" placeholder="CAT" 
                       pattern="[A-Z]{3}" title="Exactly 3 uppercase letters required">
                <span class="code-validation-message"></span>
            </div>
        </div>
    </summary>
    <div class="category-content">
        <div class="indicators-container drop-zone" data-accept="indicator" role="group"></div>
        <button class="add-indicator" aria-label="Add Indicator">+ Add Indicator</button>
    </div>
</details>
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
<details class="indicator-details">
    <summary class="indicator-summary">
        <div class="indicator-header-content">
            <div class="indicator-collapse-icon">▼</div>
            <h5 class="indicator-name" contenteditable="true">New Indicator</h5>
            <div class="indicator-code-section">
                <label class="code-label">Code:</label>
                <input type="text" class="indicator-code-input" maxlength="6" placeholder="INDIC1" 
                       pattern="[A-Z0-9]{6}" title="Exactly 6 uppercase letters/numbers required">
                <span class="code-validation-message"></span>
            </div>
        </div>
    </summary>
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
</details>
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
        const allDetails = this.container.querySelectorAll('details');
        allDetails.forEach(details => {
            details.open = true;
        });
    }

    collapseAll() {
        const allDetails = this.container.querySelectorAll('details');
        allDetails.forEach(details => {
            details.open = false;
        });
    }

    flagUnsaved() {
        this.unsavedChanges = true;
        this.saveButton.classList.add('unsaved-changes');
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
        const p = prompt(`Enter pillar (${this.pillars.join(', ')}):`);
        const col = Array.from(this.container.querySelectorAll('.pillar-column'))
            .find(c => c.dataset.pillar === p);
        if (col) {
            const z = col.querySelector('.categories-container');
            if (z.dataset.accept === el.dataset.type) z.appendChild(el);
        }
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
        const res = [];
        this.container.querySelectorAll('.indicator-card').forEach((ind, idx) => {
            const catBox = ind.closest('.category-box');
            const pillarCol = ind.closest('.pillar-column');
            
            // Get names
            const categoryName = catBox.querySelector('.category-header').textContent.trim();
            const pillarName = pillarCol.querySelector('.pillar-name').textContent.trim();
            const indicatorName = ind.querySelector('.indicator-name').textContent.trim();
            
            // Get codes
            const categoryCode = catBox.querySelector('.category-code-input').value || '';
            const pillarCode = pillarCol.querySelector('.pillar-code-input').value || '';
            const indicatorCode = ind.querySelector('.indicator-code-input').value || '';
            
            // Get datasets
            const datasets = [];
            ind.querySelectorAll('.dataset-item').forEach(item => {
                const datasetCode = item.dataset.datasetCode;
                const weight = parseFloat(item.querySelector('.weight-input').value) || 1.0;
                datasets.push({ dataset_code: datasetCode, weight: weight });
            });
            
            // Get scoring function
            const scoringFunction = ind.querySelector('.scoring-function-select').value;
            
            // Get goalposts
            const lowerGoalpost = parseFloat(ind.querySelector('.lower-goalpost').value) || 0;
            const upperGoalpost = parseFloat(ind.querySelector('.upper-goalpost').value) || 100;
            
            // Get inverted flag
            const inverted = ind.querySelector('.inverted-checkbox').checked;
            
            res.push({
                Category: categoryName,
                CategoryCode: categoryCode,
                Children: [],
                Description: ind.title || '',
                DocumentType: '',
                Indicator: indicatorName,
                IndicatorCode: indicatorCode,
                Inverted: inverted,
                ItemCode: indicatorCode,
                ItemName: indicatorName,
                ItemOrder: idx + 1,
                ItemType: 'Indicator',
                LowerGoalpost: lowerGoalpost,
                Pillar: pillarName,
                PillarCode: pillarCode,
                Policy: '',
                UpperGoalpost: upperGoalpost,
                // New fields for custom indicators
                datasets: datasets,
                scoring_function: {
                    type: scoringFunction,
                    parameters: {}
                }
            });
        });
        return res;
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
                catEl.querySelector('.category-header').textContent = catName;
                
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
    }

    async saveConfiguration() {
        try {
            const name = prompt('Enter a name for this configuration:');
            if (!name) return;

            const structure = this.exportData();
            
            const response = await this.fetch('/api/v1/customize/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    structure: structure
                })
            });

            if (response.success) {
                this.unsavedChanges = false;
                this.saveButton.classList.remove('unsaved-changes');
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
                this.importData(response.configuration.structure);
                this.unsavedChanges = false;
                this.saveButton.classList.remove('unsaved-changes');
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
        const container = input.closest(type === 'pillar' ? '.pillar-header' : 
                                      type === 'category' ? '.category-box' : 
                                      '.indicator-card');
        
        if (type === 'pillar') {
            return container.querySelector('.pillar-name').textContent.trim();
        } else if (type === 'category') {
            return container.querySelector('.category-header').textContent.trim();
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
        // Create modal overlay
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        `;

        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: white;
            padding: 2rem;
            border-radius: 8px;
            max-width: 600px;
            width: 90%;
            max-height: 80%;
            overflow-y: auto;
        `;

        modalContent.innerHTML = `
            <h3>Select Dataset</h3>
            <div style="margin-bottom: 1rem;">
                <input type="text" id="dataset-search" placeholder="Search datasets..." 
                       style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
            </div>
            <div id="dataset-list" style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px;">
                <div style="padding: 2rem; text-align: center; color: #666;">Loading datasets...</div>
            </div>
            <div style="margin-top: 1rem; text-align: right;">
                <button id="modal-cancel" style="margin-right: 0.5rem; padding: 0.5rem 1rem; border: 1px solid #ccc; background: white; border-radius: 4px; cursor: pointer;">Cancel</button>
            </div>
        `;

        modal.appendChild(modalContent);
        document.body.appendChild(modal);

        // Event listeners
        modal.querySelector('#modal-cancel').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });

        // Load and display datasets
        this.loadDatasetsIntoModal(modal, selectedDatasetsDiv);
    }

    async loadDatasetsIntoModal(modal, selectedDatasetsDiv) {
        try {
            const response = await this.fetch('/api/v1/customize/datasets?limit=200');
            const datasets = response.datasets || [];

            const datasetList = modal.querySelector('#dataset-list');
            const searchInput = modal.querySelector('#dataset-search');

            const renderDatasets = (datasetsToShow) => {
                if (datasetsToShow.length === 0) {
                    datasetList.innerHTML = '<div style="padding: 2rem; text-align: center; color: #666;">No datasets found</div>';
                    return;
                }

                datasetList.innerHTML = datasetsToShow.map(dataset => `
                    <div class="dataset-option" data-dataset-code="${dataset.dataset_code}" 
                         style="padding: 0.75rem; border-bottom: 1px solid #eee; cursor: pointer; hover:background: #f5f5f5;">
                        <div style="font-weight: bold; color: #1565c0; font-family: monospace;">${dataset.dataset_code}</div>
                        <div style="font-size: 0.9rem; margin: 0.25rem 0;">${dataset.dataset_name}</div>
                        <div style="font-size: 0.8rem; color: #666;">${dataset.description}</div>
                        <div style="font-size: 0.8rem; color: #999; margin-top: 0.25rem;">Organization: ${dataset.organization}</div>
                    </div>
                `).join('');

                // Add click handlers
                datasetList.querySelectorAll('.dataset-option').forEach(option => {
                    option.addEventListener('click', () => {
                        const datasetCode = option.dataset.datasetCode;
                        this.addDatasetToIndicator(selectedDatasetsDiv, datasetCode);
                        document.body.removeChild(modal);
                    });

                    option.addEventListener('mouseenter', () => {
                        option.style.background = '#f5f5f5';
                    });

                    option.addEventListener('mouseleave', () => {
                        option.style.background = '';
                    });
                });
            };

            // Initial render
            renderDatasets(datasets);

            // Search functionality
            searchInput.addEventListener('input', (e) => {
                const searchTerm = e.target.value.toLowerCase();
                const filtered = datasets.filter(dataset => 
                    dataset.dataset_code.toLowerCase().includes(searchTerm) ||
                    dataset.dataset_name.toLowerCase().includes(searchTerm) ||
                    dataset.description.toLowerCase().includes(searchTerm)
                );
                renderDatasets(filtered);
            });

        } catch (error) {
            console.error('Error loading datasets:', error);
            const datasetList = modal.querySelector('#dataset-list');
            datasetList.innerHTML = '<div style="padding: 2rem; text-align: center; color: #d32f2f;">Error loading datasets</div>';
        }
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
        
        datasetItem.innerHTML = `
            <span class="dataset-code">${datasetCode}</span>
            <div class="dataset-weight">
                <label>Weight:</label>
                <input type="number" class="weight-input" value="${weight}" min="0" max="10" step="0.1">
            </div>
            <button class="remove-dataset" type="button">×</button>
        `;

        datasetItem.querySelector('.remove-dataset').addEventListener('click', () => {
            datasetItem.remove();
            this.flagUnsaved();
        });

        datasetItem.querySelector('.weight-input').addEventListener('change', () => {
            this.flagUnsaved();
        });

        selectedDatasetsDiv.appendChild(datasetItem);
        this.flagUnsaved();
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
