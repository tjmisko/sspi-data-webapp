class HierarchicalIndicatorSelector {
    constructor(container, options = {}) {
        if (!(container instanceof HTMLElement)) {
            throw new Error('Container must be a valid HTMLElement');
        }
        
        this.container = container;
        this.options = {
            onSelectionChange: null,
            initialExpanded: ['SSPI'], // expand first level by default
            enableSearch: true,
            enableControls: true,
            expandFirstLevel: true,
            ...options
        };
        
        // State management
        this.treeData = null;
        this.selectedCodes = new Set();
        this.expandedNodes = new Set();
        this.searchTerm = '';
        
        // Clear container
        this.container.innerHTML = '';
        this.container.className = 'hierarchical-selector';
    }
    
    initialize(treeData) {
        if (!treeData) {
            this.container.innerHTML = '<div class="error-message">No tree data provided</div>';
            return;
        }
        
        this.treeData = treeData;
        
        // Set initial expanded state
        if (this.options.expandFirstLevel && this.treeData.children) {
            this.treeData.children.forEach(pillar => {
                this.expandedNodes.add(pillar.itemCode);
            });
        }
        
        this.render();
        this.bindEvents();
    }
    
    render() {
        if (!this.treeData) return;
        
        const html = `
            ${this.options.enableControls ? this.createControlsHTML() : ''}
            <div class="tree-container">
                ${this.renderNode(this.treeData)}
            </div>
        `;
        
        this.container.innerHTML = html;
        this.updateIndeterminateStates();
    }
    
    renderTreeOnly() {
        if (!this.treeData) return;
        
        const treeContainer = this.container.querySelector('.tree-container');
        if (treeContainer) {
            treeContainer.innerHTML = this.renderNode(this.treeData);
            this.updateIndeterminateStates();
        }
    }
    
    createControlsHTML() {
        return `
            <div class="selector-controls">
                <div class="control-buttons">
                    <button type="button" data-action="expand-all" class="control-btn">Expand All</button>
                    <button type="button" data-action="collapse-all" class="control-btn">Collapse All</button>
                    <button type="button" data-action="select-all" class="control-btn">Select All</button>
                    <button type="button" data-action="deselect-all" class="control-btn">Deselect All</button>
                </div>
                ${this.options.enableSearch ? this.createSearchHTML() : ''}
            </div>
        `;
    }
    
    createSearchHTML() {
        return `
            <div class="search-container">
                <input type="text" class="search-input" placeholder="Search indicators..." value="${this.searchTerm}">
            </div>
        `;
    }
    
    renderNode(node, isVisible = true) {
        if (!node) return '';
        
        const isExpanded = this.expandedNodes.has(node.itemCode);
        const isSelected = this.selectedCodes.has(node.itemCode);
        const hasChildren = node.children && node.children.length > 0;
        
        // Check if node matches search or has matching descendants
        const matchesSearch = this.nodeMatchesSearch(node);
        const hasMatchingDescendants = this.hasMatchingDescendants(node);
        const shouldShow = isVisible && (this.searchTerm === '' || matchesSearch || hasMatchingDescendants);
        
        if (!shouldShow) return '';
        
        // Determine checkbox state
        let checkboxState = 'unchecked';
        if (isSelected) {
            checkboxState = 'checked';
        } else if (hasChildren && this.hasSelectedChildren(node)) {
            checkboxState = 'indeterminate';
        }
        
        let html = `
            <div class="tree-node level-${node.level}" data-code="${node.itemCode}" data-type="${node.itemType}" data-pillar="${this.getPillarCode(node)}">
                <div class="node-content">
        `;
        
        // Expand/collapse button
        if (hasChildren) {
            const expandIcon = isExpanded ? '▼' : '▶';
            html += `<button type="button" class="expand-btn" data-code="${node.itemCode}">${expandIcon}</button>`;
        } else {
            html += `<span class="expand-spacer"></span>`;
        }
        
        // Checkbox
        const checkedAttr = checkboxState === 'checked' ? ' checked' : '';
        html += `
            <input type="checkbox" 
                   class="node-checkbox" 
                   data-code="${node.itemCode}"
                   data-state="${checkboxState}"
                   ${checkedAttr}>
        `;
        
        // Label
        const highlightedName = this.highlightSearchTerm(node.itemName);
        html += `
            <label class="node-label ${node.itemType.toLowerCase()}-label">
                <span class="item-text">${highlightedName} (${this.highlightSearchTerm(node.itemCode)})</span>
            </label>
                </div>
        `;
        
        // Children
        if (hasChildren && isExpanded) {
            html += `<div class="children">`;
            for (const child of node.children) {
                html += this.renderNode(child, shouldShow);
            }
            html += `</div>`;
        }
        
        html += `</div>`;
        
        return html;
    }
    
    bindEvents() {
        // Control buttons - event delegation
        this.container.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            if (action) {
                this.handleControlAction(action);
                return;
            }
            
            // Expand/collapse buttons
            if (e.target.classList.contains('expand-btn')) {
                this.toggleExpand(e.target.dataset.code);
                return;
            }
        });
        
        // Checkbox changes
        this.container.addEventListener('change', (e) => {
            if (e.target.classList.contains('node-checkbox')) {
                this.toggleSelection(e.target.dataset.code, e.target.checked);
            }
        });
        
        // Search input
        if (this.options.enableSearch) {
            this.container.addEventListener('input', (e) => {
                if (e.target.classList.contains('search-input')) {
                    this.handleSearchInput(e.target.value);
                }
            });
            
            // Handle Enter key in search input
            this.container.addEventListener('keydown', (e) => {
                if (e.target.classList.contains('search-input') && e.key === 'Enter') {
                    e.preventDefault(); // Prevent form submission
                    this.selectFirstMatch();
                }
            });
        }
    }
    
    handleControlAction(action) {
        switch (action) {
            case 'expand-all':
                this.expandAll();
                break;
            case 'collapse-all':
                this.collapseAll();
                break;
            case 'select-all':
                this.selectAll();
                break;
            case 'deselect-all':
                this.deselectAll();
                break;
        }
    }
    
    handleSearchInput(value) {
        this.searchTerm = value.toLowerCase();
        this.renderTreeOnly();
    }
    
    toggleExpand(itemCode) {
        if (this.expandedNodes.has(itemCode)) {
            this.expandedNodes.delete(itemCode);
        } else {
            this.expandedNodes.add(itemCode);
        }
        this.renderTreeOnly();
    }
    
    toggleSelection(itemCode, isChecked) {
        const node = this.findNode(this.treeData, itemCode);
        if (!node) return;
        
        if (isChecked) {
            this.selectNodeAndDescendants(node);
        } else {
            this.deselectNodeAndDescendants(node);
        }
        
        // Update parent states
        this.updateParentStates(node);
        this.renderTreeOnly();
        this.notifySelectionChange();
    }
    
    selectNodeAndDescendants(node) {
        this.selectedCodes.add(node.itemCode);
        
        if (node.children) {
            node.children.forEach(child => this.selectNodeAndDescendants(child));
        }
    }
    
    deselectNodeAndDescendants(node) {
        this.selectedCodes.delete(node.itemCode);
        
        if (node.children) {
            node.children.forEach(child => this.deselectNodeAndDescendants(child));
        }
    }
    
    updateParentStates(node) {
        const parent = this.findParentNode(this.treeData, node.itemCode);
        if (!parent) return;
        
        const selectedChildren = parent.children.filter(child => this.selectedCodes.has(child.itemCode));
        
        if (selectedChildren.length === 0) {
            this.selectedCodes.delete(parent.itemCode);
        } else if (selectedChildren.length === parent.children.length) {
            this.selectedCodes.add(parent.itemCode);
        } else {
            this.selectedCodes.delete(parent.itemCode);
        }
        
        // Recursively update grandparents
        this.updateParentStates(parent);
    }
    
    hasSelectedChildren(node) {
        if (!node.children) return false;
        return node.children.some(child => 
            this.selectedCodes.has(child.itemCode) || this.hasSelectedChildren(child)
        );
    }
    
    expandAll() {
        const addAllNodes = (node) => {
            this.expandedNodes.add(node.itemCode);
            if (node.children) {
                node.children.forEach(addAllNodes);
            }
        };
        
        addAllNodes(this.treeData);
        this.renderTreeOnly();
    }
    
    collapseAll() {
        this.expandedNodes.clear();
        this.renderTreeOnly();
    }
    
    selectAll() {
        const addAllNodes = (node) => {
            this.selectedCodes.add(node.itemCode);
            if (node.children) {
                node.children.forEach(addAllNodes);
            }
        };
        
        addAllNodes(this.treeData);
        this.renderTreeOnly();
        this.notifySelectionChange();
    }
    
    deselectAll() {
        this.selectedCodes.clear();
        this.renderTreeOnly();
        this.notifySelectionChange();
    }
    
    nodeMatchesSearch(node) {
        if (!this.searchTerm) return true;
        return node.itemName.toLowerCase().includes(this.searchTerm) ||
               node.itemCode.toLowerCase().includes(this.searchTerm);
    }
    
    hasMatchingDescendants(node) {
        if (!node.children) return false;
        return node.children.some(child => 
            this.nodeMatchesSearch(child) || this.hasMatchingDescendants(child)
        );
    }
    
    highlightSearchTerm(text) {
        if (!this.searchTerm) return text;
        
        const regex = new RegExp(`(${this.searchTerm})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }
    
    selectFirstMatch() {
        if (!this.searchTerm) return;
        
        const firstMatch = this.findFirstMatchingNode(this.treeData);
        if (firstMatch) {
            // Toggle the selection of the first match
            const isCurrentlySelected = this.selectedCodes.has(firstMatch.itemCode);
            this.toggleSelection(firstMatch.itemCode, !isCurrentlySelected);
            
            // Also expand parents to make the selection visible
            this.expandParentsToNode(firstMatch.itemCode);
        }
    }
    
    findFirstMatchingNode(node) {
        // Check if current node matches
        if (this.nodeMatchesSearch(node)) {
            return node;
        }
        
        // Recursively check children
        if (node.children) {
            for (const child of node.children) {
                const match = this.findFirstMatchingNode(child);
                if (match) return match;
            }
        }
        
        return null;
    }
    
    expandParentsToNode(itemCode) {
        const expandParent = (node, targetCode, parentCode = null) => {
            if (node.itemCode === targetCode && parentCode) {
                this.expandedNodes.add(parentCode);
                return true;
            }
            
            if (node.children) {
                for (const child of node.children) {
                    if (expandParent(child, targetCode, node.itemCode)) {
                        if (parentCode) {
                            this.expandedNodes.add(parentCode);
                        }
                        return true;
                    }
                }
            }
            
            return false;
        };
        
        expandParent(this.treeData, itemCode);
    }
    
    getPillarCode(node) {
        // If this is the root SSPI node, no pillar
        if (node.itemType === 'SSPI') {
            return '';
        }
        
        // If this is a pillar node, return its code
        if (node.itemType === 'Pillar') {
            return node.itemCode;
        }
        
        // For categories and indicators, find the pillar ancestor
        return this.findPillarAncestor(node, this.treeData);
    }
    
    findPillarAncestor(targetNode, currentNode, pillarCode = null) {
        // If current node is a pillar, remember it
        if (currentNode.itemType === 'Pillar') {
            pillarCode = currentNode.itemCode;
        }
        
        // If we found the target node, return the pillar code
        if (currentNode.itemCode === targetNode.itemCode) {
            return pillarCode;
        }
        
        // Search in children
        if (currentNode.children) {
            for (const child of currentNode.children) {
                const result = this.findPillarAncestor(targetNode, child, pillarCode);
                if (result) return result;
            }
        }
        
        return null;
    }
    
    findNode(root, itemCode) {
        if (root.itemCode === itemCode) return root;
        
        if (root.children) {
            for (const child of root.children) {
                const found = this.findNode(child, itemCode);
                if (found) return found;
            }
        }
        
        return null;
    }
    
    findParentNode(root, childCode, parent = null) {
        if (root.itemCode === childCode) return parent;
        
        if (root.children) {
            for (const child of root.children) {
                const found = this.findParentNode(child, childCode, root);
                if (found) return found;
            }
        }
        
        return null;
    }
    
    updateIndeterminateStates() {
        // Set indeterminate state for checkboxes after HTML is rendered
        const checkboxes = this.container.querySelectorAll('.node-checkbox');
        checkboxes.forEach(checkbox => {
            const state = checkbox.dataset.state;
            if (state === 'indeterminate') {
                checkbox.indeterminate = true;
            }
        });
    }
    
    notifySelectionChange() {
        if (this.options.onSelectionChange) {
            this.options.onSelectionChange(this.getSelectedCodes());
        }
    }
    
    // Public API
    getSelectedCodes() {
        return Array.from(this.selectedCodes);
    }
    
    setSelectedCodes(codes) {
        this.selectedCodes = new Set(codes);
        this.renderTreeOnly();
        this.notifySelectionChange();
    }
    
    destroy() {
        this.container.innerHTML = '';
        this.container.className = '';
        this.selectedCodes.clear();
        this.expandedNodes.clear();
        this.treeData = null;
    }
}