import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Where `manage.py runserver` listens; override with DJANGO_URL=http://127.0.0.1:8766 npm run dev
const django = process.env.DJANGO_URL ?? "http://127.0.0.1:8000";

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // The production build is collected by Django as /static/noetsa/ (STATICFILES_DIRS in
  // config/settings.py) and its index.html is served for every /notes/ page by notes.views.spa.
  base: command === "build" ? "/static/noetsa/" : "/",
  server: {
    port: 5173,
    // Open http://localhost:5173/notes/ after signing in to Django through the same proxy (/login/).
    proxy: {
      "/notes/api": django,
      "/login": django,
      "/logout": django,
      "/static": django,
    },
  },
}));
