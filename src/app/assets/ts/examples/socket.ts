import { io, Socket } from "socket.io-client";
import Alpine from "alpinejs";

try {
    const socket: Socket = io("http://localhost:8000/live", {
        path: "/sio/",
        auth: {
            "key": "val"
        }
    });

    socket.on("connect", () => {
        console.log("Connected to Socket.IO server!");
        console.log("Socket ID:", socket.id);
    });

    socket.on("connect_info", (data: any) => {
        console.log("Connect info received:", data);
    });

    socket.on("sv:live:0", (msg: ArrayBuffer) => {
        const blob = new Blob([msg], { type: 'image/jpg' });
        const url = URL.createObjectURL(blob);

        const img = document.querySelector('#frame') as HTMLImageElement | null;
        if (img) {
            img.src = url;
        }
    });

    socket.on("test:event", () => {
        const socketElement = document.getElementById('socket');
        if (socketElement && (window as any).Alpine) {
            (Alpine as any).$data(socketElement).show();
        }
    });

} catch (error) {
    console.error("Socket initialization failed:", error);
}
