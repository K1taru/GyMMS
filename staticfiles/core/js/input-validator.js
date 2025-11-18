/**
 * Global Input Validation System
 * Provides real-time input validation and formatting for forms
 */

(function() {
    'use strict';

    /**
     * Validation patterns
     */
    const VALIDATION_PATTERNS = {
        // Letters, spaces, hyphens, apostrophes only (for names)
        nameOnly: /[^a-zA-Z\s\-']/g,
        
        // Numbers only (for phone numbers, IDs, etc.)
        numbersOnly: /[^\d]/g,
        
        // Letters and symbols (no numbers) - for names and emergency contacts
        lettersAndSymbolsOnly: /[0-9]/g,
        
        // Email validation (allow standard email characters)
        email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        
        // Alphanumeric only
        alphanumericOnly: /[^a-zA-Z0-9]/g,
        
        // Decimal numbers (for currency/prices)
        decimalOnly: /[^\d.]/g,
    };

    /**
     * Apply validation to an input field
     * @param {HTMLInputElement} input - The input element
     * @param {string} validationType - Type of validation to apply
     */
    function applyValidation(input, validationType) {
        if (!input) return;

        const pattern = VALIDATION_PATTERNS[validationType];
        if (!pattern) {
            console.warn(`Unknown validation type: ${validationType}`);
            return;
        }

        // Mark input as validated to avoid duplicate handlers
        if (input.dataset.validated === 'true') return;
        input.dataset.validated = 'true';

        // Special handling for email (pattern check only, no replacement)
        if (validationType === 'email') {
            input.addEventListener('blur', function() {
                const value = this.value.trim();
                if (value && !pattern.test(value)) {
                    showNotification('Please enter a valid email address', 'warning');
                }
            });
            return;
        }

        // Special handling for decimal (only one decimal point allowed)
        if (validationType === 'decimalOnly') {
            input.addEventListener('input', function() {
                let value = this.value.replace(pattern, '');
                
                // Ensure only one decimal point
                const parts = value.split('.');
                if (parts.length > 2) {
                    value = parts[0] + '.' + parts.slice(1).join('');
                }
                
                this.value = value;
            });
            return;
        }

        // Store last notification time to prevent spam
        let lastNotificationTime = 0;
        const notificationCooldown = 2000; // 2 seconds

        // Real-time validation for text patterns
        input.addEventListener('input', function() {
            const cursorPosition = this.selectionStart;
            const originalLength = this.value.length;
            const originalValue = this.value;
            
            // Apply pattern filter
            this.value = this.value.replace(pattern, '');
            
            // Restore cursor position
            const newLength = this.value.length;
            const lengthDiff = originalLength - newLength;
            
            if (lengthDiff > 0) {
                this.setSelectionRange(
                    Math.max(0, cursorPosition - lengthDiff),
                    Math.max(0, cursorPosition - lengthDiff)
                );
                
                // Show notification for first invalid input (with cooldown)
                const now = Date.now();
                if (originalValue !== this.value && now - lastNotificationTime > notificationCooldown) {
                    const message = getValidationMessage(validationType);
                    showNotification(message, 'warning', 2000);
                    lastNotificationTime = now;
                }
            }
        });

        // Paste validation
        input.addEventListener('paste', function(e) {
            e.preventDefault();
            const pastedText = (e.clipboardData || window.clipboardData).getData('text');
            const cleanedText = pastedText.replace(pattern, '');
            
            // Insert cleaned text at cursor position
            const start = this.selectionStart;
            const end = this.selectionEnd;
            const currentValue = this.value;
            
            this.value = currentValue.substring(0, start) + cleanedText + currentValue.substring(end);
            
            // Set cursor position
            const newPosition = start + cleanedText.length;
            this.setSelectionRange(newPosition, newPosition);
            
            // Trigger input event for any listeners
            this.dispatchEvent(new Event('input', { bubbles: true }));
            
            if (pastedText !== cleanedText) {
                const message = getValidationMessage(validationType);
                showNotification(message, 'warning');
            }
        });
    }

    /**
     * Get user-friendly validation message
     * @param {string} validationType - Type of validation
     * @returns {string} - User-friendly message
     */
    function getValidationMessage(validationType) {
        const messages = {
            nameOnly: 'Only letters, spaces, hyphens, and apostrophes are allowed',
            numbersOnly: 'Only numbers are allowed',
            lettersAndSymbolsOnly: 'Numbers are not allowed in this field',
            alphanumericOnly: 'Only letters and numbers are allowed',
            decimalOnly: 'Only numbers and decimal point are allowed',
            email: 'Please enter a valid email address'
        };
        
        return messages[validationType] || 'Invalid input';
    }

    /**
     * Auto-detect and apply validation based on input attributes
     * Looks for data-validate attribute or infers from name/id
     */
    function autoDetectValidation() {
        // Fields that should have numbers-only validation
        const numberFields = document.querySelectorAll(
            'input[name="phone_number"], input[name="phone"], ' +
            'input[id="phone_number"], input[id="staffPhone"], input[id="phone"], ' +
            'input[name="emergency_phone"], input[id="emergency_phone"], input[id="emergencyPhone"]'
        );
        numberFields.forEach(input => applyValidation(input, 'numbersOnly'));

        // Fields that should have letters and symbols only (no numbers)
        const nameFields = document.querySelectorAll(
            'input[name="name"], input[id="name"], input[id="staffName"], ' +
            'input[name="emergency_contact"], input[id="emergency_contact"], input[id="emergencyContact"], ' +
            'input[id="guestName"]'
        );
        nameFields.forEach(input => applyValidation(input, 'lettersAndSymbolsOnly'));

        // Email fields
        const emailFields = document.querySelectorAll(
            'input[type="email"], input[name="email"], input[id="email"], input[id="staffEmail"]'
        );
        emailFields.forEach(input => applyValidation(input, 'email'));

        // Decimal/price fields
        const priceFields = document.querySelectorAll(
            'input[name="price"], input[name="amount"], input[name="membership_fee"], ' +
            'input[id="price"], input[id="amount"], input[id="membershipFee"]'
        );
        priceFields.forEach(input => applyValidation(input, 'decimalOnly'));

        // Custom data-validate attributes
        const customValidationFields = document.querySelectorAll('[data-validate]');
        customValidationFields.forEach(input => {
            const validationType = input.getAttribute('data-validate');
            applyValidation(input, validationType);
        });
    }

    /**
     * Initialize validation system
     * Can be called manually or automatically on DOM load
     */
    function initInputValidation() {
        autoDetectValidation();
    }

    /**
     * Re-initialize validation (useful for dynamically added forms)
     */
    function reinitInputValidation() {
        autoDetectValidation();
    }

    // Auto-initialize on DOM load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initInputValidation);
    } else {
        initInputValidation();
    }

    // Expose to global scope
    window.InputValidator = {
        init: initInputValidation,
        reinit: reinitInputValidation,
        applyValidation: applyValidation,
        PATTERNS: VALIDATION_PATTERNS
    };

    // Listen for dynamic content changes (e.g., modals opening)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        // Check if the added node is a modal or contains form inputs
                        if (node.classList && (node.classList.contains('modal') || node.querySelector('input'))) {
                            // Small delay to ensure modal is fully rendered
                            setTimeout(reinitInputValidation, 100);
                        }
                    }
                });
            }
        });
    });

    // Observe the entire document for modal additions
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

})();
