class DownloadForm {
    constructor(formElement) {
        this.form = formElement;
        this.databaseCapabilities = this.loadDatabaseCapabilities();
        this.initializeEventListeners();
    }

    loadDatabaseCapabilities() {
        // Load database capabilities from the select options
        const dbSelect = this.form.querySelector('#database-select');
        const capabilities = {};

        if (dbSelect) {
            Array.from(dbSelect.options).forEach(option => {
                const supports = option.dataset.supports;
                capabilities[option.value] = supports ? supports.split(',') : [];
            });
        }

        return capabilities;
    }

    initializeEventListeners() {
        // Database selection change listener
        const dbSelect = this.form.querySelector('#database-select');
        if (dbSelect) {
            dbSelect.addEventListener('change', () => this.handleDatabaseChange());
            // Trigger initial update
            this.handleDatabaseChange();
        }

        // Country type toggle listeners
        const countryTypeRadios = this.form.querySelectorAll('input[name="country-type"]');
        countryTypeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => this.handleCountryTypeChange(e));
        });

        // Initialize country section visibility based on current radio state
        this.initializeCountrySelection();

        // Download button listeners
        const csvBtn = this.form.querySelector('.csv-btn');
        const jsonBtn = this.form.querySelector('.json-btn');

        if (csvBtn) {
            csvBtn.addEventListener('click', () => this.downloadData('csv'));
        }

        if (jsonBtn) {
            jsonBtn.addEventListener('click', () => this.downloadData('json'));
        }
    }

    initializeCountrySelection() {
        // Check which radio button is currently selected and show the appropriate section
        const checkedRadio = this.form.querySelector('input[name="country-type"]:checked');
        if (checkedRadio) {
            this.handleCountryTypeChange({ target: checkedRadio });
        }
    }

    handleDatabaseChange() {
        const dbSelect = this.form.querySelector('#database-select');
        if (!dbSelect) return;

        const selectedDb = dbSelect.value;
        const supports = this.databaseCapabilities[selectedDb] || [];

        // Show/hide indicators section
        const indicatorsSection = this.form.querySelector('.form-section:has(.hierarchical-selector-container)');
        const supportsSeriesCode = supports.includes('SeriesCode');

        if (indicatorsSection) {
            if (supportsSeriesCode) {
                indicatorsSection.style.display = 'block';
                indicatorsSection.classList.remove('disabled-section');
            } else {
                indicatorsSection.style.display = 'none';
                indicatorsSection.classList.add('disabled-section');
            }
        }

        // Show/hide countries section
        const countriesSection = this.form.querySelector('#countries-section');
        const supportsCountries = supports.includes('CountryCode') || supports.includes('CountryGroup');

        if (countriesSection) {
            if (supportsCountries) {
                countriesSection.style.display = 'block';
                countriesSection.classList.remove('disabled-section');
            } else {
                countriesSection.style.display = 'none';
                countriesSection.classList.add('disabled-section');
                // Clear country selections
                this.clearCountrySelections();
            }
        }

        // Show/hide years section
        const yearsSection = this.form.querySelector('#years-section');
        const supportsYears = supports.includes('Year') || supports.includes('timePeriod');

        if (yearsSection) {
            if (supportsYears) {
                yearsSection.style.display = 'block';
                yearsSection.classList.remove('disabled-section');
            } else {
                yearsSection.style.display = 'none';
                yearsSection.classList.add('disabled-section');
                // Clear year selections
                this.clearYearSelections();
            }
        }

        // Disable CSV button for raw API data and metadata
        const csvBtn = this.form.querySelector('.csv-btn');
        if (csvBtn) {
            if (selectedDb === 'sspi_raw_api_data' || selectedDb === 'sspi_metadata') {
                csvBtn.disabled = true;
                csvBtn.title = selectedDb === 'sspi_metadata'
                    ? 'CSV format not available for metadata'
                    : 'CSV format not available for raw API data';
            } else {
                csvBtn.disabled = false;
                csvBtn.title = '';
            }
        }
    }

    clearCountrySelections() {
        // Clear country radio buttons
        const countryRadios = this.form.querySelectorAll('input[name="country-type"]');
        countryRadios.forEach(radio => radio.checked = false);

        // Clear country checkboxes
        const countryCheckboxes = this.form.querySelectorAll('input[name="CountryCode"]');
        countryCheckboxes.forEach(checkbox => checkbox.checked = false);

        // Clear country group checkboxes
        const groupCheckboxes = this.form.querySelectorAll('input[name="CountryGroup"]');
        groupCheckboxes.forEach(checkbox => checkbox.checked = false);
    }

    clearYearSelections() {
        const yearCheckboxes = this.form.querySelectorAll('input[name="Year"]');
        yearCheckboxes.forEach(checkbox => checkbox.checked = false);
    }

    handleCountryTypeChange(event) {
        const individualSection = document.getElementById('individual-countries');
        const groupSection = document.getElementById('country-groups');
        const countrySelect = document.getElementById('country-select');
        const groupSelect = document.getElementById('country-group-select');

        if (event.target.value === 'individual') {
            individualSection.style.display = 'block';
            groupSection.style.display = 'none';
            // Clear group selection
            if (groupSelect) {
                groupSelect.value = '';
            }
        } else {
            individualSection.style.display = 'none';
            groupSection.style.display = 'block';
            // Clear individual country selections
            if (countrySelect) {
                Array.from(countrySelect.options).forEach(option => {
                    option.selected = false;
                });
            }
        }
    }

    buildQueryParams() {
        const formData = new FormData(this.form);
        const params = new URLSearchParams();
        
        // Add database
        const database = formData.get('database');
        if (database) {
            params.append('database', database);
        }
        
        // Add series codes - get from hierarchical selector if available, fallback to form data
        // SeriesCode is the universal parameter that works for all item types:
        // SSPI, Pillars, Categories, Indicators, and Datasets
        let seriesCodes = [];
        if (window.hierarchicalSelector) {
            seriesCodes = window.hierarchicalSelector.getSelectedCodes();
        } else {
            // Fallback to traditional form data
            seriesCodes = formData.getAll('SeriesCode') || formData.getAll('IndicatorCode');
        }

        seriesCodes.forEach(code => {
            if (code) {
                params.append('SeriesCode', code);
            }
        });
        
        // Add countries or country group
        const countryType = this.form.querySelector('input[name="country-type"]:checked');
        if (countryType && countryType.value === 'individual') {
            const countries = formData.getAll('CountryCode');
            countries.forEach(country => {
                if (country) {
                    params.append('CountryCode', country);
                }
            });
        } else {
            const countryGroup = formData.get('CountryGroup');
            if (countryGroup) {
                params.append('CountryGroup', countryGroup);
            }
        }
        
        // Add years
        const years = formData.getAll('Year');
        years.forEach(year => {
            if (year) {
                params.append('Year', year);
            }
        });
        
        return params;
    }

    async downloadData(format) {
        // Validate form before download
        if (!this.validateForm()) {
            return;
        }

        // Clear any previous error messages
        this.clearErrorMessage();

        // Show loading state
        this.setLoadingState(true, format);

        const params = this.buildQueryParams();
        const downloadUrl = `/api/v1/download/${format}?${params.toString()}`;

        try {
            const response = await fetch(downloadUrl);

            if (!response.ok) {
                // Handle error response
                const errorData = await response.json();
                const errorMessage = errorData.error || 'Download failed. Please try again.';
                this.showErrorMessage(errorMessage);
                this.setLoadingState(false, format);
                return;
            }

            // Handle successful download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;

            // Generate filename with current date and database name
            const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
            const formData = new FormData(this.form);
            const databaseName = formData.get('database') || 'sspi_data';
            a.download = `${today} - ${databaseName}.${format}`;

            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            // Show success message
            this.showSuccessMessage('Download started successfully!');
            this.setLoadingState(false, format);

        } catch (error) {
            console.error('Download error:', error);
            this.showErrorMessage('Network error: Unable to download data. Please check your connection and try again.');
            this.setLoadingState(false, format);
        }
    }

    showErrorMessage(message) {
        const errorContainer = this.getOrCreateMessageContainer();
        errorContainer.className = 'download-message error-message';
        errorContainer.innerHTML = `
            <span class="message-content"><strong>Error:</strong> ${message}</span>
            <button class="close-message" onclick="this.parentElement.remove()">×</button>
        `;
        errorContainer.style.display = 'flex';

        // Scroll to error message
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    showSuccessMessage(message) {
        const messageContainer = this.getOrCreateMessageContainer();
        messageContainer.className = 'download-message success-message';
        messageContainer.innerHTML = `
            <span class="message-content"><strong>Success:</strong> ${message}</span>
            <button class="close-message" onclick="this.parentElement.remove()">×</button>
        `;
        messageContainer.style.display = 'flex';

        // Auto-hide success message after 5 seconds
        setTimeout(() => {
            messageContainer.remove();
        }, 5000);
    }

    clearErrorMessage() {
        const existingMessage = this.form.querySelector('.download-message');
        if (existingMessage) {
            existingMessage.remove();
        }
    }

    getOrCreateMessageContainer() {
        let container = this.form.querySelector('.download-message');
        if (!container) {
            container = document.createElement('div');
            container.className = 'download-message';
            // Insert at the top of the form
            this.form.insertBefore(container, this.form.firstChild);
        }
        return container;
    }

    setLoadingState(isLoading, format) {
        const csvBtn = this.form.querySelector('.csv-btn');
        const jsonBtn = this.form.querySelector('.json-btn');

        if (isLoading) {
            if (format === 'csv' && csvBtn) {
                csvBtn.disabled = true;
                csvBtn.dataset.originalText = csvBtn.textContent;
                csvBtn.textContent = 'Downloading...';
            } else if (format === 'json' && jsonBtn) {
                jsonBtn.disabled = true;
                jsonBtn.dataset.originalText = jsonBtn.textContent;
                jsonBtn.textContent = 'Downloading...';
            }
        } else {
            if (csvBtn) {
                csvBtn.disabled = false;
                if (csvBtn.dataset.originalText) {
                    csvBtn.textContent = csvBtn.dataset.originalText;
                }
            }
            if (jsonBtn) {
                jsonBtn.disabled = false;
                if (jsonBtn.dataset.originalText) {
                    jsonBtn.textContent = jsonBtn.dataset.originalText;
                }
            }
        }
    }

    // Helper method to clear all selections
    clearSelections() {
        // Clear all select elements
        const selects = this.form.querySelectorAll('select');
        selects.forEach(select => {
            if (select.multiple) {
                Array.from(select.options).forEach(option => {
                    option.selected = false;
                });
            } else {
                select.selectedIndex = 0;
            }
        });
        
        // Reset to individual countries
        const individualRadio = this.form.querySelector('input[name="country-type"][value="individual"]');
        if (individualRadio) {
            individualRadio.checked = true;
            this.handleCountryTypeChange({ target: individualRadio });
        }
    }

    // Method to validate form before download
    validateForm() {
        const params = this.buildQueryParams();
        const formData = new FormData(this.form);
        const selectedDb = formData.get('database');

        // Skip validation for metadata - it downloads the entire collection without filters
        if (selectedDb === 'sspi_metadata') {
            return true;
        }

        // Check for series code selection (indicators, categories, pillars, or datasets)
        let hasSeriesCodes = false;
        if (window.hierarchicalSelector) {
            hasSeriesCodes = window.hierarchicalSelector.getSelectedCodes().length > 0;
        } else {
            const codes = formData.getAll('SeriesCode') || formData.getAll('IndicatorCode');
            hasSeriesCodes = codes.some(code => code);
        }

        if (!hasSeriesCodes) {
            alert('Please select at least one indicator, category, pillar, or dataset before downloading.');
            return false;
        }

        return true;
    }
}
