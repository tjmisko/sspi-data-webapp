/**
 * IndicatorTable - Interactive functionality for the SSPI Indicators Overview page
 * Handles collapsible sections for pillars, categories, and indicator details
 */
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
            if (toggleBtn && (event.key === 'Enter' || event.key === ' ')) {
                event.preventDefault();
                this.handleToggle(toggleBtn);
            }
        });
    }
    
    initializeState() {
        // Set initial expanded states based on data-expanded attributes
        const collapsibleSections = this.container.querySelectorAll('[data-expanded]');
        const cachedStateObject = window.observableStorage.getItem('indicatorTableState')
        collapsibleSections.forEach(section => {
            const defaultState = section.dataset.expanded === 'true';
            const cachedState = cachedStateObject?.[section.dataset.icode] === 'true' ?? defaultState
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
        if (parentSection.classList.contains('pillar-section')) {
            return parentSection.querySelector('.indicators-pillar-header-content > button')
        } else if (parentSection.classList.contains('category-section')) {
            return parentSection.querySelector('.indicators-category-header-content > button')
        } else if (parentSection.classList.contains('indicator-item')) {
            return parentSection.querySelector('.indicator-info > button')
        }
    }
    
    findToggleableSection(toggleBtn) {
        // Find the appropriate collapsible section based on the toggle button's context
        const pillarSection = toggleBtn.closest('.pillar-section');
        const categorySection = toggleBtn.closest('.category-section');
        const indicatorItem = toggleBtn.closest('.indicator-item');
        
        if (indicatorItem && toggleBtn.closest('.indicators-indicator-header')) {
            // This is an indicator details toggle
            return indicatorItem.querySelector('.indicator-details');
        } else if (categorySection && toggleBtn.closest('.indicators-category-header')) {
            // This is a category content toggle
            return categorySection.querySelector('.indicator-table-category-content');
        } else if (pillarSection && toggleBtn.closest('.indicators-pillar-header')) {
            // This is a pillar content toggle
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
            
            // Update corresponding toggle button
            const toggleBtn = this.findToggleButtonForSection(section);
            if (toggleBtn) {
                this.updateToggleIcon(toggleBtn, true);
            }
        });
    }
    
    collapseAll() {
        const allSections = this.container.querySelectorAll('[data-expanded]');
        allSections.forEach(section => {
            section.dataset.expanded = 'false';
            this.updateSectionVisibility(section, false);
            
            // Update corresponding toggle button
            const toggleBtn = this.findToggleButtonForSection(section);
            if (toggleBtn) {
                this.updateToggleIcon(toggleBtn, false);
            }
        });
    }
    
    expandPillar(pillarCode) {
        const pillarSection = this.container.querySelector(`[data-pillar-code="${pillarCode}"]`);
        if (pillarSection) {
            const pillarContent = pillarSection.querySelector('.pillar-content');
            if (pillarContent) {
                pillarContent.dataset.expanded = 'true';
                this.updateSectionVisibility(pillarContent, true);
                
                const toggleBtn = pillarSection.querySelector('.indicator-table-pilllar-header .collapse-toggle-btn');
                if (toggleBtn) {
                    this.updateToggleIcon(toggleBtn, true);
                }
            }
        }
    }
    
    collapsePillar(pillarCode) {
        const pillarSection = this.container.querySelector(`[data-pillar-code="${pillarCode}"]`);
        if (pillarSection) {
            const pillarContent = pillarSection.querySelector('.pillar-content');
            if (pillarContent) {
                pillarContent.dataset.expanded = 'false';
                this.updateSectionVisibility(pillarContent, false);
                
                const toggleBtn = pillarSection.querySelector('.indicator-table-pilllar-header .collapse-toggle-btn');
                if (toggleBtn) {
                    this.updateToggleIcon(toggleBtn, false);
                }
            }
        }
    }
    
    findToggleButtonForSection(section) {
        const parent = section.parentElement;
        if (!parent) return null;
        
        if (section.classList.contains('pillar-content')) {
            return parent.querySelector('.indicator-table-pillar-header .collapse-toggle-btn');
        } else if (section.classList.contains('indicator-table-category-content')) {
            return parent.querySelector('.indicators-category-header .collapse-toggle-btn');
        } else if (section.classList.contains('indicator-details')) {
            return parent.querySelector('.indicator-header .collapse-toggle-btn');
        }
        
        return null;
    }

    resetView() {
        const collapsibleSections = this.container.querySelectorAll('[data-expanded]');
        collapsibleSections.forEach((section) => {
            if (section.dataset.icode.length === 6) { // indicators hidden, others expanded
                this.updateSectionVisibility(section, false);
                section.dataset.expanded = 'false';
                const toggleButton = this.findToggleButton(section)
                this.updateToggleIcon(toggleButton, false);
            } else {
                this.updateSectionVisibility(section, true);
                section.dataset.expanded = 'true';
                const toggleButton = this.findToggleButton(section)
                this.updateToggleIcon(toggleButton, true);
            }
        })
        window.observableStorage.setItem('indicatorTableState', {})
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
