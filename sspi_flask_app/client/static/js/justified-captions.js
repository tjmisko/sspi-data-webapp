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

    // Width of the caption's container, minus its padding, so the caption
    // is centered on the column rather than on its own natural width.
    outerWidth(caption) {
        const parent = caption.parentElement
        const style = window.getComputedStyle(parent)
        const padding = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight)
        return parent.clientWidth - (Number.isNaN(padding) ? 0 : padding)
    }

    setWidth(caption, width, outerWidth) {
        caption.style.width = width + 'px'
        const margin = Math.max(0, (outerWidth - width) / 2)
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
        const outerWidth = this.outerWidth(caption)
        if (fullWidth === 0 || outerWidth === 0) {
            return
        }
        // The box may grow past its natural width by `slack`, but never
        // past its container, so it can't push the page into overflow.
        const widest = Math.min(Math.ceil(fullWidth * (1 + this.slack)), Math.floor(outerWidth))
        this.setWidth(caption, widest, outerWidth)
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
            this.setWidth(caption, mid, outerWidth)
            if (this.lineCount(caption) > targetLines) {
                low = mid + 1
            } else {
                high = mid
            }
        }
        this.setWidth(caption, high, outerWidth)
    }
}
