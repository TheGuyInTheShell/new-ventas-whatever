import { defineConfig } from "rolldown";
import postcss from "rollup-plugin-postcss";
import { globSync } from 'tinyglobby';
import path from 'node:path';
import { readFileSync } from 'node:fs';

const pkg = JSON.parse(readFileSync(new URL('./package.json', import.meta.url)));

export default defineConfig({
  input: Object.fromEntries(
    globSync('plugins/admin_core/assets/**/*.js').map((file) => [
      // This removes `plugins/admin_core/assets/` as well as the file extension from each
      // file, so e.g. src/nested/foo.js becomes nested/foo, and
      // normalizes Windows backslashes to forward slashes.
      path
        .relative('plugins/admin_core/assets/', file.slice(0, file.length - path.extname(file).length))
        .split(path.sep)
        .join('/'),
      // This expands the relative paths to absolute paths, so e.g.
      // src/nested/foo.js becomes /project/src/nested/foo.js
      path.resolve(file),
    ]),
  ),
  output: {
    dir: "./plugins/admin_core/web/out",
    format: "esm",
    entryFileNames: "[name].js",
    chunkFileNames: "chunks/[name]-[hash].js",
    minify: true,
  },
  moduleTypes: {
    ".css": "js",
  },
  plugins: [
    postcss({
      extract: "css/app.css", // relative to output.dir → src/admin/web/out/css/app.css
      minimize: true,
    }),
  ],
  // Marcamos dependencias del sub-package como externas automáticamente
  external: Object.keys(pkg.dependencies || {}),
});
