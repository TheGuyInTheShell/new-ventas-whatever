/**
 * @fileoverview Socket.IO Client Example.
 *
 * This module demonstrates how to connect to the Socket.IO server, handle authentication,
 * and listen for various real-time events, such as live frame updates and custom triggers.
 */

import { io } from "socket.io-client";

try {
    /**
     * Initializes the Socket.IO connection.
     * @type {import("socket.io-client").Socket}
     */
    const socket = io("http://localhost:8000/live", {
        path: "/sio/",
        auth: {
            "key": "val" // Example authentication credentials
        }
    });

    /**
     * Event listener for successful connection.
     */
    socket.on("connect", () => {
        console.log("Connected to Socket.IO server!");
        console.log("Socket ID:", socket.id);
    });

    /**
     * Event listener for internal connection information.
     * @param {Object} data - Metadata provided by the server upon connection.
     */
    socket.on("connect_info", (data) => {
        console.log("Connect info received:", data);
    });

    /**
     * Event listener for live image frame updates.
     * Converts received binary data (ArrayBuffer) into an object URL for display.
     * @param {ArrayBuffer} msg - Binary image data (e.g., JPEG).
     */
    socket.on("sv:live:0", (msg) => {
        // let array = new Uint8ClampedArray(msg); // Optional: Process raw bytes
        const blob = new Blob([msg], { type: 'image/jpg' });
        const url = URL.createObjectURL(blob);

        const img = document.querySelector('#frame');
        if (img) {
            img.src = url;
        }
    });

    /**
     * Event listener for custom test events.
     * Triggers the 'socket' Alpine component to show the message.
     * @param {any} msg - Event payload.
     */
    socket.on("test:event", (msg) => {
        const socketElement = document.getElementById('socket');
        if (socketElement && window.Alpine) {
            // @ts-ignore - Accessing Alpine data context
            Alpine.$data(socketElement).show();
        }
    });

} catch (error) {
    /**
     * Error handling for socket initialization.
     */
    console.error("Socket initialization failed:", error);
}

