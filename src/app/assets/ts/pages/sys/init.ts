import "../../../css/app.css";
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

    Alpine.data('sys_init', () => ({
        password: '',
        loading: false,
        showPassword: false,
        get strength() {
            let score = 0;
            const self = this as any;
            if (!self.password) return 0;
            if (self.password.length >= 8) score++;
            if (/[A-Z]/.test(self.password)) score++;
            if (/[0-9]/.test(self.password)) score++;
            if (/[!@#$%^&*.]/.test(self.password)) score++;
            return score;
        },
        show() {
            (this as any).loading = true;
        },
        hide() {
            (this as any).loading = false;
        }
    }));
});

Alpine.start();

document.addEventListener('DOMContentLoaded', () => {
    const win = window as any;
    if (win.lucide) {
        win.lucide.createIcons();
    }

    const $ = (e: string) => document.querySelector(e);

    const form = $("#init-form") as HTMLFormElement | null;
    const spinner = document.getElementById('spinner');

    if (form) {
        form.addEventListener('htmx:beforeRequest' as any, function (event: any) {
            const labels = ["full_name", "username", "email", "password"];
            labels.forEach(id => {
                const element = $(`#label-${id}`);
                if (element) element.innerHTML = "";
            });

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

            const data = Object.fromEntries(new FormData(form));
            const validation = validate(data, constraints);

            if (validation) {
                event.preventDefault();

                Object.entries(validation).forEach(([keydom, errors]) => {
                    const element = $(`#label-${keydom}`);
                    if (element) {
                        element.innerHTML = (errors as string[]).join(', ');
                    }
                });
                return false;
            }

            if (spinner) {
                (Alpine as any).$data(spinner).show();
            }
            return true;
        });

        document.body.addEventListener('htmx:afterSwap' as any, function (event: any) {
            if (event.detail.target.id === "notification") {
                setTimeout(() => {
                    if (spinner) {
                        (Alpine as any).$data(spinner).hide();
                    }

                    const successTarget = $("#init-success");
                    if (successTarget) {
                        const formElem = $("#init-form");
                        if (formElem) {
                            formElem.remove();
                        }

                        setTimeout(() => {
                            window.location.replace("/sign/in");
                        }, 1500);
                    }
                    if (win.lucide) {
                        win.lucide.createIcons();
                    }
                }, 100);
            }
        });
    }
});
