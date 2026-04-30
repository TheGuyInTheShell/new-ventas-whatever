import Alpine from "alpinejs";
import { ToastOptions, ToastSender, ToastNotification } from "../types/toast";

document.addEventListener('alpine:init', () => {
    Alpine.data('toastComponent', () => ({
        notifications: [] as ToastNotification[],
        displayDuration: 8000,
        soundEffect: false,

        addNotification({ variant = 'info', sender = null, title = null, message = '' }: Partial<ToastOptions>) {
            const id = Date.now();
            const notification: ToastNotification = { id, variant: variant as any, sender, title, message };

            if (this.notifications.length >= 20) {
                this.notifications.splice(0, this.notifications.length - 19);
            }

            this.notifications.push(notification);

            if (this.soundEffect) {
                const notificationSound = new Audio('https://res.cloudinary.com/ds8pgw1pf/video/upload/v1728571480/penguinui/component-assets/sounds/ding.mp3');
                notificationSound.play().catch((error) => {
                    console.error('Error playing the sound:', error);
                });
            }

            this.$nextTick(() => {
                const win = window as any;
                if (win.lucide) { win.lucide.createIcons(); }
            });
        },
        removeNotification(id: number) {
            setTimeout(() => {
                this.notifications = this.notifications.filter(
                    (notification) => notification.id !== id,
                );
            }, 400);
        },
    }));
});

export function notify(options: ToastOptions) {
    const variant = options.variant || 'info';

    window.dispatchEvent(
        new CustomEvent('notify', {
            detail: {
                variant,
                title: options.title || null,
                message: options.message || '',
                sender: options.sender || null,
            },
            bubbles: true,
            composed: true,
        })
    );
}

export function notifySuccess(message: string, title: string = 'Success') {
    notify({ variant: 'success', title, message });
}

export function notifyError(message: string, title: string = 'Error') {
    notify({ variant: 'danger', title, message });
}

export function notifyInfo(message: string, title: string = 'Info') {
    notify({ variant: 'info', title, message });
}

export function notifyWarning(message: string, title: string = 'Warning') {
    notify({ variant: 'warning', title, message });
}

export function notifyMessage(message: string, sender: ToastSender, title: string | null = null) {
    notify({ variant: 'message', title, message, sender });
}
