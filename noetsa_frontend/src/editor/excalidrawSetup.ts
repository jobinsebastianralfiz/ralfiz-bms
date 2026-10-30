// Must be imported before @excalidraw/excalidraw: tells it to load fonts from our own static
// files (copied by scripts/copy-excalidraw-assets.mjs) instead of a CDN.
declare global {
  interface Window {
    EXCALIDRAW_ASSET_PATH?: string | string[];
  }
}

window.EXCALIDRAW_ASSET_PATH = `${import.meta.env.BASE_URL}excalidraw/`;

export {};
