(function () {
  'use strict';

  const iconMap = [
    { keyword: '在研项目总数', icon: 'fa-folder-open', cls: 'icon-project' },
    { keyword: '科研经费总额', icon: 'fa-money', cls: 'icon-fund' },
    { keyword: '科研成果总数', icon: 'fa-trophy', cls: 'icon-achievement' },
    { keyword: '国家级项目', icon: 'fa-flag', cls: 'icon-national' },
    { keyword: '省部级项目', icon: 'fa-university', cls: 'icon-provincial' },
    { keyword: '横向项目', icon: 'fa-exchange', cls: 'icon-horizontal' },
    { keyword: 'CSSCI论文', icon: 'fa-file-text-o', cls: 'icon-cssci' },
    { keyword: '专著/教材', icon: 'fa-book', cls: 'icon-book' },
    { keyword: '在研率', icon: 'fa-line-chart', cls: 'icon-progress' }
  ];

  function findConfig(text) {
    const raw = (text || '').replace(/\s+/g, '');
    return iconMap.find(item => raw.indexOf(item.keyword.replace(/\s+/g, '')) !== -1);
  }

  function injectIcon(el, mode) {
    if (!el || el.querySelector('.metric-leading-icon')) return;
    const text = (el.textContent || '').trim();
    const cfg = findConfig(text);
    if (!cfg) return;

    el.classList.add(mode === 'label' ? 'metric-label-with-icon' : 'metric-title-with-icon');

    const icon = document.createElement('i');
    icon.className = `fa ${cfg.icon} metric-leading-icon ${cfg.cls}`;
    icon.setAttribute('aria-hidden', 'true');
    el.insertBefore(icon, el.firstChild);
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.grid-container .data-card h3, .grid-container .data-card .title, .grid-container .data-card .card-title')
      .forEach(el => injectIcon(el, 'title'));

    document.querySelectorAll('.grid-6 .mini-card .label, .grid-6 .mini-card h4, .grid-6 .mini-card .title')
      .forEach(el => injectIcon(el, 'label'));
  });
})();