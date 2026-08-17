/**
 * AgriTinyML Lab — Main Application Controller
 * TEAM TRONICS | Group B2
 * Handles SPA navigation, mobile menu, overlay, and bottom nav.
 */

const App = (() => {
  'use strict';

  let currentPage = 'dashboard';

  // Pages that get a bottom nav button
  const BOTTOM_NAV_PAGES = ['dashboard','playground','evaluation','architecture','team'];

  function navigate(page) {
    // Hide all sections
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));

    // Deactivate all sidebar nav items
    document.querySelectorAll('.nav-item').forEach(n => {
      n.classList.remove('active');
      n.removeAttribute('aria-current');
    });

    // Deactivate all bottom nav buttons
    document.querySelectorAll('.mobile-nav-btn').forEach(b => b.classList.remove('active'));

    // Show target section
    const section = document.getElementById(`page-${page}`);
    const navBtn  = document.getElementById(`nav-${page}`);
    const mobBtn  = document.getElementById(`mob-nav-${page}`);

    if (section) section.classList.add('active');
    if (navBtn)  { navBtn.classList.add('active'); navBtn.setAttribute('aria-current', 'page'); }
    if (mobBtn)  mobBtn.classList.add('active');

    currentPage = page;
    window.location.hash = page;

    // Close mobile drawer + overlay
    closeNav();

    // Scroll main to top
    const main = document.getElementById('app-main');
    if (main) main.scrollTo({ top: 0, behavior: 'smooth' });

    // Trigger page-specific init
    switch (page) {
      case 'evaluation':   if (window.EvaluationPage)  EvaluationPage.init();  break;
      case 'comparison':   if (window.ComparisonPage)  ComparisonPage.init();  break;
      case 'architecture': if (window.ArchPage)        ArchPage.init();        break;
      case 'experiments':  if (window.ExperimentsPage) ExperimentsPage.init(); break;
    }
  }

  function openNav() {
    const nav     = document.getElementById('app-nav');
    const toggle  = document.getElementById('menu-toggle');
    const overlay = document.getElementById('nav-overlay');
    if (nav)     nav.classList.add('open');
    if (toggle)  toggle.setAttribute('aria-expanded', 'true');
    if (overlay) overlay.classList.add('show');
    document.body.style.overflow = 'hidden'; // prevent background scroll
  }

  function closeNav() {
    const nav     = document.getElementById('app-nav');
    const toggle  = document.getElementById('menu-toggle');
    const overlay = document.getElementById('nav-overlay');
    if (nav)     nav.classList.remove('open');
    if (toggle)  toggle.setAttribute('aria-expanded', 'false');
    if (overlay) overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  function initNav() {
    // Sidebar nav buttons
    document.querySelectorAll('.nav-item[data-page]').forEach(btn => {
      btn.addEventListener('click', () => navigate(btn.dataset.page));
    });

    // Bottom nav buttons
    document.querySelectorAll('.mobile-nav-btn[data-page]').forEach(btn => {
      btn.addEventListener('click', () => navigate(btn.dataset.page));
    });

    // Hamburger toggle
    const toggle = document.getElementById('menu-toggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        const nav = document.getElementById('app-nav');
        if (nav.classList.contains('open')) closeNav();
        else openNav();
      });
    }

    // Overlay tap — close drawer
    const overlay = document.getElementById('nav-overlay');
    if (overlay) overlay.addEventListener('click', closeNav);

    // Escape key — close drawer
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') closeNav();
    });

    // Hash routing on load
    const hash  = window.location.hash.replace('#', '');
    const pages = ['dashboard','models','playground','evaluation','comparison',
                   'experiments','architecture','project','team'];
    if (hash && pages.includes(hash)) navigate(hash);
  }

  async function checkHealth() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const pill = document.getElementById('system-status-pill');
        if (pill) pill.className = 'status-pill online';
        const val = document.getElementById('inference-status-val');
        if (val) val.textContent = 'ACTIVE';
      }
    } catch {
      const pill = document.getElementById('system-status-pill');
      if (pill) pill.className = 'status-pill offline';
      const val = document.getElementById('inference-status-val');
      if (val) { val.textContent = 'OFFLINE'; val.style.color = 'var(--accent-red)'; }
    }
  }

  function init() {
    initNav();
    checkHealth();
  }

  return { init, navigate };
})();

document.addEventListener('DOMContentLoaded', App.init);
