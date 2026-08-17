/**
 * AgriTinyML Lab — Main Application Controller
 * TEAM TRONICS | Group B2
 * Handles SPA navigation, mobile menu, and app initialization.
 */

const App = (() => {
  'use strict';

  let currentPage = 'dashboard';

  function navigate(page) {
    // Hide current
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => {
      n.classList.remove('active');
      n.removeAttribute('aria-current');
    });

    // Show new
    const section = document.getElementById(`page-${page}`);
    const navBtn  = document.getElementById(`nav-${page}`);

    if (section) section.classList.add('active');
    if (navBtn) {
      navBtn.classList.add('active');
      navBtn.setAttribute('aria-current', 'page');
    }

    currentPage = page;

    // Update URL hash for bookmarking
    window.location.hash = page;

    // Close mobile nav
    const nav = document.getElementById('app-nav');
    nav.classList.remove('open');
    document.getElementById('menu-toggle')?.setAttribute('aria-expanded', 'false');

    // Scroll to top
    document.getElementById('app-main').scrollTo({ top: 0, behavior: 'smooth' });

    // Trigger page-specific init
    switch (page) {
      case 'evaluation':  if (window.EvaluationPage)  EvaluationPage.init();  break;
      case 'comparison':  if (window.ComparisonPage)  ComparisonPage.init();  break;
      case 'architecture': if (window.ArchPage)       ArchPage.init();        break;
      case 'experiments': if (window.ExperimentsPage) ExperimentsPage.init(); break;
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function initNav() {
    // Wire up nav buttons
    document.querySelectorAll('.nav-item[data-page]').forEach(btn => {
      btn.addEventListener('click', () => navigate(btn.dataset.page));
    });

    // Mobile menu toggle
    const toggle = document.getElementById('menu-toggle');
    const nav    = document.getElementById('app-nav');
    if (toggle && nav) {
      toggle.addEventListener('click', () => {
        const isOpen = nav.classList.toggle('open');
        toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      });
      // Close nav on outside click
      document.addEventListener('click', e => {
        if (!nav.contains(e.target) && !toggle.contains(e.target)) {
          nav.classList.remove('open');
          toggle.setAttribute('aria-expanded', 'false');
        }
      });
    }

    // Handle hash on load
    const hash = window.location.hash.replace('#', '');
    const pages = ['dashboard','models','playground','evaluation','comparison','experiments','architecture','project','team'];
    if (hash && pages.includes(hash)) {
      navigate(hash);
    }
  }

  async function checkHealth() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        document.getElementById('system-status-pill').className = 'status-pill online';
        document.getElementById('inference-status-val').textContent = 'ACTIVE';
      }
    } catch {
      document.getElementById('system-status-pill').className = 'status-pill offline';
      document.getElementById('inference-status-val').textContent = 'OFFLINE';
      document.getElementById('inference-status-val').style.color = 'var(--accent-red)';
    }
  }

  function init() {
    initNav();
    checkHealth();
    // Wire playground button in nav
    const pgBtn = document.getElementById('nav-playground');
    if (pgBtn) pgBtn.addEventListener('click', () => navigate('playground'));
  }

  return { init, navigate };
})();

document.addEventListener('DOMContentLoaded', App.init);
