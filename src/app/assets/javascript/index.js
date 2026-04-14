/**
 * @fileoverview App Module - JavaScript Entry Point.
 *
 * This module coordinates the initialization of Alpine.js and its plugins,
 * integrates HTMX, and handles global CSS imports for bundling.
 */

import "../css/app.css";
import Alpine from "alpinejs";
import mask from '@alpinejs/mask';
import focus from '@alpinejs/focus';
import collapse from '@alpinejs/collapse';
import "htmx.org";

// Register Alpine.js plugins
Alpine.plugin(mask);
Alpine.plugin(focus);
Alpine.plugin(collapse);

/**
 * Initializes global Alpine.js data components.
 */
document.addEventListener('alpine:init', () => {
    /**
     * Socket data component for simple message toggling.
     * @typedef {Object} SocketComponent
     * @property {string} message - The current message string.
     * @property {function} show - Sets the message to 'Hello!'.
     * @property {function} hide - Clears the message string.
     */
    Alpine.data('socket', () => ({
        message: '',
        show() {
            this.message = 'Hello!';
        },
        hide() {
            this.message = '';
        }
    }));
});

// Start the Alpine.js framework
Alpine.start();
