/* ============================================================
   Enterprise Theme — 亮/暗配色切换
   导航滚动、移动菜单、滚动动画、返回顶部由 js/main.js 负责
   ============================================================ */
(function () {
  'use strict';

  var STORAGE_KEY = 'py2htmlblog-enterprise-theme';
  var root = document.documentElement;
  var defaultTheme = root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    var btn = document.getElementById('themeToggle');
    if (btn) {
      var label = theme === 'light' ? '切换到深色配色' : '切换到亮色配色';
      btn.setAttribute('aria-label', label);
      btn.title = label;
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
})();
