/**
 * CSRF Token Utilities
 * Provides helper functions for including CSRF tokens in API requests
 */

/**
 * Get the CSRF token from the page's meta tag or hidden input
 * @returns {string|null} The CSRF token or null if not found
 */
function getCSRFToken() {
    // Try to get from meta tag first
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }

    // Fall back to hidden input
    const inputField = document.querySelector('input[name="csrf_token"]');
    if (inputField) {
        return inputField.value;
    }

    // Last resort: check if it's in a global variable
    if (window.csrfToken) {
        return window.csrfToken;
    }

    console.warn('CSRF token not found. Requests may fail.');
    return null;
}

/**
 * Enhanced fetch function that automatically includes CSRF token
 * @param {string} url - The URL to fetch
 * @param {object} options - Fetch options (method, headers, body, etc.)
 * @returns {Promise<Response>} The fetch promise
 */
async function fetchWithCSRF(url, options = {}) {
    const csrfToken = getCSRFToken();

    // Only add CSRF token for state-changing methods
    const method = (options.method || 'GET').toUpperCase();
    const needsCSRF = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method);

    if (needsCSRF && csrfToken) {
        options.headers = {
            ...options.headers,
            'X-CSRFToken': csrfToken
        };
    }

    try {
        const response = await fetch(url, options);

        // Handle CSRF errors specially
        if (response.status === 400 || response.status === 403) {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                if (data.error && (
                    data.error.toLowerCase().includes('csrf') ||
                    data.error.toLowerCase().includes('token')
                )) {
                    console.error('CSRF token validation failed. Token may have expired.');
                    // Optionally trigger a page reload to get a fresh token
                    if (window.notifications) {
                        window.notifications.error('Session expired. Please reload the page.');
                    }
                }
            }
        }

        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

/**
 * Set the CSRF token in a form before submission
 * @param {HTMLFormElement} form - The form element
 */
function addCSRFToForm(form) {
    const csrfToken = getCSRFToken();
    if (!csrfToken) return;

    // Check if form already has a CSRF token field
    let csrfInput = form.querySelector('input[name="csrf_token"]');

    if (!csrfInput) {
        // Create hidden input for CSRF token
        csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        form.appendChild(csrfInput);
    }

    csrfInput.value = csrfToken;
}

/**
 * Initialize CSRF protection for all forms on the page
 * Automatically adds CSRF token to forms without it
 */
function initCSRFProtection() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // Only add to forms that POST/PUT/DELETE
        const method = (form.method || 'get').toUpperCase();
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
            addCSRFToForm(form);
        }
    });
}

// Auto-initialize if DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCSRFProtection);
} else {
    initCSRFProtection();
}

// Export functions for use in other modules
if (typeof window !== 'undefined') {
    window.csrf = {
        getToken: getCSRFToken,
        fetchWithCSRF: fetchWithCSRF,
        addToForm: addCSRFToForm,
        init: initCSRFProtection
    };
}
