(function () {
    'use strict';

    function safeReturnUrl() {
        const raw = new URLSearchParams(location.search).get('return_url');
        if (!raw) return '';
        try {
            const u = new URL(raw, location.origin);
            if (u.origin !== location.origin) return '';
            if (!u.pathname.startsWith('/')) return '';
            return u.pathname + u.search + u.hash;
        } catch (_) {
            return '';
        }
    }

    function fallbackBack(defaultUrl) {
        const ret = safeReturnUrl();
        if (ret) {
            location.href = ret;
            return;
        }

        try {
            if (document.referrer) {
                const ref = new URL(document.referrer);
                if (ref.origin === location.origin && ref.href !== location.href) {
                    history.back();
                    return;
                }
            }
        } catch (_) {}

        location.href = defaultUrl;
    }

    function bindExactText(text, handler) {
        const nodes = Array.from(document.querySelectorAll('a,button'));
        const matches = nodes.filter(el =>
            (el.textContent || '').replace(/\s+/g, ' ').trim() === text
        );
        if (matches.length !== 1) return false;

        const el = matches[0];
        el.addEventListener('click', function (e) {
            e.preventDefault();
            handler(el);
        }, true);
        return true;
    }

    function appendReturnUrlToQueryLinks(root) {
        const current = location.pathname + location.search;
        const scope = root || document;

        scope.querySelectorAll('a[href]').forEach(a => {
            const raw = a.getAttribute('href');
            if (!raw || raw.startsWith('#') || raw.startsWith('javascript:')) return;

            let u;
            try {
                u = new URL(raw, location.origin);
            } catch (_) {
                return;
            }
            if (u.origin !== location.origin) return;

            const isDetail =
                u.pathname.startsWith('/project-detail') ||
                u.pathname.startsWith('/achievement-detail') ||
                u.pathname.startsWith('/analysis/teacher');

            if (!isDetail || u.searchParams.has('return_url')) return;

            u.searchParams.set('return_url', current);
            a.setAttribute('href', u.pathname + u.search + u.hash);
        });
    }

    const p = location.pathname;

    if (p.startsWith('/project-detail')) {
        bindExactText('返回上一页', () => fallbackBack('/research-query/'));
        bindExactText('进入项目管理', () => { location.href = '/project/'; });
    }

    if (p.startsWith('/achievement-detail')) {
        bindExactText('返回上一页', () => fallbackBack('/research-query/'));
        bindExactText('进入成果管理', () => { location.href = '/achievement/'; });
    }

    if (p.startsWith('/analysis/teacher')) {
        const ret = safeReturnUrl();
        if (ret) {
            bindExactText('返回教师目录', () => { location.href = ret; });
        }
    }

    if (p.startsWith('/research-query')) {
        appendReturnUrlToQueryLinks(document);

        const observer = new MutationObserver(records => {
            records.forEach(record => {
                record.addedNodes.forEach(node => {
                    if (node.nodeType === 1) {
                        if (node.matches && node.matches('a[href]')) {
                            appendReturnUrlToQueryLinks(node.parentElement || node);
                        } else {
                            appendReturnUrlToQueryLinks(node);
                        }
                    }
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }
})();
