import { createIcons, icons } from 'lucide';

document.addEventListener('DOMContentLoaded', () => {
    createIcons({ icons });
});

document.addEventListener('htmx:load', () => {
    createIcons({ icons });
});
