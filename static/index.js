/* --- Continue reading card --- */
(function() {
    try {
        const progress = JSON.parse(localStorage.getItem('readingProgress'));
        if (progress && progress.text_id && progress.title) {
            const card = document.getElementById('continue-reading');
            const link = document.getElementById('continue-reading-link');
            const title = document.getElementById('cr-title');
            const meta = document.getElementById('cr-meta');
            link.href = '/read/' + progress.text_id + '/' + progress.juan + (progress.anchor ? '#' + progress.anchor : '');
            title.textContent = progress.title;
            const date = new Date(progress.timestamp);
            meta.textContent = '卷' + progress.juan + ' · ' + date.toLocaleDateString('zh-TW');
            card.style.display = '';
        }
    } catch(e) {}
})();

/* --- Catalog search --- */
(function() {
    const input = document.getElementById('catalog-search');
    const clearBtn = document.getElementById('catalog-search-clear');
    const catalog = document.querySelector('.catalog');
    const allLinks = catalog.querySelectorAll('.catalog > details a[href^="/read/"]');
    // Pre-build search data: { element, text, id }
    const entries = Array.from(allLinks).map(function(a) {
        // href like "/read/T30n1564/1" → extract text_id "T30n1564"
        const parts = a.getAttribute('href').split('/');
        const textId = parts[2] || '';
        return { el: a, li: a.closest('li'), text: a.textContent, id: textId };
    });

    let debounceTimer;
    input.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(doSearch, 150);
        clearBtn.style.display = input.value ? '' : 'none';
    });

    function doSearch() {
        const q = input.value.trim().toLowerCase();
        if (!q) {
            // Reset: show all, collapse all details
            entries.forEach(function(e) { e.li.style.display = ''; });
            catalog.querySelectorAll('details').forEach(function(d) { d.removeAttribute('open'); });
            catalog.querySelectorAll('li:has(> details)').forEach(function(li) { li.style.display = ''; });
            return;
        }

        // Hide all entries first
        entries.forEach(function(e) { e.li.style.display = 'none'; });
        // Collapse all details and hide category <li>s
        catalog.querySelectorAll('details').forEach(function(d) { d.removeAttribute('open'); });
        catalog.querySelectorAll('li:has(> details)').forEach(function(li) { li.style.display = 'none'; });

        // Show matching entries and open their ancestor details
        entries.forEach(function(e) {
            if (e.text.toLowerCase().indexOf(q) === -1 && e.id.toLowerCase().indexOf(q) === -1) return;
            e.li.style.display = '';
            // Open all ancestor <details> and show their <li> wrappers
            let node = e.li.parentElement;
            while (node && node !== catalog) {
                if (node.tagName === 'DETAILS') {
                    node.setAttribute('open', '');
                    // If this details is inside a <li>, show that <li>
                    if (node.parentElement && node.parentElement.tagName === 'LI') {
                        node.parentElement.style.display = '';
                    }
                }
                node = node.parentElement;
            }
        });
    }

    window.clearSearch = function() {
        input.value = '';
        clearBtn.style.display = 'none';
        doSearch();
        input.focus();
    };
})();
