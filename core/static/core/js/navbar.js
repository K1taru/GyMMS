// Navbar dropdown behavior (separated)
document.addEventListener('DOMContentLoaded', function(){
  var profileIcon = document.getElementById('profile-icon');
  var profileDropdown = document.getElementById('profile-dropdown');
  if(!profileIcon || !profileDropdown) return;

  profileIcon.addEventListener('click', function(e){
    e.stopPropagation();
    var isShown = profileDropdown.classList.contains('show');
    if(isShown){
      profileDropdown.classList.remove('show');
      profileIcon.setAttribute('aria-expanded','false');
    } else {
      profileDropdown.classList.add('show');
      profileIcon.setAttribute('aria-expanded','true');
    }
  });

  // Close when clicking outside
  window.addEventListener('click', function(event){
    if(event.target !== profileIcon && !profileDropdown.contains(event.target)){
      profileDropdown.classList.remove('show');
      profileIcon.setAttribute('aria-expanded','false');
    }
  });
});
