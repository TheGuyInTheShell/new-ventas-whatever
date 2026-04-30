import Alpine from "alpinejs";
import mask from '@alpinejs/mask';
import focus from '@alpinejs/focus';
import collapse from '@alpinejs/collapse';
import "htmx.org";

// Register Alpine.js plugins
Alpine.plugin(mask);
Alpine.plugin(focus);
Alpine.plugin(collapse);

document.addEventListener('alpine:init', () => {
    Alpine.data('spinner', () => ({
        loading: false,
        show() {
            (this as any).loading = true;
        },
        hide() {
            (this as any).loading = false;
        }
    }));
});

// Start the Alpine.js framework
Alpine.start();

document.addEventListener('DOMContentLoaded', () => {
    const spinnerElement = document.getElementById('spinner');
    const signInForm = document.getElementById("sign-in");

    if (signInForm && spinnerElement) {
        signInForm.addEventListener('htmx:beforeRequest' as any, function () {
            const spinnerData = (Alpine as any).$data(spinnerElement);
            if (spinnerData) {
                spinnerData.show();
            }

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

        signInForm.addEventListener('htmx:afterOnLoad' as any, function () {
            setTimeout(() => {
                const spinnerData = (Alpine as any).$data(spinnerElement);
                if (spinnerData) {
                    spinnerData.hide();
                }

                const notificationArea = document.getElementById("notification");
                if (notificationArea && notificationArea.querySelector('.success-msg')) {
                    setTimeout(() => {
                        window.location.replace("/dashboard");
                    }, 1000);
                }
            }, 300);
        });
    }
});
