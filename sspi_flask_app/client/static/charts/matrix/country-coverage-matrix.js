class CountryCoverageMatrixChart {
    constructor(parentElement, countryCode, {
        minYear = 2000,
        maxYear = 2023
    } = {}) {
        this.parentElement = parentElement;
        this.countryCode = countryCode;
        this.minYear = minYear;
        this.maxYear = maxYear;
        this.currentView = 'indicator';
        this.indicatorData = null;
        this.datasetData = null;
        this.setTheme(window.observableStorage.getItem("theme"));
        this.initRoot();
        this.initChartContainer();
        this.updateChartOptions();
        this.fetch();
    }

    setTheme(theme) {
        if (theme !== "light") {
            this.theme = "dark";
            this.tickColor = "#bbb";
            this.axisTitleColor = "#bbb";
            // Darker but saturated green for dark mode
            this.observedBg = 'rgba(0, 140, 0, 0.7)';
            this.observedBorder = 'rgba(0, 140, 0, 1)';
            this.observedSummary = 'rgba(0, 140, 0, 0.8)';
        } else {
            this.theme = "light";
            this.tickColor = "#444";
            this.axisTitleColor = "#444";
            this.observedBg = 'rgba(0, 180, 0, 0.7)';
            this.observedBorder = 'rgba(0, 180, 0, 1)';
            this.observedSummary = 'rgba(0, 180, 0, 0.8)';
        }
        if (this.chart) {
            this.updateChartOptions();
            this.chart.update();
        }
    }

    updateChartOptions() {
        if (!this.chart) return;
        this.chart.options.scales.x.ticks.color = this.tickColor;
        this.chart.options.scales.y.ticks.color = this.tickColor;
    }

    initRoot() {
        this.root = document.createElement('div');
        this.root.classList.add('country-coverage-matrix-root');
        this.parentElement.appendChild(this.root);
    }

    initChartContainer() {
        this.chartContainer = document.createElement('div');
        this.chartContainer.classList.add('country-coverage-matrix-container');
        this.chartContainer.innerHTML = `
<div class="country-coverage-matrix-header">
    <h3 class="country-coverage-matrix-title">Data Coverage Matrix</h3>
    <div class="coverage-view-tabs">
        <button class="view-tab active" data-view="indicator">By Indicator</button>
        <button class="view-tab" data-view="dataset">By Dataset</button>
    </div>
</div>
<div class="country-coverage-summary"></div>
<div class="country-coverage-canvas-wrapper">
    <canvas class="country-coverage-matrix-canvas"></canvas>
</div>
`;
        this.root.appendChild(this.chartContainer);

        this.title = this.chartContainer.querySelector('.country-coverage-matrix-title');
        this.summaryContainer = this.chartContainer.querySelector('.country-coverage-summary');
        this.canvasWrapper = this.chartContainer.querySelector('.country-coverage-canvas-wrapper');
        this.canvas = this.chartContainer.querySelector('.country-coverage-matrix-canvas');
        this.context = this.canvas.getContext('2d');

        // Set up tab click handlers
        this.tabButtons = this.chartContainer.querySelectorAll('.view-tab');
        this.tabButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const view = e.target.dataset.view;
                this.toggleView(view);
            });
        });

        this.font = {
            family: 'Courier New',
            size: 10,
            style: "normal",
            weight: "normal"
        };

        this.chart = new Chart(this.context, {
            type: 'matrix',
            options: {
                maintainAspectRatio: false,
                animation: {
                    duration: 500
                },
                layout: {
                    padding: { top: 40, right: 25, left: 10 }
                },
                plugins: {
                    legend: false,
                    tooltip: {
                        callbacks: {
                            title: () => 'Data Coverage',
                            label: (context) => {
                                const cell = context.dataset.data[context.dataIndex];
                                return this.buildTooltipLabel(cell);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        position: 'top',
                        offset: true,
                        ticks: {
                            font: this.font,
                            maxRotation: 45,
                            minRotation: 45,
                            autoSkip: false
                        },
                        grid: { display: true, drawOnChartArea: false }
                    },
                    y: {
                        type: 'category',
                        offset: true,
                        reverse: false,
                        ticks: {
                            font: this.font,
                            autoSkip: false
                        },
                        grid: { display: true }
                    }
                }
            },
            plugins: []
        });
    }

    buildTooltipLabel(cell) {
        const status = cell.v === 'observed' ? 'Observed Data' : 'Imputed Data';

        // Dataset view
        if (cell.yDataset) {
            const lines = [
                'Dataset: ' + (cell.yDatasetName || cell.yDataset),
                'Indicator: ' + (cell.yIndicatorName || cell.yIndicator),
                'Year: ' + cell.x,
                'Status: ' + status
            ];
            if (cell.value !== null && cell.value !== undefined) {
                lines.push('Value: ' + cell.value.toFixed(3));
            }
            // Show imputation method for imputed datasets
            if (cell.imputationMethod) {
                lines.push('Imputation: ' + cell.imputationMethod);
            }
            return lines;
        }

        // Indicator view
        const lines = [
            'Indicator: ' + (cell.yName || cell.y),
            'Year: ' + cell.x,
            'Status: ' + status
        ];

        if (cell.score !== null && cell.score !== undefined) {
            lines.push('Score: ' + cell.score.toFixed(3));
        }

        // Add dataset breakdown with colored squares
        if (cell.datasetBreakdown && Object.keys(cell.datasetBreakdown).length > 0) {
            // Build a string of colored squares using the breakdown
            const greenSquare = '🟩';  // Green for observed
            const orangeSquare = '🟧'; // Orange for imputed

            let squares = '';
            const breakdown = cell.datasetBreakdown;
            const datasetCodes = Object.keys(breakdown);

            datasetCodes.forEach((dsCode, idx) => {
                const dsInfo = breakdown[dsCode];
                // Data should only be 'observed' or 'imputed'
                squares += dsInfo.status === 'observed' ? greenSquare : orangeSquare;
                // Add space between squares
                if (idx < datasetCodes.length - 1) {
                    squares += ' ';
                }
            });

            lines.push('Datasets: ' + squares);
        }

        return lines;
    }

    async fetch() {
        // Fetch both views in parallel for instant toggling
        const [indicatorRes, datasetRes] = await Promise.all([
            fetch(`/api/v1/country/coverage/matrix/${this.countryCode}?view=indicator`),
            fetch(`/api/v1/country/coverage/matrix/${this.countryCode}?view=dataset`)
        ]);

        this.indicatorData = await indicatorRes.json();
        this.datasetData = await datasetRes.json();

        // Initial render with indicator view
        this.update(this.indicatorData);
    }

    toggleView(view) {
        if (this.currentView === view) return;

        this.currentView = view;

        // Update active tab styling
        this.tabButtons.forEach(btn => {
            if (btn.dataset.view === view) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Render the appropriate view
        const data = view === 'dataset' ? this.datasetData : this.indicatorData;
        if (data) {
            this.update(data);
        }
    }

    updateSummary(summary) {
        this.summaryContainer.innerHTML = '';
        const items = [
            { label: 'Observed Data', value: summary.observedPercent, count: summary.observedCount, color: this.observedSummary },
            { label: 'Imputed Data', value: summary.imputedPercent, count: summary.imputedCount, color: 'rgba(255, 165, 0, 0.8)' }
        ];

        items.forEach(item => {
            const line = document.createElement('div');
            line.classList.add('coverage-summary-line');
            line.innerHTML = `
                <span class="coverage-color-block" style="background-color: ${item.color}"></span>
                <span class="coverage-label">${item.label}:</span>
                <span class="coverage-value">${item.value}%\u0020(${item.count}\u0020cells)</span>
            `;
            this.summaryContainer.appendChild(line);
        });
    }

    update(res) {
        this.n_years = res.years.length;

        // Determine number of rows based on view type
        let yLabels;
        if (res.view === 'dataset') {
            // Use compound keys for datasets
            yLabels = res.datasets || [];
            this.n_rows = yLabels.length;
        } else {
            // Use indicator codes
            yLabels = res.indicators || [];
            this.n_rows = yLabels.length;
        }

        // Update title with country name
        this.title.textContent = res.countryName + ' Data Coverage Matrix';

        // Set canvas wrapper height based on number of rows
        // Dataset view has more rows, use smaller height per row
        const heightPerRow = res.view === 'dataset' ? 12 : 15;
        const chartHeight = Math.max(400, this.n_rows * heightPerRow + 100);
        this.canvasWrapper.style.height = `${chartHeight}px`;

        // Update summary
        this.updateSummary(res.summary);

        // Update chart data
        this.chart.data = {
            datasets: [{
                label: `${res.countryName} Data Coverage`,
                data: res.data,
                backgroundColor: (context) => {
                    const cell = context.dataset.data[context.dataIndex];
                    // Data should only be 'observed' or 'imputed'
                    return cell.v === 'observed'
                        ? this.observedBg
                        : 'rgba(255, 165, 0, 0.7)'; // Orange
                },
                borderColor: (context) => {
                    const cell = context.dataset.data[context.dataIndex];
                    // Data should only be 'observed' or 'imputed'
                    return cell.v === 'observed'
                        ? this.observedBorder
                        : 'rgba(255, 165, 0, 1)';
                },
                borderWidth: 1,
                width: ({ chart }) => (chart.chartArea || {}).width / this.n_years - 1,
                height: ({ chart }) => (chart.chartArea || {}).height / this.n_rows - 1
            }]
        };

        // Update scales
        this.chart.options.scales.x.labels = res.years;
        this.chart.options.scales.y.labels = yLabels;

        // Customize y-axis tick callback for dataset view to show DatasetCode
        if (res.view === 'dataset' && res.yLabels) {
            const yLabelLookup = {};
            res.yLabels.forEach(label => {
                if (label.type === 'dataset') {
                    // Use DatasetCode instead of DatasetName
                    yLabelLookup[label.compoundKey] = label.code;
                }
            });

            this.chart.options.scales.y.ticks.callback = function(value, index, ticks) {
                const compoundKey = this.getLabelForValue(value);
                // Show DatasetCode, truncate to 20 chars with ellipsis
                let label = yLabelLookup[compoundKey] || compoundKey;
                if (label.length > 20) {
                    label = label.substring(0, 17) + '...';
                }
                return label;
            };
        } else {
            // For indicator view, show indicator codes, truncate to 20 chars
            this.chart.options.scales.y.ticks.callback = function(value) {
                let label = this.getLabelForValue(value);
                if (label.length > 20) {
                    label = label.substring(0, 17) + '...';
                }
                return label;
            };
        }

        this.chart.update();
    }
}
