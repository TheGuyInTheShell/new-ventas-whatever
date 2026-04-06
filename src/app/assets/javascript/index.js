/**
 * App Module - JavaScript Entry Point
 *
 * Import your CSS here so Rolldown bundles it via PostCSS (Tailwind).
 * Add any app-level JS imports below.
 */
import "../css/app.css"
import Alpine from "alpinejs"
import mask from '@alpinejs/mask'
import focus from '@alpinejs/focus'
import collapse from '@alpinejs/collapse'
import { io } from "socket.io-client";

Alpine.plugin(mask)
Alpine.plugin(focus)
Alpine.plugin(collapse)

document.addEventListener('alpine:init', () => {
    Alpine.data('socket', () => ({
        message: '',
        show() {
            this.message = 'Hello!';
        },
        hide() {
            this.message = '';
        }
    }))
})


Alpine.start();

try {
    const socket = io("http://localhost:8000/live", {
        path: "/sio/",
        auth: {
            "key": "val"
        }
    });

    socket.on("connect", () => {
        console.log("Connected to Socket.IO server!");
        console.log("Socket ID:", socket.id);
    });

    socket.on("connect_info", (data) => {
        console.log("Connect info received:", data);
    });


    socket.on("sv:live:0", (msg) => {
        let array = new Uint8ClampedArray(msg);
        let url = URL.createObjectURL(new Blob([msg], { type: 'image/jpg' }));

        let img = document.querySelector('#frame');
        img.src = url;
    })

    socket.on("test:event", (msg) => {
        const socket = document.getElementById('socket');
        Alpine.$data(socket).show();
    })

} catch (error) {
    console.log(error);
}


