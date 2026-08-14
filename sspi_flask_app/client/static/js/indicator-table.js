class IndicatorTable {
    constructor() {
        this.container = document.querySelector('.indicator-table-container');
        if (!this.container) {
            console.warn('IndicatorTable: Container not found');
            return;
        }
        this.initializeEventListeners();
        this.initializeState();
        this.rigUnloadListener();
    }

    initializeEventListeners() {
        /* The whole header row toggles its section, at every level. Clicks on
         * the row data link fall through to the browser untouched.
         * NB: apostrophes inside // comments make the bundler swallow the line
         * that follows them, so keep block comments here. */
        const rowLevels = [
            ['.indicators-pillar-header', '.indicators-pillar-header-content > button'],
            ['.indicators-category-header', '.indicators-category-header-content > button'],
            ['.indicators-indicator-header', '.indicator-info > button'],
        ];
        rowLevels.forEach(([headerSelector, buttonSelector]) => {
            this.container.querySelectorAll(headerSelector).forEach((header) => {
                header.addEventListener('click', (event) => {
                    if (event.target.closest('a')) return;
                    const toggleBtn = header.querySelector(buttonSelector);
                    if (!toggleBtn) return;
                    event.stopPropagation();
                    this.handleToggle(toggleBtn);
                })
            })
        })
        // Add click listeners to all collapse toggle buttons
        this.container.addEventListener('click', (event) => {
            const toggleBtn = event.target.closest('.collapse-toggle-btn');
            if (toggleBtn) {
                event.preventDefault();
                event.stopPropagation();
                this.handleToggle(toggleBtn);
            }
        });
        // Add keyboard support for toggle buttons
        this.container.addEventListener('keydown', (event) => {
            const toggleBtn = event.target.closest('.collapse-toggle-btn');
            if (toggleBtn && (event.key === 'Enter' || event.key === ' ' || event.key === "Spacebar")) {
                event.preventDefault();
                this.handleToggle(toggleBtn);
            }
        });
    }

    initializeState() {
        // Set initial expanded states based on data-expanded attributes
        const collapsibleSections = this.container.querySelectorAll('[data-expanded]');
        const cachedStateObject = window.observableStorage.getItem('indicatorTableState');
        collapsibleSections.forEach(section => {
            const defaultState = section.dataset.expanded === 'true';
            const cachedValue = cachedStateObject?.[section.dataset.icode];
            const cachedState = cachedValue !== undefined ? cachedValue === 'true' : defaultState;
            this.updateSectionVisibility(section, cachedState);
            section.dataset.expanded = cachedState.toString();
            const toggleButton = this.findToggleButton(section)
            this.updateToggleIcon(toggleButton, cachedState);
        });
    }

    handleToggle(toggleBtn) {
        const section = this.findToggleableSection(toggleBtn);
        if (!section) return;
        const isCurrentlyExpanded = section.dataset.expanded === 'true';
        const newExpandedState = !isCurrentlyExpanded;
        // Update the data attribute
        section.dataset.expanded = newExpandedState.toString();
        // Update visual state
        this.updateSectionVisibility(section, newExpandedState);
        this.updateToggleIcon(toggleBtn, newExpandedState);
    }

    findToggleButton(toggleSection) {
        const parentSection = toggleSection.parentElement
        if (!parentSection) return null;
        if (parentSection.classList.contains('pillar-section')) {
            return parentSection.querySelector('.indicators-pillar-header-content > button')
        } else if (parentSection.classList.contains('category-section')) {
            return parentSection.querySelector('.indicators-category-header-content > button')
        } else if (parentSection.classList.contains('indicator-item')) {
            return parentSection.querySelector('.indicator-info > button')
        }
        return null;
    }

    findToggleableSection(toggleBtn) {
        // Find the appropriate collapsible section for this toggle button
        const pillarSection = toggleBtn.closest('.pillar-section');
        const categorySection = toggleBtn.closest('.category-section');
        const indicatorItem = toggleBtn.closest('.indicator-item');
        if (indicatorItem && toggleBtn.closest('.indicators-indicator-header')) {
            return indicatorItem.querySelector('.indicator-details');
        } else if (categorySection && toggleBtn.closest('.indicators-category-header')) {
            return categorySection.querySelector('.indicator-table-category-content');
        } else if (pillarSection && toggleBtn.closest('.indicators-pillar-header')) {
            return pillarSection.querySelector('.pillar-content');
        }

        return null;
    }

    updateSectionVisibility(section, isExpanded) {
        if (isExpanded) {
            section.style.display = '';
            section.style.maxHeight = '';
            section.style.opacity = '';
        } else {
            section.style.display = 'none';
        }
    }

    updateToggleIcon(toggleBtn, isExpanded) {
        if (!toggleBtn) return;
        const icon = toggleBtn.querySelector('.collapse-icon');
        if (icon) {
            if (isExpanded) {
                icon.style.transform = 'rotate(0deg)';
            } else {
                icon.style.transform = 'rotate(-90deg)';
            }
        }
    }

    // Utility methods for programmatic control
    expandAll() {
        const allSections = this.container.querySelectorAll('[data-expanded]');
        allSections.forEach(section => {
            section.dataset.expanded = 'true';
            this.updateSectionVisibility(section, true);
            this.updateToggleIcon(this.findToggleButton(section), true);
        });
    }

    collapseAll() {
        const allSections = this.container.querySelectorAll('[data-expanded]');
        allSections.forEach(section => {
            section.dataset.expanded = 'false';
            this.updateSectionVisibility(section, false);
            this.updateToggleIcon(this.findToggleButton(section), false);
        });
    }

    resetView() {
        const collapsibleSections = this.container.querySelectorAll('[data-expanded]');
        let stateLookup = {};
        collapsibleSections.forEach((section) => {
            if (section.dataset.icode.length === 6) { // indicators hidden, others expanded
                this.updateSectionVisibility(section, false);
                section.dataset.expanded = 'false';
                const toggleButton = this.findToggleButton(section)
                this.updateToggleIcon(toggleButton, false);
                stateLookup[section.dataset.icode] = false;
            } else {
                this.updateSectionVisibility(section, true);
                section.dataset.expanded = 'true';
                const toggleButton = this.findToggleButton(section)
                stateLookup[section.dataset.icode] = true;
                this.updateToggleIcon(toggleButton, true);
            }
        })
        window.observableStorage.setItem('indicatorTableState', stateLookup)
    }

    rigUnloadListener() {
        window.addEventListener('beforeunload', () => {
            const collapsibleSections = this.container.querySelectorAll('[data-expanded]');
            let stateLookup = {};
            collapsibleSections.forEach((section) => {
                stateLookup[section.dataset.icode] = section.dataset.expanded;
            })
            window.observableStorage.setItem('indicatorTableState', stateLookup)
        })
    }
}
