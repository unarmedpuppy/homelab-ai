/**
 * Dashboard Utility Functions
 * 
 * Shared utilities for dashboard JavaScript functionality.
 * These functions can be used across multiple dashboard pages.
 */

/**
 * Format a number as currency
 * @param {number} value - The value to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted currency string (e.g., "$1,234.56")
 */
function formatCurrency(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'N/A';
    }
    return '$' + value.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Format a number as percentage
 * @param {number} value - The value to format (0.685 = 68.5%)
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted percentage string (e.g., "68.5%")
 */
function formatPercentage(value, decimals = 1) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'N/A';
    }
    return (value * 100).toFixed(decimals) + '%';
}

/**
 * Format a timestamp to relative time (e.g., "2 minutes ago")
 * @param {Date|string} timestamp - The timestamp to format
 * @returns {string} Relative time string
 */
function formatTimeAgo(timestamp) {
    if (!timestamp) return 'Unknown';
    
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
    if (isNaN(date.getTime())) return 'Invalid date';
    
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) {
        return seconds === 1 ? '1 second ago' : `${seconds} seconds ago`;
    }
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
        return minutes === 1 ? '1 minute ago' : `${minutes} minutes ago`;
    }
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
        return hours === 1 ? '1 hour ago' : `${hours} hours ago`;
    }
    
    const days = Math.floor(hours / 24);
    if (days < 7) {
        return days === 1 ? '1 day ago' : `${days} days ago`;
    }
    
    // For older dates, show actual date
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Format a timestamp to readable time format
 * @param {Date|string} timestamp - The timestamp to format
 * @param {boolean} includeDate - Whether to include date (default: false)
 * @returns {string} Formatted time string
 */
function formatTime(timestamp, includeDate = false) {
    if (!timestamp) return 'N/A';
    
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
    if (isNaN(date.getTime())) return 'Invalid date';
    
    const options = {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    };
    
    if (includeDate) {
        options.month = 'short';
        options.day = 'numeric';
        options.year = 'numeric';
    }
    
    return date.toLocaleTimeString([], options);
}

/**
 * Get color class for P&L values (positive = green, negative = red)
 * @param {number} value - The P&L value
 * @returns {string} Tailwind CSS color class
 */
function getPnLColorClass(value) {
    if (value === null || value === undefined || isNaN(value)) {
        return 'text-gray-500';
    }
    return value >= 0 ? 'text-green-600' : 'text-red-600';
}

/**
 * Format P&L value with sign and color
 * @param {number} value - The P&L value
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {Object} Object with formatted text and color class
 */
function formatPnL(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) {
        return {
            text: 'N/A',
            colorClass: 'text-gray-500',
            sign: ''
        };
    }
    
    const sign = value >= 0 ? '+' : '';
    const absValue = Math.abs(value);
    const colorClass = getPnLColorClass(value);
    
    return {
        text: `${sign}$${absValue.toFixed(decimals)}`,
        colorClass: colorClass,
        sign: sign
    };
}

/**
 * Show an error message to the user
 * @param {string} message - Error message to display
 * @param {Error|Object} error - Optional error object for details
 * @param {HTMLElement} container - Optional container element (default: document.body)
 */
function showErrorMessage(message, error = null, container = null) {
    const targetContainer = container || document.body;
    
    // Limit concurrent error messages to prevent page growth
    const existingErrors = targetContainer.querySelectorAll('.error-alert-toast');
    const MAX_ERRORS = 3;
    
    // Remove oldest errors if we're at the limit
    if (existingErrors.length >= MAX_ERRORS) {
        existingErrors[existingErrors.length - 1].remove();
    }
    
    // Check if this exact error message is already displayed (prevent duplicates)
    const errorText = error ? (error.message || String(error)) : '';
    const allErrorMessages = Array.from(targetContainer.querySelectorAll('.error-alert-toast'));
    const isDuplicate = allErrorMessages.some(el => {
        const msgEl = el.querySelector('.font-medium');
        const detailEl = el.querySelector('.text-sm');
        return msgEl && msgEl.textContent === message && 
               (!errorText || !detailEl || detailEl.textContent === errorText);
    });
    
    if (isDuplicate) {
        // Don't show duplicate errors
        return;
    }
    
    // Create error alert element
    const alert = document.createElement('div');
    alert.className = 'error-alert-toast fixed top-4 right-4 bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded shadow-lg z-50 max-w-md';
    alert.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <i class="fas fa-exclamation-circle text-red-500"></i>
            </div>
            <div class="ml-3 flex-1">
                <p class="font-medium">${escapeHtml(message)}</p>
                ${error ? `<p class="mt-1 text-sm text-red-600">${escapeHtml(error.message || String(error))}</p>` : ''}
            </div>
            <div class="ml-4">
                <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                        class="text-red-500 hover:text-red-700">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
    
    // Position based on existing errors
    const topOffset = 4 + (existingErrors.length * 80); // 80px per error
    alert.style.top = `${topOffset}px`;
    
    targetContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Show a success message to the user
 * @param {string} message - Success message to display
 * @param {HTMLElement} container - Optional container element (default: document.body)
 */
function showSuccessMessage(message, container = null) {
    const targetContainer = container || document.body;
    
    const alert = document.createElement('div');
    alert.className = 'fixed top-4 right-4 bg-green-50 border-l-4 border-green-500 text-green-700 p-4 rounded shadow-lg z-50 max-w-md';
    alert.innerHTML = `
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <i class="fas fa-check-circle text-green-500"></i>
            </div>
            <div class="ml-3 flex-1">
                <p class="font-medium">${escapeHtml(message)}</p>
            </div>
            <div class="ml-4">
                <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                        class="text-green-500 hover:text-green-700">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
    
    targetContainer.appendChild(alert);
    
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 3000);
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML string
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Make an API call with error handling
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options (method, headers, body, etc.)
 * @returns {Promise<Object>} Response data or null on error
 */
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
            throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        return { ok: true, data, response };
    } catch (error) {
        console.error(`API call failed: ${url}`, error);
        return { ok: false, error: error.message, data: null };
    }
}

/**
 * Debounce function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function calls
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Update a loading state indicator
 * @param {HTMLElement|string} element - Element or selector
 * @param {boolean} isLoading - Whether loading
 */
function setLoadingState(element, isLoading) {
    const el = typeof element === 'string' ? document.querySelector(element) : element;
    if (!el) return;
    
    if (isLoading) {
        el.classList.add('opacity-50', 'pointer-events-none');
        el.setAttribute('data-loading', 'true');
    } else {
        el.classList.remove('opacity-50', 'pointer-events-none');
        el.removeAttribute('data-loading');
    }
}

// Export for use in modules (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatCurrency,
        formatPercentage,
        formatTimeAgo,
        formatTime,
        getPnLColorClass,
        formatPnL,
        showErrorMessage,
        showSuccessMessage,
        escapeHtml,
        apiCall,
        debounce,
        throttle,
        setLoadingState
    };
}

