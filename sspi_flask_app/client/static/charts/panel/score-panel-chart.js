class ScorePanelChart extends PanelChart {
    constructor(parentElement, itemCode, { CountryList = [], width = 600, height = 600 } = {} ) {
        super(parentElement, { CountryList: CountryList, endpointURL: `/api/v1/panel/score/${itemCode}`, width: width, height: height })
        this.itemCode = itemCode
        this.moveBurgerToBreadcrumb()
    }

    moveBurgerToBreadcrumb() {
        // Move hamburger menu from title actions to breadcrumb actions
        if (this.showChartOptions && this.breadcrumbActions) {
            this.breadcrumbActions.appendChild(this.showChartOptions)
        }
    }

    updateChartOptions() {
        this.chart.options.scales = {
            x: {
                ticks: {
                    color: this.tickColor,
                },
                type: "category",
                title: {
                    display: true,
                    text: 'Year',
                    color: this.axisTitleColor,
                    font: {
                        size: 16
                    }
                },
            },
            y: {
                ticks: {
                    color: this.tickColor,
                },
                beginAtZero: true,
                min: 0,
                max: 1,
                title: {
                    display: true,
                    text: 'Indicator Score',
                    color: this.axisTitleColor,
                    font: {
                        size: 16
                    }
                }
            }
        }
    }

    updateItemDropdown(options, itemType) {
        let itemTypeCapped = itemType
        if (itemType === "sspi") {
            itemTypeCapped = this.itemType.toUpperCase()
        } else {
            itemTypeCapped = this.itemType.charAt(0).toUpperCase() + this.itemType.slice(1)
        }
        const itemTitle = itemTypeCapped + ' Information';
        const itemSummary = this.itemInformation.querySelector('.item-information-summary')
        itemSummary.textContent = itemTitle;
        const defaultValue = '/data/' + itemType.toLowerCase() + '/' + this.itemCode
        console.log('Default value for item dropdown:', defaultValue)
        for (const option of options) {
            const opt = document.createElement('option')
            opt.value = option.Value
            if (option.Value === defaultValue) {
                opt.selected = true;
            }
            opt.textContent = option.Text;
            this.itemDropdown.appendChild(opt)
        }
        this.itemDropdown.addEventListener('change', (event) => {
            window.location.href = event.target.value
        })
    }

    initChartJSCanvas() {
        this.chartContainer = document.createElement('div');
        this.chartContainer.classList.add('panel-chart-container');
        this.chartContainer.innerHTML = `
<div class="panel-chart-breadcrumb-container" style="display: none;">
    <nav class="panel-chart-breadcrumb" aria-label="Hierarchy navigation"></nav>
    <div class="panel-chart-breadcrumb-actions"></div>
</div>
<div class="panel-chart-title-container">
    <h2 class="panel-chart-title"></h2>
    <div class="panel-chart-title-actions"></div>
</div>
<div class="panel-canvas-wrapper">
    <canvas class="panel-chart-canvas"></canvas>
</div>
`;
        this.root.appendChild(this.chartContainer);
        this.breadcrumbContainer = this.chartContainer.querySelector('.panel-chart-breadcrumb-container');
        this.breadcrumb = this.chartContainer.querySelector('.panel-chart-breadcrumb');
        this.breadcrumbActions = this.chartContainer.querySelector('.panel-chart-breadcrumb-actions');
        this.title = this.chartContainer.querySelector('.panel-chart-title');
        this.titleActions = this.chartContainer.querySelector('.panel-chart-title-actions');
        this.canvas = this.chartContainer.querySelector('.panel-chart-canvas');
        this.context = this.canvas.getContext('2d');
        this.chart = new Chart(this.context, {
            type: 'line',
            plugins: [this.chartInteractionPlugin, this.extrapolateBackwardPlugin],
            options: {
                // animation: false,
                responsive: true,
                hover: {
                    mode: null
                },
                maintainAspectRatio: false,
                datasets: {
                    line: {
                        spanGaps: true,
                        pointRadius: 2,
                        pointHoverRadius: 4,
                        segment: {
                            borderWidth: 2,
                            borderDash: ctx => {
                                return ctx.p0.skip || ctx.p1.skip ? [10, 4] : [];
                                // Dashed when spanning gaps, solid otherwise
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        enabled: false,
                    },
                    chartInteractionPlugin: {
                        enabled: true,
                        radius: 20,
                        clickRadius: 4,
                        tooltipBg: this.headerBackgroundColor,
                        tooltipFg: this.titleColor,
                        labelField: 'CCode',
                        showDefaultLabels: true,
                        defaultLabelSpacing: 5,
                        onDatasetClick: (datasets, event, chart) => {
                            datasets.forEach((dataset) => {
                                this.activeCountry = dataset;
                                window.observableStorage.setItem('activeCountry', dataset)
                                this.updateCountryInformation();
                            });
                        }
                    },
                },
                layout: {
                    padding: {
                        right: 40
                    }
                }
            }
        });
    }

    renderBreadcrumb(treePath, title, itemCode, itemType) {
        if (!treePath || treePath.length === 0) {
            // Show simple title container if no treepath
            this.chartContainer.querySelector('.panel-chart-title-container').style.display = 'flex';
            this.breadcrumbContainer.style.display = 'none';
            return;
        }
        // Hide title container and show breadcrumb container for items with treepath
        this.chartContainer.querySelector('.panel-chart-title-container').style.display = 'none';
        this.breadcrumbContainer.style.display = 'flex';
        // Build breadcrumb HTML
        let breadcrumbHTML = '';
        // Process each level in the tree path (except the last one)
        for (let i = 0; i < treePath.length - 1; i++) {
            const item = treePath[i];
            let code, itemName, displayName, url;
            // Handle both old format (strings) and new format (objects) for backwards compatibility
            if (typeof item === 'string') {
                code = item.toLowerCase();
                // Fallback to old logic for backwards compatibility
                if (code === 'sspi') {
                    displayName = 'SSPI';
                    itemName = 'Social Policy and Progress Index';
                    url = '/data';
                } else if (i === 1) {
                    displayName = code.toUpperCase();
                    itemName = code.toUpperCase();
                    url = '/data/pillar/' + code.toUpperCase();
                } else if (i === 2) {
                    displayName = code.toUpperCase();
                    itemName = code.toUpperCase();
                    url = '/data/category/' + code.toUpperCase();
                } else {
                    displayName = code.toUpperCase();
                    itemName = code.toUpperCase();
                    url = null;
                }
            } else {
                // New object format with itemCode and itemName
                code = item.itemCode;
                itemName = item.itemName;
                
                // Map codes to display names and URLs
                if (code === 'sspi') {
                    displayName = 'SSPI';
                    url = '/data';
                } else if (i === 1) {
                    // Second level is pillar
                    displayName = code.toUpperCase();
                    url = '/data/pillar/' + code.toUpperCase();
                } else if (i === 2) {
                    // Third level is category
                    displayName = code.toUpperCase();
                    url = '/data/category/' + code.toUpperCase();
                } else {
                    // Fallback for other levels
                    displayName = code.toUpperCase();
                    url = null;
                }
            }
            // Add separator if not first item
            if (i > 0) {
                breadcrumbHTML += '<span class="breadcrumb-separator">></span>';
            }
            // Add breadcrumb item with link and tooltip
            breadcrumbHTML += '<a href="' + url + '" class="breadcrumb-item" title="' + itemName + '">' + displayName + '</a>';
        }

        // Add final separator and current page title with itemCode (no link)
        if (treePath.length > 0) {
            breadcrumbHTML += '<span class="breadcrumb-separator">></span>';
        }
        breadcrumbHTML += '<span class="breadcrumb-current">' + title + ' (' + itemCode + ')</span>';
        this.breadcrumb.innerHTML = breadcrumbHTML;
    }

    generateTooltipText(parentItemName, parentItemType, childTypeTitle, childrenCount) {
        // Proper plural to singular mapping
        const pluralToSingular = {
            'Pillars': 'Pillar',
            'Categories': 'Category', 
            'Indicators': 'Indicator'
        };
        
        const childTypeSingular = pluralToSingular[childTypeTitle] || childTypeTitle;
        const childTypeDisplay = childrenCount === 1 ? childTypeSingular : childTypeTitle;
        const parentTypeDisplay = parentItemType === 'SSPI' ? 'SSPI' : parentItemName + ' ' + parentItemType;
        
        return parentTypeDisplay + ' scores are the arithmetic average of the ' + childTypeSingular.toLowerCase() + ' scores of the ' + childrenCount + ' ' + childTypeDisplay.toLowerCase() + ' below';
    }

    updateChildren(children, childTypeTitle, parentItemName, parentItemType) {
        const descriptionContainer = this.chartOptions.querySelector('.dynamic-item-description-container');
        
        // Remove existing children section if it exists
        const existingChildrenSection = descriptionContainer.querySelector('.item-children-section');
        if (existingChildrenSection) {
            existingChildrenSection.remove();
        }
        
        // Add children section if children exist
        if (children && children.length > 0 && childTypeTitle) {
            const tooltipText = this.generateTooltipText(parentItemName, parentItemType, childTypeTitle, children.length);
            console.log('Generated tooltip text:', tooltipText);
            
            const childrenHTML = '<div class="item-children-section">' +
                '<div class="children-title-wrapper">' +
                '<h4>' + childTypeTitle + '</h4>' +
                '<span class="children-info-icon" title="' + tooltipText + '" aria-label="Information about scoring">i</span>' +
                '</div>' +
                '<ul class="children-list">' +
                children.map(child => {
                    const url = child.itemType === 'Category' ? 
                        '/data/category/' + child.itemCode : 
                        '/data/indicator/' + child.itemCode;
                    return '<li><a href="' + url + '" class="child-link">' + child.itemName + ' (' + child.itemCode + ')</a></li>';
                }).join('') +
                '</ul>' +
                '</div>';
            descriptionContainer.insertAdjacentHTML('beforeend', childrenHTML);
        }
    }

    update(data) {
        // Force refresh of chart interaction plugin labels when data changes
        if (this.chartInteractionPlugin && this.chartInteractionPlugin._forceRefreshLabels) {
            this.chartInteractionPlugin._forceRefreshLabels(this.chart);
        }
        this.chart.data.datasets = data.data;
        this.chart.data.labels = data.labels;
        if (this.pinnedOnly) {
            this.hideUnpinned();
        } else {
            this.showGroup(this.countryGroup);
        }
        // Store treepath for breadcrumb rendering
        this.treepath = data.treepath;
        // Use breadcrumb navigation if treepath is available
        if (data.treepath && data.treepath.length > 0) {
            this.renderBreadcrumb(data.treepath, data.title, data.itemCode, data.itemType);
        } else {
            // Fallback to simple title if no treepath
            this.title.innerText = data.title;
            this.chartContainer.querySelector('.panel-chart-title-container').style.display = 'flex';
            if (this.breadcrumbContainer) {
                this.breadcrumbContainer.style.display = 'none';
            }
        }
        this.itemType = data.itemType;
        this.groupOptions = data.groupOptions;
        this.getPins();
        this.updateLegend();
        this.updateItemDropdown(data.itemOptions, data.itemType);
        this.updateDescription(data.description);
        this.updateChildren(data.children, data.childTypeTitle, data.itemName, data.itemType);
        this.updateChartColors();
        this.updateCountryGroups();
        this.chart.update();
        this.activeCountry = window.observableStorage.getItem('activeCountry')
        if (this.activeCountry) {
            this.updateCountryInformation();
        }
    }
}
