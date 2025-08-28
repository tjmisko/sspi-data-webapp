class DownloadForm {
    constructor(formElement) {
        this.form = formElement;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Country type toggle listeners
        const countryTypeRadios = this.form.querySelectorAll('input[name="country-type"]');
        countryTypeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => this.handleCountryTypeChange(e));
        });

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
        
        // Add indicators - get from hierarchical selector if available, fallback to form data
        let indicators = [];
        if (window.hierarchicalSelector) {
            indicators = window.hierarchicalSelector.getSelectedCodes();
        } else {
            // Fallback to traditional form data
            indicators = formData.getAll('IndicatorCode');
        }
        
        indicators.forEach(indicator => {
            if (indicator) {
                params.append('IndicatorCode', indicator);
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

    downloadData(format) {
        // Validate form before download
        if (!this.validateForm()) {
            return;
        }
        
        const params = this.buildQueryParams();
        const downloadUrl = `/api/v1/download/${format}?${params.toString()}`;
        
        // Trigger download
        window.location.href = downloadUrl;
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
        
        // Check for indicator selection
        let hasIndicators = false;
        if (window.hierarchicalSelector) {
            hasIndicators = window.hierarchicalSelector.getSelectedCodes().length > 0;
        } else {
            const formData = new FormData(this.form);
            hasIndicators = formData.getAll('IndicatorCode').some(code => code);
        }
        
        if (!hasIndicators) {
            alert('Please select at least one indicator, category, or pillar before downloading.');
            return false;
        }
        
        return true;
    }
}