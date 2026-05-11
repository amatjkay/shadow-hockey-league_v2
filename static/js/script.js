// === Loading skeleton (TIK-84 step 6) =================================
// Replaces the league-table <tbody> with N placeholder rows that share
// the column shape (rank / score / participant / cups) and shimmer
// with a magenta→cyan gradient. CSS handles the animation; JS only
// injects the markup. Safe under prefers-reduced-motion (CSS
// neutralises the keyframes). Per-row breakdown lives in a drawer
// (`#breakdown-sheet`), so the legacy 5th column is gone.
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
        '</tr>';
    tbody.innerHTML = new Array(rowCount).fill(rowHtml).join('');
}

// === Header tooltips (TIK-85 polish v2) ===============================
// Replaces the legacy hover/tap toggle with a centered fixed modal +
// backdrop. Each toggle button carries data-tooltip-toggle="<id>";
// the same id appears on the matching .tooltip-content and on the
// adjacent .tooltip-backdrop (data-tooltip-backdrop). Open: button
// click. Close: backdrop click, Escape key, or re-clicking the
// button. aria-expanded mirrors the open state.
function shlInitTooltips() {
    const buttons = document.querySelectorAll('[data-tooltip-toggle]');
    if (!buttons.length) return;
    let activeId = null;

    function setOpen(id, isOpen) {
        const btn = document.querySelector(
            '[data-tooltip-toggle="' + id + '"]'
        );
        const content = document.getElementById(id);
        const backdrop = document.querySelector(
            '[data-tooltip-backdrop="' + id + '"]'
        );
        if (!btn || !content || !backdrop) return;
        if (isOpen) {
            backdrop.hidden = false;
            content.hidden = false;
            // Two frames so the browser paints the hidden→shown swap
            // before the transition class lands, giving us the
            // fade/scale-in instead of an instant pop.
            requestAnimationFrame(function () {
                requestAnimationFrame(function () {
                    backdrop.classList.add('is-visible');
                    content.classList.add('tooltip-visible');
                });
            });
            btn.setAttribute('aria-expanded', 'true');
            activeId = id;
        } else {
            backdrop.classList.remove('is-visible');
            content.classList.remove('tooltip-visible');
            btn.setAttribute('aria-expanded', 'false');
            window.setTimeout(function () {
                backdrop.hidden = true;
                content.hidden = true;
            }, 220);
            if (activeId === id) activeId = null;
        }
    }

    buttons.forEach(function (btn) {
        const id = btn.getAttribute('data-tooltip-toggle');
        btn.addEventListener('click', function () {
            setOpen(id, btn.getAttribute('aria-expanded') !== 'true');
        });
    });

    document.querySelectorAll('[data-tooltip-backdrop]').forEach(function (el) {
        el.addEventListener('click', function () {
            const id = el.getAttribute('data-tooltip-backdrop');
            setOpen(id, false);
        });
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && activeId) {
            setOpen(activeId, false);
        }
    });
}

// === Breakdown sheet (TIK-84 polish v2) ==============================
// Click (or Enter/Space) on a leaderboard row → opens a drawer with the
// per-row achievement breakdown. Replaces the inline
// `<details>Детали` pattern. Each row carries:
//   - data-breakdown:    JSON array [{label, base, mul_display, points, icon_html}, ...]
//   - data-rank, data-name, data-country-flag, data-country-code,
//     data-total, data-tandem
// The drawer is rendered once in `index.html` and re-populated on each
// open. ESC, click on backdrop, or close button → closes. Focus is
// returned to the row that opened it.
function shlEscapeHtml(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// Allow only the safe `<img>` markup that comes from `Achievement.to_html()`
// (server-side, trusted). Strips anything else that could appear in the
// JSON payload to keep the drawer XSS-resistant even if the payload is
// ever sourced from user input later.
function shlSanitizeIconHtml(html) {
    const tmp = document.createElement('div');
    tmp.innerHTML = String(html || '');
    const out = document.createElement('div');
    tmp.querySelectorAll('img').forEach(function (img) {
        const safe = document.createElement('img');
        safe.setAttribute('src', img.getAttribute('src') || '');
        safe.setAttribute('alt', img.getAttribute('alt') || '');
        safe.setAttribute('width', img.getAttribute('width') || '32');
        safe.setAttribute('height', img.getAttribute('height') || '32');
        safe.setAttribute('loading', 'lazy');
        safe.setAttribute('decoding', 'async');
        out.appendChild(safe);
    });
    return out.innerHTML;
}

function shlInitBreakdownSheet() {
    const sheet = document.getElementById('breakdown-sheet');
    if (!sheet) return;
    const panel = sheet.querySelector('.breakdown-sheet__panel');
    const rankEl = sheet.querySelector('.breakdown-sheet__rank-num');
    const nameEl = sheet.querySelector('.breakdown-sheet__name');
    const flagEl = sheet.querySelector('.breakdown-sheet__flag');
    const tandemEl = sheet.querySelector('.breakdown-sheet__tandem-badge');
    const totalEl = sheet.querySelector('.breakdown-sheet__total-value');
    const listEl = sheet.querySelector('.breakdown-sheet__list');
    let lastFocused = null;
    let openRow = null;

    function renderItems(items) {
        if (!items.length) {
            listEl.innerHTML =
                '<li class="breakdown-card breakdown-card--empty">' +
                'У участника пока нет достижений в этом сезоне.' +
                '</li>';
            return;
        }
        listEl.innerHTML = items.map(function (a) {
            return (
                '<li class="breakdown-card">' +
                '<div class="breakdown-card__icon" aria-hidden="true">' +
                shlSanitizeIconHtml(a.icon_html) +
                '</div>' +
                '<div class="breakdown-card__main">' +
                '<div class="breakdown-card__label">' +
                shlEscapeHtml(a.label) +
                '</div>' +
                '<div class="breakdown-card__formula">' +
                'база ' + shlEscapeHtml(a.base) +
                ' × множитель ' + shlEscapeHtml(a.mul_display) +
                '</div>' +
                '</div>' +
                '<div class="breakdown-card__points">+' +
                shlEscapeHtml(a.points) +
                '</div>' +
                '</li>'
            );
        }).join('');
    }

    function open(row) {
        let items = [];
        try {
            items = JSON.parse(row.getAttribute('data-breakdown') || '[]');
        } catch (e) {
            items = [];
        }
        rankEl.textContent = row.getAttribute('data-rank') || '—';
        nameEl.textContent = row.getAttribute('data-name') || '—';
        flagEl.setAttribute('src', row.getAttribute('data-country-flag') || '');
        flagEl.setAttribute('alt', row.getAttribute('data-country-code') || '');
        tandemEl.hidden = row.getAttribute('data-tandem') !== 'true';
        totalEl.textContent = row.getAttribute('data-total') || '0';
        renderItems(items);

        lastFocused = document.activeElement;
        openRow = row;
        row.setAttribute('aria-expanded', 'true');
        sheet.hidden = false;
        sheet.removeAttribute('aria-hidden');
        document.body.classList.add('breakdown-sheet-open');
        // Two-frame delay so the browser has the panel painted at its
        // off-screen transform before we flip the visibility class —
        // gives us the slide-in transition instead of an instant pop.
        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                sheet.classList.add('is-visible');
                if (panel && typeof panel.focus === 'function') {
                    panel.focus();
                }
            });
        });
    }

    function close() {
        if (sheet.hidden) return;
        sheet.classList.remove('is-visible');
        sheet.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('breakdown-sheet-open');
        if (openRow) {
            openRow.setAttribute('aria-expanded', 'false');
        }
        const restore = lastFocused;
        const wasRow = openRow;
        openRow = null;
        lastFocused = null;
        // Wait for the slide-out transition to finish before hiding the
        // panel — otherwise the disappearance is jarring. Reduced-motion
        // CSS sets transition: none so this resolves instantly.
        window.setTimeout(function () {
            sheet.hidden = true;
        }, 320);
        const target = restore || wasRow;
        if (target && typeof target.focus === 'function') {
            target.focus();
        }
    }

    document.querySelectorAll('.table-row[data-breakdown]').forEach(function (row) {
        row.addEventListener('click', function () {
            open(row);
        });
        row.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
                e.preventDefault();
                open(row);
            }
        });
    });

    sheet.querySelectorAll('[data-breakdown-close]').forEach(function (el) {
        el.addEventListener('click', close);
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !sheet.hidden) {
            close();
        }
    });
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
    // Polish v1: animate the theme swap with the View Transitions API
    // where supported (Chrome 111+, Edge, Safari TP). The API freezes
    // the page, applies the swap, and cross-fades to the new state. On
    // browsers without support OR under prefers-reduced-motion we fall
    // back to an instant swap (the existing behaviour).
    const reduceMotion = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const next = shlGetCurrentTheme() === 'light' ? 'dark' : 'light';
            if (
                !reduceMotion &&
                typeof document.startViewTransition === 'function'
            ) {
                document.startViewTransition(function () {
                    shlApplyTheme(next);
                });
            } else {
                shlApplyTheme(next);
            }
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

    shlInitTooltips();

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

    // Sticky-nav scroll-shadow (TIK-84 step 4 follow-up).
    // The CSS rule `.header.is-scrolled` adds a soft drop-shadow once the
    // user scrolls past the header. We toggle the class via an
    // IntersectionObserver watching a 1px sentinel placed immediately
    // below the sticky header. When the sentinel leaves the viewport,
    // the user has scrolled past the header. IO is no-op'd when the
    // browser doesn't support it.
    const header = document.querySelector('.header');
    const sentinel = document.querySelector('.header-sentinel');
    if (header && sentinel && 'IntersectionObserver' in window) {
        const io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                header.classList.toggle('is-scrolled', !entry.isIntersecting);
            });
        }, { threshold: 0 });
        io.observe(sentinel);
    }

    shlInitBreakdownSheet();

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
