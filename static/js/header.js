// Header sidebar toggle logic
(function(){
  document.addEventListener("DOMContentLoaded", function() {
    const userMenu = document.querySelector('.user-menu');
    const sidebar = document.getElementById('userSidebar');
    const overlay = document.getElementById('sidebarOverlay');

    if (!userMenu || !sidebar || !overlay) return;

    function isOpen() {
      return sidebar.classList.contains('show');
    }

    function openSidebar() {
      sidebar.classList.add('show');
      overlay.classList.add('show');
      userMenu.setAttribute('aria-expanded', 'true');
      const firstLink = sidebar.querySelector('a');
      if (firstLink) firstLink.focus();
    }

    function closeSidebar(returnFocus) {
      sidebar.classList.remove('show');
      overlay.classList.remove('show');
      userMenu.setAttribute('aria-expanded', 'false');
      if (returnFocus) userMenu.focus();
    }

    userMenu.addEventListener('click', (e) => {
      e.stopPropagation();
      if (isOpen()) closeSidebar(true);
      else openSidebar();
    });

    document.addEventListener('click', (e) => {
      const isClickInside = sidebar.contains(e.target) || userMenu.contains(e.target);
      if (!isClickInside && isOpen()) {
        closeSidebar(false);
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && isOpen()) {
        closeSidebar(true);
      }
    });
  });
})();
