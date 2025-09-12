const toggle = document.getElementById('checkbox');
const root = document.documentElement;
const currentTheme = localStorage.getItem('theme');

if (currentTheme) {
    root.setAttribute('data-theme', currentTheme);
    if (currentTheme === 'dark') {
        toggle.checked = true;
    }
}

toggle.addEventListener('change', function() {
    if (this.checked) {
        root.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    } else {
        root.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
    }
});
