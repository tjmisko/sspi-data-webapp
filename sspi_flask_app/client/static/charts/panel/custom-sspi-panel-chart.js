class CustomSSPIPanelChart extends SSPIPanelChart {
    constructor(parentElement, configId, { CountryList = [], width = 600, height = 600 } = {}) {
        // Initialize with cached data endpoint instead of regular panel endpoint
        super(parentElement, { 
            CountryList: CountryList, 
            endpointURL: `/api/v1/customize/cached-scores/${configId}?format=panel_data`, 
            width: width, 
            height: height 
        });
        
        this.configId = configId;
        this.configData = null;
        this.cachingInProgress = false;
        this.lastCacheCheck = null;
        
        // Override the item tree initialization for custom structures
        this.initCustomItemTree();
        
        // Add custom controls for configuration management
        this.addCustomControls();
    }

    initCustomItemTree() {
        // Override the item tree container to include custom configuration info
        this.itemTree = document.createElement('div');
        this.itemTree.classList.add('custom-sspi-tree-container');
        this.itemTree.innerHTML = `
            <div class="custom-sspi-tree-description">
                <h3 class="custom-sspi-tree-header">Custom SSPI Structure</h3>
                <div class="config-info-container">
                    <div class="config-name">Loading configuration...</div>
                    <div class="config-stats"></div>
                </div>
                <p class="custom-sspi-tree-description-text">
                    Explore the scores across your custom SSPI structure below. Click on an item to view its data.
                </p>
            </div>
            <div class="item-tree-content">
            </div>
        `;
    }

    initRoot() {
        this.initCustomItemTree();
        this.root = document.createElement('div');
        this.root.classList.add('custom-panel-chart-root-container');
        this.root.appendChild(this.itemTree);
        this.parentElement.appendChild(this.root);
    }

    addCustomControls() {
        // Create custom controls container
        const customControls = document.createElement('div');
        customControls.classList.add('custom-controls-container');
        customControls.innerHTML = `
            <div class="custom-controls-header">
                <h4>Custom Configuration Controls</h4>
            </div>
            <div class="custom-controls-buttons">
                <button class="custom-control-btn refresh-cache-btn" title="Refresh cached scoring data">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M8 3a5 5 0 0 1 4.546 2.914.5.5 0 0 0 .908-.408A6 6 0 0 0 8 2v1z"/>
                        <path d="M8 13a5 5 0 0 0 4.546-2.914.5.5 0 0 1 .908.408A6 6 0 0 1 8 14v-1z"/>
                        <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1z"/>
                    </svg>
                    Refresh Cache
                </button>
                <button class="custom-control-btn clear-cache-btn" title="Clear cached data">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                        <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1z"/>
                    </svg>
                    Clear Cache
                </button>
                <button class="custom-control-btn edit-config-btn" title="Edit this configuration">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
                        <path d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5v11z"/>
                    </svg>
                    Edit Configuration
                </button>
                <div class="cache-status-indicator">
                    <span class="cache-status-text">Cache Status: Unknown</span>
                </div>
            </div>
        `;

        // Insert custom controls before the chart container
        this.root.insertBefore(customControls, this.chartContainer);

        // Add event listeners for custom controls
        this.setupCustomControls(customControls);
    }

    setupCustomControls(customControls) {
        const refreshBtn = customControls.querySelector('.refresh-cache-btn');
        const clearBtn = customControls.querySelector('.clear-cache-btn');
        const editBtn = customControls.querySelector('.edit-config-btn');

        refreshBtn.addEventListener('click', () => {
            this.refreshCache();
        });

        clearBtn.addEventListener('click', () => {
            this.clearCache();
        });

        editBtn.addEventListener('click', () => {
            this.editConfiguration();
        });
    }

    async refreshCache() {
        if (this.cachingInProgress) {
            console.log('Cache refresh already in progress');
            return;
        }

        try {
            this.cachingInProgress = true;
            this.updateCacheStatus('Refreshing cache...');
            
            // Call the score-and-cache endpoint with force_refresh
            const response = await fetch(`/api/v1/customize/score-and-cache/${this.configId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    force_refresh: true,
                    years: [2023] // Default to latest year
                })
            });

            const result = await response.json();

            if (result.success) {
                this.updateCacheStatus(`Cache refreshed: ${result.cached_results} results`);
                
                // Reload the chart data
                await this.reloadChartData();
                
                console.log('Cache refreshed successfully:', result.stats);
            } else {
                throw new Error(result.error || 'Cache refresh failed');
            }

        } catch (error) {
            console.error('Error refreshing cache:', error);
            this.updateCacheStatus('Cache refresh failed');
            alert('Failed to refresh cache: ' + error.message);
        } finally {
            this.cachingInProgress = false;
        }
    }

    async clearCache() {
        if (!confirm('Are you sure you want to clear the cached data? This will remove all stored scores for this configuration.')) {
            return;
        }

        try {
            const response = await fetch(`/api/v1/customize/cached-scores/${this.configId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.updateCacheStatus('Cache cleared');
                
                // Clear the chart
                this.chart.data.datasets = [];
                this.chart.data.labels = [];
                this.chart.update();
                
                console.log('Cache cleared:', result.cleared_results, 'results removed');
            } else {
                throw new Error(result.error || 'Cache clear failed');
            }

        } catch (error) {
            console.error('Error clearing cache:', error);
            alert('Failed to clear cache: ' + error.message);
        }
    }

    editConfiguration() {
        // Navigate to the configuration editor
        const editUrl = `/customize?config=${this.configId}`;
        window.open(editUrl, '_blank');
    }

    updateCacheStatus(status) {
        const statusElement = this.root.querySelector('.cache-status-text');
        if (statusElement) {
            statusElement.textContent = `Cache Status: ${status}`;
        }
    }

    async reloadChartData() {
        try {
            // Fetch fresh data from the cached-scores endpoint
            const data = await this.fetch(`/api/v1/customize/cached-scores/${this.configId}?format=panel_data`);
            this.update(data);
        } catch (error) {
            console.error('Error reloading chart data:', error);
            this.updateCacheStatus('Data reload failed');
        }
    }

    async loadConfigurationInfo() {
        try {
            // Fetch configuration metadata
            const response = await fetch(`/api/v1/customize/load/${this.configId}`);
            const result = await response.json();

            if (result.success) {
                this.configData = result.configuration;
                this.updateConfigurationDisplay();
                this.checkCacheStatus();
            } else {
                console.error('Failed to load configuration:', result.error);
                this.updateConfigurationDisplay('Failed to load configuration');
            }

        } catch (error) {
            console.error('Error loading configuration info:', error);
            this.updateConfigurationDisplay('Error loading configuration');
        }
    }

    updateConfigurationDisplay(errorMessage = null) {
        const configNameElement = this.itemTree.querySelector('.config-name');
        const configStatsElement = this.itemTree.querySelector('.config-stats');

        if (errorMessage) {
            configNameElement.textContent = errorMessage;
            configStatsElement.textContent = '';
            return;
        }

        if (this.configData) {
            configNameElement.textContent = this.configData.name || 'Unnamed Configuration';
            
            // Count structure elements
            const structure = this.configData.structure || this.configData.metadata || [];
            const pillars = new Set();
            const categories = new Set();
            const indicators = structure.length;

            structure.forEach(item => {
                if (item.PillarCode) pillars.add(item.PillarCode);
                if (item.CategoryCode) categories.add(item.CategoryCode);
            });

            configStatsElement.textContent = `${pillars.size} pillars, ${categories.size} categories, ${indicators} indicators`;
        }
    }

    async checkCacheStatus() {
        try {
            // Check if cached data exists
            const response = await fetch(`/api/v1/customize/cached-scores/${this.configId}`);
            
            if (response.status === 404) {
                this.updateCacheStatus('No cached data - refresh to generate');
                return;
            }

            const result = await response.json();
            if (result.success && result.results.length > 0) {
                this.updateCacheStatus(`${result.total_results} cached results available`);
                this.lastCacheCheck = new Date();
            } else {
                this.updateCacheStatus('No cached data available');
            }

        } catch (error) {
            console.error('Error checking cache status:', error);
            this.updateCacheStatus('Cache status unknown');
        }
    }

    // Override the buildItemTree method to handle custom structures
    buildItemTree(tree, selectedItemCode) {
        if (!tree) {
            // If no tree provided, build one from available data
            this.buildCustomItemTree(this.chart.data.datasets, selectedItemCode);
            return;
        }

        // Use the standard item tree if tree data is provided
        super.buildItemTree(tree, selectedItemCode);
    }

    buildCustomItemTree(datasets, selectedItemCode) {
        // Build a simple tree from the available datasets
        if (!datasets || datasets.length === 0) {
            this.itemTree.querySelector('.item-tree-content').innerHTML = 
                '<div class="no-data-message">No data available. Try refreshing the cache.</div>';
            return;
        }

        const treeContent = this.itemTree.querySelector('.item-tree-content');
        
        // For custom structures, create a simple item selector
        const itemSelector = document.createElement('div');
        itemSelector.classList.add('custom-item-selector');
        
        // Group items by type if possible, or just list them
        const itemCodes = new Set();
        datasets.forEach(dataset => {
            if (dataset.ICode) {
                itemCodes.add(dataset.ICode);
            }
        });

        if (itemCodes.size > 0) {
            itemSelector.innerHTML = '<h4>Available Items:</h4>';
            
            Array.from(itemCodes).sort().forEach(itemCode => {
                const itemButton = document.createElement('button');
                itemButton.classList.add('custom-item-button');
                itemButton.textContent = itemCode;
                itemButton.dataset.itemCode = itemCode;
                
                if (itemCode === selectedItemCode) {
                    itemButton.classList.add('selected');
                }
                
                itemButton.addEventListener('click', () => {
                    this.selectCustomItem(itemCode);
                });
                
                itemSelector.appendChild(itemButton);
            });
        } else {
            itemSelector.innerHTML = '<div class="no-items-message">No items available in current data</div>';
        }

        treeContent.innerHTML = '';
        treeContent.appendChild(itemSelector);
    }

    selectCustomItem(itemCode) {
        // Update URL or trigger data fetch for the selected item
        const newUrl = `/api/v1/customize/cached-scores/${this.configId}?format=panel_data&item_code=${itemCode}`;
        
        this.fetch(newUrl)
            .then(data => {
                this.update(data);
                this.updateSelectedItemInTree(itemCode);
            })
            .catch(error => {
                console.error('Error loading item data:', error);
                alert('Failed to load data for selected item');
            });
    }

    updateSelectedItemInTree(selectedItemCode) {
        // Update the visual selection in the custom item tree
        const buttons = this.itemTree.querySelectorAll('.custom-item-button');
        buttons.forEach(button => {
            if (button.dataset.itemCode === selectedItemCode) {
                button.classList.add('selected');
            } else {
                button.classList.remove('selected');
            }
        });
    }

    // Override the update method to handle custom data format
    update(data) {
        // Load configuration info on first update
        if (!this.configData) {
            this.loadConfigurationInfo();
        }

        // Check if this is an error response
        if (!data.success) {
            this.handleDataError(data);
            return;
        }

        // If no data available, show appropriate message
        if (!data.data || data.data.length === 0) {
            this.handleNoData(data);
            return;
        }

        // Call parent update method
        super.update(data);
        
        // Update cache status
        if (data.data && data.data.length > 0) {
            this.updateCacheStatus(`Displaying ${data.data.length} countries`);
        }
    }

    handleDataError(data) {
        console.error('Data error:', data.error);
        
        // Show error in chart title
        this.title.innerText = 'Error Loading Custom SSPI Data';
        
        // Clear chart
        this.chart.data.datasets = [];
        this.chart.data.labels = [];
        this.chart.update();
        
        // Show error in item tree
        const treeContent = this.itemTree.querySelector('.item-tree-content');
        treeContent.innerHTML = `
            <div class="error-message">
                <h4>Error Loading Data</h4>
                <p>${data.error}</p>
                ${data.suggestion ? `<p><strong>Suggestion:</strong> ${data.suggestion}</p>` : ''}
                <button class="retry-btn" onclick="window.location.reload()">Retry</button>
            </div>
        `;

        this.updateCacheStatus('Error loading data');
    }

    handleNoData(data) {
        console.log('No data available');
        
        // Show message in chart title
        this.title.innerText = data.title || 'Custom SSPI - No Data';
        
        // Clear chart
        this.chart.data.datasets = [];
        this.chart.data.labels = [];
        this.chart.update();
        
        // Show no data message in item tree
        const treeContent = this.itemTree.querySelector('.item-tree-content');
        treeContent.innerHTML = `
            <div class="no-data-message">
                <h4>No Data Available</h4>
                <p>This configuration has no cached scoring data.</p>
                <button class="generate-data-btn" onclick="this.parentElement.parentElement.parentElement.parentElement.querySelector('.refresh-cache-btn').click()">
                    Generate Data
                </button>
            </div>
        `;

        this.updateCacheStatus('No cached data');
    }

    // Enhanced error handling for network issues
    async fetch(url) {
        try {
            const response = await window.fetch(url);
            
            if (!response.ok) {
                // Try to parse error response
                try {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
                } catch (parseError) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            }
            
            return await response.json();
        } catch (error) {
            console.error('Fetch error:', error);
            throw error;
        }
    }
}

// Usage:
// const chart = new CustomSSPIPanelChart(document.getElementById('chart-container'), 'config_id_123');