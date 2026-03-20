const themes = ['light', 'sepia', 'modus-dark', 'dark'];
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
                <select id="font-family" onchange="setFontPreset(this.value)">
                    <option value='"Noto Serif CJK TC", "Source Han Serif TC", "Songti TC", "Songti SC", "SimSun", "MingLiU", serif'>系統襯線</option>
                    <option value='"Noto Sans CJK TC", "Source Han Sans TC", "PingFang TC", "PingFang SC", "Microsoft JhengHei", "Microsoft YaHei", sans-serif'>系統無襯線</option>
                    <option value='"Noto Serif CJK TC", "Source Han Serif TC"'>思源宋體</option>
                    <option value='"Noto Sans CJK TC", "Source Han Sans TC"'>思源黑體</option>
                    <option value='"FZPingXianYaSong-R-GBK"'>方正屏显宋</option>
                    <option value='"Fusion Kai T"'>缝合楷</option>
                </select>
            </label>
            <label>自訂字體
                <input type="text" id="custom-font" placeholder="輸入字體名稱"
                    onchange="setCustomFont(this.value)" oninput="setCustomFont(this.value)">
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
            <details class="settings-about">
                <summary>关于</summary>
                <ul>
                    <li>字體需已安裝於系統中方可使用。</li>
                    <li>花園明朝（HanaMin）已設為備用字體，用於顯示罕見漢字。</li>
                    <li>版寬／版高設有最小值，在較小螢幕上可能無法生效。</li>
                </ul>
                网站源碼：<a href="https://github.com/semio/cbeta-reader" target="_blank">GitHub</a>
            </details>
        </div>
        <button class="drawer-close-bottom" onclick="toggleSettings()">→</button>`;
    syncSettingsUI();
}

function syncSettingsUI() {
    const fontPreset = localStorage.getItem('fontPreset') || '"Noto Serif CJK TC", "Source Han Serif TC", "Songti TC", "Songti SC", "SimSun", "MingLiU", serif';
    const customFont = localStorage.getItem('customFont') || '';
    const size = localStorage.getItem('fontSize') || '20';
    const width = localStorage.getItem('contentWidth') || '48';
    const height = localStorage.getItem('contentHeight') || '80';
    const vertical = localStorage.getItem('vertical') === 'true';
    document.getElementById('font-size').value = size;
    document.getElementById('content-width').value = width;
    document.getElementById('content-height').value = height;
    document.getElementById('vertical-btn').textContent = vertical ? '橫排' : '直排';
    document.getElementById('custom-font').value = customFont;
    const sel = document.getElementById('font-family');
    for (let opt of sel.options) {
        if (opt.value === fontPreset) { opt.selected = true; break; }
    }
}

const FONT_FALLBACKS = '"HanaMinA", "HanaMinB", serif';

function buildFontFamily() {
    const customFont = localStorage.getItem('customFont') || '';
    const fontPreset = localStorage.getItem('fontPreset') || '"Noto Serif CJK TC", "Source Han Serif TC", "Songti TC", "Songti SC", "SimSun", "MingLiU", serif';
    const primary = customFont
        ? customFont.split(',').map(f => '"' + f.trim().replace(/"/g, '') + '"').join(', ')
        : fontPreset;
    return primary + ', ' + FONT_FALLBACKS;
}

function applySettings() {
    const theme = localStorage.getItem('theme') || 'light';
    const size = localStorage.getItem('fontSize') || '20';
    const width = localStorage.getItem('contentWidth') || '48';
    const height = localStorage.getItem('contentHeight') || '80';
    const vertical = localStorage.getItem('vertical') === 'true';
    document.documentElement.dataset.theme = theme;
    document.body.style.fontFamily = buildFontFamily();
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

function setFontPreset(val) {
    localStorage.setItem('fontPreset', val);
    localStorage.removeItem('customFont');
    document.getElementById('custom-font').value = '';
    document.body.style.fontFamily = buildFontFamily();
}

function setCustomFont(val) {
    const trimmed = val.trim();
    localStorage.setItem('customFont', trimmed);
    document.body.style.fontFamily = buildFontFamily();
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

// Migrate old fontFamily setting
if (localStorage.getItem('fontFamily') && !localStorage.getItem('fontPreset')) {
    localStorage.setItem('fontPreset', localStorage.getItem('fontFamily'));
    localStorage.removeItem('fontFamily');
}

applySettings();
