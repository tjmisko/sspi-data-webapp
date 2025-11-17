class DatasetSelector {
    constructor(options = {}) {
        this.options = {
            maxSelections: 10,
            multiSelect: true,
            showOrganizations: true,
            showTypes: true,
            enableFilters: true,
            enableSearch: true,
            onSelectionChange: null,
            apiEndpoint: '/api/v1/customize/datasets',
            preloadedDatasets: null,  // Optional: pre-loaded datasets to avoid API call
            ...options
        }

        this.datasets = []
        this.filteredDatasets = []
        this.selectedDatasets = []
        this.currentFilters = {
            search: '',
            organization: ''
        }

        this.modal = null
    }

    async initialize() {
        // Use preloaded datasets if available, otherwise fetch from API
        if (this.options.preloadedDatasets && Array.isArray(this.options.preloadedDatasets)) {
            console.log('Using preloaded datasets:', this.options.preloadedDatasets.length);
            this.datasets = this.normalizeDatasets(this.options.preloadedDatasets);
        } else {
            await this.loadDatasets();
        }
        this.applyFilters();
    }

    normalizeDatasets(datasets) {
        // Normalize dataset format to ensure consistent field names
        return datasets.map(d => ({
            dataset_code: d.DatasetCode || d.dataset_code,
            dataset_name: d.DatasetName || d.dataset_name,
            description: d.Description || d.description || '',
            organization: d.Source?.OrganizationName || d.organization || 'Unknown',
            organizationCode: d.Source?.OrganizationCode || d.OrganizationCode || d.organizationCode || '',
            dataset_type: d.DatasetType || d.dataset_type || 'Unknown',
            topic_category: d.TopicCategory || d.topic_category || 'General'
        }));
    }

    async loadDatasets() {
        try {
            const response = await fetch(`${this.options.apiEndpoint}?limit=1000`)
            const data = await response.json()
            this.datasets = this.normalizeDatasets(data.datasets || [])
        } catch (error) {
            console.error('Error loading datasets:', error)
            this.datasets = []
        }
    }
    
    async show(currentSelections = []) {
        try {
            if (!this.datasets.length) {
                await this.initialize()
            }
            
            this.selectedDatasets = [...currentSelections]
            this.createModal()
            
            if (!this.modal) {
                console.error('Failed to create modal')
                return
            }
            
            this.renderModal()
            this.bindEvents()
            document.body.appendChild(this.modal)
        } catch (error) {
            console.error('Error showing dataset selector:', error)
        }
    }
    
    createModal() {
        this.modal = document.createElement('div')
        this.modal.className = 'dataset-modal-overlay'
        
        const modalContent = document.createElement('div')
        modalContent.className = 'dataset-modal-content enhanced'
        
        modalContent.innerHTML = 
            '<div class="dataset-modal-header">' +
            '<h3 class="dataset-modal-title">Select Dataset</h3>' +
            '<div class="dataset-selection-counter">' +
            '<span class="selected-count">' + this.selectedDatasets.length + '</span> of ' +
            '<span class="max-count">' + this.options.maxSelections + '</span> selected' +
            '</div>' +
            '</div>' +
            (this.options.enableSearch ? this.createSearchHTML() : '') +
            (this.options.enableFilters ? this.createFiltersHTML() : '') +
            '<div class="dataset-list-container">' +
            '<div id="dataset-list" class="dataset-list enhanced">' +
            '<div class="dataset-loading-message">Loading datasets...</div>' +
            '</div>' +
            '</div>' +
            '<div class="dataset-modal-actions">' +
            '<button id="modal-cancel" class="dataset-modal-cancel">Close</button>' +
            '</div>'
        
        this.modal.appendChild(modalContent)
    }
    
    createSearchHTML() {
        return '<div class="dataset-search-container">' +
               '<input type="text" id="dataset-search" class="dataset-search-input" ' +
               'placeholder="Search datasets by code, name, or description...">' +
               '<div class="search-results-count"></div>' +
               '</div>';
    }
    
    createFiltersHTML() {
        // Build unique organization list with codes
        const orgMap = new Map()
        this.datasets.forEach(d => {
            if (!orgMap.has(d.organization)) {
                orgMap.set(d.organization, d.organizationCode)
            }
        })

        // Sort organizations by name and create options with "Name (Code)" format
        const organizations = Array.from(orgMap.entries()).sort((a, b) => a[0].localeCompare(b[0]))
        const orgOptions = organizations.map(([orgName, orgCode]) => {
            const displayText = orgCode ? orgName + ' (' + orgCode + ')' : orgName
            return '<option value="' + orgName + '">' + displayText + '</option>'
        }).join('')

        return '<div class="dataset-filters-container">' +
               '<div class="filter-group">' +
               '<label for="org-filter">Organization:</label>' +
               '<select id="org-filter" class="filter-select">' +
               '<option value="">All Organizations</option>' +
               orgOptions +
               '</select>' +
               '</div>' +
               '<button id="clear-filters" class="clear-filters-btn">Clear Filters</button>' +
               '</div>';
    }
    
    renderModal() {
        this.applyFilters()
        this.renderDatasetList()
        this.updateSelectionCounter()
    }
    
    applyFilters() {
        this.filteredDatasets = this.datasets.filter(dataset => {
            const matchesSearch = !this.currentFilters.search ||
                dataset.dataset_code.toLowerCase().includes(this.currentFilters.search.toLowerCase()) ||
                dataset.dataset_name.toLowerCase().includes(this.currentFilters.search.toLowerCase()) ||
                (dataset.description && dataset.description.toLowerCase().includes(this.currentFilters.search.toLowerCase()))

            const matchesOrg = !this.currentFilters.organization ||
                dataset.organization === this.currentFilters.organization

            return matchesSearch && matchesOrg
        })

        this.updateResultsCount()
    }
    
    renderDatasetList() {
        if (!this.modal) {
            console.error('Modal not found in renderDatasetList')
            return
        }
        
        const datasetList = this.modal.querySelector('#dataset-list')
        if (!datasetList) {
            console.error('Dataset list element not found')
            return
        }
        
        if (this.filteredDatasets.length === 0) {
            datasetList.innerHTML = '<div class="dataset-no-results">No datasets found matching your criteria.</div>'
            return
        }
        
        const htmlParts = []
        
        this.filteredDatasets.forEach(dataset => {
            const isSelected = this.selectedDatasets.includes(dataset.dataset_code)
            const isDisabled = !isSelected && this.selectedDatasets.length >= this.options.maxSelections
            
            let cssClasses = 'dataset-option enhanced'
            if (isSelected) cssClasses += ' selected'
            if (isDisabled) cssClasses += ' disabled'
            
            let badges = ''
            if (this.options.showOrganizations) {
                // Show only the organization code if available, otherwise the full name
                const orgDisplay = dataset.organizationCode || dataset.organization
                badges += '<span class="dataset-organization-badge ' + dataset.organization.toLowerCase().replace(/\s+/g, '-') + '">' + orgDisplay + '</span>'
            }
            if (this.options.showTypes) {
                badges += '<span class="dataset-type-badge ' + dataset.dataset_type.toLowerCase() + '">' + dataset.dataset_type + '</span>'
            }
            
            let actions = ''
            if (isSelected) {
                actions = '<button class="dataset-remove-btn">Remove</button>'
            } else {
                actions = '<button class="dataset-add-btn"' + (isDisabled ? ' disabled' : '') + '>Add Dataset</button>'
            }
            if (isDisabled && !isSelected) {
                actions += '<div class="dataset-limit-note">Selection limit reached</div>'
            }
            
            const description = dataset.description_short || dataset.description || ''
            const organization = dataset.organization_name || dataset.organization || ''
            
            htmlParts.push(
                '<div class="' + cssClasses + ' compact" data-dataset-code="' + dataset.dataset_code + '">' +
                '<div class="dataset-compact-header">' +
                '<div class="dataset-compact-code">' + dataset.dataset_code + '</div>' +
                '<div class="dataset-compact-badges">' + badges + '</div>' +
                '</div>' +
                '<div class="dataset-compact-name">' + dataset.dataset_name + '</div>' +
                '<div class="dataset-compact-description">' + description + '</div>' +
                '</div>'
            )
        })
        
        datasetList.innerHTML = htmlParts.join('')
        this.bindDatasetEvents()
    }
    
    bindEvents() {
        if (!this.modal) {
            console.error('Modal not found in bindEvents')
            return
        }
        
        // Search functionality
        if (this.options.enableSearch) {
            const searchInput = this.modal.querySelector('#dataset-search')
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    this.currentFilters.search = e.target.value
                    this.applyFilters()
                    this.renderDatasetList()
                })
            }
        }
        
        // Filter functionality
        if (this.options.enableFilters) {
            const orgFilter = this.modal.querySelector('#org-filter')
            const clearButton = this.modal.querySelector('#clear-filters')

            if (orgFilter) {
                orgFilter.addEventListener('change', (e) => {
                    this.currentFilters.organization = e.target.value
                    this.applyFilters()
                    this.renderDatasetList()
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
        const clearButton = this.modal.querySelector('#modal-clear')
        
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
        
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                this.clearAll()
            })
        }
        
        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close()
            }
        })

        // Close on ESC key press
        this.escapeHandler = (e) => {
            if (e.key === 'Escape' || e.keyCode === 27) {
                this.close()
            }
        }
        document.addEventListener('keydown', this.escapeHandler)
    }
    
    bindDatasetEvents() {
        if (!this.modal) return
        
        this.modal.querySelectorAll('.dataset-option').forEach(option => {
            const datasetCode = option.dataset.datasetCode
            const isSelected = this.selectedDatasets.includes(datasetCode)
            const isDisabled = !isSelected && this.selectedDatasets.length >= this.options.maxSelections
            
            if (!isDisabled) {
                option.style.cursor = 'pointer'
                option.addEventListener('click', (e) => {
                    e.stopPropagation()
                    if (isSelected) {
                        this.removeDataset(datasetCode)
                    } else {
                        this.addDataset(datasetCode)
                    }
                })
            } else {
                option.style.cursor = 'not-allowed'
            }
        })
    }
    
    addDataset(datasetCode) {
        if (this.selectedDatasets.length >= this.options.maxSelections) return
        if (this.selectedDatasets.includes(datasetCode)) return

        this.selectedDatasets.push(datasetCode)

        // Immediately notify parent with full dataset objects
        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(this.getSelectedDatasetObjects())
        }

        // Update the display to reflect the change
        this.renderDatasetList()
        this.updateSelectionCounter()
    }

    removeDataset(datasetCode) {
        this.selectedDatasets = this.selectedDatasets.filter(code => code !== datasetCode)

        // Immediately notify parent with full dataset objects
        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(this.getSelectedDatasetObjects())
        }

        this.renderDatasetList()
        this.updateSelectionCounter()
    }

    getSelectedDatasetObjects() {
        // Return full dataset objects for selected codes, preserving all details
        return this.selectedDatasets.map(code => {
            return this.datasets.find(d => d.dataset_code === code)
        }).filter(d => d) // Filter out any undefined entries
    }
    
    clearAll() {
        this.selectedDatasets = []
        this.renderDatasetList()
        this.updateSelectionCounter()
    }
    
    clearFilters() {
        this.currentFilters = {
            search: '',
            organization: ''
        }

        if (!this.modal) return

        // Reset form inputs
        const searchInput = this.modal.querySelector('#dataset-search')
        if (searchInput) searchInput.value = ''

        const orgFilter = this.modal.querySelector('#org-filter')
        if (orgFilter) orgFilter.value = ''

        this.applyFilters()
        this.renderDatasetList()
    }
    
    updateSelectionCounter() {
        if (!this.modal) return
        const counter = this.modal.querySelector('.selected-count')
        if (counter) counter.textContent = this.selectedDatasets.length
    }
    
    updateResultsCount() {
        if (!this.modal) return
        const resultsCount = this.modal.querySelector('.search-results-count')
        if (resultsCount) {
            resultsCount.textContent = this.filteredDatasets.length + ' dataset' + (this.filteredDatasets.length !== 1 ? 's' : '') + ' found'
        }
    }
    
    confirm() {
        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(this.getSelectedDatasetObjects())
        }
        this.close()
    }
    
    close() {
        // Remove escape key handler
        if (this.escapeHandler) {
            document.removeEventListener('keydown', this.escapeHandler)
            this.escapeHandler = null
        }

        if (this.modal && this.modal.parentNode) {
            document.body.removeChild(this.modal)
        }
        this.modal = null
    }
    
    hide() {
        this.close()
    }
    
    getSelectedDatasets() {
        return this.selectedDatasets
    }
}