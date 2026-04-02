/**
 * App Module - JavaScript Entry Point
 *
 * Import your CSS here so Rolldown bundles it via PostCSS (Tailwind).
 * Add any app-level JS imports below.
 */
import "../css/app.css";
import Alpine from "alpinejs";
import { createIcons, icons } from 'lucide';

// Re-initialize icons dynamically when HTMX swaps content (useful since you use htmx)
document.addEventListener('DOMContentLoaded', () => {
    createIcons({ icons });
});

Alpine.start();