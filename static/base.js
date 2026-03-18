const themes = ['light', 'sepia', 'dark'];
let themeIdx = themes.indexOf(localStorage.getItem('theme') || 'light');

function buildSettingsPanel() {
    const panel = document.getElementById('settings-panel');
    if (panel.dataset.built) return;
    panel.dataset.built = '1';
    panel.innerHTML = `
        <div class="settings-header">
            <strong>設定</strong>
            <button class="settings-close" onclick="toggleSettings()">&times;</button>
        </div>
        <div class="settings-body">
            <a href="/" class="settings-home">← 返回首頁</a>
            <label>字體
                <select id="font-family" onchange="setFont(this.value)">
                    <option value='"Noto Serif CJK TC", "Source Han Serif TC", "HanaMinA", "HanaMinB", serif'>思源宋體</option>
                    <option value='"Noto Sans CJK TC", "Source Han Sans TC", "HanaMinA", "HanaMinB", sans-serif'>思源黑體</option>
                    <option value='"FZPingXianYaSong-R-GBK", "HanaMinA", "HanaMinB", serif'>方正屏显宋</option>
                    <option value='"Fusion Kai T", "HanaMinA", "HanaMinB", serif'>缝合楷</option>
                    <option value='serif'>系統襯線</option>
                    <option value='sans-serif'>系統無襯線</option>
                </select>
            </label>
            <label>大小
                <input type="range" id="font-size" min="16" max="32" value="20" onchange="setSize(this.value)">
            </label>
            <label class="width-control">版寬
                <input type="range" id="content-width" min="30" max="80" value="48" onchange="setWidth(this.value)">
            </label>
            <label class="height-control">版高
                <input type="range" id="content-height" min="50" max="95" value="80" onchange="setHeight(this.value)">
            </label>
            <div class="settings-buttons">
                <button class="theme-btn" id="vertical-btn" onclick="toggleVertical()">直排</button>
                <button class="theme-btn" onclick="cycleTheme()">主題</button>
            </div>
        </div>
        <button class="drawer-close-bottom" onclick="toggleSettings()">→</button>`;
    syncSettingsUI();
}

function syncSettingsUI() {
    const font = localStorage.getItem('fontFamily') || '"Noto Serif CJK TC", serif';
    const size = localStorage.getItem('fontSize') || '20';
    const width = localStorage.getItem('contentWidth') || '48';
    const height = localStorage.getItem('contentHeight') || '80';
    const vertical = localStorage.getItem('vertical') === 'true';
    document.getElementById('font-size').value = size;
    document.getElementById('content-width').value = width;
    document.getElementById('content-height').value = height;
    document.getElementById('vertical-btn').textContent = vertical ? '橫排' : '直排';
    const sel = document.getElementById('font-family');
    for (let opt of sel.options) {
        if (opt.value === font) { opt.selected = true; break; }
    }
}

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
    if (vertical) document.documentElement.classList.add('vertical');
}

function toggleSettings() {
    buildSettingsPanel();
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
