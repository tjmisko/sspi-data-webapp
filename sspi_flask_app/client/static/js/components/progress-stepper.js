// progress-stepper.js
// Horizontal progress stepper component for customizable SSPI workflow

class ProgressStepper {
    constructor(parentElement, options = {}) {
        this.parentElement = parentElement;
        this.currentStage = options.currentStage || 0;
        this.completedStages = options.completedStages || [];
        this.onStageClick = options.onStageClick || (() => {});

        this.stages = [
            { id: 0, name: 'Structure', number: '1' },
            { id: 1, name: 'View Changes', number: '2' },
            { id: 2, name: 'Score', number: '3' },
            { id: 3, name: 'Compare', number: '4' }
        ];

        this.render();
    }

    render() {
        const stepper = document.createElement('div');
        stepper.classList.add('progress-stepper');
        stepper.setAttribute('role', 'navigation');
        stepper.setAttribute('aria-label', 'Progress steps');

        // Create the steps container
        const stepsContainer = document.createElement('div');
        stepsContainer.classList.add('progress-stepper-steps');

        // Create progress fill bar
        const progressFill = document.createElement('div');
        progressFill.classList.add('progress-bar-fill');

        // Calculate progress fill width based on current stage
        let fillPercentage = 0;
        if (this.currentStage > 0) {
            fillPercentage = (this.currentStage / (this.stages.length - 1)) * 100;
        }
        // Set width, ensuring it never goes negative (0% when at first stage)
        progressFill.style.width = fillPercentage === 0 ? '0' : `${fillPercentage}%`;

        this.stages.forEach((stage, index) => {
            // Create step container
            const stepContainer = document.createElement('div');
            stepContainer.classList.add('step-container');

            // Create step circle
            const step = document.createElement('div');
            step.classList.add('step');
            step.dataset.stage = stage.id;
            step.setAttribute('role', 'button');
            step.setAttribute('tabindex', '0');
            step.setAttribute('aria-label', `${stage.name} stage`);

            // Determine step state
            const isCompleted = this.completedStages.includes(stage.id);
            const isCurrent = stage.id === this.currentStage;
            const isClickable = isCompleted || stage.id < this.currentStage;

            if (isCompleted) {
                step.classList.add('completed');
                step.setAttribute('aria-current', 'false');
            }
            if (isCurrent) {
                step.classList.add('current');
                step.setAttribute('aria-current', 'step');
            }
            if (!isClickable && !isCurrent) {
                step.classList.add('locked');
                step.setAttribute('aria-disabled', 'true');
            }

            // Step content (number or checkmark)
            const stepIcon = document.createElement('span');
            stepIcon.classList.add('step-icon');
            if (isCompleted && !isCurrent) {
                stepIcon.textContent = '✓';
                stepIcon.classList.add('checkmark');
            } else {
                stepIcon.textContent = stage.number;
            }
            step.appendChild(stepIcon);

            // Step label
            const stepLabel = document.createElement('div');
            stepLabel.classList.add('step-label');
            stepLabel.textContent = stage.name;

            // Add click handler for clickable steps
            if (isClickable || isCurrent) {
                step.style.cursor = 'pointer';
                step.addEventListener('click', () => this.handleStageClick(stage.id));
                step.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.handleStageClick(stage.id);
                    }
                });
            }

            stepContainer.appendChild(step);
            stepContainer.appendChild(stepLabel);
            stepsContainer.appendChild(stepContainer);
        });

        // Assemble stepper
        stepper.appendChild(progressFill);
        stepper.appendChild(stepsContainer);

        // Clear parent and append stepper
        this.parentElement.innerHTML = '';
        this.parentElement.appendChild(stepper);
    }

    handleStageClick(stageId) {
        this.onStageClick(stageId);
    }

    setCurrentStage(stageId) {
        this.currentStage = stageId;
        this.render();
    }

    markStageCompleted(stageId) {
        if (!this.completedStages.includes(stageId)) {
            this.completedStages.push(stageId);
            this.render();
        }
    }

    resetProgress() {
        this.currentStage = 0;
        this.completedStages = [];
        this.render();
    }

    getState() {
        return {
            currentStage: this.currentStage,
            completedStages: [...this.completedStages]
        };
    }

    setState(state) {
        this.currentStage = state.currentStage || 0;
        this.completedStages = state.completedStages || [];
        this.render();
    }
}
