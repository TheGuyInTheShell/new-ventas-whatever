import { createIcons, icons } from 'lucide';

// Initialize Lucide icons on initial page load
document.addEventListener('DOMContentLoaded', () => {
    createIcons({ icons });
});

// Re-initialize icons dynamically when HTMX swaps content
document.addEventListener('htmx:load', () => {
    createIcons({ icons });
});