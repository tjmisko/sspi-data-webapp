class SSPIPanelChart extends PanelChart {
    constructor(parentElement, itemCode, { CountryList = [], width = 600, height = 600 } = {} ) {
        super(parentElement, { CountryList: CountryList, endpointURL: `/api/v1/panel/score/${itemCode}`, width: width, height: height })
        this.itemCode = itemCode
    }

    initItemTree() {
        this.itemTree = document.createElement('div')
        this.itemTree.classList.add('sspi-tree-container')
        this.itemTree.innerHTML = `
            <div class="sspi-tree-description">
                <h3 class="sspi-tree-header">SSPI Structure</h3>
                <p class="sspi-tree-description-text">
                    Explore the scores across SSPI's pillars, categories, and indicators below. Click on an item below to view its data.
                </p>
            </div>
            <div class="item-tree-content">
            </div>
        `;
    }


    initRoot() {
        this.initItemTree()
        this.root = document.createElement('div')
        this.root.classList.add('panel-chart-root-container')
        this.root.appendChild(this.itemTree)
        this.parentElement.appendChild(this.root)
    }

    rigItemDropdown() {
        this.itemInformation = this.chartOptions.querySelector('.item-information')
        this.itemDropdown = this.itemInformation.querySelector('.item-dropdown')
        this.itemDropdown.style.display = "none";
    }

    updateItemDropdown(options, itemType) {
        let itemTypeCapped = itemType
        if (itemType === "sspi") {
            itemTypeCapped = this.itemType.toUpperCase()
        } else {
            itemTypeCapped = this.itemType.charAt(0).toUpperCase() + this.itemType.slice(1)
        }
        const itemTitle = itemTypeCapped + " Information";
        const itemSummary = this.itemInformation.querySelector('.item-information-summary')
        itemSummary.textContent = itemTitle;
    }

    update(data) {
        super.update(data);
        this.buildItemTree(data.tree);
    }

    buildItemTree(tree) {
      this.itemTreeObject = new SSPIItemTree(
        this.itemTree.querySelector('.item-tree-content'),   // only the content box
        tree,
        (itemCode) => {
          // fetch new data, then re-run the usual update pipeline
          this.fetch(`/api/v1/panel/score/${itemCode}`)
              .then(d => this.update(d));
        }
      );
    }
}
