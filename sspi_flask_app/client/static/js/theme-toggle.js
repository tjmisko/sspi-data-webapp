class ThemeToggle {
    constructor(parentElement) {
        this.parentElement = parentElement
        this.currentTheme = window.theme || localStorage.getItem("theme") || "dark"
        this.initToggle()
        this.rigEventListeners()
        this.updateToggleState()
    }

    initToggle() {
        // Create the theme toggle structure
        this.parentElement.innerHTML = '<div id="theme-label-header-span" class="theme-label"></div>' +
            '<label class="theme-toggle">' +
                '<input type="checkbox" id="darkModeToggle" />' +
                '<span class="icons moon-svg">' +
                    '<svg class="icon moon" viewBox="0 0 24 24">' +
                        '<path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />' +
                    '</svg>' +
                '</span>' +
                '<span class="slider"></span>' +
                '<span class="icons sun-svg">' +
                    '<svg class="icon sun" viewBox="0 0 24 24">' +
                        '<circle cx="12" cy="12" r="5" />' +
                        '<g stroke-width="2">' +
                            '<line x1="12" y1="1" x2="12" y2="3" />' +
                            '<line x1="12" y1="21" x2="12" y2="23" />' +
                            '<line x1="4.2" y1="4.2" x2="5.6" y2="5.6" />' +
                            '<line x1="18.4" y1="18.4" x2="19.8" y2="19.8" />' +
                            '<line x1="1" y1="12" x2="3" y2="12" />' +
                            '<line x1="21" y1="12" x2="23" y2="12" />' +
                            '<line x1="4.2" y1="19.8" x2="5.6" y2="18.4" />' +
                            '<line x1="18.4" y1="5.6" x2="19.8" y2="4.2" />' +
                        '</g>' +
                    '</svg>' +
                '</span>' +
            '</label>';

        // Get references to elements
        this.checkbox = this.parentElement.querySelector("#darkModeToggle");
        this.label = this.parentElement.querySelector("#theme-label-header-span");
    }

    rigEventListeners() {
        // Set up checkbox properties
        this.checkbox.title = "Toggle Light/Dark Page Theme"
        
        // Add event listener for theme changes
        this.checkbox.addEventListener("change", () => {
            this.handleThemeChange()
        })
    }

    handleThemeChange() {
        const newTheme = this.checkbox.checked ? "light" : "dark"
        this.setTheme(newTheme)
    }

    setTheme(theme) {
        this.currentTheme = theme
        const htmlTag = document.documentElement
        
        if (theme === "light") {
            htmlTag.classList.remove("dark-theme")
            htmlTag.classList.add("light-theme")
            localStorage.setItem("theme", "light")
            window.theme = "light"
            this.label.innerText = "Light Theme"
            this.checkbox.checked = true
        } else {
            htmlTag.classList.remove("light-theme")
            htmlTag.classList.add("dark-theme")
            localStorage.setItem("theme", "dark")
            window.theme = "dark"
            this.label.innerText = "Dark Theme"
            this.checkbox.checked = false
        }
        
        this.updateCharts()
    }

    updateToggleState() {
        // Update the toggle to reflect current theme
        this.checkbox.checked = this.currentTheme === "light"
        this.label.innerText = this.currentTheme.replace(/\b\w/g, char => char.toUpperCase()) + " Theme"
    }

    updateCharts() {
        // Update charts if SSPICharts array exists
        if (window.SSPICharts && Array.isArray(window.SSPICharts)) {
            window.SSPICharts.forEach((chartObj) => {
                if (chartObj && typeof chartObj.setTheme === 'function') {
                    chartObj.setTheme(window.theme)
                }
            })
        }
    }

    // Public method to get current theme
    getTheme() {
        return this.currentTheme
    }
}