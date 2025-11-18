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
        this.highlightedIndex = -1  // For keyboard navigation (independent of mouse)
    }

    async initialize() {
        // Use preloaded datasets if available, otherwise fetch from API
        if (this.options.preloadedDatasets && Array.isArray(this.options.preloadedDatasets)) {
            console.log('Using preloaded datasets:', this.options.preloadedDatasets.length);
            this.datasets = this.options.preloadedDatasets;
        } else {
            await this.loadDatasets();
        }
        this.applyFilters();
    }

    async loadDatasets() {
        try {
            const response = await fetch(`${this.options.apiEndpoint}?limit=1000`)
            const data = await response.json()
            this.datasets = data.datasets || []
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

            // Autofocus search input for immediate typing
            if (this.options.enableSearch) {
                const searchInput = this.modal.querySelector('#dataset-search')
                if (searchInput) {
                    // Small delay to ensure modal is fully rendered
                    setTimeout(() => searchInput.focus(), 100)
                }
            }
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
            this.createSelectedDatasetsHTML() +
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
            const orgName = d.Source?.OrganizationName || 'Unknown';
            const orgCode = d.Source?.OrganizationCode || '';
            if (!orgMap.has(orgName)) {
                orgMap.set(orgName, orgCode)
            }
        })

        // Sort organizations by name and create options with "Name (Code)" format
        const organizations = Array.from(orgMap.entries()).sort((a, b) => a[0].localeCompare(b[0]))
        const orgOptions = organizations.map(([orgName, orgCode]) => {
            const displayText = orgCode ? orgName + ' (' + orgCode + ')' : orgName
            return '<option value="' + orgName + '">' + displayText + '</option>'
        }).join('')

        return '<div class="dataset-filters-container">' +
               '<label for="org-filter" class="visually-hidden">Organization:</label>' +
               '<select id="org-filter" class="filter-select">' +
               '<option value="">All Organizations</option>' +
               orgOptions +
               '</select>' +
               '</div>';
    }

    createSelectedDatasetsHTML() {
        return '<div class="selected-datasets-container" id="selected-datasets-container">' +
               '<div class="selected-datasets-list" id="selected-datasets-list"></div>' +
               '</div>';
    }

    renderModal() {
        this.applyFilters()
        this.renderSelectedDatasets()
        this.renderDatasetList()
        this.updateSelectionCounter()
    }
    
    applyFilters() {
        this.filteredDatasets = this.datasets.filter(dataset => {
            const matchesSearch = !this.currentFilters.search ||
                dataset.DatasetCode.toLowerCase().includes(this.currentFilters.search.toLowerCase()) ||
                dataset.DatasetName.toLowerCase().includes(this.currentFilters.search.toLowerCase()) ||
                (dataset.Description && dataset.Description.toLowerCase().includes(this.currentFilters.search.toLowerCase()))

            const orgName = dataset.Source?.OrganizationName || 'Unknown';
            const matchesOrg = !this.currentFilters.organization ||
                orgName === this.currentFilters.organization

            return matchesSearch && matchesOrg
        })

        this.updateResultsCount()
    }

    renderSelectedDatasets() {
        if (!this.modal) return
        const container = this.modal.querySelector('#selected-datasets-list')
        if (!container) return
        // Clear existing content
        container.innerHTML = ''
        if (this.selectedDatasets.length === 0) {
            return
        }
        // Create bubbles for each selected dataset
        const bubbles = this.selectedDatasets.map(datasetCode => {
            const dataset = this.datasets.find(d => d.DatasetCode === datasetCode)
            if (!dataset) return ''

            return '<div class="selected-dataset-bubble" data-dataset-code="' + datasetCode + '">' +
                   '<span class="bubble-text">' + datasetCode + '</span>' +
                   '<button class="bubble-remove-btn" data-dataset-code="' + datasetCode + '" title="Remove ' + datasetCode + '">' +
                   '&times;' +
                   '</button>' +
                   '</div>'
        }).filter(html => html !== '').join('')

        container.innerHTML = bubbles

        // Bind click events to remove buttons
        this.bindSelectedDatasetEvents()
    }

    bindSelectedDatasetEvents() {
        if (!this.modal) return

        const removeButtons = this.modal.querySelectorAll('.bubble-remove-btn')
        removeButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation()
                const datasetCode = button.dataset.datasetCode
                this.removeDataset(datasetCode)
            })
        })
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
            const isSelected = this.selectedDatasets.includes(dataset.DatasetCode)
            const isDisabled = !isSelected && this.selectedDatasets.length >= this.options.maxSelections

            let cssClasses = 'dataset-option enhanced'
            if (isSelected) cssClasses += ' selected'
            if (isDisabled) cssClasses += ' disabled'

            let badges = ''
            if (this.options.showOrganizations) {
                // Show only the organization code if available, otherwise the full name
                const orgName = dataset.Source?.OrganizationName || 'Unknown';
                const orgCode = dataset.Source?.OrganizationCode || '';
                const orgDisplay = orgCode || orgName
                badges += '<span class="dataset-organization-badge ' + orgName.toLowerCase().replace(/\s+/g, '-') + '">' + orgDisplay + '</span>'
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

            const description = dataset.Description || ''

            htmlParts.push(
                '<div class="' + cssClasses + ' compact" data-dataset-code="' + dataset.DatasetCode + '">' +
                '<div class="dataset-compact-header">' +
                '<div class="dataset-compact-code">' + dataset.DatasetCode + '</div>' +
                '</div>' +
                '<div class="dataset-compact-name">' + dataset.DatasetName + '</div>' +
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
                    this.highlightedIndex = -1  // Reset on search
                    this.applyFilters()
                    this.renderDatasetList()
                })

                // Keyboard navigation on search input
                searchInput.addEventListener('keydown', (e) => {
                    // Handle Escape explicitly to close modal immediately
                    if (e.key === 'Escape') {
                        e.preventDefault()
                        e.stopPropagation()
                        e.stopImmediatePropagation()
                        this.close()
                        return
                    }

                    this.handleKeyboardNavigation(e)
                    // Prevent event from bubbling to avoid double-handling
                    const navKeys = ['ArrowDown', 'ArrowUp', 'Home', 'End', 'PageUp', 'PageDown', 'Enter', ' ']
                    if (navKeys.includes(e.key)) {
                        e.stopPropagation()
                    }
                })
            }
        }

        // Global keyboard navigation (backup for when search is not focused)
        // Only handles navigation keys, not text input
        this.keyboardHandler = (e) => {
            const navKeys = ['ArrowDown', 'ArrowUp', 'Home', 'End', 'PageUp', 'PageDown', 'Enter', ' ']
            if (navKeys.includes(e.key)) {
                this.handleKeyboardNavigation(e)
            }
        }
        document.addEventListener('keydown', this.keyboardHandler)
        
        // Filter functionality
        if (this.options.enableFilters) {
            const orgFilter = this.modal.querySelector('#org-filter')

            if (orgFilter) {
                orgFilter.addEventListener('change', (e) => {
                    this.currentFilters.organization = e.target.value
                    this.applyFilters()
                    this.renderDatasetList()
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

        // Close on ESC key press (document-level fallback)
        this.escapeHandler = (e) => {
            if ((e.key === 'Escape' || e.keyCode === 27) && this.modal) {
                e.preventDefault()
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
        this.renderSelectedDatasets()
        this.renderDatasetList()
        this.updateSelectionCounter()
    }

    removeDataset(datasetCode) {
        this.selectedDatasets = this.selectedDatasets.filter(code => code !== datasetCode)

        // Immediately notify parent with full dataset objects
        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(this.getSelectedDatasetObjects())
        }

        this.renderSelectedDatasets()
        this.renderDatasetList()
        this.updateSelectionCounter()
    }

    getSelectedDatasetObjects() {
        // Return full dataset objects for selected codes, preserving all details
        return this.selectedDatasets.map(code => {
            return this.datasets.find(d => d.DatasetCode === code)
        }).filter(d => d) // Filter out any undefined entries
    }
    
    clearAll() {
        this.selectedDatasets = []
        this.renderSelectedDatasets()
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
            resultsCount.textContent = this.filteredDatasets.length + '/' + this.datasets.length
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

        // Remove keyboard navigation handler
        if (this.keyboardHandler) {
            document.removeEventListener('keydown', this.keyboardHandler)
            this.keyboardHandler = null
        }

        if (this.modal && this.modal.parentNode) {
            document.body.removeChild(this.modal)
        }
        this.modal = null
    }
    
    hide() {
        this.close()
    }

    // Keyboard Navigation Methods

    handleKeyboardNavigation(e) {
        if (!this.modal) return

        const datasetList = this.modal.querySelector('#dataset-list')
        if (!datasetList) return

        const items = datasetList.querySelectorAll('.dataset-option')
        if (items.length === 0) return

        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault()
                if (this.highlightedIndex < items.length - 1) {
                    this.highlightedIndex++
                    this.highlightSelectedIndex()
                    this.scrollHighlightedIntoView()
                }
                break

            case 'ArrowUp':
                e.preventDefault()
                if (this.highlightedIndex > -1) {
                    this.highlightedIndex--
                    this.highlightSelectedIndex()
                    this.scrollHighlightedIntoView()
                }
                break

            case 'Home':
                e.preventDefault()
                this.highlightedIndex = 0
                this.highlightSelectedIndex()
                this.scrollHighlightedIntoView()
                break

            case 'End':
                e.preventDefault()
                this.highlightedIndex = items.length - 1
                this.highlightSelectedIndex()
                this.scrollHighlightedIntoView()
                break

            case 'PageUp':
                e.preventDefault()
                this.highlightedIndex = Math.max(0, this.highlightedIndex - 10)
                this.highlightSelectedIndex()
                this.scrollHighlightedIntoView()
                break

            case 'PageDown':
                e.preventDefault()
                this.highlightedIndex = Math.min(items.length - 1, this.highlightedIndex + 10)
                this.highlightSelectedIndex()
                this.scrollHighlightedIntoView()
                break

            case 'Enter':
            case ' ':  // Space key
                // Only toggle if there's a highlighted item
                if (this.highlightedIndex >= 0) {
                    e.preventDefault()
                    this.toggleHighlightedDataset()
                }
                // Otherwise, allow space to be typed normally in the search input
                break
        }

        // Keep search input focused
        if (this.options.enableSearch) {
            const searchInput = this.modal.querySelector('#dataset-search')
            if (searchInput && document.activeElement !== searchInput) {
                searchInput.focus()
            }
        }
    }

    highlightSelectedIndex() {
        if (!this.modal) return

        const datasetList = this.modal.querySelector('#dataset-list')
        if (!datasetList) return

        const items = datasetList.querySelectorAll('.dataset-option')

        // Clamp highlightedIndex to valid range
        if (this.highlightedIndex > items.length - 1) {
            this.highlightedIndex = items.length - 1
        }

        // Update visual highlight
        items.forEach((item, index) => {
            if (index === this.highlightedIndex) {
                item.classList.add('keyboard-highlighted')
            } else {
                item.classList.remove('keyboard-highlighted')
            }
        })
    }

    scrollHighlightedIntoView() {
        if (!this.modal || this.highlightedIndex === -1) return

        const datasetList = this.modal.querySelector('#dataset-list')
        if (!datasetList) return

        const items = datasetList.querySelectorAll('.dataset-option')
        const highlightedItem = items[this.highlightedIndex]

        if (highlightedItem) {
            highlightedItem.scrollIntoView({
                block: 'nearest',
                behavior: 'smooth'
            })
        }
    }

    toggleHighlightedDataset() {
        if (!this.modal || this.highlightedIndex === -1) return

        const datasetList = this.modal.querySelector('#dataset-list')
        if (!datasetList) return

        const items = datasetList.querySelectorAll('.dataset-option')
        const highlightedItem = items[this.highlightedIndex]

        if (highlightedItem) {
            // Get the dataset code from the element
            const datasetCode = highlightedItem.dataset.datasetCode
            if (datasetCode) {
                // Toggle selection
                if (this.selectedDatasets.includes(datasetCode)) {
                    this.removeDataset(datasetCode)
                } else {
                    this.addDataset(datasetCode)
                }
            }
        }
    }

    getSelectedDatasets() {
        return this.selectedDatasets
    }
}
