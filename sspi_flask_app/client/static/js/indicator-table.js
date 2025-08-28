/**
 * IndicatorTable - Interactive functionality for the SSPI Indicators Overview page
 * Handles collapsible sections for pillars, categories, and indicator details
 */
class IndicatorTable {
    constructor() {
        this.container = document.querySelector('.indicators-container');
        if (!this.container) {
            console.warn('IndicatorTable: Container not found');
            return;
        }
        
        this.initializeEventListeners();
        this.initializeState();
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
        collapsibleSections.forEach(section => {
            const isExpanded = section.dataset.expanded === 'true';
            this.updateSectionVisibility(section, isExpanded);
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
            return categorySection.querySelector('.category-content');
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
            return parent.querySelector('.indicator-table-pilllar-header .collapse-toggle-btn');
        } else if (section.classList.contains('category-content')) {
            return parent.querySelector('.indicator-table-category-header .collapse-toggle-btn');
        } else if (section.classList.contains('indicator-details')) {
            return parent.querySelector('.indicator-header .collapse-toggle-btn');
        }
        
        return null;
    }
}

// Make IndicatorTable available globally for console debugging
window.IndicatorTable = IndicatorTable;
