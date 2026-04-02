/* ============================================
   CLIENT PORTAL - JavaScript
   ============================================ */

// ─── Theme Management ──────────────────────────
function toggleTheme() {
  const html = document.documentElement;
  const icon = document.getElementById('themeIcon');
  const current = html.getAttribute('data-theme');

  if (current === 'dark') {
    html.removeAttribute('data-theme');
    localStorage.setItem('portal-theme', 'light');
    if (icon) {
      icon.classList.remove('fa-sun');
      icon.classList.add('fa-moon');
    }
  } else {
    html.setAttribute('data-theme', 'dark');
    localStorage.setItem('portal-theme', 'dark');
    if (icon) {
      icon.classList.remove('fa-moon');
      icon.classList.add('fa-sun');
    }
  }
}

// Apply saved theme on load
(function() {
  const saved = localStorage.getItem('portal-theme');
  if (saved === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    const icon = document.getElementById('themeIcon');
    if (icon) {
      icon.classList.remove('fa-moon');
      icon.classList.add('fa-sun');
    }
  }
})();


// ─── User Dropdown ─────────────────────────────
function toggleUserDropdown() {
  const dropdown = document.getElementById('userDropdown');
  if (dropdown) {
    dropdown.classList.toggle('show');
  }
}

// Close dropdown on click outside
document.addEventListener('click', function(e) {
  const dropdown = document.getElementById('userDropdown');
  const btn = document.querySelector('.portal-user-btn');
  if (dropdown && btn && !btn.contains(e.target) && !dropdown.contains(e.target)) {
    dropdown.classList.remove('show');
  }
});


// ─── Mobile Navigation ─────────────────────────
function togglePortalNav() {
  const nav = document.getElementById('portalNavLinks');
  if (nav) {
    nav.classList.toggle('show');
  }
}


// ─── Alert Auto-dismiss ────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function(alert) {
    setTimeout(function() {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      alert.style.transition = 'all 0.3s ease';
      setTimeout(function() { alert.remove(); }, 300);
    }, 5000);
  });
});
