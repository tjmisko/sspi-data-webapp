class IndicatorSelector {
    constructor(options = {}) {
        this.options = {
            maxSelections: 1,
            multiSelect: false,
            showCategories: true,
            showPillars: true,
            enableFilters: true,
            enableSearch: true,
            onSelectionChange: null,
            apiEndpoint: '/api/v1/customize/indicators',
            ...options
        }
        
        this.indicators = []
        this.filteredIndicators = []
        this.selectedIndicator = null
        this.currentFilters = {
            search: '',
            category: '',
            pillar: ''
        }
        
        this.modal = null
    }
    
    async initialize() {
        await this.loadIndicators()
        this.applyFilters()
    }
    
    async loadIndicators() {
        try {
            const response = await fetch(`${this.options.apiEndpoint}?limit=300`)
            const data = await response.json()
            this.indicators = data.indicators || []
        } catch (error) {
            console.error('Error loading indicators:', error)
            this.indicators = []
        }
    }
    
    async show(currentSelection = null) {
        try {
            if (!this.indicators.length) {
                await this.initialize()
            }
            
            this.selectedIndicator = currentSelection
            this.createModal()
            
            if (!this.modal) {
                console.error('Failed to create modal')
                return
            }
            
            this.renderModal()
            this.bindEvents()
            document.body.appendChild(this.modal)
        } catch (error) {
            console.error('Error showing indicator selector:', error)
        }
    }
    
    createModal() {
        this.modal = document.createElement('div')
        this.modal.className = 'dataset-modal-overlay'
        
        const modalContent = document.createElement('div')
        modalContent.className = 'dataset-modal-content enhanced'
        
        modalContent.innerHTML = 
            '<div class="dataset-modal-header">' +
            '<h3 class="dataset-modal-title">Select Existing Indicator</h3>' +
            '<div class="dataset-selection-counter">' +
            '<span class="selected-count">' + (this.selectedIndicator ? 1 : 0) + '</span> of 1 selected' +
            '</div>' +
            '</div>' +
            (this.options.enableSearch ? this.createSearchHTML() : '') +
            (this.options.enableFilters ? this.createFiltersHTML() : '') +
            '<div class="dataset-list-container">' +
            '<div id="indicator-list" class="dataset-list enhanced">' +
            '<div class="dataset-loading-message">Loading indicators...</div>' +
            '</div>' +
            '</div>' +
            '<div class="dataset-modal-actions">' +
            '<button id="modal-cancel" class="dataset-modal-cancel">Cancel</button>' +
            '<button id="modal-confirm" class="dataset-modal-confirm" ' + 
            (this.selectedIndicator ? '' : 'disabled') + '>Add Indicator</button>' +
            '</div>'
        
        this.modal.appendChild(modalContent)
    }
    
    createSearchHTML() {
        return '<div class="dataset-search-container">' +
               '<input type="text" id="indicator-search" class="dataset-search-input" ' +
               'placeholder="Search indicators by code, name, or description...">' +
               '<div class="search-results-count"></div>' +
               '</div>';
    }
    
    createFiltersHTML() {
        const categories = [...new Set(this.indicators.map(i => i.category_name).filter(Boolean))].sort()
        const pillars = [...new Set(this.indicators.map(i => i.pillar_name).filter(Boolean))].sort()
        
        const catOptions = categories.map(cat => '<option value="' + cat + '">' + cat + '</option>').join('')
        const pillarOptions = pillars.map(pillar => '<option value="' + pillar + '">' + pillar + '</option>').join('')
        
        return '<div class="dataset-filters-container">' +
               '<div class="filter-group">' +
               '<label for="pillar-filter">Pillar:</label>' +
               '<select id="pillar-filter" class="filter-select">' +
               '<option value="">All Pillars</option>' +
               pillarOptions +
               '</select>' +
               '</div>' +
               '<div class="filter-group">' +
               '<label for="category-filter">Category:</label>' +
               '<select id="category-filter" class="filter-select">' +
               '<option value="">All Categories</option>' +
               catOptions +
               '</select>' +
               '</div>' +
               '<button id="clear-filters" class="clear-filters-btn">Clear Filters</button>' +
               '</div>';
    }
    
    renderModal() {
        this.applyFilters()
        this.renderIndicatorList()
        this.updateSelectionCounter()
    }
    
    applyFilters() {
        this.filteredIndicators = this.indicators.filter(indicator => {
            const matchesSearch = !this.currentFilters.search || 
                indicator.indicator_code.toLowerCase().includes(this.currentFilters.search.toLowerCase()) ||
                indicator.indicator_name.toLowerCase().includes(this.currentFilters.search.toLowerCase()) ||
                (indicator.description && indicator.description.toLowerCase().includes(this.currentFilters.search.toLowerCase()))
            
            const matchesCategory = !this.currentFilters.category || 
                indicator.category_name === this.currentFilters.category
            
            const matchesPillar = !this.currentFilters.pillar || 
                indicator.pillar_name === this.currentFilters.pillar
            
            return matchesSearch && matchesCategory && matchesPillar
        })
        
        this.updateResultsCount()
    }
    
    renderIndicatorList() {
        if (!this.modal) {
            console.error('Modal not found in renderIndicatorList')
            return
        }
        
        const indicatorList = this.modal.querySelector('#indicator-list')
        if (!indicatorList) {
            console.error('Indicator list element not found')
            return
        }
        
        if (this.filteredIndicators.length === 0) {
            indicatorList.innerHTML = '<div class="dataset-no-results">No indicators found matching your criteria.</div>'
            return
        }
        
        const htmlParts = []
        
        this.filteredIndicators.forEach(indicator => {
            const isSelected = this.selectedIndicator === indicator.indicator_code
            
            let cssClasses = 'dataset-option enhanced'
            if (isSelected) cssClasses += ' selected'
            
            let badges = ''
            if (this.options.showPillars && indicator.pillar_name) {
                badges += '<span class="dataset-organization-badge ' + indicator.pillar_code.toLowerCase() + '">' + indicator.pillar_name + '</span>'
            }
            if (this.options.showCategories && indicator.category_name) {
                badges += '<span class="dataset-category-badge ' + indicator.category_code.toLowerCase() + '">' + indicator.category_name + '</span>'
            }
            
            const description = indicator.description || ''
            
            htmlParts.push(
                '<div class="' + cssClasses + ' compact" data-indicator-code="' + indicator.indicator_code + '">' +
                '<div class="dataset-compact-header">' +
                '<div class="dataset-compact-code">' + indicator.indicator_code + '</div>' +
                '<div class="dataset-compact-badges">' + badges + '</div>' +
                '</div>' +
                '<div class="dataset-compact-name">' + indicator.indicator_name + '</div>' +
                '<div class="dataset-compact-description">' + description + '</div>' +
                '</div>'
            )
        })
        
        indicatorList.innerHTML = htmlParts.join('')
        this.bindIndicatorEvents()
    }
    
    bindEvents() {
        if (!this.modal) {
            console.error('Modal not found in bindEvents')
            return
        }
        
        // Search functionality
        if (this.options.enableSearch) {
            const searchInput = this.modal.querySelector('#indicator-search')
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    this.currentFilters.search = e.target.value
                    this.applyFilters()
                    this.renderIndicatorList()
                })
            }
        }
        
        // Filter functionality
        if (this.options.enableFilters) {
            const pillarFilter = this.modal.querySelector('#pillar-filter')
            const categoryFilter = this.modal.querySelector('#category-filter')
            const clearButton = this.modal.querySelector('#clear-filters')
            
            if (pillarFilter) {
                pillarFilter.addEventListener('change', (e) => {
                    this.currentFilters.pillar = e.target.value
                    this.applyFilters()
                    this.renderIndicatorList()
                })
            }
            
            if (categoryFilter) {
                categoryFilter.addEventListener('change', (e) => {
                    this.currentFilters.category = e.target.value
                    this.applyFilters()
                    this.renderIndicatorList()
                })
            }
            
            if (clearButton) {
                clearButton.addEventListener('click', () => {
                    this.clearFilters()
                })
            }
        }
        
        // Modal action buttons
        const cancelButton = this.modal.querySelector('#modal-cancel')
        const confirmButton = this.modal.querySelector('#modal-confirm')
        
        if (cancelButton) {
            cancelButton.addEventListener('click', () => {
                this.close()
            })
        }
        
        if (confirmButton) {
            confirmButton.addEventListener('click', () => {
                this.confirm()
            })
        }
        
        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close()
            }
        })
    }
    
    bindIndicatorEvents() {
        if (!this.modal) return
        
        this.modal.querySelectorAll('.dataset-option').forEach(option => {
            const indicatorCode = option.dataset.indicatorCode
            
            option.style.cursor = 'pointer'
            option.addEventListener('click', (e) => {
                e.stopPropagation()
                this.selectIndicator(indicatorCode)
            })
        })
    }
    
    selectIndicator(indicatorCode) {
        this.selectedIndicator = indicatorCode
        this.renderIndicatorList()
        this.updateSelectionCounter()
        this.updateConfirmButton()
    }
    
    updateConfirmButton() {
        if (!this.modal) return
        const confirmButton = this.modal.querySelector('#modal-confirm')
        if (confirmButton) {
            confirmButton.disabled = !this.selectedIndicator
        }
    }
    
    clearFilters() {
        this.currentFilters = {
            search: '',
            category: '',
            pillar: ''
        }
        
        if (!this.modal) return
        
        // Reset form inputs
        const searchInput = this.modal.querySelector('#indicator-search')
        if (searchInput) searchInput.value = ''
        
        const pillarFilter = this.modal.querySelector('#pillar-filter')
        const categoryFilter = this.modal.querySelector('#category-filter')
        
        if (pillarFilter) pillarFilter.value = ''
        if (categoryFilter) categoryFilter.value = ''
        
        this.applyFilters()
        this.renderIndicatorList()
    }
    
    updateSelectionCounter() {
        if (!this.modal) return
        const counter = this.modal.querySelector('.selected-count')
        if (counter) counter.textContent = this.selectedIndicator ? 1 : 0
    }
    
    updateResultsCount() {
        if (!this.modal) return
        const resultsCount = this.modal.querySelector('.search-results-count')
        if (resultsCount) {
            resultsCount.textContent = this.filteredIndicators.length + ' indicator' + (this.filteredIndicators.length !== 1 ? 's' : '') + ' found'
        }
    }
    
    confirm() {
        if (this.selectedIndicator && this.options.onSelectionChange) {
            // Find the full indicator object
            const indicator = this.indicators.find(i => i.indicator_code === this.selectedIndicator)
            this.options.onSelectionChange(indicator)
        }
        this.close()
    }
    
    close() {
        if (this.modal && this.modal.parentNode) {
            document.body.removeChild(this.modal)
        }
        this.modal = null
    }
    
    hide() {
        this.close()
    }
    
    getSelectedIndicator() {
        return this.selectedIndicator
    }
}