/* ============================================================
   Enterprise Theme — 交互脚本
   1) 亮/暗配色切换（记忆到 localStorage）
   2) 导航栏滚动态、移动端菜单、返回顶部
   ============================================================ */
(function () {
  'use strict';

  var STORAGE_KEY = 'py2htmlblog-enterprise-theme';
  var root = document.documentElement;
  var defaultTheme = root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';

  /* ---------- 配色切换 ---------- */
  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    var btn = document.getElementById('themeToggle');
    if (btn) {
      btn.setAttribute('aria-label', theme === 'light' ? '切换到深色配色' : '切换到亮色配色');
      btn.title = theme === 'light' ? '切换到深色配色' : '切换到亮色配色';
    }
  }

  // 配色由模板决定（enterprise=深色 / enterprise_light=亮色），
  // 仅当用户在页面上手动切换过时才覆盖默认值
  var saved = null;
  try { saved = localStorage.getItem(STORAGE_KEY); } catch (e) { /* 隐私模式忽略 */ }
  applyTheme(saved === 'light' || saved === 'dark' ? saved : defaultTheme);

  var toggle = document.getElementById('themeToggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      applyTheme(next);
      try { localStorage.setItem(STORAGE_KEY, next); } catch (e) { /* ignore */ }
    });
  }

  /* ---------- 导航栏滚动态 ---------- */
  var header = document.getElementById('siteHeader');
  if (header) {
    var onScroll = function () {
      header.classList.toggle('scrolled', window.scrollY > 20);
      var top = document.getElementById('backToTop');
      if (top) top.style.display = window.scrollY > 400 ? 'flex' : 'none';
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------- 移动端菜单 ---------- */
  var menuBtn = document.getElementById('menuToggle');
  var menu = document.getElementById('navMenu');
  if (menuBtn && menu) {
    menuBtn.addEventListener('click', function () {
      menu.classList.toggle('open');
      menuBtn.classList.toggle('active');
    });
    menu.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        menu.classList.remove('open');
        menuBtn.classList.remove('active');
      }
    });
  }

  /* ---------- 返回顶部 ---------- */
  var backBtn = document.getElementById('backToTop');
  if (backBtn) {
    backBtn.addEventListener('click', function (e) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
})();
