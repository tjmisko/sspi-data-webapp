/* --------------------------------------------------------------------- */
/*  SSPIItemTree  – Robust ARIA navigation tree with keyboard support   */
/* --------------------------------------------------------------------- */

/**
 * TreeNode - Represents a single node in the tree hierarchy
 */
class TreeNode {
    constructor(data, parent = null, level = 1) {
        this.itemCode = data.ItemCode;
        this.itemName = data.ItemName;
        this.parent = parent;
        this.children = [];
        this.level = level;
        // Root level (level 1) is always expanded and cannot be collapsed
        this.expanded = data.Children?.length > 0 && (level === 1 || level < 3); // Expand SSPI and pillars, collapse categories (hiding indicators)
        this.element = null; // Will hold the DOM element
        
        // Create child nodes
        if (data.Children?.length) {
            this.children = data.Children.map(child => 
                new TreeNode(child, this, level + 1)
            );
        }
    }
    
    // Get all descendant nodes in visual display order (depth-first traversal)
    getVisibleDescendants() {
        if (!this.expanded || !this.children.length) {
            return [];
        }
        
        const visible = [];
        this.children.forEach(child => {
            visible.push(child);
            visible.push(...child.getVisibleDescendants());
        });
        
        return visible;
    }
    
    // Find ancestor at specific level (1=root, 2=pillar, 3=category, 4=indicator)
    getAncestorAtLevel(targetLevel) {
        if (this.level === targetLevel) return this;
        if (this.level < targetLevel || !this.parent) return null;
        return this.parent.getAncestorAtLevel(targetLevel);
    }
    
    // Toggle expansion state (root level cannot be toggled)
    toggle() {
        if (this.children.length > 0 && this.level > 1) {
            this.expanded = !this.expanded;
            if (this.element) {
                this.element.ariaExpanded = this.expanded ? 'true' : 'false';
            }
            return true; // State changed
        }
        return false; // No change
    }
    
    // Expand this node (without toggling)
    expand() {
        if (this.children.length > 0 && !this.expanded) {
            this.expanded = true;
            if (this.element) {
                this.element.ariaExpanded = 'true';
            }
            return true; // State changed
        }
        return false; // No change
    }
    
    // Ensure this node and all its ancestors are expanded
    expandToRoot() {
        const changedNodes = [];
        let current = this;
        
        while (current) {
            if (current.expand()) {
                changedNodes.push(current);
            }
            current = current.parent;
        }
        
        return changedNodes; // Return nodes that changed state
    }
}

/**
 * NavigationManager - Handles flat navigation index for keyboard navigation
 */
class NavigationManager {
    constructor(rootNode) {
        this.rootNode = rootNode;
        this.navigationIndex = [];
        this.currentIndex = 0;
        this.rebuild();
    }
    
    // Rebuild the flat navigation index based on current tree state
    rebuild() {
        this.navigationIndex = [this.rootNode];
        this.navigationIndex.push(...this.rootNode.getVisibleDescendants());
    }
    
    // Get currently focused node
    getCurrentNode() {
        return this.navigationIndex[this.currentIndex] || null;
    }
    
    // Move to specific node and return it
    moveTo(node) {
        const index = this.navigationIndex.indexOf(node);
        if (index !== -1) {
            this.currentIndex = index;
            return node;
        }
        return null;
    }
    
    // Navigation methods
    moveNext() {
        if (this.currentIndex < this.navigationIndex.length - 1) {
            this.currentIndex++;
            return this.getCurrentNode();
        }
        return null;
    }
    
    movePrevious() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            return this.getCurrentNode();
        }
        return null;
    }
    
    moveFirst() {
        this.currentIndex = 0;
        return this.getCurrentNode();
    }
    
    moveLast() {
        this.currentIndex = this.navigationIndex.length - 1;
        return this.getCurrentNode();
    }
    
    // Handle expand/collapse - returns {node, stateChanged, targetNode}
    handleExpand() {
        const current = this.getCurrentNode();
        if (!current) return null;
        
        if (current.children.length > 0) {
            if (!current.expanded) {
                // Expand and rebuild index
                const stateChanged = current.toggle();
                this.rebuild();
                return { node: current, stateChanged, targetNode: current }; // Stay on current node
            } else {
                // Already expanded, move to first child
                const targetNode = this.moveNext();
                return { node: current, stateChanged: false, targetNode };
            }
        }
        return null;
    }
    
    handleCollapse() {
        const current = this.getCurrentNode();
        if (!current) return null;
        
        if (current.expanded && current.children.length > 0) {
            // Collapse current node
            const stateChanged = current.toggle();
            this.rebuild();
            return { node: current, stateChanged, targetNode: current }; // Stay on current node
        } else if (current.parent) {
            // Move to parent
            const targetNode = this.moveTo(current.parent);
            return { node: current, stateChanged: false, targetNode };
        }
        return null;
    }
    
    // Find node by item code
    findByItemCode(itemCode) {
        return this.navigationIndex.find(node => node.itemCode === itemCode) || null;
    }
    
    // Type-ahead search
    findByPrefix(prefix, startFromCurrent = true) {
        const startIndex = startFromCurrent ? this.currentIndex + 1 : 0;
        
        // Search forward from current position
        for (let i = startIndex; i < this.navigationIndex.length; i++) {
            if (this.navigationIndex[i].itemName.toLowerCase().startsWith(prefix.toLowerCase())) {
                return this.navigationIndex[i];
            }
        }
        
        // Wrap around search from beginning
        if (startFromCurrent) {
            for (let i = 0; i < this.currentIndex; i++) {
                if (this.navigationIndex[i].itemName.toLowerCase().startsWith(prefix.toLowerCase())) {
                    return this.navigationIndex[i];
                }
            }
        }
        
        return null;
    }
}

/**
 * SSPIItemTree - Main tree component with keyboard navigation
 */
class SSPIItemTree {
    constructor(container, json, reloadCallback = null, activeItemCode = null) {
        if (!(container instanceof HTMLElement) || !json) return;

        this.container = container;
        this.reload = reloadCallback;
        this.activeItemCode = activeItemCode || null;
        
        // Clear container and build tree
        container.innerHTML = '';
        
        // Build data structure
        this.rootNode = new TreeNode(json, null, 1);
        this.navigationManager = new NavigationManager(this.rootNode);
        
        // Build DOM
        this.buildDOM();
        
        // Set up navigation
        this.setupNavigation();
        
        // Highlight active item and ensure it's visible
        if (this.activeItemCode) {
            this.ensureItemVisible(this.activeItemCode);
        } else {
            // No active item, set root as tab target
            if (this.rootNode.element) {
                this.rootNode.element.tabIndex = 0;
            }
        }
    }
    
    buildDOM() {
        const treeElement = this.createNodeElement(this.rootNode, true);
        this.container.appendChild(treeElement);
        
        // Cache all treeitem elements for quick access
        this.tree = this.container.querySelector('[role="tree"]');
        this.navShell = this.tree.parentElement;
    }
    
    createNodeElement(node, isRoot = false) {
        const listElement = document.createElement('ul');
        listElement.role = isRoot ? 'tree' : 'group';
        listElement.className = 'treeview-navigation';

        if (!isRoot) {
            listElement.id = `id-${node.itemCode.toLowerCase()}-subtree`;
        }

        const li = document.createElement('li');
        li.role = 'none';

        const a = document.createElement('a');
        a.role = 'treeitem';
        a.ariaOwns = node.children.length ? `id-${node.itemCode.toLowerCase()}-subtree` : null;
        // Only set aria-expanded for collapsible nodes (not root level)
        a.ariaExpanded = (node.children.length && node.level > 1) ? (node.expanded ? 'true' : 'false') : null;
        a.tabIndex = -1;
        a.dataset.itemCode = node.itemCode;

        // Store reference to DOM element in node
        node.element = a;

        const label = document.createElement('span');
        label.className = 'label';

        // Add disclosure icon for nodes with children (except root level)
        if (node.children.length > 0 && node.level > 1) {
            const icon = document.createElement('span');
            icon.className = 'icon';
            icon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="10" height="8" viewBox="0 0 13 10">
                <polygon points="2 1, 12 1, 7 9"></polygon>
            </svg>`;

            icon.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleToggle(node);
            });

            label.appendChild(icon);
        }

        const textSpan = document.createElement('span');
        textSpan.className = 'text';
        textSpan.appendChild(document.createTextNode(node.itemName));
        label.appendChild(textSpan);
        a.appendChild(label);
        li.appendChild(a);

        // Add child elements if expanded
        if (node.expanded && node.children.length > 0) {
            // If this is a category (level 3), create a single ordered list for all indicators
            if (node.level === 3) {
                const ol = document.createElement('ol');
                ol.role = 'group';
                ol.className = 'treeview-navigation';
                ol.id = `id-${node.itemCode.toLowerCase()}-indicators`;

                node.children.forEach(child => {
                    const indicatorLi = this.createIndicatorElement(child);
                    ol.appendChild(indicatorLi);
                });

                li.appendChild(ol);
            } else {
                // For other levels, use the standard recursive approach
                node.children.forEach(child => {
                    li.appendChild(this.createNodeElement(child));
                });
            }
        }

        listElement.appendChild(li);
        return listElement;
    }

    createIndicatorElement(node) {
        const li = document.createElement('li');
        li.role = 'none';

        const a = document.createElement('a');
        a.role = 'treeitem';
        a.tabIndex = -1;
        a.dataset.itemCode = node.itemCode;

        // Store reference to DOM element in node
        node.element = a;

        const label = document.createElement('span');
        label.className = 'label';

        const textSpan = document.createElement('span');
        textSpan.className = 'text';
        textSpan.appendChild(document.createTextNode(node.itemName));
        label.appendChild(textSpan);
        a.appendChild(label);
        li.appendChild(a);

        return li;
    }
    
    setupNavigation() {
        // Initial tab focus will be set by highlightTreeItem/ensureItemVisible
        // or default to first item if no active item
        
        // Store bound functions for proper cleanup
        this.boundHandleKeyDown = this.handleKeyDown.bind(this);
        this.boundHandleClick = this.handleClick.bind(this);
        this.boundHandleFocusChange = this.handleFocusChange.bind(this);
        
        // Add event listeners
        this.container.addEventListener('keydown', this.boundHandleKeyDown);
        this.container.addEventListener('click', this.boundHandleClick);
        
        // Focus management
        document.body.addEventListener('focusin', this.boundHandleFocusChange);
        document.body.addEventListener('mousedown', this.boundHandleFocusChange);
    }
    
    handleKeyDown(e) {
        // Don't intercept keys when user is typing in input fields
        const activeElement = document.activeElement;
        if (activeElement && (
            activeElement.tagName === 'INPUT' || 
            activeElement.tagName === 'TEXTAREA' ||
            activeElement.contentEditable === 'true'
        )) {
            return;
        }
        
        // Only handle keys on treeitem elements
        if (e.target.getAttribute('role') !== 'treeitem') {
            return;
        }
        
        const currentNode = this.findNodeByElement(e.target);
        if (!currentNode) return;
        
        // Update navigation manager to current position
        this.navigationManager.moveTo(currentNode);
        
        let targetNode = null;
        
        switch (e.key) {
            case 'ArrowDown':
                targetNode = this.navigationManager.moveNext();
                break;
            case 'ArrowUp':
                targetNode = this.navigationManager.movePrevious();
                break;
            case 'ArrowRight':
                const expandResult = this.navigationManager.handleExpand();
                if (expandResult) {
                    if (expandResult.stateChanged) {
                        // State changed, rebuild DOM subtree
                        this.rebuildSubtree(expandResult.node);
                    }
                    targetNode = expandResult.targetNode;
                }
                break;
            case 'ArrowLeft':
                const collapseResult = this.navigationManager.handleCollapse();
                if (collapseResult) {
                    if (collapseResult.stateChanged) {
                        // State changed, rebuild DOM subtree
                        this.rebuildSubtree(collapseResult.node);
                    }
                    targetNode = collapseResult.targetNode;
                }
                break;
            case 'Home':
                targetNode = this.navigationManager.moveFirst();
                break;
            case 'End':
                targetNode = this.navigationManager.moveLast();
                break;
            case ' ':
            case 'Enter':
                this.handleActivate(currentNode);
                e.preventDefault();
                return;
            default:
                // Type-ahead search
                if (e.key.length === 1 && /\S/.test(e.key)) {
                    targetNode = this.navigationManager.findByPrefix(e.key);
                    if (targetNode) {
                        this.navigationManager.moveTo(targetNode);
                    }
                }
        }
        
        if (targetNode && targetNode.element) {
            this.focusNode(targetNode);
            e.preventDefault();
        }
    }
    
    handleClick(e) {
        // Find the treeitem element (might be the target or an ancestor)
        let treeitem = e.target;
        while (treeitem && treeitem.getAttribute('role') !== 'treeitem') {
            treeitem = treeitem.parentElement;
        }
        
        if (treeitem) {
            const node = this.findNodeByElement(treeitem);
            if (node) {
                this.handleActivate(node);
                e.stopPropagation();
            }
        }
    }
    
    handleToggle(node) {
        if (node.toggle()) {
            // Rebuild DOM for this subtree
            this.rebuildSubtree(node);
            // Rebuild navigation index
            this.navigationManager.rebuild();
        }
    }
    
    handleActivate(node) {
        // Expand ancestors to ensure the activated node remains visible
        const changedNodes = node.expandToRoot();
        
        // Rebuild DOM for any nodes that changed expansion state
        if (changedNodes.length > 0) {
            changedNodes.forEach(changedNode => {
                this.rebuildSubtree(changedNode);
            });
            // Rebuild navigation index to include newly visible nodes
            this.navigationManager.rebuild();
        }
        
        this.highlightTreeItem(node.itemCode);
        
        if (this.reload) {
            this.reload(node.itemCode);
        }
    }
    
    rebuildSubtree(node) {
        if (!node.element) return;
        
        const li = node.element.parentElement;
        
        // Remove ALL existing child groups (not just the first one)
        const existingGroups = li.querySelectorAll('[role="group"]');
        existingGroups.forEach(group => group.remove());
        
        // Clear element references for all descendants
        this.clearElementReferences(node);
        
        if (node.expanded && node.children.length > 0) {
            // Add new children
            node.children.forEach(child => {
                li.appendChild(this.createNodeElement(child));
            });
        }
    }
    
    // Recursively clear element references for a node and all its descendants
    clearElementReferences(node) {
        node.children.forEach(child => {
            child.element = null;
            this.clearElementReferences(child);
        });
    }
    
    focusNode(node) {
        if (!node.element) return;
        
        // Update tabIndex
        this.container.querySelectorAll('[role="treeitem"]').forEach(el => {
            el.tabIndex = -1;
        });
        
        node.element.tabIndex = 0;
        node.element.focus();
    }
    
    findNodeByElement(element) {
        const itemCode = element.dataset.itemCode;
        return this.findNodeByItemCode(this.rootNode, itemCode);
    }
    
    findNodeByItemCode(node, itemCode) {
        if (node.itemCode === itemCode) return node;
        
        for (const child of node.children) {
            const found = this.findNodeByItemCode(child, itemCode);
            if (found) return found;
        }
        
        return null;
    }
    
    handleFocusChange(e) {
        if (this.tree) {
            this.navShell.classList.toggle('focus', this.tree.contains(e.target));
        }
    }
    
    highlightTreeItem(itemCode) {
        // Remove existing highlights and reset tab indexes
        this.container.querySelectorAll('[role="treeitem"]').forEach(el => {
            el.classList.remove('active-view-element');
            el.tabIndex = -1;
        });
        
        // Add highlight to target item and make it the tab target
        const node = this.findNodeByItemCode(this.rootNode, itemCode);
        if (node && node.element) {
            node.element.classList.add('active-view-element');
            node.element.tabIndex = 0;
        } else {
            // Fallback: if no active item found, make root the tab target
            if (this.rootNode.element) {
                this.rootNode.element.tabIndex = 0;
            }
        }
    }
    
    ensureItemVisible(itemCode) {
        const node = this.findNodeByItemCode(this.rootNode, itemCode);
        if (node) {
            // Expand ancestors to make this item visible
            const changedNodes = node.expandToRoot();
            
            // Rebuild DOM for any nodes that changed expansion state
            if (changedNodes.length > 0) {
                changedNodes.forEach(changedNode => {
                    this.rebuildSubtree(changedNode);
                });
                // Rebuild navigation index to include newly visible nodes
                this.navigationManager.rebuild();
            }
            
            // Highlight the item
            this.highlightTreeItem(itemCode);
        }
    }
    
    // Cleanup method to remove all event listeners and clear references
    destroy() {
        // Remove event listeners using stored bound functions
        if (this.container && this.boundHandleKeyDown) {
            this.container.removeEventListener('keydown', this.boundHandleKeyDown);
            this.container.removeEventListener('click', this.boundHandleClick);
        }
        
        if (document.body && this.boundHandleFocusChange) {
            document.body.removeEventListener('focusin', this.boundHandleFocusChange);
            document.body.removeEventListener('mousedown', this.boundHandleFocusChange);
        }
        
        // Clear all references
        this.container = null;
        this.reload = null;
        this.rootNode = null;
        this.navigationManager = null;
        this.tree = null;
        this.navShell = null;
        this.activeItemCode = null;
        this.boundHandleKeyDown = null;
        this.boundHandleClick = null;
        this.boundHandleFocusChange = null;
    }
}
