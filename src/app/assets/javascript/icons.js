import { createIcons, icons } from 'lucide';

// Re-initialize icons dynamically when HTMX swaps content (useful since you use htmx)
document.addEventListener('DOMContentLoaded', () => {
    createIcons({ icons });
});