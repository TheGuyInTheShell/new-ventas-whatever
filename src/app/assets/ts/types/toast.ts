export interface ToastSender {
    name: string;
    avatar: string;
}

export interface ToastOptions {
    variant: 'info' | 'success' | 'warning' | 'danger' | 'error' | 'message';
    title?: string | null;
    message: string;
    sender?: ToastSender | null;
}

export interface ToastNotification extends ToastOptions {
    id: number;
}
