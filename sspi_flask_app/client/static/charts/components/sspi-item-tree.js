/* --------------------------------------------------------------------- */
/*  SSPIItemTree  – ARIA navigation tree with built-in keyboard support  */
/* --------------------------------------------------------------------- */

class SSPIItemTree {

    constructor(container, json, reloadCallback = null) {
        if (!(container instanceof HTMLElement) || !json) return;

        this.container  = container;
        this.reload     = reloadCallback;
        container.innerHTML = '';                             // clear old content
        container.appendChild(this.#build(json, 1));

        /* cache nodes & wire behaviour ------------------------------------ */
        this.tree     = container.querySelector('[role="tree"]');
        this.items    = [...this.tree.querySelectorAll('[role="treeitem"]')];
        this.navShell = this.tree.parentElement;

        this.items.forEach((ti, i) => {
            ti.tabIndex = i ? -1 : 0;                           // only first in tab-order
            ti.addEventListener('keydown',  this.#onKey.bind(this));
            ti.addEventListener('click',    this.#onActivate.bind(this));
        });

        /* highlight focus ring on entry/exit ------------------------------ */
        document.body.addEventListener('focusin',  this.#focusShell.bind(this));
        document.body.addEventListener('mousedown',this.#focusShell.bind(this));
    }

    /* ---------- DOM construction -------------------------------------- */

    #build(node, level) {
        const ul = Object.assign(document.createElement('ul'), {
            role      : level === 1 ? 'tree' : 'group',
            className : 'treeview-navigation'
        });

        const li = Object.assign(document.createElement('li'), { role:'none' });

        const a  = Object.assign(document.createElement('a'), {
            role         : 'treeitem',
            // href         : `#${node.ItemCode.toLowerCase()}`,
            ariaOwns     : `id-${node.ItemCode.toLowerCase()}-subtree`,
            ariaExpanded : node.Children?.length && level < 3 ? 'true' : 'false',
            tabIndex     : -1,
        });
        a.dataset.itemCode = node.ItemCode

        const label = document.createElement('span');
        label.className = 'label';

        if (node.Children?.length) {                         // disclosure icon
            const icon = document.createElement('span');
            icon.className = 'icon';
            icon.innerHTML =
                `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="10" viewBox="0 0 13 10">
                    <polygon points="2 1, 12 1, 7 9"></polygon>
                </svg>`;
            icon.addEventListener('click', (e) => {
                e.stopPropagation();
                const ti = e.currentTarget.parentElement.parentElement;
                ti.ariaExpanded = ti.ariaExpanded === 'true' ? 'false' : 'true';
            });
            label.appendChild(icon);
        }

        label.append(node.ItemName);
        a.appendChild(label);
        li.appendChild(a);

        if (node.Children?.length) {
            const group = document.createElement('ul');
            group.role = 'group';
            group.id   = `id-${node.ItemCode.toLowerCase()}-subtree`;
            node.Children.flat().forEach(child => group.appendChild(this.#build(child, level + 1)));
            li.appendChild(group);
        }

        ul.appendChild(li);
        return ul;
    }

    /* ---------- keyboard & click handling ----------------------------- */

    #onActivate(e) {
        e.stopPropagation();
        this.reload?.(e.currentTarget.dataset.itemCode);
    }

    #onKey(e) {
        const key   = e.key;
        const ti    = e.currentTarget;
        const vis   = this.items.filter(n => !this.#parent(n) || this.#parent(n).ariaExpanded === 'true');
        const i     = vis.indexOf(ti);
        let target  = null;

        const move = (idx) => { target = vis[idx]; };
        const next = () => move((i + 1) % vis.length);
        const prev = () => move((i - 1 + vis.length) % vis.length);
        const home = () => move(0);
        const end  = () => move(vis.length - 1);
        const expand = () => {
            if (ti.hasAttribute('aria-expanded')) {
                if (ti.ariaExpanded === 'false') ti.ariaExpanded = 'true';
                    else next();
            }
        };
        const collapse = () => {
            if (ti.hasAttribute('aria-expanded') && ti.ariaExpanded === 'true')
                ti.ariaExpanded = 'false';
                else target = this.#parent(ti);
        };

        /* actions --------------------------------------------------------- */
        const printable = key.length === 1 && /\S/.test(key);
        switch (key) {
            case 'ArrowDown':   next();       break;
            case 'ArrowUp':     prev();       break;
            case 'ArrowRight':  expand();     break;
            case 'ArrowLeft':   collapse();   break;
            case 'Home':        home();       break;
            case 'End':         end();        break;
            case ' ':           ti.click();   break;
            default:
                if (printable) {
                    target = vis.find((n, idx) => idx > i && n.textContent.trim().toLowerCase().startsWith(key.toLowerCase()))
                        || vis.find(n => n.textContent.trim().toLowerCase().startsWith(key.toLowerCase()));
                }
        }

        if (target) {
            target.focus();
            this.items.forEach(n => n.tabIndex = -1);
            target.tabIndex = 0;
            e.preventDefault();
        }
    }

    #focusShell(e) {
        this.navShell.classList.toggle('focus', this.tree.contains(e.target));
    }

    #parent(ti) {
        return ti.parentElement?.parentElement?.previousElementSibling?.role === 'treeitem'
            ? ti.parentElement.parentElement.previousElementSibling : null;
    }
}
