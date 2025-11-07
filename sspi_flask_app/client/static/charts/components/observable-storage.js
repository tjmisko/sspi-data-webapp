class ObservableStorage {
    constructor() {
        this.listeners = {};
        this.store = {};

        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            this.store[key] = this._parse(localStorage.getItem(key));
        }
    }

    setItem(key, value) {
        const oldValue = this.store[key];
        const stringValue = JSON.stringify(value);
        localStorage.setItem(key, stringValue);
        this.store[key] = value;
        this._emit(key, oldValue, value);
    }

    getItem(key) {
        return this.store[key];
    }

    removeItem(key) {
        const oldValue = this.store[key];
        localStorage.removeItem(key);
        delete this.store[key];
        this._emit(key, oldValue, undefined);
    }

    clear() {
        for (const key of Object.keys(this.store)) {
            this.removeItem(key);
        }
    }

    onChange(key, callback) {
        if (!this.listeners[key]) {
            this.listeners[key] = [];
        }
        this.listeners[key].push(callback);
    }

    _emit(key, oldValue, newValue) {
        // if (JSON.stringify(oldValue) === JSON.stringify(newValue)) return;
        const callbacks = this.listeners[key] || [];
        for (const cb of callbacks) {
            cb(oldValue, newValue);
        }
    }

    _parse(value) {
        try {
            return JSON.parse(value);
        } catch {
            return value;
        }
    }
}

