import { io } from "socket.io-client";

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

