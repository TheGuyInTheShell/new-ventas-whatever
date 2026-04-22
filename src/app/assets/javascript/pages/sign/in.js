/**
 * @fileoverview Sign-In Module.
 *
 * This module manages the client-side logic for the authentication page,
 * including loader state management via Alpine.js and form lifecycle
 * interception using HTMX event listeners.
 */

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
 * Initializes Alpine.js data components for the sign-in page.
 */
document.addEventListener('alpine:init', () => {
    /**
     * Spinner component to manage loading state.
     * @typedef {Object} SpinnerComponent
     * @property {boolean} loading - Whether the spinner should be visible.
     * @property {function} show - Sets loading to true.
     * @property {function} hide - Sets loading to false.
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
 * Attaches event listeners to the sign-in form for HTMX request lifecycle management.
 */
document.addEventListener('DOMContentLoaded', () => {
    const spinnerElement = document.getElementById('spinner');
    const signInForm = document.getElementById("sign-in");

    if (signInForm && spinnerElement) {
        /**
         * Intercepts HTMX request before it is sent.
         * Shows the spinner and clears previous notifications.
         */
        signInForm.addEventListener('htmx:beforeRequest', function (event) {
            // @ts-ignore - Accessing Alpine data context
            const spinnerData = Alpine.$data(spinnerElement);
            if (spinnerData) {
                spinnerData.show();
            }

            // Clear previous notification while preserving the spinner structure
            const notificationArea = document.getElementById('notification');
            if (notificationArea) {
                Array.from(notificationArea.children).forEach(child => {
                    if (child.id !== 'spinner') {
                        child.remove();
                    }
                });
            }

            return true;
        });

        /**
         * Cleans up after HTMX request completes.
         * Hides the spinner and handles redirection on success.
         */
        signInForm.addEventListener('htmx:afterOnLoad', function (event) {
            // Add a small delay for a smoother animation transition
            setTimeout(() => {
                // @ts-ignore - Accessing Alpine data context
                const spinnerData = Alpine.$data(spinnerElement);
                if (spinnerData) {
                    spinnerData.hide();
                }

                const notificationArea = document.getElementById("notification");
                // Check if the response contains a success message class
                if (notificationArea && notificationArea.querySelector('.success-msg')) {
                    setTimeout(() => {
                        window.location.replace("/dashboard");
                    }, 1000);
                }
            }, 300);
        });
    }
});


