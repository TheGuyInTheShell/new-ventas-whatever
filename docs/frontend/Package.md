# Frontend Packages and Build System

This document outlines the libraries and tools used for construction, building, and styling the frontend of the application.

## Build and Construction

The project uses a modern, high-performance build stack designed for rapid development and efficient production bundles.

| Tool | Purpose | Description |
| :--- | :--- | :--- |
| **Rolldown** | Bundler | A high-performance Rust-based bundler (API-compatible with Rollup). Handles the consolidation of JS and CSS assets. |
| **PostCSS** | CSS Processor | Transforms CSS with JS plugins. Used for Tailwind CSS integration and autoprefixing. |
| **Nodemon** | Dev Runner | Monitors for file changes and restarts the build process during development. |

### Build Scripts
- `npm run build`: Executes the full build process via Rolldown.
- `npm run watch`: Starts Rolldown in watch mode for continuous development.

---

## Core Frontend Libraries

### 1. Styling
- **Tailwind CSS v4**: The latest utility-first CSS framework. It provides the base design system without writing custom CSS.
- **DaisyUI 5**: A plugin for Tailwind CSS that provides high-level, accessible UI components (buttons, cards, drawers, etc.).
- **Tailwind Animations**: Utility classes for modern web animations.

### 2. Interactivity and AJAX
- **HTMX 2.0**: Allows access to AJAX, CSS Transitions, WebSockets, and Server Sent Events directly in HTML using attributes. It is the primary tool for partial page updates.
- **Alpine.js 3.14+**: A rugged, minimal framework for composing JavaScript behavior in your markup. Used for client-side state (modals, dropdowns, local data).
  - *Plugins*: Includes `@alpinejs/collapse`, `@alpinejs/focus`, and `@alpinejs/mask`.

### 3. Data Visualization and Media
- **ApexCharts**: Used for complex, interactive charts and data visualizations.
- **Mermaid**: Enables the generation of diagrams and flowcharts from text definitions.
- **Lucide**: The icon set used throughout the application.

### 4. Utilities
- **Socket.io-client**: Used for real-time, bi-directional communication with the backend.
- **Yup**: A schema builder for runtime value parsing and validation (often used for form validation).
- **XState Store**: A lightweight state management library for managing complex client-side logic states.
