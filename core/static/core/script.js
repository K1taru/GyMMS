// Wait until DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
    // === Profile Dropdown ===
    const profileIcon = document.getElementById("profile-icon");
    const profileDropdown = document.getElementById("profile-dropdown");

    if (profileIcon) {
        profileIcon.addEventListener("click", function () {
            profileDropdown.style.display =
                profileDropdown.style.display === "block" ? "none" : "block";
        });

        // Close dropdown if clicking outside
        window.addEventListener("click", function (event) {
            if (
                event.target !== profileIcon &&
                !profileDropdown.contains(event.target)
            ) {
                profileDropdown.style.display = "none";
            }
        });
    }

    // === Modals ===
    const loginBtn = document.getElementById("login-btn");
    const signupBtn = document.getElementById("signup-btn");
    const loginModal = document.getElementById("login-modal");
    const signupModal = document.getElementById("signup-modal");

    const closeButtons = document.querySelectorAll(".close");

    // Open login modal
    if (loginBtn && loginModal) {
        loginBtn.addEventListener("click", function () {
            loginModal.classList.add("show");
        });
    }

    // Open signup modal
    if (signupBtn && signupModal) {
        signupBtn.addEventListener("click", function () {
            signupModal.classList.add("show");
        });
    }

    // Close modals when clicking "x"
    closeButtons.forEach(function (btn) {
        btn.addEventListener("click", function () {
            const modalId = btn.getAttribute("data-close");
            document.getElementById(modalId).classList.remove("show");
        });
    });

    // Close modals when clicking outside modal content
    window.addEventListener("click", function (event) {
        if (event.target.classList.contains("modal")) {
            event.target.classList.remove("show");
        }
    });
});
