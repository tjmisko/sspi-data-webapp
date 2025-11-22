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
            preloadedIndicators: null,  // Optional: pre-loaded indicators to avoid API call
            ...options
        }

        this.indicators = []
        this.filteredIndicators = []
        this.selectedIndicator = null
        this.pillarOptions = []
        this.categoryOptions = []
        this.currentFilters = {
            search: '',
            category: '',
            pillar: ''
        }

        this.modal = null
        this.highlightedIndex = -1  // For keyboard navigation (independent of mouse)
        this.inputMode = 'mouse'  // Track current input mode: 'mouse' or 'keyboard'
    }

    async initialize() {
        // Use preloaded indicators if available, otherwise fetch from API
        if (this.options.preloadedIndicators && Array.isArray(this.options.preloadedIndicators)) {
            console.log('Using preloaded indicators:', this.options.preloadedIndicators.length);
            this.indicators = this.options.preloadedIndicators;
        } else {
            await this.loadIndicators();
        }
        this.applyFilters();
    }
    
    async loadIndicators() {
        try {
            const response = await fetch(`${this.options.apiEndpoint}?limit=1000`)
            const data = await response.json()
            this.indicators = data.indicators || []
            this.pillarOptions = data.pillars || []
            this.categoryOptions = data.categories || []
        } catch (error) {
            console.error('Error loading indicators:', error)
            this.indicators = []
            this.pillarOptions = []
            this.categoryOptions = []
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

            // Autofocus search input for immediate typing
            if (this.options.enableSearch) {
                const searchInput = this.modal.querySelector('#indicator-search')
                if (searchInput) {
                    // Small delay to ensure modal is fully rendered
                    setTimeout(() => searchInput.focus(), 100)
                }
            }
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
            '<span class="selected-count">' + (this.selectedIndicator ? 1 : 0) + '</span>' +
            '<span>of</span>' +
            '<span>1</span>' +
            '<span>selected</span>' +
            '</div>' +
            '<button class="modal-close-btn" id="modal-close-btn" aria-label="Close" tabindex="0">&times;</button>' +
            '</div>' +
            (this.options.enableSearch ? this.createSearchHTML() : '') +
            (this.options.enableFilters ? this.createFiltersHTML() : '') +
            '<div class="dataset-list-container" tabindex="0">' +
            '<div id="indicator-list" class="dataset-list enhanced">' +
            '<div class="dataset-loading-message">Loading indicators...</div>' +
            '</div>' +
            '</div>' +
            '<div class="dataset-modal-actions">' +
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
        // Build pillar options from API data with format: "Name (CODE)"
        const pillarOptions = this.pillarOptions
            .map(p => {
                const code = p.PillarCode || p.ItemCode
                const name = p.Pillar || p.ItemName || code
                return '<option value="' + code + '">' + name + '\u0020(' + code + ')</option>'
            })
            .join('')

        // Build category options from API data with format: "Name (CODE)"
        const categoryOptions = this.categoryOptions
            .map(c => {
                const code = c.CategoryCode || c.ItemCode
                const name = c.Category || c.ItemName || code
                return '<option value="' + code + '">' + name + '\u0020(' + code + ')</option>'
            })
            .join('')

        return '<div class="dataset-filters-container">' +
               '<select id="pillar-filter" class="filter-select pillar-select">' +
               '<option value="" class="default-option">All Pillars</option>' +
               pillarOptions +
               '</select>' +
               '<select id="category-filter" class="filter-select category-select">' +
               '<option value="" class="default-option">All Categories</option>' +
               categoryOptions +
               '</select>' +
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
                indicator.IndicatorCode.toLowerCase().includes(this.currentFilters.search.toLowerCase()) ||
                (indicator.Indicator && indicator.Indicator.toLowerCase().includes(this.currentFilters.search.toLowerCase())) ||
                (indicator.ItemName && indicator.ItemName.toLowerCase().includes(this.currentFilters.search.toLowerCase())) ||
                (indicator.Description && indicator.Description.toLowerCase().includes(this.currentFilters.search.toLowerCase()))

            // Parse TreePath for category and pillar (e.g., "sspi/sus/eco/biodiv" -> pillar="sus", category="eco")
            const pathParts = indicator.TreePath ? indicator.TreePath.split('/') : []
            const pillar = pathParts.length > 1 ? pathParts[1].toUpperCase() : ''
            const category = pathParts.length > 2 ? pathParts[2].toUpperCase() : ''

            const matchesCategory = !this.currentFilters.category ||
                category === this.currentFilters.category

            const matchesPillar = !this.currentFilters.pillar ||
                pillar === this.currentFilters.pillar

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
            const isSelected = this.selectedIndicator === indicator.IndicatorCode

            let cssClasses = 'dataset-option enhanced'
            if (isSelected) cssClasses += ' selected'

            // Parse TreePath for breadcrumb display (PillarCode > CategoryCode > IndicatorCode)
            const pathParts = indicator.TreePath ? indicator.TreePath.split('/') : []
            const pillar = pathParts.length > 1 ? pathParts[1].toUpperCase() : ''
            const category = pathParts.length > 2 ? pathParts[2].toUpperCase() : ''
            const breadcrumb = pillar + '\u0020>\u0020' + category + '\u0020>\u0020' + indicator.IndicatorCode

            const description = indicator.Description || ''
            const indicatorName = indicator.Indicator || indicator.ItemName || indicator.IndicatorCode

            htmlParts.push(
                '<div class="' + cssClasses + ' compact" data-indicator-code="' + indicator.IndicatorCode + '">' +
                '<div class="dataset-compact-header">' +
                '<div class="dataset-compact-code">' + breadcrumb + '</div>' +
                '</div>' +
                '<div class="dataset-compact-name">' + indicatorName + '</div>' +
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
                    this.highlightedIndex = -1  // Reset on search
                    this.applyFilters()
                    this.renderIndicatorList()
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
            const pillarFilter = this.modal.querySelector('#pillar-filter')
            const categoryFilter = this.modal.querySelector('#category-filter')

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
        }

        // Modal action buttons
        const closeButton = this.modal.querySelector('#modal-close-btn')
        const confirmButton = this.modal.querySelector('#modal-confirm')

        if (closeButton) {
            closeButton.addEventListener('click', () => {
                this.close()
            })
            closeButton.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    this.close()
                }
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

        // Close on ESC key press (document-level fallback)
        this.escapeHandler = (e) => {
            if ((e.key === 'Escape' || e.keyCode === 27) && this.modal) {
                e.preventDefault()
                this.close()
            }
        }
        document.addEventListener('keydown', this.escapeHandler)

        // Focus trap - prevent tabbing out of modal
        this.focusTrapHandler = (e) => {
            if (e.key !== 'Tab' || !this.modal) return

            const focusableElements = this.modal.querySelectorAll(
                'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])'
            )
            const focusableArray = Array.from(focusableElements)
            const firstElement = focusableArray[0]
            const lastElement = focusableArray[focusableArray.length - 1]

            if (e.shiftKey) {
                // Shift+Tab: if on first element, go to last
                if (document.activeElement === firstElement) {
                    e.preventDefault()
                    lastElement.focus()
                }
            } else {
                // Tab: if on last element, go to first
                if (document.activeElement === lastElement) {
                    e.preventDefault()
                    firstElement.focus()
                }
            }
        }
        document.addEventListener('keydown', this.focusTrapHandler)

        // Track mouse movement to switch back to mouse mode
        const indicatorList = this.modal.querySelector('#dataset-list')
        if (indicatorList) {
            indicatorList.addEventListener('mousemove', () => {
                if (this.inputMode !== 'mouse') {
                    this.inputMode = 'mouse'
                    this.updateInputModeClass()
                }
            })
        }
    }
    
    bindIndicatorEvents() {
        if (!this.modal) return

        this.modal.querySelectorAll('.dataset-option').forEach(option => {
            const indicatorCode = option.dataset.indicatorCode

            // Switch to mouse mode on mouseenter
            option.addEventListener('mouseenter', () => {
                if (this.inputMode !== 'mouse') {
                    this.inputMode = 'mouse'
                    this.updateInputModeClass()
                }
            })

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
    
    async confirm() {
        if (this.selectedIndicator && this.options.onSelectionChange) {
            // Find the full indicator object from the loaded list
            const indicator = this.indicators.find(i => i.IndicatorCode === this.selectedIndicator)
            if (indicator) {
                this.options.onSelectionChange(indicator)
            }
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

        // Remove focus trap handler
        if (this.focusTrapHandler) {
            document.removeEventListener('keydown', this.focusTrapHandler)
            this.focusTrapHandler = null
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

        const indicatorList = this.modal.querySelector('#indicator-list')
        if (!indicatorList) return

        const items = indicatorList.querySelectorAll('.dataset-option')
        if (items.length === 0) return

        // Switch to keyboard mode on any keyboard navigation
        if (this.inputMode !== 'keyboard') {
            this.inputMode = 'keyboard'
            this.updateInputModeClass()
        }

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

            case 'Enter': {
                // Only process if search input or list container is focused (not buttons/dropdowns)
                const searchInput = this.modal.querySelector('#indicator-search')
                const listContainer = this.modal.querySelector('.dataset-list-container')
                const isFocusedOnInput = document.activeElement === searchInput || document.activeElement === listContainer

                if (this.highlightedIndex >= 0 && isFocusedOnInput) {
                    e.preventDefault()

                    // Get the currently highlighted indicator's code
                    const indicatorList = this.modal.querySelector('#indicator-list')
                    const items = indicatorList ? indicatorList.querySelectorAll('.dataset-option') : []
                    const highlightedItem = items[this.highlightedIndex]
                    const highlightedCode = highlightedItem ? highlightedItem.dataset.indicatorCode : null

                    // Check if the highlighted indicator is already selected
                    const isAlreadySelected = this.selectedIndicator === highlightedCode

                    if (isAlreadySelected) {
                        // If already selected and Enter pressed again, submit and close
                        this.confirm()
                    } else {
                        // Otherwise, just toggle (select) the indicator
                        this.toggleHighlightedIndicator()
                    }
                }
                break
            }

            case ' ': {  // Space key
                // Only process if search input or list container is focused (not buttons/dropdowns)
                const searchInput = this.modal.querySelector('#indicator-search')
                const listContainer = this.modal.querySelector('.dataset-list-container')
                const isFocusedOnInput = document.activeElement === searchInput || document.activeElement === listContainer

                // Space should ONLY toggle, never submit
                if (this.highlightedIndex >= 0 && isFocusedOnInput) {
                    e.preventDefault()
                    this.toggleHighlightedIndicator()
                }
                // Otherwise, allow default behavior (space in search, button clicks, etc.)
                break
            }
        }

        // Keep search input focused ONLY for navigation keys (arrows, page up/down)
        // Don't refocus if user is on a button (Space/Enter on buttons should work)
        const isNavigationKey = ['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown'].includes(e.key)
        const isOnButton = document.activeElement && document.activeElement.tagName === 'BUTTON'
        const isOnSelect = document.activeElement && document.activeElement.tagName === 'SELECT'

        if (this.options.enableSearch && isNavigationKey && !isOnButton) {
            const searchInput = this.modal.querySelector('#indicator-search')
            const listContainer = this.modal.querySelector('.dataset-list-container')

            // Refocus if we're on the list container OR a dropdown/select (navigating from filter)
            if (searchInput && (document.activeElement === listContainer || isOnSelect)) {
                searchInput.focus()
            }
        }
    }

    highlightSelectedIndex() {
        if (!this.modal) return

        const indicatorList = this.modal.querySelector('#indicator-list')
        if (!indicatorList) return

        const items = indicatorList.querySelectorAll('.dataset-option')

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

        const indicatorList = this.modal.querySelector('#indicator-list')
        if (!indicatorList) return

        const items = indicatorList.querySelectorAll('.dataset-option')
        const highlightedItem = items[this.highlightedIndex]

        if (highlightedItem) {
            highlightedItem.scrollIntoView({
                block: 'nearest',
                behavior: 'smooth'
            })
        }
    }

    toggleHighlightedIndicator() {
        if (!this.modal || this.highlightedIndex === -1) return

        const indicatorList = this.modal.querySelector('#indicator-list')
        if (!indicatorList) return

        const items = indicatorList.querySelectorAll('.dataset-option')
        const highlightedItem = items[this.highlightedIndex]

        if (highlightedItem) {
            // Get the indicator code from the element
            const indicatorCode = highlightedItem.dataset.indicatorCode
            if (indicatorCode) {
                // Set as selected (single selection)
                this.selectIndicator(indicatorCode)
            }
        }
    }

    getSelectedIndicator() {
        return this.selectedIndicator
    }

    updateInputModeClass() {
        if (!this.modal) return

        const indicatorList = this.modal.querySelector('#indicator-list')
        if (!indicatorList) return

        if (this.inputMode === 'keyboard') {
            indicatorList.classList.add('keyboard-mode')

            // Restore visual highlight at current index when entering keyboard mode
            if (this.highlightedIndex >= 0) {
                this.highlightSelectedIndex()
            }
        } else {
            // Mouse mode: remove keyboard-mode class and clear visual keyboard highlights
            indicatorList.classList.remove('keyboard-mode')

            // Remove keyboard highlighting from all options (visual only)
            const items = indicatorList.querySelectorAll('.dataset-option.keyboard-highlighted')
            items.forEach(item => item.classList.remove('keyboard-highlighted'))

            // Keep highlightedIndex - don't reset it!
            // This allows returning to the same position when switching back to keyboard mode
        }
    }
}