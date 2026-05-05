document.addEventListener('DOMContentLoaded', function() {
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
