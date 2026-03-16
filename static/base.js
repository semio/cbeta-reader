const themes = ['light', 'sepia', 'dark'];
let themeIdx = themes.indexOf(localStorage.getItem('theme') || 'light');

function applySettings() {
    const theme = localStorage.getItem('theme') || 'light';
    const font = localStorage.getItem('fontFamily') || '"Noto Serif CJK TC", serif';
    const size = localStorage.getItem('fontSize') || '20';
    const width = localStorage.getItem('contentWidth') || '48';
    const height = localStorage.getItem('contentHeight') || '80';
    const vertical = localStorage.getItem('vertical') === 'true';
    document.documentElement.dataset.theme = theme;
    document.body.style.fontFamily = font;
    document.body.style.fontSize = size + 'px';
    document.documentElement.style.setProperty('--content-width', width + 'rem');
    document.documentElement.style.setProperty('--content-height', height + 'vh');
    document.getElementById('font-size').value = size;
    document.getElementById('content-width').value = width;
    document.getElementById('content-height').value = height;
    if (vertical) document.documentElement.classList.add('vertical');
    document.getElementById('vertical-btn').textContent = vertical ? '橫排' : '直排';
    const sel = document.getElementById('font-family');
    for (let opt of sel.options) {
        if (opt.value === font) { opt.selected = true; break; }
    }
}

function toggleSettings() {
    document.getElementById('settings-panel').classList.toggle('open');
    document.getElementById('settings-toggle').classList.toggle('hidden');
}

function cycleTheme() {
    themeIdx = (themeIdx + 1) % themes.length;
    localStorage.setItem('theme', themes[themeIdx]);
    document.documentElement.dataset.theme = themes[themeIdx];
}

function setFont(val) {
    localStorage.setItem('fontFamily', val);
    document.body.style.fontFamily = val;
}

function setSize(val) {
    localStorage.setItem('fontSize', val);
    document.body.style.fontSize = val + 'px';
}

function setWidth(val) {
    localStorage.setItem('contentWidth', val);
    document.documentElement.style.setProperty('--content-width', val + 'rem');
}

function setHeight(val) {
    localStorage.setItem('contentHeight', val);
    document.documentElement.style.setProperty('--content-height', val + 'vh');
}

function toggleVertical() {
    // Save current anchor before switching
    const anchor = typeof findNearestAnchor === 'function' ? findNearestAnchor() : null;
    const on = document.documentElement.classList.toggle('vertical');
    localStorage.setItem('vertical', on);
    document.getElementById('vertical-btn').textContent = on ? '橫排' : '直排';
    // Restore position after layout change
    if (anchor) {
        requestAnimationFrame(() => {
            const target = document.getElementById(anchor);
            if (target) target.scrollIntoView();
        });
    }
}

// Adjust button positions for mobile URL bar
if (window.visualViewport) {
    function updateBtnBottom() {
        const offset = window.innerHeight - window.visualViewport.height;
        document.documentElement.style.setProperty('--btn-bottom',
            (offset + 24) + 'px');
    }
    window.visualViewport.addEventListener('resize', updateBtnBottom);
    updateBtnBottom();
}

document.addEventListener('click', function(e) {
    const settings = document.getElementById('settings-panel');
    const settingsBtn = document.getElementById('settings-toggle');
    if (settings.classList.contains('open') &&
        !settings.contains(e.target) && e.target !== settingsBtn) {
        toggleSettings();
    }
    const toc = document.getElementById('toc-sidebar');
    const tocBtn = document.getElementById('toc-toggle');
    if (toc && toc.classList.contains('open') &&
        !toc.contains(e.target) && e.target !== tocBtn) {
        toggleToc();
    }
});

applySettings();
