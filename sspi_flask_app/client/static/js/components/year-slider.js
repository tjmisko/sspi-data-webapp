/**
 * YearSlider - Reusable year slider component with play/pause functionality
 *
 * Used across multiple charts (Globe, Radar, Correlation) for consistent
 * year selection and timeline playback.
 *
 * Features:
 * - Range slider with visual year display
 * - Editable year input with validation
 * - Play/pause timeline animation
 * - Persistent state via observableStorage
 *
 * @example
 * const slider = new YearSlider({
 *     containerId: 'my-slider',
 *     minYear: 2000,
 *     maxYear: 2023,
 *     initialYear: 2020,
 *     storageKey: 'myChartYear',
 *     onChange: (year) => { console.log('Year changed:', year) },
 *     playInterval: 1200
 * })
 */
class YearSlider {
    /**
     * @param {Object} options - Configuration options
     * @param {string} options.containerId - Unique ID for the slider container element
     * @param {number} options.minYear - Minimum year value
     * @param {number} options.maxYear - Maximum year value
     * @param {number} [options.initialYear] - Starting year (defaults to maxYear)
     * @param {string} [options.storageKey] - Key for persistent storage (defaults to 'yearSlider_{containerId}')
     * @param {Function} [options.onChange] - Callback when year changes: (year) => void
     * @param {number} [options.playInterval=1200] - Milliseconds between year advances during playback
     * @param {boolean} [options.enablePlayback=true] - Whether to show play/pause button
     */
    constructor(options) {
        // Required options
        this.containerId = options.containerId;
        this.minYear = options.minYear;
        this.maxYear = options.maxYear;
        this.storageKey = options.storageKey || `yearSlider_${this.containerId}`;
        this.playStorageKey = `${this.storageKey}_playing`;
        this.playInterval = options.playInterval || 1200;
        this.enablePlayback = options.enablePlayback !== false; // Default true
        this.onChange = options.onChange || (() => {});
        const storedYear = window.observableStorage?.getItem(this.storageKey);
        this.year = storedYear || options.initialYear || this.maxYear;
        this.year = Math.max(this.minYear, Math.min(this.maxYear, this.year));
        const storedPlaying = window.observableStorage?.getItem(this.playStorageKey);
        this.playing = storedPlaying || false;
        this.playIntervalId = null;
        // Build DOM
        this.build();
        this.attachEventListeners();
        // Restore playing state if it was active
        if (this.playing) {
            this.startPlay();
        }
    }

    build() {
        this.container = document.createElement('div');
        this.container.id = this.containerId;
        this.container.classList.add('globe-year-slider-container'); // Reuse existing CSS class

        const playPauseButton = this.enablePlayback
            ? `<button class="year-play-pause-button" aria-label="Play timeline">
                <span class="play-icon">▶</span>
                <span class="pause-icon" style="display:none;">⏸</span>
               </button>`
            : '';

        this.container.innerHTML = `
<div class="year-slider-controls">
    <label class="year-slider-label" for="${this.containerId}-input">
        <span class="year-value-display" contenteditable="true" spellcheck="false">${this.year}</span>
    </label>
    <div class="year-slider-wrapper">
        <div class="year-slider-track-container">
            <div class="year-slider-ticks"></div>
            <input
                type="range"
                class="year-slider-input"
                id="${this.containerId}-input"
                min="${this.minYear}"
                max="${this.maxYear}"
                value="${this.year}"
                step="1"
            />
        </div>
        <div class="year-slider-bounds">
            <span class="year-slider-min">${this.minYear}</span>
            <span class="year-slider-max">${this.maxYear}</span>
        </div>
    </div>
    ${playPauseButton}
</div>`;
    }

    attachEventListeners() {
        this.input = this.container.querySelector('.year-slider-input');
        this.display = this.container.querySelector('.year-value-display');

        // Range slider input
        this.input.addEventListener('input', (e) => {
            if (this.playing) {
                this.stopPlay();
            }
            this.setYear(parseInt(e.target.value));
        });

        // Editable display - keyboard handling
        this.display.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.display.blur();
            } else if (!/^\d$/.test(e.key) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key)) {
                e.preventDefault();
            }
        });

        // Editable display - blur validation
        this.display.addEventListener('blur', () => {
            const inputYear = parseInt(this.display.textContent.trim());

            if (isNaN(inputYear) || inputYear < this.minYear || inputYear > this.maxYear) {
                // Invalid year, revert to current year
                this.display.textContent = this.year;
                this.display.classList.add('year-input-error');
                setTimeout(() => {
                    this.display.classList.remove('year-input-error');
                }, 500);
            } else if (inputYear !== this.year) {
                // Valid year and different from current, update
                if (this.playing) {
                    this.stopPlay();
                }
                this.setYear(inputYear);
            } else {
                // Same year, just ensure formatting is correct
                this.display.textContent = this.year;
            }
        });

        // Play/pause button
        if (this.enablePlayback) {
            this.playPauseButton = this.container.querySelector('.year-play-pause-button');
            this.playIcon = this.container.querySelector('.play-icon');
            this.pauseIcon = this.container.querySelector('.pause-icon');

            this.playPauseButton.addEventListener('click', () => {
                this.togglePlay();
            });
        }
    }

    /**
     * Set the current year and trigger onChange callback
     * @param {number} year - Year to set
     * @param {boolean} [silent=false] - If true, don't trigger onChange callback
     */
    setYear(year, silent = false) {
        // Clamp to valid range
        year = Math.max(this.minYear, Math.min(this.maxYear, year));

        this.year = year;
        this.input.value = year;
        this.display.textContent = year;

        if (window.observableStorage) {
            window.observableStorage.setItem(this.storageKey, year);
        }

        if (!silent) {
            this.onChange(year);
        }
    }

    /**
     * Update the year range (useful for dynamic data loading)
     * @param {number} minYear - New minimum year
     * @param {number} maxYear - New maximum year
     */
    updateRange(minYear, maxYear) {
        this.minYear = minYear;
        this.maxYear = maxYear;

        this.input.min = minYear;
        this.input.max = maxYear;
        this.container.querySelector('.year-slider-min').textContent = minYear;
        this.container.querySelector('.year-slider-max').textContent = maxYear;

        // Clamp current year to new range
        if (this.year < minYear || this.year > maxYear) {
            this.setYear(Math.max(minYear, Math.min(maxYear, this.year)));
        }
    }

    advanceYear() {
        if (this.year < this.maxYear) {
            this.setYear(this.year + 1);
        } else {
            // Loop back to beginning
            this.setYear(this.minYear);
        }
    }

    startPlay() {
        if (!this.enablePlayback) return;

        this.playing = true;
        if (window.observableStorage) {
            window.observableStorage.setItem(this.playStorageKey, true);
        }
        this.playIcon.style.display = 'none';
        this.pauseIcon.style.display = 'inline';
        this.playIntervalId = setInterval(() => this.advanceYear(), this.playInterval);
    }

    stopPlay() {
        if (!this.enablePlayback) return;

        this.playing = false;
        if (window.observableStorage) {
            window.observableStorage.setItem(this.playStorageKey, false);
        }
        this.playIcon.style.display = 'inline';
        this.pauseIcon.style.display = 'none';
        if (this.playIntervalId) {
            clearInterval(this.playIntervalId);
            this.playIntervalId = null;
        }
    }

    togglePlay() {
        if (this.playing) {
            this.stopPlay();
        } else {
            this.startPlay();
        }
    }

    /**
     * Get the DOM element to append to parent
     * @returns {HTMLElement}
     */
    getElement() {
        return this.container;
    }

    /**
     * Clean up resources (stop playback, clear intervals)
     */
    destroy() {
        if (this.playing) {
            this.stopPlay();
        }
    }
}
