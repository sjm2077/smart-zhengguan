// 搜索功能（全局）
(function() {
    const searchInput = document.getElementById('searchInput');
    const resultsContainer = document.getElementById('searchResults');
    if (!searchInput || !resultsContainer) {
        console.warn('搜索元素未找到，请检查页面是否有 searchInput 和 searchResults 元素');
        return;
    }

    let debounceTimer;

    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const q = this.value.trim();
        if (q.length < 2) {
            resultsContainer.style.display = 'none';
            return;
        }
        debounceTimer = setTimeout(() => {
            fetch(`/api/search?q=${encodeURIComponent(q)}`)
                .then(res => res.json())
                .then(data => {
                    renderSearchResults(data);
                })
                .catch(err => {
                    console.error('搜索失败', err);
                    resultsContainer.style.display = 'none';
                });
        }, 300);
    });

    // 点击其他区域关闭下拉
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-box')) {
            resultsContainer.style.display = 'none';
        }
    });

    function renderSearchResults(data) {
        const hasResults = data.projects.length > 0 || data.achievements.length > 0 || data.teachers.length > 0;
        if (!hasResults) {
            resultsContainer.innerHTML = `<div style="padding:15px; color:#999;">未找到相关结果</div>`;
            resultsContainer.style.display = 'block';
            return;
        }

        let html = '';

        // 项目
        if (data.projects.length > 0) {
            html += `<div style="padding:8px 15px; background:#f8f9fa; font-weight:bold; color:#555;">项目</div>`;
            data.projects.forEach(p => {
                html += `<div class="search-result-item" data-type="project" data-id="${p.id}">
                    <span class="type-badge badge-project">项目</span>
                    <span class="title">${escapeHtml(p.project_name)}</span>
                    <span class="sub">${escapeHtml(p.leader__real_name)} | ${escapeHtml(p.subject || '未分类')}</span>
                </div>`;
            });
        }

        // 成果
        if (data.achievements.length > 0) {
            html += `<div style="padding:8px 15px; background:#f8f9fa; font-weight:bold; color:#555;">成果</div>`;
            data.achievements.forEach(a => {
                html += `<div class="search-result-item" data-type="achievement" data-id="${a.id}">
                    <span class="type-badge badge-achievement">成果</span>
                    <span class="title">${escapeHtml(a.title)}</span>
                    <span class="sub">${escapeHtml(a.author__real_name)} | ${a.publish_year}</span>
                </div>`;
            });
        }

        // 教师
        if (data.teachers.length > 0) {
            html += `<div style="padding:8px 15px; background:#f8f9fa; font-weight:bold; color:#555;">教师</div>`;
            data.teachers.forEach(t => {
                html += `<div class="search-result-item" data-type="teacher" data-id="${t.id}">
                    <span class="type-badge badge-teacher">教师</span>
                    <span class="title">${escapeHtml(t.real_name)}</span>
                    <span class="sub">${escapeHtml(t.title || '')} | ${escapeHtml(t.dept__dept_name || '')}</span>
                </div>`;
            });
        }

        resultsContainer.innerHTML = html;
        resultsContainer.style.display = 'block';

        // 绑定点击事件（委托）
        resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', function() {
                const type = this.dataset.type;
                const id = this.dataset.id;
                let url = '';
                if (type === 'project') url = `/project/?id=${id}`;
                else if (type === 'achievement') url = `/achievement/?id=${id}`;
                else if (type === 'teacher') url = `/analysis/teacher/?id=${id}`;
                if (url) window.location.href = url;
                resultsContainer.style.display = 'none';
            });
        });
    }

    // 简单的转义（防止 XSS）
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();