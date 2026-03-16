function toggleBookmarks() {
    document.getElementById('bookmark-drawer').classList.toggle('open');
    document.getElementById('bookmark-toggle').classList.toggle('hidden');
}

function getBookmarks() {
    try { return JSON.parse(localStorage.getItem('bookmarks')) || []; }
    catch(e) { return []; }
}

function saveBookmarks(bm) {
    localStorage.setItem('bookmarks', JSON.stringify(bm));
}

function deleteBookmark(idx) {
    const bm = getBookmarks();
    bm.splice(idx, 1);
    saveBookmarks(bm);
    renderBookmarks();
}

function renderBookmarks() {
    const list = document.getElementById('bookmark-list');
    const bm = getBookmarks();
    if (bm.length === 0) {
        list.innerHTML = '<li class="bookmark-empty">尚無書籤</li>';
        return;
    }
    list.innerHTML = bm.map(function(b, i) {
        const date = new Date(b.timestamp).toLocaleDateString('zh-TW');
        const href = '/read/' + b.text_id + '/' + b.juan + (b.anchor ? '#' + b.anchor : '');
        return '<li class="bookmark-item">' +
            '<a href="' + href + '">' +
            '<span class="bookmark-item-title">' + b.title + '</span>' +
            '<span class="bookmark-item-meta">卷' + b.juan + ' · ' + date + '</span>' +
            '</a>' +
            '<button class="bookmark-delete" onclick="deleteBookmark(' + i + ')" title="刪除">&times;</button>' +
            '</li>';
    }).join('');
}

renderBookmarks();

document.addEventListener('click', function(e) {
    const drawer = document.getElementById('bookmark-drawer');
    const btn = document.getElementById('bookmark-toggle');
    if (drawer.classList.contains('open') &&
        !drawer.contains(e.target) && e.target !== btn) {
        toggleBookmarks();
    }
});
