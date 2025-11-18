// Navbar dropdown behavior
document.addEventListener('DOMContentLoaded', function(){
  console.log('Navbar JS loaded');
  
  // Elements
  const profileIcon = document.getElementById('profile-icon');
  const profileDropdown = document.getElementById('profile-dropdown');
  const authLinks = document.querySelectorAll('[data-requires-auth="true"]');
  const authAlert = document.getElementById('auth-alert');
  const alertOkButton = document.getElementById('alert-ok');
  const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
  const navLinks = document.getElementById('nav-links');
  const mobileOverlay = document.getElementById('mobile-overlay');
  const menuIcon = document.getElementById('menu-icon');
  
  console.log('Profile icon:', profileIcon);
  console.log('Profile dropdown:', profileDropdown);
  console.log('Auth required links:', authLinks.length);
  console.log('Mobile menu toggle:', mobileMenuToggle);
  
  // Mobile menu functionality
  if (mobileMenuToggle && navLinks && mobileOverlay) {
    function toggleMobileMenu() {
      const isOpen = navLinks.classList.contains('show');
      
      if (isOpen) {
        navLinks.classList.remove('show');
        mobileOverlay.classList.remove('show');
        mobileMenuToggle.setAttribute('aria-expanded', 'false');
        menuIcon.textContent = '☰';
        document.body.style.overflow = '';
        console.log('Mobile menu closed');
      } else {
        navLinks.classList.add('show');
        mobileOverlay.classList.add('show');
        mobileMenuToggle.setAttribute('aria-expanded', 'true');
        menuIcon.textContent = '✕';
        document.body.style.overflow = 'hidden';
        console.log('Mobile menu opened');
      }
    }
    
    // Toggle menu on button click
    mobileMenuToggle.addEventListener('click', function(e) {
      e.stopPropagation();
      toggleMobileMenu();
    });
    
    // Close mobile menu when clicking overlay
    mobileOverlay.addEventListener('click', function() {
      if (navLinks.classList.contains('show')) {
        toggleMobileMenu();
      }
    });
    
    // Close mobile menu when clicking a link
    const navLinkElements = navLinks.querySelectorAll('a');
    navLinkElements.forEach(link => {
      link.addEventListener('click', function() {
        if (window.innerWidth <= 768 && navLinks.classList.contains('show')) {
          toggleMobileMenu();
        }
      });
    });
    
    // Close mobile menu on window resize to desktop
    let resizeTimer;
    window.addEventListener('resize', function() {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function() {
        if (window.innerWidth > 768 && navLinks.classList.contains('show')) {
          navLinks.classList.remove('show');
          mobileOverlay.classList.remove('show');
          mobileMenuToggle.setAttribute('aria-expanded', 'false');
          menuIcon.textContent = '☰';
          document.body.style.overflow = '';
          console.log('Mobile menu closed on resize');
        }
      }, 250);
    });
    
    // Close mobile menu on escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && navLinks.classList.contains('show')) {
        toggleMobileMenu();
      }
    });
  }
  
  // Handle authentication required links and profile icon
  if (authLinks.length > 0 && authAlert && alertOkButton) {
    // Function to show alert
    function showAuthAlert(e) {
      e.preventDefault();
      authAlert.classList.add('show');
      alertOkButton.focus();
      
      // Close mobile menu if open
      if (navLinks && navLinks.classList.contains('show') && mobileMenuToggle && mobileOverlay) {
        navLinks.classList.remove('show');
        mobileOverlay.classList.remove('show');
        mobileMenuToggle.setAttribute('aria-expanded', 'false');
        menuIcon.textContent = '☰';
        document.body.style.overflow = '';
      }
    }
    
    // Add click handlers to all auth-required elements
    authLinks.forEach(link => {
      link.addEventListener('click', showAuthAlert);
    });
    
    // Handle alert close button
    alertOkButton.addEventListener('click', function(e) {
      e.preventDefault();
      authAlert.classList.remove('show');
    });
    
    // Close alert when clicking outside
    authAlert.addEventListener('click', function(e) {
      if (e.target === authAlert) {
        authAlert.classList.remove('show');
      }
    });
    
    // Close alert on escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && authAlert.classList.contains('show')) {
        authAlert.classList.remove('show');
      }
    });
  }
  
  // Only run dropdown logic if user is logged in (dropdown exists)
  if(!profileIcon || !profileDropdown) {
    console.log('Profile dropdown not found - user is logged out');
    return;
  }

  // Toggle dropdown when profile icon is clicked
  profileIcon.addEventListener('click', function(e){
    e.stopPropagation();
    e.preventDefault();
    
    const isShown = profileDropdown.classList.contains('show');
    console.log('Icon clicked, current state:', isShown ? 'shown' : 'hidden');
    
    if(isShown){
      profileDropdown.classList.remove('show');
      profileIcon.setAttribute('aria-expanded','false');
      console.log('Hiding dropdown');
    } else {
      profileDropdown.classList.add('show');
      profileIcon.setAttribute('aria-expanded','true');
      console.log('Showing dropdown');
    }
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', function(event){
    if(!profileIcon.contains(event.target) && !profileDropdown.contains(event.target)){
      if(profileDropdown.classList.contains('show')) {
        profileDropdown.classList.remove('show');
        profileIcon.setAttribute('aria-expanded','false');
        console.log('Closing dropdown - clicked outside');
      }
    }
  });

  // Close dropdown on escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && profileDropdown.classList.contains('show')) {
      profileDropdown.classList.remove('show');
      profileIcon.setAttribute('aria-expanded','false');
      console.log('Closing dropdown - escape key');
    }
  });
});
