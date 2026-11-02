/**
 * Agnel Polytechnic SHMS - Core Client Interactions
 */
document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Menu Drawer Navigation
  const menuToggle = document.getElementById('mobileMenuToggle');
  const navLinks = document.getElementById('navLinks');

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', function () {
      const isExpanded = menuToggle.getAttribute('aria-expanded') === 'true';
      menuToggle.setAttribute('aria-expanded', !isExpanded);
      navLinks.classList.toggle('is-open');
    });

    // Close mobile nav on Esc key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && navLinks.classList.contains('is-open')) {
        navLinks.classList.remove('is-open');
        menuToggle.setAttribute('aria-expanded', 'false');
      }
    });

    // Close mobile nav when clicking outside
    document.addEventListener('click', function (e) {
      if (navLinks.classList.contains('is-open')) {
        if (!navLinks.contains(e.target) && !menuToggle.contains(e.target)) {
          navLinks.classList.remove('is-open');
          menuToggle.setAttribute('aria-expanded', 'false');
        }
      }
    });
  }

  // 2. Dismissible Flash Alerts
  const alertCloseButtons = document.querySelectorAll('.alert-close');
  alertCloseButtons.forEach(button => {
    button.addEventListener('click', function () {
      const alert = this.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 200);
      }
    });
  });

  // 3. Password Visibility Toggle
  const toggleButtons = document.querySelectorAll('.password-toggle-btn');
  toggleButtons.forEach(btn => {
    btn.addEventListener('click', function () {
      const targetId = this.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        const isPassword = input.getAttribute('type') === 'password';
        input.setAttribute('type', isPassword ? 'text' : 'password');
        this.textContent = isPassword ? 'Hide' : 'Show';
        this.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
      }
    });
  });

  // 4. Update Unread Notification Counter for logged-in users
  const notifBadge = document.getElementById('notifCountBadge');
  if (notifBadge) {
    fetch('/notifications/unread-count')
      .then(response => response.json())
      .then(data => {
        if (data.unread_count > 0) {
          notifBadge.textContent = data.unread_count;
          notifBadge.style.display = 'inline-block';
        } else {
          notifBadge.style.display = 'none';
        }
      })
      .catch(() => {});
  }
});
