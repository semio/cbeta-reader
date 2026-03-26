function buildBookmarkDrawer() {
  const drawer = document.getElementById("bookmark-drawer");
  if (drawer.dataset.built) return;
  drawer.dataset.built = "1";
  const isReader = !!document.querySelector(".reader");
  drawer.innerHTML =
    '<div class="bookmark-header">' +
    "<strong>書籤</strong>" +
    '<button class="bookmark-close" onclick="toggleBookmarks()">&times;</button>' +
    "</div>" +
    (isReader
      ? '<button class="bookmark-add-btn" id="bookmark-add" onclick="addBookmark()">＋ 加入書籤</button>'
      : "") +
    '<ul class="bookmark-list" id="bookmark-list"></ul>' +
    '<button class="drawer-close-bottom" onclick="toggleBookmarks()">→</button>';
  renderBookmarks();
}

function toggleBookmarks() {
  buildBookmarkDrawer();
  document.getElementById("bookmark-drawer").classList.toggle("open");
  document.getElementById("bookmark-toggle").classList.toggle("hidden");
}

function getBookmarks() {
  try {
    return JSON.parse(localStorage.getItem("bookmarks")) || [];
  } catch (e) {
    return [];
  }
}

function saveBookmarks(bm) {
  localStorage.setItem("bookmarks", JSON.stringify(bm));
}

function deleteBookmark(idx, event) {
  if (event) event.stopPropagation();
  const bm = getBookmarks();
  bm.splice(idx, 1);
  saveBookmarks(bm);
  renderBookmarks();
}

function renderBookmarks() {
  const list = document.getElementById("bookmark-list");
  const bm = getBookmarks();
  if (bm.length === 0) {
    list.innerHTML = '<li class="bookmark-empty">尚無書籤</li>';
    return;
  }
  // Group bookmarks by text_id, preserving insertion order
  var groups = [];
  var groupMap = {};
  bm.forEach(function (b, i) {
    if (!groupMap[b.text_id]) {
      groupMap[b.text_id] = { title: b.title, text_id: b.text_id, items: [] };
      groups.push(groupMap[b.text_id]);
    }
    groupMap[b.text_id].items.push({ bm: b, idx: i });
  });
  list.innerHTML = groups
    .map(function (g) {
      var items = g.items
        .map(function (item) {
          var b = item.bm;
          var date = new Date(b.timestamp).toLocaleDateString("zh-TW");
          var href =
            "/read/" +
            b.text_id +
            "/" +
            b.juan +
            (b.anchor ? "#" + b.anchor : "");
          return (
            '<li class="bookmark-item">' +
            '<a href="' +
            href +
            '">' +
            '<span class="bookmark-item-meta">卷' +
            b.juan +
            " · " +
            date +
            "</span>" +
            "</a>" +
            '<button class="bookmark-delete" onclick="deleteBookmark(' +
            item.idx +
            ', event)" title="刪除">&times;</button>' +
            "</li>"
          );
        })
        .join("");
      return (
        '<li class="bookmark-group">' +
        '<div class="bookmark-group-header" onclick="this.parentElement.classList.toggle(\'collapsed\')">' +
        '<span class="bookmark-group-arrow">▾</span>' +
        '<span class="bookmark-group-title">' +
        g.title +
        "</span>" +
        '<span class="bookmark-group-count">' +
        g.items.length +
        "</span>" +
        "</div>" +
        '<ul class="bookmark-group-list">' +
        items +
        "</ul>" +
        "</li>"
      );
    })
    .join("");
}

document.addEventListener("click", function (e) {
  const drawer = document.getElementById("bookmark-drawer");
  const btn = document.getElementById("bookmark-toggle");
  if (
    drawer.classList.contains("open") &&
    !drawer.contains(e.target) &&
    e.target !== btn
  ) {
    toggleBookmarks();
  }
});
