import "./excalidrawSetup";
import { useState } from "react";
import { createPortal } from "react-dom";
import { Excalidraw, exportToBlob } from "@excalidraw/excalidraw";
import type { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";
import type { ExcalidrawElement } from "@excalidraw/excalidraw/element/types";
import "@excalidraw/excalidraw/index.css";
import { LoaderCircle } from "lucide-react";
import { useResolvedTheme } from "../theme";
import { CLEAN_DEFAULTS } from "./boardStyle";
import { uploadImage } from "./uploads";

export type DrawingScene = { elements: readonly ExcalidrawElement[]; background: string };

type Saved = { src: string; scene: DrawingScene; width: number };

/** Full-screen Excalidraw for editing a drawing block. Saving exports a PNG to the asset store. */
export function DrawingDialog({ scene, onSave, onCancel }: { scene: DrawingScene | null; onSave: (saved: Saved) => void; onCancel: () => void }) {
  const dark = useResolvedTheme() === "dark";
  const [api, setApi] = useState<ExcalidrawImperativeAPI | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    if (!api) return;
    const elements = api.getSceneElements();
    if (!elements.length) {
      onCancel();
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const background = scene?.background ?? "#ffffff";
      // Exported at 2x so it stays sharp on high-density screens and in PDFs; shown at 1x.
      const blob = await exportToBlob({
        elements,
        appState: { exportBackground: true, viewBackgroundColor: background },
        files: null,
        mimeType: "image/png",
        exportPadding: 16,
        getDimensions: (width: number, height: number) => ({ width: width * 2, height: height * 2, scale: 2 }),
      });
      const bitmap = await createImageBitmap(blob);
      const width = Math.round(bitmap.width / 2);
      bitmap.close();
      const { url } = await uploadImage(new File([blob], "drawing.png", { type: "image/png" }));
      onSave({ src: url, scene: { elements, background }, width });
    } catch (e) {
      setError((e as Error).message || "Couldn't save the drawing.");
      setSaving(false);
    }
  }

  return createPortal(
    <div className="drawing-dialog" role="dialog" aria-modal="true" aria-label="Drawing">
      <header className="drawing-dialog-bar">
        <strong>Drawing</strong>
        <span className="muted small hide-sm">Shapes, arrows, text and freehand. Saved into your note as a picture.</span>
        {error && <span className="field-error small">{error}</span>}
        <div className="drawing-dialog-actions">
          <button className="btn btn-sm" onClick={onCancel} disabled={saving}>Cancel</button>
          <button className="btn btn-sm btn-primary" onClick={save} disabled={saving || !api}>
            {saving ? <><LoaderCircle size={14} className="spin" /> Saving…</> : "Save drawing"}
          </button>
        </div>
      </header>
      <div className="drawing-dialog-canvas">
        <Excalidraw
          excalidrawAPI={setApi}
          initialData={{
            elements: scene?.elements ?? [],
            appState: { viewBackgroundColor: scene?.background ?? "#ffffff", ...CLEAN_DEFAULTS },
            scrollToContent: true,
          }}
          theme={dark ? "dark" : "light"}
          UIOptions={{
            canvasActions: { saveToActiveFile: false, loadScene: false, export: false, saveAsImage: false, clearCanvas: true },
            // Images would bloat the note; they belong in the note itself.
            tools: { image: false },
          }}
        />
      </div>
    </div>,
    document.body,
  );
}
