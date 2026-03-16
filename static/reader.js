const readerEl = document.querySelector('.reader');
const TEXT_ID = readerEl.dataset.textId;
const JUAN = parseInt(readerEl.dataset.juan, 10);
const TEXT_TITLE = readerEl.dataset.title;

function toggleToc() {
    const sidebar = document.getElementById('toc-sidebar');
    const toggle = document.getElementById('toc-toggle');
    sidebar.classList.toggle('open');
    toggle.classList.toggle('hidden');
}

/* --- Reading progress --- */
function getScrollElement() {
    const isVertical = document.documentElement.classList.contains('vertical');
    return isVertical ? readerEl : document.documentElement;
}

function findNearestAnchor() {
    const anchors = document.querySelectorAll('.reader .pb[id], .reader h3[id]');
    if (!anchors.length) return null;
    const isVertical = document.documentElement.classList.contains('vertical');
    let best = null;
    for (const a of anchors) {
        const rect = a.getBoundingClientRect();
        const passed = isVertical
            ? rect.right >= window.innerWidth - 10
            : rect.top <= 10;
        if (passed) best = a.id;
    }
    return best || anchors[0].id;
}

function saveProgress() {
    const anchor = findNearestAnchor();
    const data = {
        text_id: TEXT_ID,
        juan: JUAN,
        title: TEXT_TITLE,
        anchor: anchor,
        timestamp: Date.now()
    };
    localStorage.setItem('readingProgress', JSON.stringify(data));
}

function restoreProgress() {
    try {
        const progress = JSON.parse(localStorage.getItem('readingProgress'));
        if (!progress || progress.text_id !== TEXT_ID || progress.juan !== JUAN) return;
        if (!progress.anchor) return;
        const hash = window.location.hash.slice(1);
        if (hash && hash !== progress.anchor) return;
        const target = document.getElementById(progress.anchor);
        if (!target) return;
        const isVertical = document.documentElement.classList.contains('vertical');
        if (isVertical) {
            const targetRect = target.getBoundingClientRect();
            const readerRect = readerEl.getBoundingClientRect();
            readerEl.scrollLeft += targetRect.right - readerRect.right;
        } else {
            target.scrollIntoView();
        }
        const toast = document.createElement('div');
        toast.className = 'restore-toast';
        toast.textContent = '已恢復上次閱讀位置';
        document.body.appendChild(toast);
        setTimeout(() => toast.classList.add('visible'), 10);
        setTimeout(() => {
            toast.classList.remove('visible');
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    } catch(e) {}
}

let scrollTimer;
function onScroll() {
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(saveProgress, 300);
}

window.addEventListener('scroll', onScroll, { passive: true });
if (readerEl) readerEl.addEventListener('scroll', onScroll, { passive: true });

// Defer restore to after layout is complete (needed for vertical mode)
requestAnimationFrame(() => requestAnimationFrame(restoreProgress));

// Convert vertical mouse wheel to horizontal scroll when in vertical mode
if (readerEl) readerEl.addEventListener('wheel', function(e) {
    if (!document.documentElement.classList.contains('vertical')) return;
    if (e.deltaX) return;
    e.preventDefault();
    readerEl.scrollLeft -= e.deltaY;
}, { passive: false });

// Save text info so "繼續閱讀" shows this text, but preserve existing anchor
(function() {
    try {
        const existing = JSON.parse(localStorage.getItem('readingProgress'));
        if (existing && existing.text_id === TEXT_ID && existing.juan === JUAN && existing.anchor) return;
    } catch(e) {}
    localStorage.setItem('readingProgress', JSON.stringify({
        text_id: TEXT_ID, juan: JUAN, title: TEXT_TITLE, anchor: null, timestamp: Date.now()
    }));
})();

/* --- Bookmarks (reader-specific: addBookmark) --- */
function addBookmark() {
    const bm = getBookmarks();
    const anchor = findNearestAnchor();
    bm.unshift({
        text_id: TEXT_ID,
        juan: JUAN,
        title: TEXT_TITLE,
        anchor: anchor,
        timestamp: Date.now()
    });
    saveBookmarks(bm);
    renderBookmarks();
}
