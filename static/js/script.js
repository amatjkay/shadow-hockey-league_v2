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

    // Loading indicator on season filter change (T11/TIK-66).
    // Replaces the previous inline `onchange` so we can show a spinner
    // overlay while the page reloads with the new query string.
    const seasonFilter = document.getElementById('season-filter');
    if (seasonFilter) {
        seasonFilter.addEventListener('change', function() {
            document.body.classList.add('is-loading');
            window.location.href = '/?season=' + this.value;
        });
    }
});
