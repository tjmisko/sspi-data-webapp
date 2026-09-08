class JustifiedCaptions {
    // Picks a box width for each caption so that CSS justification fills it
    // evenly. The box may grow a little past its natural width (by `slack`)
    // when that saves a whole line; otherwise it shrinks to the narrowest
    // width that keeps the line count, so the last line comes out nearly
    // full. The box stays centered on the column either way. Widths are
    // recomputed when fonts load and on resize.
    constructor(selector = '.methodology-figure-caption', slack = 0.12) {
        this.captions = Array.from(document.querySelectorAll(selector))
        this.slack = slack
        if (this.captions.length === 0) {
            return
        }
        this.resizeTimer = null
        this.fit()
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(() => this.fit())
        }
        window.addEventListener('resize', () => {
            window.clearTimeout(this.resizeTimer)
            this.resizeTimer = window.setTimeout(() => this.fit(), 120)
        })
    }

    lineCount(caption) {
        const style = window.getComputedStyle(caption)
        let lineHeight = parseFloat(style.lineHeight)
        if (Number.isNaN(lineHeight)) {
            lineHeight = parseFloat(style.fontSize) * 1.5
        }
        return Math.max(1, Math.round(caption.getBoundingClientRect().height / lineHeight))
    }

    setWidth(caption, width, fullWidth) {
        caption.style.width = width + 'px'
        const margin = (fullWidth - width) / 2
        caption.style.marginLeft = margin + 'px'
        caption.style.marginRight = margin + 'px'
    }

    reset(caption) {
        caption.style.width = ''
        caption.style.marginLeft = ''
        caption.style.marginRight = ''
    }

    fit() {
        this.captions.forEach(caption => this.fitOne(caption))
    }

    fitOne(caption) {
        this.reset(caption)
        const fullWidth = caption.getBoundingClientRect().width
        if (fullWidth === 0) {
            return
        }
        const widest = Math.ceil(fullWidth * (1 + this.slack))
        this.setWidth(caption, widest, fullWidth)
        const targetLines = this.lineCount(caption)
        if (targetLines < 2) {
            this.reset(caption)
            return
        }
        // Smallest width that still fits in targetLines. Line count is
        // monotone in width, so a binary search finds it.
        let low = 1
        let high = widest
        while (low < high) {
            const mid = Math.floor((low + high) / 2)
            this.setWidth(caption, mid, fullWidth)
            if (this.lineCount(caption) > targetLines) {
                low = mid + 1
            } else {
                high = mid
            }
        }
        this.setWidth(caption, high, fullWidth)
    }
}
