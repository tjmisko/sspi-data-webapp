class CountryRankingsPanel {
    constructor(parentElement, countryCode, itemLevel, options = {}) {
        this.parentElement = parentElement;
        this.countryCode = countryCode;
        this.itemLevel = itemLevel;
        this.options = options;
        this.data = null;
        this.selectedTimePeriod = null;
        this.totalCountries = null;

        this.init();
    }

    async init() {
        await this.fetchData();
        this.render();
    }

    async fetchData() {
        try {
            const response = await fetch(`/api/v1/country/rankings/${this.countryCode}/${this.itemLevel}`);
            if (!response.ok) {
                throw new Error(`HTTP\u0020error!\u0020status:\u0020${response.status}`);
            }
            const result = await response.json();
            this.data = result;
            this.totalCountries = result.totalCountries || 67; // Default to 67 if not provided

            // Set default to Overall (2000-2023) if available
            if (this.data.timePeriods) {
                if (this.data.timePeriods['Overall'] && this.data.timePeriods['Overall'].length > 0) {
                    this.selectedTimePeriod = this.data.timePeriods['Overall'][0]; // Overall period (2000-2023)
                } else if (this.data.timePeriods['Single Year']) {
                    const years = this.data.timePeriods['Single Year'];
                    this.selectedTimePeriod = years[years.length - 1]; // Fallback to most recent year
                } else {
                    // Fallback to first available period
                    const firstType = Object.keys(this.data.timePeriods)[0];
                    this.selectedTimePeriod = this.data.timePeriods[firstType][0];
                }
            }
        } catch (error) {
            console.error('Error fetching rankings data:', error);
            this.renderError(error.message);
        }
    }

    render() {
        if (!this.data) {
            return;
        }
        // Build dropdown options with optgroups
        const dropdownHTML = this.buildDropdownOptions();

        // Determine if current period is single year
        const isSingleYear = this.isSingleYearPeriod(this.selectedTimePeriod);
        const layoutClass = isSingleYear ? 'single-year' : 'intervals';

        this.parentElement.innerHTML = `
            <div class="rankings-panel">
                <div class="rankings-panel-header">
                    <h3>Time Period</h3>
                    <select class="time-period-selector">
                        ${dropdownHTML}
                    </select>
                </div>
                <!-- Absolute Performance Section -->
                <div class="rankings-section">
                    <div class="rankings-section-header">
                        <h4>Absolute Indicator Performance\u0020(Score-Based)</h4>
                        <p class="rankings-section-description">Policy indicators of note when comparing with the set of all indicators for ${this.countryCode}.</p>
                    </div>
                    <div class="rankings-panel-content ${layoutClass}">
                        <div class="rankings-column">
                            <h5>Highest Scores</h5>
                            <div class="rankings-cards" id="absolute-highest-cards"></div>
                        </div>
                        <div class="rankings-column">
                            <h5>Lowest Scores</h5>
                            <div class="rankings-cards" id="absolute-lowest-cards"></div>
                        </div>
                        ${!isSingleYear ? `
                        <div class="rankings-column">
                            <h5>Most Improved Scores</h5>
                            <div class="rankings-cards" id="absolute-improved-cards"></div>
                        </div>
                        <div class="rankings-column">
                            <h5>Biggest Score Declines</h5>
                            <div class="rankings-cards" id="absolute-declined-cards"></div>
                        </div>
                        ` : ''}
                    </div>
                </div>

                <!-- Relative Performance Section -->
                <div class="rankings-section">
                    <div class="rankings-section-header">
                        <h4>Relative Indicator Performance (Rank-Based)</h4>
                        <p class="rankings-section-description">Policy indicators on which ${this.countryCode} ranks best/worst compared to other countries.</p>
                    </div>
                    <div class="rankings-panel-content ${layoutClass}">
                        <div class="rankings-column">
                            <h5>Best Ranks</h5>
                            <div class="rankings-cards" id="relative-strongest-cards"></div>
                        </div>
                        <div class="rankings-column">
                            <h5>Worst Ranks</h5>
                            <div class="rankings-cards" id="relative-weakest-cards"></div>
                        </div>
                        ${!isSingleYear ? `
                        <div class="rankings-column">
                            <h5>Most Improved Ranks</h5>
                            <div class="rankings-cards" id="relative-improved-cards"></div>
                        </div>
                        <div class="rankings-column">
                            <h5>Biggest Rank Declines</h5>
                            <div class="rankings-cards" id="relative-declined-cards"></div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;

        // Attach event listener to time period selector
        const selector = this.parentElement.querySelector('.time-period-selector');
        selector.addEventListener('change', (e) => {
            this.selectedTimePeriod = e.target.value;
            this.render(); // Re-render entire panel to handle layout changes
        });

        this.updateCards();
    }

    buildDropdownOptions() {
        if (!this.data.timePeriods) {
            return '<option>No time periods available</option>';
        }

        const typeOrder = ['Overall', 'Year-to-Present', 'Ten Year Interval', 'Five Year Interval', 'Single Year'];
        let html = '';

        for (const type of typeOrder) {
            if (this.data.timePeriods[type]) {
                const periods = this.data.timePeriods[type];
                html += `<optgroup label="${type}">`;

                // Reverse order for Single Year to show most recent first
                const orderedPeriods = type === 'Single Year' ? [...periods].reverse() : periods;

                for (const period of orderedPeriods) {
                    const selected = period === this.selectedTimePeriod ? 'selected' : '';
                    html += `<option value="${period}" ${selected}>${period}</option>`;
                }
                html += '</optgroup>';
            }
        }

        return html;
    }

    isSingleYearPeriod(period) {
        // Check if the period is in the Single Year list
        return this.data.timePeriods['Single Year'] &&
               this.data.timePeriods['Single Year'].includes(period);
    }

    updateCards() {
        const filteredData = this.filterDataByTimePeriod(this.selectedTimePeriod);
        const isSingleYear = this.isSingleYearPeriod(this.selectedTimePeriod);

        // ABSOLUTE PERFORMANCE (Score-based)
        const highestScores = this.getHighestScores(filteredData, 5);
        const lowestScores = this.getLowestScores(filteredData, 5);

        // Render absolute performance cards
        this.renderCards('absolute-highest-cards', highestScores, 'absolute-high');
        this.renderCards('absolute-lowest-cards', lowestScores, 'absolute-low');

        if (!isSingleYear) {
            // Only show change columns for intervals
            const mostImprovedScores = this.getMostImprovedScores(filteredData, 5);
            const biggestScoreDeclines = this.getBiggestScoreDeclines(filteredData, 5);
            this.renderCards('absolute-improved-cards', mostImprovedScores, 'absolute-improved');
            this.renderCards('absolute-declined-cards', biggestScoreDeclines, 'absolute-declined');
        }

        // RELATIVE PERFORMANCE (Rank-based)
        const bestRanks = this.getBestRanks(filteredData, 5);
        const worstRanks = this.getWorstRanks(filteredData, 5);

        // Render relative performance cards
        this.renderCards('relative-strongest-cards', bestRanks, 'relative-strong');
        this.renderCards('relative-weakest-cards', worstRanks, 'relative-weak');

        if (!isSingleYear) {
            // Only show change columns for intervals
            const mostImprovedRanks = this.getMostImprovedRanks(filteredData, 5);
            const biggestRankDeclines = this.getBiggestRankDeclines(filteredData, 5);
            this.renderCards('relative-improved-cards', mostImprovedRanks, 'relative-improved');
            this.renderCards('relative-declined-cards', biggestRankDeclines, 'relative-declined');
        }
    }

    filterDataByTimePeriod(timePeriod) {
        return this.data.data.filter(d => d.TimePeriod === timePeriod);
    }

    // ABSOLUTE PERFORMANCE METHODS (Score-based)
    getHighestScores(data, limit) {
        // Higher scores are better
        return data
            .map(d => ({
                ...d,
                sortValue: this.getScoreValue(d, 'avg')
            }))
            .filter(d => d.sortValue !== null)
            .sort((a, b) => b.sortValue - a.sortValue) // Descending
            .slice(0, limit);
    }

    getLowestScores(data, limit) {
        // Lower scores are worse
        return data
            .map(d => ({
                ...d,
                sortValue: this.getScoreValue(d, 'avg')
            }))
            .filter(d => d.sortValue !== null)
            .sort((a, b) => a.sortValue - b.sortValue) // Ascending
            .slice(0, limit);
    }

    getMostImprovedScores(data, limit) {
        // Positive score change is improvement
        return data
            .map(d => ({
                ...d,
                sortValue: this.getScoreValue(d, 'chg')
            }))
            .filter(d => d.sortValue !== null && d.sortValue > 0)
            .sort((a, b) => b.sortValue - a.sortValue) // Descending
            .slice(0, limit);
    }

    getBiggestScoreDeclines(data, limit) {
        // Negative score change is decline
        return data
            .map(d => ({
                ...d,
                sortValue: this.getScoreValue(d, 'chg')
            }))
            .filter(d => d.sortValue !== null && d.sortValue < 0)
            .sort((a, b) => a.sortValue - b.sortValue) // Ascending (most negative first)
            .slice(0, limit);
    }

    // RELATIVE PERFORMANCE METHODS (Rank-based)
    getBestRanks(data, limit) {
        // Lower rank numbers are better
        return data
            .map(d => ({
                ...d,
                sortValue: this.getRankValue(d, 'avg')
            }))
            .filter(d => d.sortValue !== null)
            .sort((a, b) => a.sortValue - b.sortValue) // Ascending
            .slice(0, limit);
    }

    getWorstRanks(data, limit) {
        // Higher rank numbers are worse
        return data
            .map(d => ({
                ...d,
                sortValue: this.getRankValue(d, 'avg')
            }))
            .filter(d => d.sortValue !== null)
            .sort((a, b) => b.sortValue - a.sortValue) // Descending
            .slice(0, limit);
    }

    getMostImprovedRanks(data, limit) {
        // Positive rank change means improvement (moving from higher to lower rank number)
        return data
            .map(d => ({
                ...d,
                sortValue: this.getRankValue(d, 'chg')
            }))
            .filter(d => d.sortValue !== null && d.sortValue > 0)
            .sort((a, b) => b.sortValue - a.sortValue) // Descending
            .slice(0, limit);
    }

    getBiggestRankDeclines(data, limit) {
        // Negative rank change means decline (moving from lower to higher rank number)
        return data
            .map(d => ({
                ...d,
                sortValue: this.getRankValue(d, 'chg')
            }))
            .filter(d => d.sortValue !== null && d.sortValue < 0)
            .sort((a, b) => a.sortValue - b.sortValue) // Ascending (most negative first)
            .slice(0, limit);
    }

    // HELPER METHODS
    getRankValue(item, metric) {
        // Handle both Single Year (direct Rank) and intervals (Ranks object)
        if (item.TimePeriodType === 'Single Year') {
            return metric === 'avg' ? item.Rank : null;
        } else {
            return item.Ranks ? item.Ranks[metric] : null;
        }
    }

    getScoreValue(item, metric) {
        // Handle both Single Year (direct Score) and intervals (Scores object)
        if (item.TimePeriodType === 'Single Year') {
            return metric === 'avg' ? item.Score : null;
        } else {
            return item.Scores ? item.Scores[metric] : null;
        }
    }

    renderCards(containerId, items, type) {
        const container = this.parentElement.querySelector(`#${containerId}`);

        if (!container) {
            return; // Container doesn't exist (e.g., change columns hidden for single year)
        }

        if (!items || items.length === 0) {
            container.innerHTML = '<div class="no-data-message">No data available</div>';
            return;
        }

        container.innerHTML = items.map(item => this.createCard(item, type)).join('');

        // Add click event listeners only to non-single-year cards
        // Single year periods don't have time series data to visualize
        const isSingleYear = items.length > 0 && this.isSingleYearPeriod(items[0].TimePeriod);

        if (!isSingleYear) {
            container.querySelectorAll('.ranking-card').forEach(card => {
                card.style.cursor = 'pointer';
                card.addEventListener('click', (e) => {
                    this.showPreviewModal(card);
                });
            });
        }
    }

    createCard(item, type) {
        const rank = this.getRankValue(item, 'avg');
        const score = this.getScoreValue(item, 'avg');
        const scoreChange = this.getScoreValue(item, 'chg');
        const rankChange = this.getRankValue(item, 'chg');
        // Determine if this is an absolute or relative card, and if it's a change card
        const isAbsolute = type.startsWith('absolute');
        const isChangeCard = type.includes('improved') || type.includes('declined');
        const change = isAbsolute ? scoreChange : rankChange;
        let changeHtml = '';
        // Only show change metric for improved/declined columns
        if (isChangeCard && change !== null && change !== undefined) {
            const changeSign = change > 0 ? '+' : '';
            const changeClass = change > 0 ? 'positive-change' : 'negative-change';
            changeHtml = `<span class="rank-change ${changeClass}">${changeSign}${change.toFixed(isAbsolute ? 3 : 0)}</span>`;
        }
        return `
            <div class="ranking-card ${type}" data-item-code="${item.ItemCode}" data-time-period="${item.TimePeriod}" data-item-name="${item.ItemName || item.ItemCode}">
                <div class="card-header">
                    <span class="item-name">${item.ItemName || item.ItemCode}</span>
                    ${rank ? `<span class="rank-badge">#\u0020${rank}\u0020/\u0020${this.totalCountries}</span>` : ''}
                </div>
                <div class="card-body">
                    <div class="score-row">
                        <span class="score-display">Score:\u0020${score !== null ? score.toFixed(3) : 'N/A'}</span>
                        ${changeHtml}
                    </div>
                </div>
                <div class="card-footer">
                    <span class="time-period">${item.TimePeriod}</span>
                </div>
            </div>
        `;
    }

    renderError(message) {
        this.parentElement.innerHTML = `
            <div class="rankings-panel-error">
                <p>Error\u0020loading\u0020rankings\u0020data:\u0020${message}</p>
            </div>
        `;
    }

    /**
     * Parse time period string to extract start and end years
     * Examples: "2000-2023", "2020-2025", "2015", "2010-2015", "2005-2010"
     * @param {string} timePeriod - The time period string
     * @returns {{startYear: number, endYear: number}} Object with startYear and endYear
     */
    parseTimePeriod(timePeriod) {
        if (!timePeriod) {
            return { startYear: 2000, endYear: 2023 }; // Default fallback
        }

        // Match pattern like "2000-2023" or "2015"
        const match = timePeriod.match(/(\d{4})(?:-(\d{4}))?/);

        if (match) {
            const startYear = parseInt(match[1], 10);
            const endYear = match[2] ? parseInt(match[2], 10) : startYear;
            return { startYear, endYear };
        }

        // Fallback to defaults if parsing fails
        return { startYear: 2000, endYear: 2023 };
    }

    /**
     * Show preview modal for a ranking card
     * Opens a modal with a chart showing the indicator data for the current country
     * over the selected time period
     * @param {HTMLElement} card - The ranking card element that was clicked
     */
    showPreviewModal(card) {
        // Extract data from the card
        const itemCode = card.dataset.itemCode;
        const itemName = card.dataset.itemName;
        const timePeriod = card.dataset.timePeriod;

        if (!itemCode) {
            console.warn('Cannot preview: No item code found on card');
            return;
        }

        // Disable preview for single year periods (no time series to visualize)
        if (this.isSingleYearPeriod(timePeriod)) {
            return;
        }

        // Parse the time period to get start and end years
        const { startYear, endYear } = this.parseTimePeriod(timePeriod);

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'preview-modal-overlay';
        overlay.innerHTML = `
            <div class="preview-modal">
                <div class="preview-modal-header">
                    <h3>${itemName} (${itemCode}) - ${this.countryCode}</h3>
                    <button class="modal-close-btn" type="button">×</button>
                </div>
                <div class="preview-modal-body">
                    <div id="preview-chart-container"></div>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        const modal = overlay.querySelector('.preview-modal');
        const closeBtn = overlay.querySelector('.modal-close-btn');
        const chartContainer = overlay.querySelector('#preview-chart-container');

        // Store chart reference for cleanup
        let chartInstance = null;

        // Create the chart with country list mode
        try {
            chartInstance = new IndicatorPanelChart(chartContainer, itemCode, {
                CountryList: [this.countryCode]
            });

            // Set year range after chart creation
            // We need to set the properties directly and update the chart
            // because IndicatorPanelChart doesn't forward year parameters to parent constructor
            if (chartInstance) {
                chartInstance.startYear = startYear;
                chartInstance.endYear = endYear;

                // Update the chart's x-axis scale to reflect the new year range
                if (chartInstance.chart && chartInstance.chart.options && chartInstance.chart.options.scales && chartInstance.chart.options.scales.x) {
                    chartInstance.chart.options.scales.x.min = startYear;
                    chartInstance.chart.options.scales.x.max = endYear;
                }

                // Update year input values if they exist (they might not in modal context)
                if (chartInstance.startYearInput) {
                    chartInstance.startYearInput.value = startYear;
                }
                if (chartInstance.endYearInput) {
                    chartInstance.endYearInput.value = endYear;
                }

                // Trigger chart update to apply the year range
                if (chartInstance.chart) {
                    chartInstance.chart.update();
                }
            }

            // Add to global charts array for tracking
            if (window.SSPICharts) {
                window.SSPICharts.push(chartInstance);
            }
        } catch (error) {
            console.error('Error creating preview chart:', error);
            chartContainer.innerHTML = `<div style="padding: 2rem; text-align: center; color: var(--error-color);">
                <p>Error loading preview chart.</p>
                <p>${error.message}</p>
            </div>`;
        }

        const closeModal = () => {
            // Destroy chart if it exists
            if (chartInstance && typeof chartInstance.destroy === 'function') {
                try {
                    chartInstance.destroy();
                } catch (error) {
                    console.error('Error destroying chart:', error);
                }
            }

            // Remove from global charts array
            if (window.SSPICharts && chartInstance) {
                const index = window.SSPICharts.indexOf(chartInstance);
                if (index > -1) {
                    window.SSPICharts.splice(index, 1);
                }
            }

            // Remove overlay
            overlay.remove();
        };

        // Event listeners for closing
        closeBtn.addEventListener('click', closeModal);

        // Close on escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);

        // Close on click outside modal
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeModal();
            }
        });
    }
}
