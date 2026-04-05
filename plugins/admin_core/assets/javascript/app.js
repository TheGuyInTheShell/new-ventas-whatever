/**
 * Admin Module - JavaScript Entry Point
 *
 * Import your CSS here so Rolldown bundles it via PostCSS (Tailwind).
 * Add any admin-level JS imports below.
 */
import "../css/app.css";
import Alpine from "alpinejs";
import { createIcons, icons } from 'lucide';

// Initialize Lucide icons on first load
createIcons({ icons });

// Re-initialize icons dynamically when HTMX swaps content (useful since you use htmx)
document.addEventListener('htmx:load', () => {
    createIcons({ icons });
});

Alpine.start();
