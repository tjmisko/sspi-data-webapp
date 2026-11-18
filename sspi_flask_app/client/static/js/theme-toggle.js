class ThemeToggle {
    constructor(parentElement) {
        this.parentElement = parentElement
        this.currentTheme = window.theme || localStorage.getItem("theme") || "dark"
        this.initToggle()
        this.rigEventListeners()
        this.updateToggleState()
    }

    initToggle() {
        this.parentElement.innerHTML =
            '<button type="button" class="theme-toggle">' +
                '<svg class="theme-toggle-icon theme-toggle-moon" viewBox="0 0 24 24" aria-hidden="true">' +
                    '<path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />' +
                '</svg>' +
                '<svg class="theme-toggle-icon theme-toggle-sun" viewBox="0 0 24 24" aria-hidden="true">' +
                    '<circle cx="12" cy="12" r="4.5" />' +
                    '<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41' +
                        'M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />' +
                '</svg>' +
            '</button>'
        this.button = this.parentElement.querySelector(".theme-toggle")
    }

    rigEventListeners() {
        this.button.addEventListener("click", () => {
            this.setTheme(this.currentTheme === "light" ? "dark" : "light")
        })
    }

    setTheme(theme) {
        this.currentTheme = theme === "light" ? "light" : "dark"
        const htmlTag = document.documentElement
        htmlTag.classList.toggle("light-theme", this.currentTheme === "light")
        htmlTag.classList.toggle("dark-theme", this.currentTheme === "dark")
        localStorage.setItem("theme", this.currentTheme)
        window.theme = this.currentTheme
        this.updateToggleState()
        this.updateCharts()
    }

    updateToggleState() {
        const nextTheme = this.currentTheme === "light" ? "dark" : "light"
        this.button.dataset.theme = this.currentTheme
        this.button.setAttribute("aria-label", "Switch to " + nextTheme + " theme")
        this.button.title = "Switch to " + nextTheme + " theme"
    }

    updateCharts() {
        if (!window.SSPICharts || !Array.isArray(window.SSPICharts)) return
        window.SSPICharts.forEach((chartObj) => {
            if (chartObj && typeof chartObj.setTheme === "function") {
                chartObj.setTheme(window.theme)
            }
        })
    }

    getTheme() {
        return this.currentTheme
    }
}
