class MethodologyContents {
    constructor(articleSelector = '.methodology-article', linkSelector = '.methodology-toc-link') {
        this.article = document.querySelector(articleSelector)
        this.links = Array.from(document.querySelectorAll(linkSelector))
        if (!this.article || this.links.length === 0) {
            return
        }
        this.headings = Array.from(this.article.querySelectorAll('.methodology-heading[id]'))
        if (this.headings.length === 0) {
            return
        }
        this.activeAnchor = null
        this.frameRequested = false
        this.rigEventListeners()
        this.update()
    }

    rigEventListeners() {
        const schedule = () => {
            if (this.frameRequested) {
                return
            }
            this.frameRequested = true
            window.requestAnimationFrame(() => {
                this.frameRequested = false
                this.update()
            })
        }
        window.addEventListener('scroll', schedule, { passive: true })
        window.addEventListener('resize', schedule)
        window.addEventListener('hashchange', schedule)
        window.addEventListener('load', schedule)
    }

    currentAnchor() {
        const documentHeight = document.documentElement.scrollHeight
        const atBottom = window.innerHeight + window.scrollY >= documentHeight - 2
        if (atBottom) {
            return this.headings[this.headings.length - 1].id
        }
        // The reading line sits a quarter of the way down the viewport; the
        // active section is the last one whose heading has crossed it.
        const readingLine = window.innerHeight * 0.25
        let current = this.headings[0].id
        for (const heading of this.headings) {
            if (heading.getBoundingClientRect().top > readingLine) {
                break
            }
            current = heading.id
        }
        return current
    }

    update() {
        const anchor = this.currentAnchor()
        if (anchor === this.activeAnchor) {
            return
        }
        this.activeAnchor = anchor
        const target = '#' + anchor
        this.links.forEach(link => {
            const active = link.getAttribute('href') === target
            link.classList.toggle('is-active', active)
            if (active) {
                link.setAttribute('aria-current', 'true')
            } else {
                link.removeAttribute('aria-current')
            }
        })
    }
}
