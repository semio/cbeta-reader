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
