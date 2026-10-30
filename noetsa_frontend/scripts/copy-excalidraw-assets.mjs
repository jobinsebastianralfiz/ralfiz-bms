// Copies Excalidraw's fonts into public/ so boards don't depend on a CDN (and work offline).
// Runs before `dev` and `build`; the copy is gitignored.
import { cpSync, existsSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const source = join(root, "node_modules/@excalidraw/excalidraw/dist/prod/fonts");
const target = join(root, "public/excalidraw/fonts");

if (!existsSync(source)) {
  console.error("Excalidraw fonts not found; run npm install first.");
  process.exit(1);
}
rmSync(target, { recursive: true, force: true });
cpSync(source, target, { recursive: true });
