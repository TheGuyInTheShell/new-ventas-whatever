/**
 * @fileoverview App Module - JavaScript Entry Point.
 *
 * This module coordinates the initialization of Alpine.js and its plugins,
 * integrates HTMX, and handles global CSS imports for bundling.
 */

import "../../css/app.css";
import Alpine from "alpinejs";
import mask from '@alpinejs/mask';
import focus from '@alpinejs/focus';
import collapse from '@alpinejs/collapse';
import "htmx.org";
import validate from "validate.js";

// Register Alpine.js plugins
Alpine.plugin(mask);
Alpine.plugin(focus);
Alpine.plugin(collapse);

/**
 * @typedef {Object} SpinnerComponent
 * @property {boolean} loading - Indicates if an operation is in progress.
 * @property {function} show - Sets the loading state to true.
 * @property {function} hide - Sets the loading state to false.
 */

/**
 * Initializes global Alpine.js data components.
 */
document.addEventListener('alpine:init', () => {
    /**
     * Spinner component for controlling the loading state during async operations.
     * @type {SpinnerComponent}
     */
    Alpine.data('spinner', () => ({
        loading: false,
        show() {
            this.loading = true;
        },
        hide() {
            this.loading = false;
        }
    }));
});

// Start the Alpine.js framework
Alpine.start();

/**
 * HTMX & Validation Logic for System Initialization
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    if (window.lucide) {
        window.lucide.createIcons();
    }

    /**
     * Selector helper for DOM elements.
     * @param {string} e - Selector string.
     * @returns {Element|null} The matched element.
     */
    const $ = (e) => document.querySelector(e);

    /** @type {HTMLFormElement|null} */
    const form = /** @type {HTMLFormElement} */ ($("#init-form"));

    /** @type {HTMLElement|null} */
    const spinner = document.getElementById('spinner');

    if (form) {
        form.addEventListener('htmx:beforeRequest', function (event) {
            // Clear previous error messages
            const labels = ["full_name", "username", "email", "password"];
            labels.forEach(id => {
                const element = $(`#label-${id}`);
                if (element) element.innerHTML = "";
            });

            /** 
             * Validation constraints for validate.js
             * @type {Object}
             */
            const constraints = {
                full_name: {
                    presence: { allowEmpty: false, message: "is required" },
                    length: { minimum: 3, message: "must be at least 3 characters" }
                },
                username: {
                    presence: { allowEmpty: false, message: "is required" },
                    length: { minimum: 4, message: "must be at least 4 characters" }
                },
                email: {
                    presence: { allowEmpty: false, message: "is required" },
                    email: { message: "is not a valid email" }
                },
                password: {
                    presence: { allowEmpty: false, message: "is required" },
                    length: { minimum: 8, message: "must be at least 8 characters" }
                }
            };

            /** @type {Object} */
            const data = Object.fromEntries(new FormData(form));

            /** @type {Object|undefined} */
            const validation = validate(data, constraints);

            if (!!validation) {
                // STOP the request if validation fails
                event.preventDefault();

                Object.entries(validation).forEach(([keydom, errors]) => {
                    const element = $(`#label-${keydom}`);
                    if (element) {
                        element.innerHTML = errors.join(', ');
                    }
                });
                return false;
            }

            // Show loading via Alpine state
            if (spinner) {
                Alpine.$data(spinner).show();
            }
            return true;
        });

        /**
         * Handle HTMX successful completion to redirect.
         * @param {Event} event 
         */
        form.addEventListener('htmx:afterOnLoad', function (event) {
            setTimeout(() => {
                // Hide loading
                if (spinner) {
                    Alpine.$data(spinner).hide();
                }

                const successTarget = $("#init-success");
                if (successTarget) {
                    setTimeout(() => {
                        window.location.replace("/auth/sign-in");
                    }, 1500);
                }
            }, 500);
        });
    }
});
