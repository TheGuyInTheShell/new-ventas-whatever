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

document.addEventListener('alpine:init', () => {
    Alpine.data('socket', () => ({
        message: '',
        show() {
            (this as any).message = 'Hello!';
        },
        hide() {
            (this as any).message = '';
        }
    }));
});

// Start the Alpine.js framework
Alpine.start();
