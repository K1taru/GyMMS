# Input Validator - Quick Reference Guide

This validator automatically detects and validates input fields based on their
name or id attributes. No manual initialization needed in most cases!

---

## AUTOMATIC VALIDATION (No code needed - just use these field names/IDs)

### NUMBERS ONLY
```html
<input name="phone_number">
<input name="phone">
<input id="phone">
<input name="emergency_phone">
<input id="emergencyPhone">
```

### LETTERS AND SYMBOLS ONLY (no numbers)
```html
<input name="name">
<input id="name">
<input name="emergency_contact">
<input id="emergencyContact">
```

### EMAIL
```html
<input type="email">
<input name="email">
<input id="email">
```

### DECIMAL/CURRENCY
```html
<input name="price">
<input name="amount">
<input name="membership_fee">
```

---

## CUSTOM VALIDATION (Use `data-validate` attribute)

- Numbers only:
  ```html
  <input type="text" data-validate="numbersOnly">
  ```
- Letters and symbols (no numbers):
  ```html
  <input type="text" data-validate="lettersAndSymbolsOnly">
  ```
- Alphanumeric only:
  ```html
  <input type="text" data-validate="alphanumericOnly">
  ```
- Decimal numbers:
  ```html
  <input type="text" data-validate="decimalOnly">
  ```
- Email:
  ```html
  <input type="text" data-validate="email">
  ```

---

## MANUAL API USAGE (For dynamic forms or special cases)

- Initialize validation on page load (automatic by default):
  ```js
  window.InputValidator.init();
  ```
- Re-initialize after adding new form fields dynamically:
  ```js
  window.InputValidator.reinit();
  ```
- Apply validation to a specific field:
  ```js
  const phoneInput = document.getElementById('myPhoneInput');
  window.InputValidator.applyValidation(phoneInput, 'numbersOnly');
  ```

---

## VALIDATION TYPES

Available validation types:
- `numbersOnly`           → Only digits 0-9
- `lettersAndSymbolsOnly` → Letters, spaces, symbols (no numbers)
- `nameOnly`              → Letters, spaces, hyphens, apostrophes
- `alphanumericOnly`      → Letters and numbers only
- `decimalOnly`           → Numbers and decimal point
- `email`                 → Valid email format

---

## NOTIFICATIONS

- Notifications appear automatically when invalid input is attempted
- They appear in the upper-right corner and auto-dismiss after 2 seconds
- Cooldown period prevents notification spam (2 seconds between notifications)

---

## EXAMPLES

**Example 1:** Basic phone number field (auto-detected)
```html
<input type="tel" name="phone_number" placeholder="Phone Number">
```

**Example 2:** Custom validation for employee ID
```html
<input type="text" data-validate="alphanumericOnly" name="employee_id">
```

**Example 3:** Dynamic form field with manual validation
```js
const newInput = document.createElement('input');
newInput.type = 'text';
newInput.name = 'custom_field';
document.getElementById('myForm').appendChild(newInput);
window.InputValidator.applyValidation(newInput, 'numbersOnly');
```

---

## INTEGRATION WITH TEMPLATES

Make sure to include these scripts in your template:
```html
<script defer src="{% static 'core/js/notifications.js' %}"></script>
<script defer src="{% static 'core/js/input-validator.js' %}"></script>
```

The validator will automatically:
1. Scan all inputs on page load
2. Detect validation type based on field name/id
3. Apply real-time validation
4. Show notifications for invalid input
5. Handle paste events
6. Watch for dynamically added forms (modals, AJAX content)

---

## TESTING

Test checklist:
- ✓ Type invalid characters - they should not appear
- ✓ Paste content with invalid characters - should be filtered
- ✓ Check notification appears in upper-right corner
- ✓ Verify cursor position is maintained
- ✓ Test in different browsers
- ✓ Test on mobile devices
- ✓ Test with screen readers (validation is non-intrusive)
