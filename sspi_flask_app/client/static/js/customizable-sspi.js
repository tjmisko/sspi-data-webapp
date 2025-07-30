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
        this.saveButton.addEventListener('click', () => {
            console.log('Save clicked');
            this.unsavedChanges = false;
            this.saveButton.classList.remove('unsaved-changes');
        });

        toolbar.append(importBtn, exportBtn, this.saveButton);
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
            header.contentEditable = true;
            header.spellcheck = false;
            header.tabIndex = 0;
            header.textContent = name;
            col.appendChild(header);

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
                const list = e.target.previousElementSibling;
                const ind = this.createIndicatorElement();
                list.appendChild(ind);
                this.validate(list);
                this.flagUnsaved();
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
<div class="category-header-wrapper" role="treeitem">
    <h4 class="category-header" contenteditable="true">New Category</h4>
</div>
<div class="indicators-container drop-zone" data-accept="indicator" role="group"></div>
<button class="add-indicator" aria-label="Add Indicator">+ Add Indicator</button>
`;
        return cat;
    }

    createIndicatorElement() {
        const ind = document.createElement('div');
        ind.classList.add('indicator-card','draggable-item');
        ind.setAttribute('draggable','true');
        ind.setAttribute('role','treeitem');
        ind.dataset.type='indicator';
        ind.innerHTML = `
<div class="indicator-label">
    <h5 class="indicator-name">Indicator Name </h5>
    <span class="indicator-code">IDCODE</span>
    <button class="indicator-options" aria-label="Indicator Options">...</button>
</div>
<input type="range" class="goal-slider" min="0" max="100" value="50" aria-label="Goal Slider">
<input type="range" class="goal-slider" min="0" max="100" value="50" aria-label="Goal Slider">
`;
        return ind;
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
            const cat = ind.closest('.category-box').querySelector('.category-header').textContent;
            const p = ind.closest('.pillar-column').dataset.pillar;
            const slider = ind.querySelector('.goal-slider');
            res.push({
                Category: cat,
                CategoryCode: '',
                Children: [],
                Description: ind.title || '',
                DocumentType: '',
                Indicator: ind.querySelector('.indicator-label').textContent,
                IndicatorCode: ind.dataset.indicatorCode || '',
                Inverted: ind.dataset.inverted === 'true',
                ItemCode: '',
                ItemName: '',
                ItemOrder: idx + 1,
                ItemType: '',
                LowerGoalpost: parseFloat(slider.min),
                Pillar: p,
                PillarCode: '',
                Policy: '',
                UpperGoalpost: parseFloat(slider.max)
            });
        });
        return res;
    }

    importData(data) {
        console.log('Importing data:', data);
        this.container.querySelectorAll('.category-box, .indicator-card').forEach(e => e.remove());
        const grouping = {};
        data.forEach(item => {
            const { Pillar, Category, CategoryCode, ItemOrder } = item;
            grouping[Pillar] = grouping[Pillar] || {};
            grouping[Pillar][Category] = grouping[Pillar][Category] || { CategoryCode, items: [] };
            grouping[Pillar][Category].items.push(item);
        });
        this.pillars.forEach(p => {
            const col = Array.from(this.container.querySelectorAll('.pillar-column'))
                .find(c => c.dataset.pillar === p);
            if (!col || !grouping[p]) return;
            const zone = col.querySelector('.categories-container');
            Object.entries(grouping[p]).forEach(([catName, info]) => {
                const catEl = this.createCategoryElement();
                catEl.querySelector('.category-header').textContent = catName;
                catEl.dataset.categoryCode = info.CategoryCode;
                zone.appendChild(catEl);
                info.items.sort((a, b) => a.ItemOrder - b.ItemOrder).forEach(item => {
                    const indEl = this.createIndicatorElement();
                    indEl.querySelector('.indicator-label').textContent = item.Indicator;
                    indEl.dataset.indicatorCode = item.IndicatorCode;
                    indEl.dataset.inverted = item.Inverted;
                    indEl.title = item.Description || '';
                    const slider = indEl.querySelector('.goal-slider');
                    if (item.LowerGoalpost != null) slider.min = item.LowerGoalpost;
                    if (item.UpperGoalpost != null) slider.max = item.UpperGoalpost;
                    if (item.LowerGoalpost != null) slider.value = item.LowerGoalpost;
                    catEl.querySelector('.indicators-container').appendChild(indEl);
                });
                this.validate(catEl.querySelector('.indicators-container'));
            });
        });
    }
}

// Usage example:
// const root = document.getElementById('sspi-root');
// new CustomizableSSPIStructure(root);
