class IndicatorSelectionMenu {
    constructor(options = {}) {
        this.options = {
            onCreateNew: null,
            onAddExisting: null,
            ...options
        }
        
        this.modal = null
    }
    
    show(indicatorsContainer) {
        this.indicatorsContainer = indicatorsContainer
        this.createModal()
        this.bindEvents()
        document.body.appendChild(this.modal)

        // Auto-focus the first button for keyboard navigation
        setTimeout(() => {
            const createNewBtn = this.modal?.querySelector('#create-new-indicator')
            if (createNewBtn) {
                createNewBtn.focus()
            }
        }, 100)
    }
    
    createModal() {
        this.modal = document.createElement('div')
        this.modal.className = 'indicator-selection-overlay'
        
        const modalContent = document.createElement('div')
        modalContent.className = 'indicator-selection-content'
        
        modalContent.innerHTML = `
            <div class="indicator-selection-header">
                <h3>Add Indicator</h3>
                <p>Choose how you'd like to add an indicator to this category:</p>
            </div>
            <div class="indicator-selection-options">
                <button id="create-new-indicator" class="indicator-option-btn create-new">
                    <div class="option-icon">+</div>
                    <div class="option-text">
                        <div class="option-title">Create New Indicator</div>
                        <div class="option-description">Start with a blank indicator and customize it</div>
                    </div>
                </button>
                <button id="add-existing-indicator" class="indicator-option-btn add-existing">
                    <div class="option-icon">📋</div>
                    <div class="option-text">
                        <div class="option-title">Add Existing Indicator</div>
                        <div class="option-description">Choose from the SSPI indicator library</div>
                    </div>
                </button>
            </div>
            <div class="indicator-selection-actions">
                <button id="menu-cancel" class="cancel-btn">Cancel</button>
            </div>
        `
        
        this.modal.appendChild(modalContent)
    }
    
    bindEvents() {
        if (!this.modal) return
        
        const createNewBtn = this.modal.querySelector('#create-new-indicator')
        const addExistingBtn = this.modal.querySelector('#add-existing-indicator')
        const cancelBtn = this.modal.querySelector('#menu-cancel')
        
        if (createNewBtn) {
            createNewBtn.addEventListener('click', () => {
                this.close()
                if (this.options.onCreateNew) {
                    this.options.onCreateNew(this.indicatorsContainer)
                }
            })
        }
        
        if (addExistingBtn) {
            addExistingBtn.addEventListener('click', () => {
                this.close()
                if (this.options.onAddExisting) {
                    this.options.onAddExisting(this.indicatorsContainer)
                }
            })
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.close()
            })
        }
        
        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close()
            }
        })
        
        // Close on escape key and handle keyboard navigation
        this.keydownHandler = this.handleKeyDown.bind(this)
        document.addEventListener('keydown', this.keydownHandler)
    }

    handleKeyDown(e) {
        if (!this.modal) return

        if (e.key === 'Escape') {
            e.preventDefault()
            this.close()
            return
        }

        // Arrow key navigation between buttons
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault()
            const createNewBtn = this.modal.querySelector('#create-new-indicator')
            const addExistingBtn = this.modal.querySelector('#add-existing-indicator')
            const cancelBtn = this.modal.querySelector('#menu-cancel')

            const focusedElement = document.activeElement

            if (e.key === 'ArrowDown') {
                if (focusedElement === createNewBtn) {
                    addExistingBtn?.focus()
                } else if (focusedElement === addExistingBtn) {
                    cancelBtn?.focus()
                } else {
                    createNewBtn?.focus()
                }
            } else { // ArrowUp
                if (focusedElement === cancelBtn) {
                    addExistingBtn?.focus()
                } else if (focusedElement === addExistingBtn) {
                    createNewBtn?.focus()
                } else {
                    cancelBtn?.focus()
                }
            }
        }
    }
    
    close() {
        if (this.modal && this.modal.parentNode) {
            document.body.removeChild(this.modal)
        }
        if (this.keydownHandler) {
            document.removeEventListener('keydown', this.keydownHandler)
            this.keydownHandler = null
        }
        this.modal = null
    }
}
