// static/js/script.js
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

    menuButton.addEventListener('click', openMenu);
    closeButton.addEventListener('click', closeMenu);
    overlay.addEventListener('click', closeMenu);
});