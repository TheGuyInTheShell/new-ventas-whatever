/**
 * @fileoverview Global Toast Notification Hook.
 * Use this module to dispatch notifications from any JS file or component
 * agnostically to the HTML structure.
 */

/**
 * @typedef {Object} ToastSender
 * @property {string} name - Name of the sender (used in 'message' variant).
 * @property {string} avatar - URL to the sender's avatar image.
 */

/**
 * @typedef {Object} ToastOptions
 * @property {'info'|'success'|'warning'|'danger'|'error'|'message'} variant - The style of the notification.
 * @property {string} [title] - The title of the notification.
 * @property {string} message - The main body message.
 * @property {ToastSender} [sender] - Sender info for message variants.
 */


import Alpine from "alpinejs";

document.addEventListener('alpine:init', () => {
    Alpine.data('toastComponent', () => ({
        notifications: [],
        displayDuration: 8000,
        soundEffect: false,

        addNotification({ variant = 'info', sender = null, title = null, message = null }) {
            const id = Date.now()
            const notification = { id, variant, sender, title, message }

            // Keep only the most recent 20 notifications
            if (this.notifications.length >= 20) {
                this.notifications.splice(0, this.notifications.length - 19)
            }

            // Add the new notification to the notifications stack
            this.notifications.push(notification)

            if (this.soundEffect) {
                // Play the notification sound
                const notificationSound = new Audio('https://res.cloudinary.com/ds8pgw1pf/video/upload/v1728571480/penguinui/component-assets/sounds/ding.mp3')
                notificationSound.play().catch((error) => {
                    console.error('Error playing the sound:', error)
                })
            }

            // Render lucide icons after adding
            this.$nextTick(() => {
                if (window.lucide) { lucide.createIcons(); }
            });
        },
        removeNotification(id) {
            setTimeout(() => {
                this.notifications = this.notifications.filter(
                    (notification) => notification.id !== id,
                )
            }, 400);
        },
    }));
})


/**
 * Dispatches a notification event to the global Alpine.js listener.
 * 
 * @param {ToastOptions} options - The notification options.
 */
export function notify(options) {
    // Ensure variant is valid, default to info
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

/**
 * Utility function to dispatch a success toast.
 * @param {string} message - The success message.
 * @param {string} [title='Success'] - Optional title.
 */
export function notifySuccess(message, title = 'Success') {
    notify({ variant: 'success', title, message });
}

/**
 * Utility function to dispatch an error/danger toast.
 * @param {string} message - The error message.
 * @param {string} [title='Error'] - Optional title.
 */
export function notifyError(message, title = 'Error') {
    notify({ variant: 'danger', title, message });
}

/**
 * Utility function to dispatch an info toast.
 * @param {string} message - The info message.
 * @param {string} [title='Info'] - Optional title.
 */
export function notifyInfo(message, title = 'Info') {
    notify({ variant: 'info', title, message });
}

/**
 * Utility function to dispatch a warning toast.
 * @param {string} message - The warning message.
 * @param {string} [title='Warning'] - Optional title.
 */
export function notifyWarning(message, title = 'Warning') {
    notify({ variant: 'warning', title, message });
}

/**
 * Utility function to dispatch a message toast (with sender details).
 * @param {string} message - The message body.
 * @param {ToastSender} sender - The sender details object {name, avatar}.
 * @param {string} [title] - Optional title.
 */
export function notifyMessage(message, sender, title = null) {
    notify({ variant: 'message', title, message, sender });
}
