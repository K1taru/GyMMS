// Wait until DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
    console.log("Index page loaded");
    
    // Focus on username field for better UX
    const usernameInput = document.getElementById('username');
    if (usernameInput) {
        usernameInput.focus();
    }
});
