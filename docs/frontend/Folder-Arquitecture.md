# Folder Architecture

This document describes the structure and responsibilities of the folders within the documentation and the main application directory, specifically focusing on the `src/app` architecture.

## Root Directory

| Folder | Responsibility |
| :--- | :--- |
| `core/` | **Application Kernel**. Contains the engine of the application: security, database logic, registration systems, and shared libraries. |
| `extension/` | **Enhancements**. Wrappers for external libraries and custom FastAPI extensions like guards and plugins. |
| `plugins/` | **Modular Components**. Independent modules that can be plugged into the system. |
| `src/` | **Source Code**. The main business logic and UI code. |
| `public/` | **Static Assets**. Files served directly by the web server (images, favicon). |
| `docs/` | **Documentation**. Technical and operational documentation. |

---

## Application Directory (`src/app`)

The `src/app` folder is the heart of the frontend and web application. It follows a class-per-page pattern combined with HTMX for interactivity.

### `src/app/assets/`
Contains the **Source Assets**.
- **CSS**: Tailwind CSS source files (using the new Tailwind v4 engine).
- **JS**: Custom JavaScript modules before being processed/bundled.

### `src/app/partials/`
Contains **HTMX Partials**.
- These are small blocks of HTML managed by controllers that return partial views.
- Added fastcore to the project to use it for generate HTML from Python code.
- Used for dynamic updates without full page reloads.

### `src/app/templates/`
Contains **Page Controllers and Views**.
- Every folder here typically represents a feature or route (e.g., `sign/`).
- **`template.py`**: The Python controller inheriting from `Template` that defines routes and enqueues assets.
- **HTML files**: The actual page templates.

### `src/app/web/`
Contains **Global Web Assets**.
- **`layouts/`**: Shared layouts (e.g., `panel.html`).
- **`base.html`**: The main HTML skeleton with injection points for scripts and styles.
- **`out/`**: The build destination for compiled CSS and JS.

---

## Technical Responsibilities

- **Controllers**: Located in `src/app/templates/*/template.py`. They handle the logic for a specific route.
- **Styling**: Handled at the root level via Tailwind CSS, with local overrides if necessary.
- **State Management**: Alpine.js is used within the HTML templates for client-side state, while Python handles the server-side state.
