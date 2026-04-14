/**
 * @fileoverview Lucide Icon Initialization Module.
 * This module handles the initial and dynamic rendering of Lucide icons
 * throughout the application, including support for HTMX content swaps.
 */

import { createIcons, icons } from 'lucide';

/**
 * Initializes Lucide icons on the initial page load.
 */
document.addEventListener('DOMContentLoaded', () => {
    createIcons({ icons });
});

/**
 * Re-initializes Lucide icons dynamically when HTMX swaps content.
 * This ensures that icons inside elements loaded via HTMX are rendered correctly.
 */
document.addEventListener('htmx:load', () => {
    createIcons({ icons });
});