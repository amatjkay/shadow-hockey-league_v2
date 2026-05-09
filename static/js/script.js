// === Loading skeleton (TIK-84 step 6) =================================
// Replaces the league-table <tbody> with N placeholder rows that share
// the column shape (rank / score / participant / cups / breakdown) and
// shimmer with a magenta→cyan gradient. CSS handles the animation; JS
// only injects the markup. Safe under prefers-reduced-motion (CSS
// neutralises the keyframes).
function showLeaderboardSkeleton(rowCount) {
    const tbody = document.querySelector('.league-table tbody');
    if (!tbody) return;
    const rowHtml =
        '<tr class="table-row table-row--skeleton" aria-hidden="true">' +
        '<td class="table-items rank-cell">' +
        '<span class="skeleton skeleton--rank"></span></td>' +
        '<td class="table-items score-cell">' +
        '<span class="skeleton skeleton--score"></span></td>' +
        '<td class="table-items manager-cell">' +
        '<span class="skeleton skeleton--avatar"></span>' +
        '<span class="skeleton skeleton--name"></span></td>' +
        '<td class="table-items league-cups-cell">' +
        '<span class="skeleton skeleton--cups"></span></td>' +
        '<td class="table-items rating-breakdown-cell">' +
        '<span class="skeleton skeleton--breakdown"></span></td>' +
        '</tr>';
    tbody.innerHTML = new Array(rowCount).fill(rowHtml).join('');
}

// === Theme toggle (TIK-84) ============================================
// Toggles `<html data-theme>` between "light" and "dark", persists to
// localStorage('shl-theme'). Multiple toggle buttons may exist (desktop
// header + mobile menu); they stay in sync through the data-theme attr.
function shlGetCurrentTheme() {
    const dt = document.documentElement.getAttribute('data-theme');
    if (dt === 'light' || dt === 'dark') return dt;
    return window.matchMedia &&
        window.matchMedia('(prefers-color-scheme: light)').matches
        ? 'light'
        : 'dark';
}

function shlApplyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try {
        localStorage.setItem('shl-theme', theme);
    } catch (e) {
        /* ignore */
    }
    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
        const isLight = theme === 'light';
        btn.setAttribute('aria-pressed', isLight ? 'true' : 'false');
        btn.setAttribute(
            'aria-label',
            isLight ? 'Включить тёмную тему' : 'Включить светлую тему'
        );
        const icon = btn.querySelector('.theme-toggle__icon');
        if (icon) {
            // Light → show 🌙 (click to switch to dark);
            // Dark → show ☀ (click to switch to light).
            icon.textContent = isLight ? '🌙' : '☀';
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    shlApplyTheme(shlGetCurrentTheme());
    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const next = shlGetCurrentTheme() === 'light' ? 'dark' : 'light';
            shlApplyTheme(next);
        });
    });

    const menuButton = document.querySelector('.mobile-menu-button');
    const closeButton = document.querySelector('.close-button');
    const menuContent = document.querySelector('.mobile-menu-content');
    const overlay = document.querySelector('.overlay');

    function openMenu() {
        menuContent.classList.add('active');
        menuButton.classList.add('hidden');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
        menuContent.classList.remove('active');
        menuButton.classList.remove('hidden');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (menuButton) {
        menuButton.addEventListener('click', openMenu);
    }
    if (closeButton) {
        closeButton.addEventListener('click', closeMenu);
    }
    if (overlay) {
        overlay.addEventListener('click', closeMenu);
    }

    // Tooltip click toggle for touch devices (T8/TIK-68).
    // Hover is unreliable on touch screens; tap on the `?` icon toggles
    // visibility, and a tap anywhere else closes it.
    const tooltipIcon = document.querySelector('.tooltip-icon');
    const tooltipContent = document.querySelector('.tooltip-content');
    if (tooltipIcon && tooltipContent) {
        tooltipIcon.addEventListener('click', function(e) {
            e.stopPropagation();
            tooltipContent.classList.toggle('tooltip-visible');
        });
        tooltipContent.addEventListener('click', function(e) {
            e.stopPropagation();
        });
        document.addEventListener('click', function() {
            tooltipContent.classList.remove('tooltip-visible');
        });
    }

    // Season tabs (TIK-84 step 5). Replaces the previous <select> with a
    // radio-group; selecting a tab navigates to ?season=N (or `/` for
    // Lifetime). On click we replace the table body with skeleton rows
    // so users get instant visual feedback before the new page paints.
    const seasonTabs = document.querySelector('[data-season-tabs]');
    document.querySelectorAll('[data-season-radio]').forEach(function (radio) {
        radio.addEventListener('change', function () {
            if (!radio.checked) return;
            document.body.classList.add('is-loading');
            showLeaderboardSkeleton(10);
            window.location.href = radio.value
                ? '/?season=' + encodeURIComponent(radio.value)
                : '/';
        });
    });

    // Center the active tab horizontally in its scroll container so the
    // user can immediately see which season is selected (mobile bias).
    if (seasonTabs) {
        requestAnimationFrame(function () {
            const checked = seasonTabs.querySelector('input:checked');
            if (!checked) return;
            const label = seasonTabs.querySelector(
                'label[for="' + checked.id + '"]'
            );
            if (!label) return;
            const offset =
                label.offsetLeft +
                label.offsetWidth / 2 -
                seasonTabs.clientWidth / 2;
            seasonTabs.scrollTo({ left: Math.max(0, offset), behavior: 'auto' });
        });
    }
});
