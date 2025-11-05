// Wait until DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
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

    // === Toggle Login / Register forms on landing page ===
    (function(){
        var toggleBtn = document.getElementById('toggle-btn');
        var loginForm = document.getElementById('login-form');
        var registerForm = document.getElementById('register-form');
        var formTitle = document.getElementById('form-title');
        var formError = document.getElementById('form-error');

        if (!toggleBtn) return;

        toggleBtn.addEventListener('click', function(e){
            e.preventDefault();
            var showingRegister = !registerForm.classList.contains('hidden');
            if (showingRegister) {
                // switch to login
                registerForm.classList.add('hidden');
                loginForm.classList.remove('hidden');
                formTitle.textContent = 'Login';
                toggleBtn.textContent = 'Register';
            } else {
                // switch to register
                loginForm.classList.add('hidden');
                registerForm.classList.remove('hidden');
                formTitle.textContent = 'Register';
                toggleBtn.textContent = 'Login';
            }
            if (formError) { formError.classList.add('hidden'); }
        });
    })();
});

