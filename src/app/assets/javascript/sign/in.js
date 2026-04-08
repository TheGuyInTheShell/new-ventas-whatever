/**
 * App Module - JavaScript Entry Point
 *
 * Import your CSS here so Rolldown bundles it via PostCSS (Tailwind).
 * Add any app-level JS imports below.
 */

import Alpine from "alpinejs"
import mask from '@alpinejs/mask'
import focus from '@alpinejs/focus'
import collapse from '@alpinejs/collapse'
import "htmx.org"

Alpine.plugin(mask)
Alpine.plugin(focus)
Alpine.plugin(collapse)

document.addEventListener('alpine:init', () => {
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

document.addEventListener('DOMContentLoaded', () => {
    const spinner = document.getElementById('spinner');
    const form = document.getElementById("sign-in");

    if (form && spinner) {
        form.addEventListener('htmx:beforeRequest', function (event) {
            const spinnerData = Alpine.$data(spinner);
            if (spinnerData) {
                spinnerData.show();
            }

            // Clear previous notification if it's there (keep the spinner element)
            const notification = document.getElementById('notification');
            if (notification) {
                Array.from(notification.children).forEach(child => {
                    if (child.id !== 'spinner') {
                        child.remove();
                    }
                });
            }

            // Wait until HTMX fires the request
            return true;
        });

        form.addEventListener('htmx:afterOnLoad', function (event) {
            // Fake small delay to show off the loader animation smoothly
            setTimeout(() => {
                const spinnerData = Alpine.$data(spinner);
                if (spinnerData) {
                    spinnerData.hide();
                }

                const target = document.getElementById("notification");
                if (target && target.querySelector('.success-msg')) {
                    setTimeout(() => {
                        window.location.replace("/dashboard");
                    }, 1000);
                }
            }, 300);
        });
    }
});

Alpine.start();
