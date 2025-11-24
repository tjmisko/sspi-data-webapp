/**
 * SearchableDropdown - A custom dropdown component with search functionality
 *
 * Features:
 * - Keyboard-navigable search input
 * - Grouped options (optgroups)
 * - Filters options in real-time
 * - Maintains visual consistency with site theme
 * - Accessible keyboard navigation
 */
class SearchableDropdown {
    constructor(selectElement, options = {}) {
        this.originalSelect = selectElement;
        this.options = {
            placeholder: options.placeholder || 'Search...',
            onChange: options.onChange || (() => {}),
            ...options
        };

        // Parse options from original select element
        this.parseOptions();

        // Create custom dropdown elements
        this.createDropdown();

        // Initialize state
        this.isOpen = false;
        this.selectedValue = this.originalSelect.value;
        this.selectedLabel = this.getSelectedLabel();
        this.filteredOptions = [...this.allOptions];
        this.highlightedIndex = -1;

        // Bind events
        this.bindEvents();

        // Hide original select
        this.originalSelect.style.display = 'none';

        // Insert custom dropdown after original select
        this.originalSelect.parentNode.insertBefore(this.container, this.originalSelect.nextSibling);

        // Update display
        this.updateSelectedDisplay();
    }

    parseOptions() {
        this.groups = [];
        this.allOptions = [];

        // Parse optgroups and options
        const children = Array.from(this.originalSelect.children);

        children.forEach(child => {
            if (child.tagName === 'OPTGROUP') {
                const groupLabel = child.label;
                const groupOptions = Array.from(child.children).map(option => ({
                    value: option.value,
                    label: option.textContent,
                    group: groupLabel,
                    selected: option.selected
                }));

                this.groups.push({
                    label: groupLabel,
                    options: groupOptions
                });

                this.allOptions.push(...groupOptions);
            } else if (child.tagName === 'OPTION') {
                const option = {
                    value: child.value,
                    label: child.textContent,
                    group: null,
                    selected: child.selected
                };

                // Only add non-placeholder options
                if (child.value) {
                    this.allOptions.push(option);
                }
            }
        });
    }

    createDropdown() {
        // Main container
        this.container = document.createElement('div');
        this.container.className = 'searchable-dropdown';

        // Selected value display
        this.selectedDisplay = document.createElement('div');
        this.selectedDisplay.className = 'searchable-dropdown-selected';
        this.selectedDisplay.innerHTML = `
            <span class="searchable-dropdown-label"></span>
            <svg class="searchable-dropdown-arrow" width="12" height="12" viewBox="0 0 12 12">
                <path d="M2 4 L6 8 L10 4" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>
            </svg>
        `;
        this.container.appendChild(this.selectedDisplay);

        // Dropdown panel
        this.panel = document.createElement('div');
        this.panel.className = 'searchable-dropdown-panel';

        // Search input
        this.searchInput = document.createElement('input');
        this.searchInput.type = 'text';
        this.searchInput.className = 'searchable-dropdown-search';
        this.searchInput.placeholder = this.options.placeholder;
        this.panel.appendChild(this.searchInput);

        // Options list
        this.optionsList = document.createElement('div');
        this.optionsList.className = 'searchable-dropdown-options';
        this.panel.appendChild(this.optionsList);

        this.container.appendChild(this.panel);
    }

    bindEvents() {
        // Toggle dropdown
        this.selectedDisplay.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });

        // Search input
        this.searchInput.addEventListener('input', (e) => {
            this.filterOptions(e.target.value);
        });

        this.searchInput.addEventListener('keydown', (e) => {
            this.handleKeyDown(e);
        });

        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.close();
            }
        });

        // Option selection
        this.optionsList.addEventListener('click', (e) => {
            const optionEl = e.target.closest('.searchable-dropdown-option');
            if (optionEl) {
                const value = optionEl.dataset.value;
                this.selectOption(value);
            }
        });
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        this.isOpen = true;
        this.container.classList.add('is-open');
        this.searchInput.value = '';
        this.filterOptions('');
        this.searchInput.focus();
        this.highlightedIndex = -1;
    }

    close() {
        this.isOpen = false;
        this.container.classList.remove('is-open');
        this.highlightedIndex = -1;
    }

    filterOptions(query) {
        const lowerQuery = query.toLowerCase();

        if (!query) {
            this.filteredOptions = [...this.allOptions];
        } else {
            this.filteredOptions = this.allOptions.filter(option => {
                return option.label.toLowerCase().includes(lowerQuery) ||
                       option.value.toLowerCase().includes(lowerQuery);
            });
        }

        this.renderOptions();
        this.highlightedIndex = -1;
    }

    renderOptions() {
        this.optionsList.innerHTML = '';

        if (this.filteredOptions.length === 0) {
            this.optionsList.innerHTML = '<div class="searchable-dropdown-no-results">No results found</div>';
            return;
        }

        // Group options by category
        const grouped = {};
        this.filteredOptions.forEach(option => {
            const group = option.group || 'Other';
            if (!grouped[group]) {
                grouped[group] = [];
            }
            grouped[group].push(option);
        });

        // Render grouped options
        Object.entries(grouped).forEach(([groupLabel, options]) => {
            const groupEl = document.createElement('div');
            groupEl.className = 'searchable-dropdown-group';

            const groupLabelEl = document.createElement('div');
            groupLabelEl.className = 'searchable-dropdown-group-label';
            groupLabelEl.textContent = groupLabel;
            groupEl.appendChild(groupLabelEl);

            options.forEach(option => {
                const optionEl = document.createElement('div');
                optionEl.className = 'searchable-dropdown-option';
                optionEl.dataset.value = option.value;

                if (option.value === this.selectedValue) {
                    optionEl.classList.add('is-selected');
                }

                optionEl.textContent = option.label;
                groupEl.appendChild(optionEl);
            });

            this.optionsList.appendChild(groupEl);
        });
    }

    selectOption(value) {
        // Update original select
        this.originalSelect.value = value;

        // Update state
        this.selectedValue = value;
        this.selectedLabel = this.getSelectedLabel();

        // Update display
        this.updateSelectedDisplay();

        // Close dropdown
        this.close();

        // Trigger change event on original select
        const event = new Event('change', { bubbles: true });
        this.originalSelect.dispatchEvent(event);

        // Call onChange callback
        this.options.onChange(value);
    }

    getSelectedLabel() {
        const option = this.allOptions.find(opt => opt.value === this.selectedValue);
        return option ? option.label : (this.originalSelect.querySelector('option[value=""]')?.textContent || 'Select...');
    }

    updateSelectedDisplay() {
        const label = this.container.querySelector('.searchable-dropdown-label');
        label.textContent = this.selectedLabel;

        if (!this.selectedValue) {
            label.classList.add('is-placeholder');
        } else {
            label.classList.remove('is-placeholder');
        }
    }

    handleKeyDown(e) {
        const options = Array.from(this.optionsList.querySelectorAll('.searchable-dropdown-option'));

        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.highlightedIndex = Math.min(this.highlightedIndex + 1, options.length - 1);
                this.updateHighlight(options);
                break;

            case 'ArrowUp':
                e.preventDefault();
                this.highlightedIndex = Math.max(this.highlightedIndex - 1, 0);
                this.updateHighlight(options);
                break;

            case 'Enter':
                e.preventDefault();
                if (this.highlightedIndex >= 0 && options[this.highlightedIndex]) {
                    const value = options[this.highlightedIndex].dataset.value;
                    this.selectOption(value);
                }
                break;

            case 'Escape':
                e.preventDefault();
                this.close();
                break;
        }
    }

    updateHighlight(options) {
        options.forEach((option, index) => {
            if (index === this.highlightedIndex) {
                option.classList.add('is-highlighted');
                option.scrollIntoView({ block: 'nearest' });
            } else {
                option.classList.remove('is-highlighted');
            }
        });
    }

    // Public API
    getValue() {
        return this.selectedValue;
    }

    setValue(value) {
        this.selectOption(value);
    }

    destroy() {
        this.container.remove();
        this.originalSelect.style.display = '';
    }
}
