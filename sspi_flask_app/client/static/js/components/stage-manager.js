// stage-manager.js
// Manages stage view switching and rendering for customizable SSPI workflow

class StageManager {
    constructor(parentElement, sspiStructure, options = {}) {
        this.parentElement = parentElement;
        this.sspiStructure = sspiStructure;
        this.currentStage = options.currentStage || 0;
        this.onStageComplete = options.onStageComplete || (() => {});
        this.onStageChange = options.onStageChange || (() => {});

        this.stageViews = {
            0: this.renderLoadStage.bind(this),
            1: this.renderBuildStage.bind(this),
            2: this.renderReviewStage.bind(this),
            3: this.renderScoreStage.bind(this),
            4: this.renderExploreStage.bind(this)
        };

        this.currentView = null;
    }

    setStage(stageId) {
        this.currentStage = stageId;
        this.render();
        this.onStageChange(stageId);
    }

    render() {
        const renderFn = this.stageViews[this.currentStage];
        if (renderFn) {
            this.currentView = renderFn();
        } else {
            console.error(`Unknown stage: ${this.currentStage}`);
        }
    }

    // Stage 0: Load Configuration
    renderLoadStage() {
        const container = document.createElement('div');
        container.classList.add('stage-view', 'load-stage');

        const header = document.createElement('h2');
        header.textContent = 'Load Configuration';
        container.appendChild(header);

        const description = document.createElement('p');
        description.textContent = 'Choose a pre-built SSPI configuration or load one of your saved customizations.';
        description.classList.add('stage-description');
        container.appendChild(description);

        // Pre-built configurations section
        const prebuiltSection = document.createElement('div');
        prebuiltSection.classList.add('config-section');

        const prebuiltTitle = document.createElement('h3');
        prebuiltTitle.textContent = 'Pre-built Configurations';
        prebuiltSection.appendChild(prebuiltTitle);

        const prebuiltConfigs = [
            { id: 'default', name: 'Default SSPI', description: 'Standard SSPI structure with all indicators' },
            { id: 'environment', name: 'Environment Focus', description: 'Emphasis on environmental sustainability indicators' },
            { id: 'economy', name: 'Economy Focus', description: 'Emphasis on economic prosperity indicators' }
        ];

        prebuiltConfigs.forEach(config => {
            const configCard = this.createConfigCard(config, 'prebuilt');
            prebuiltSection.appendChild(configCard);
        });

        container.appendChild(prebuiltSection);

        // User saved configurations section
        const savedSection = document.createElement('div');
        savedSection.classList.add('config-section');

        const savedTitle = document.createElement('h3');
        savedTitle.textContent = 'Your Saved Configurations';
        savedSection.appendChild(savedTitle);

        const savedList = document.createElement('div');
        savedList.classList.add('saved-configs-list');
        savedList.id = 'saved-configs-list';
        savedList.innerHTML = '<p class="loading-message">Loading saved configurations...</p>';
        savedSection.appendChild(savedList);

        container.appendChild(savedSection);

        // Navigation buttons
        const nav = this.createNavButtons({ showBack: false, showNext: false, showSkip: true });
        container.appendChild(nav);

        // Clear parent and append
        this.parentElement.innerHTML = '';
        this.parentElement.appendChild(container);

        // Load saved configurations
        this.loadSavedConfigurations();

        return container;
    }

    createConfigCard(config, type) {
        const card = document.createElement('div');
        card.classList.add('config-card');
        card.dataset.configId = config.id;
        card.dataset.configType = type;

        const cardName = document.createElement('div');
        cardName.classList.add('config-name');
        cardName.textContent = config.name;

        const cardDesc = document.createElement('div');
        cardDesc.classList.add('config-description');
        cardDesc.textContent = config.description || 'No description available';

        const loadBtn = document.createElement('button');
        loadBtn.textContent = 'Load';
        loadBtn.classList.add('btn-primary');
        loadBtn.addEventListener('click', () => this.loadConfiguration(config.id, type));

        card.appendChild(cardName);
        card.appendChild(cardDesc);
        card.appendChild(loadBtn);

        return card;
    }

    async loadSavedConfigurations() {
        const listEl = document.getElementById('saved-configs-list');
        try {
            const response = await fetch('/api/v1/customize/list');
            const data = await response.json();

            if (data.success && data.configurations && data.configurations.length > 0) {
                listEl.innerHTML = '';
                data.configurations.forEach(config => {
                    const card = this.createConfigCard(config, 'saved');
                    listEl.appendChild(card);
                });
            } else {
                listEl.innerHTML = '<p class="empty-message">No saved configurations yet. Start by building a custom SSPI!</p>';
            }
        } catch (error) {
            console.error('Error loading saved configurations:', error);
            listEl.innerHTML = '<p class="error-message">Error loading saved configurations.</p>';
        }
    }

    async loadConfiguration(configId, type) {
        this.sspiStructure.showLoadingState(`Loading configuration "${configId}"...`);

        try {
            let endpoint = type === 'prebuilt'
                ? `/api/v1/customize/prebuilt/${configId}`
                : `/api/v1/customize/load/${configId}`;

            const response = await fetch(endpoint);
            const data = await response.json();

            if (data.success && data.metadata) {
                await this.sspiStructure.importDataAsync(data.metadata);
                if (data.datasetDetailsMap) {
                    this.sspiStructure.datasetDetails = data.datasetDetailsMap;
                }
                this.sspiStructure.hideLoadingState();
                this.completeStage(0);
            } else {
                this.sspiStructure.hideLoadingState();
                notifications.error('Error loading configuration: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            this.sspiStructure.hideLoadingState();
            console.error('Error loading configuration:', error);
            notifications.error('Error loading configuration. Please try again.');
        }
    }

    // Stage 1: Build (existing UI)
    renderBuildStage() {
        const container = document.createElement('div');
        container.classList.add('stage-view', 'build-stage');

        const header = document.createElement('h2');
        header.textContent = 'Build Your Custom SSPI';
        container.appendChild(header);

        const description = document.createElement('p');
        description.textContent = 'Customize the SSPI structure by adding, removing, or reorganizing indicators and categories.';
        description.classList.add('stage-description');
        container.appendChild(description);

        // The actual customization UI (pillars container) is already rendered by sspiStructure
        // We just show it in this stage
        const sspiContainer = this.sspiStructure.container;
        sspiContainer.style.display = 'block';
        container.appendChild(sspiContainer);

        // Navigation buttons
        const nav = this.createNavButtons({ showBack: true, showNext: true, nextLabel: 'Review Changes' });
        container.appendChild(nav);

        this.parentElement.innerHTML = '';
        this.parentElement.appendChild(container);

        return container;
    }

    // Stage 2: Review Changes
    renderReviewStage() {
        const container = document.createElement('div');
        container.classList.add('stage-view', 'review-stage');

        const header = document.createElement('h2');
        header.textContent = 'Review Your Changes';
        container.appendChild(header);

        const description = document.createElement('p');
        description.textContent = 'Review the changes you\'ve made before submitting for scoring.';
        description.classList.add('stage-description');
        container.appendChild(description);

        // Summary of changes
        const summary = this.generateChangesSummary();
        container.appendChild(summary);

        // Navigation buttons
        const nav = this.createNavButtons({
            showBack: true,
            showNext: true,
            nextLabel: 'Submit for Scoring',
            backLabel: 'Back to Build'
        });
        container.appendChild(nav);

        this.parentElement.innerHTML = '';
        this.parentElement.appendChild(container);

        return container;
    }

    generateChangesSummary() {
        const summaryContainer = document.createElement('div');
        summaryContainer.classList.add('changes-summary');

        const actions = this.sspiStructure.actionHistory.actions;

        if (actions.length === 0) {
            const noChanges = document.createElement('p');
            noChanges.textContent = 'No changes have been made to the default SSPI structure.';
            noChanges.classList.add('no-changes-message');
            summaryContainer.appendChild(noChanges);
            return summaryContainer;
        }

        // Group actions by type
        const groupedActions = {};
        actions.forEach(action => {
            const type = action.type || 'other';
            if (!groupedActions[type]) {
                groupedActions[type] = [];
            }
            groupedActions[type].push(action);
        });

        // Create summary cards for each action type
        Object.entries(groupedActions).forEach(([type, actionsList]) => {
            const card = document.createElement('div');
            card.classList.add('summary-card');

            const cardHeader = document.createElement('div');
            cardHeader.classList.add('summary-card-header');
            cardHeader.textContent = `${this.formatActionType(type)} (${actionsList.length})`;

            const cardBody = document.createElement('div');
            cardBody.classList.add('summary-card-body');

            const list = document.createElement('ul');
            actionsList.forEach(action => {
                const item = document.createElement('li');
                item.textContent = action.message || 'Unknown action';
                list.appendChild(item);
            });

            cardBody.appendChild(list);
            card.appendChild(cardHeader);
            card.appendChild(cardBody);
            summaryContainer.appendChild(card);
        });

        return summaryContainer;
    }

    formatActionType(type) {
        const typeMap = {
            'add-indicator': 'Indicators Added',
            'remove-indicator': 'Indicators Removed',
            'move-indicator': 'Indicators Moved',
            'add-category': 'Categories Added',
            'remove-category': 'Categories Removed',
            'move-category': 'Categories Moved',
            'add-dataset': 'Datasets Added',
            'remove-dataset': 'Datasets Removed',
            'modify-indicator': 'Indicators Modified',
            'set-indicator-name': 'Indicator Names Changed',
            'set-category-name': 'Category Names Changed',
            'set-pillar-name': 'Pillar Names Changed'
        };
        return typeMap[type] || type.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    // Stage 3: Score (with SSE streaming)
    renderScoreStage() {
        const container = document.createElement('div');
        container.classList.add('stage-view', 'score-stage');

        const header = document.createElement('h2');
        header.textContent = 'Scoring in Progress';
        container.appendChild(header);

        const description = document.createElement('p');
        description.textContent = 'Computing scores for your custom SSPI structure...';
        description.classList.add('stage-description');
        container.appendChild(description);

        // Progress indicator
        const progressContainer = document.createElement('div');
        progressContainer.classList.add('scoring-progress');

        const progressBar = document.createElement('div');
        progressBar.classList.add('progress-bar');

        const progressFill = document.createElement('div');
        progressFill.classList.add('progress-fill');
        progressFill.id = 'scoring-progress-fill';
        progressFill.style.width = '0%';

        progressBar.appendChild(progressFill);
        progressContainer.appendChild(progressBar);

        const progressText = document.createElement('div');
        progressText.classList.add('progress-text');
        progressText.id = 'scoring-progress-text';
        progressText.textContent = 'Initializing...';
        progressContainer.appendChild(progressText);

        container.appendChild(progressContainer);

        // Log area
        const logContainer = document.createElement('div');
        logContainer.classList.add('scoring-log');
        logContainer.id = 'scoring-log';
        container.appendChild(logContainer);

        this.parentElement.innerHTML = '';
        this.parentElement.appendChild(container);

        // Start scoring with SSE
        this.startScoring();

        return container;
    }

    async startScoring() {
        const metadata = this.sspiStructure.exportData();
        const actions = this.sspiStructure.actionHistory.actions.map(a => a.delta);

        try {
            // Submit the scoring request via POST
            const response = await fetch('/api/v1/customize/score', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ metadata, actions })
            });

            if (!response.ok) {
                throw new Error('Failed to start scoring');
            }

            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'Failed to initiate scoring');
            }

            // Now connect to SSE stream for progress updates
            const eventSource = new EventSource('/api/v1/customize/score-stream');

            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.updateScoringProgress(data);
            };

            eventSource.addEventListener('complete', (event) => {
                const data = JSON.parse(event.data);
                eventSource.close();
                this.scoringComplete(data);
            });

            eventSource.addEventListener('error', (event) => {
                eventSource.close();
                this.scoringError(event);
            });

        } catch (error) {
            console.error('Error starting scoring:', error);
            this.scoringError(error);
        }
    }

    updateScoringProgress(data) {
        const progressFill = document.getElementById('scoring-progress-fill');
        const progressText = document.getElementById('scoring-progress-text');
        const logContainer = document.getElementById('scoring-log');

        if (data.progress !== undefined) {
            progressFill.style.width = `${data.progress}%`;
        }

        if (data.message) {
            progressText.textContent = data.message;

            const logEntry = document.createElement('div');
            logEntry.classList.add('log-entry');
            logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${data.message}`;
            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;
        }
    }

    scoringComplete(data) {
        const progressText = document.getElementById('scoring-progress-text');
        progressText.textContent = 'Scoring complete!';

        notifications.success('Scoring completed successfully!');

        // Auto-advance to Explore stage after a short delay
        setTimeout(() => {
            this.completeStage(3);
        }, 1500);
    }

    scoringError(error) {
        const progressText = document.getElementById('scoring-progress-text');
        progressText.textContent = 'Error during scoring';
        progressText.style.color = 'var(--error-color)';

        notifications.error('Error during scoring: ' + (error.message || 'Unknown error'));
    }

    // Stage 4: Explore (placeholder)
    renderExploreStage() {
        const container = document.createElement('div');
        container.classList.add('stage-view', 'explore-stage');

        const header = document.createElement('h2');
        header.textContent = 'Explore Your Results';
        container.appendChild(header);

        const placeholder = document.createElement('div');
        placeholder.classList.add('placeholder-content');
        placeholder.innerHTML = `
            <div class="placeholder-icon">🎉</div>
            <h3>Results Ready!</h3>
            <p>The exploration interface is coming soon. For now, you can view your results in the main SSPI visualization page.</p>
            <button class="btn-primary" onclick="window.location.href='/'">View Main Dashboard</button>
        `;
        container.appendChild(placeholder);

        // Navigation buttons
        const nav = this.createNavButtons({ showBack: true, showNext: false });
        container.appendChild(nav);

        this.parentElement.innerHTML = '';
        this.parentElement.appendChild(container);

        return container;
    }

    createNavButtons({ showBack = true, showNext = true, showSkip = false, nextLabel = 'Next', backLabel = 'Back' } = {}) {
        const nav = document.createElement('div');
        nav.classList.add('stage-navigation');

        if (showBack) {
            const backBtn = document.createElement('button');
            backBtn.textContent = backLabel;
            backBtn.classList.add('btn-secondary');
            backBtn.addEventListener('click', () => this.goBack());
            nav.appendChild(backBtn);
        }

        if (showSkip) {
            const skipBtn = document.createElement('button');
            skipBtn.textContent = 'Skip to Build';
            skipBtn.classList.add('btn-secondary');
            skipBtn.addEventListener('click', () => this.completeStage(0));
            nav.appendChild(skipBtn);
        }

        if (showNext) {
            const nextBtn = document.createElement('button');
            nextBtn.textContent = nextLabel;
            nextBtn.classList.add('btn-primary');
            nextBtn.addEventListener('click', () => this.goNext());
            nav.appendChild(nextBtn);
        }

        return nav;
    }

    goBack() {
        if (this.currentStage > 0) {
            this.setStage(this.currentStage - 1);
        }
    }

    goNext() {
        this.completeStage(this.currentStage);
    }

    completeStage(stageId) {
        this.onStageComplete(stageId);
    }

    validateStageCompletion(stageId) {
        switch (stageId) {
            case 0: // Load
                return true; // Always can proceed from Load
            case 1: // Build
                // Check if any changes were made or structure is valid
                return this.sspiStructure.container !== null;
            case 2: // Review
                // Can proceed if user has reviewed changes
                return true;
            case 3: // Score
                // Scoring must complete before proceeding
                return false; // Auto-advances when complete
            case 4: // Explore
                return false; // Final stage
            default:
                return false;
        }
    }
}
