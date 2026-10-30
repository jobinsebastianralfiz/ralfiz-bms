import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Download, LoaderCircle, TriangleAlert } from "lucide-react";
import { Modal } from "../components/Modal";
import { api, apiBlob, ApiError } from "../api";
import { useNoteList } from "../notes";
import type { Note, PageSettings } from "../types";

/** Paper sizes in millimetres, portrait. Must match notes/pages.py. */
export const PAGE_SIZES: Record<PageSettings["size"], [number, number]> = {
  A4: [210, 297],
  Letter: [215.9, 279.4],
  Legal: [215.9, 355.6],
};

export function pageWidthMm(settings: PageSettings) {
  const [w, h] = PAGE_SIZES[settings.size];
  return settings.orientation === "landscape" ? h : w;
}

export function PageSetupDialog({ note, onClose }: { note: Note; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [s, setS] = useState<PageSettings>(note.page_settings);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const set = <K extends keyof PageSettings>(key: K, value: PageSettings[K]) => setS((prev) => ({ ...prev, [key]: value }));
  const setMargin = (side: keyof PageSettings["margins"], value: string) =>
    setS((prev) => ({ ...prev, margins: { ...prev.margins, [side]: value === "" ? 0 : Number(value) } }));

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const saved = await api<Note>(`/notes/${note.id}/`, { method: "PATCH", body: { page_settings: s } });
      // Only page settings changed; keep the cached title/content the editor is working from.
      queryClient.setQueryData<Note>(["note", note.id], (old) => old && { ...old, page_settings: saved.page_settings });
      onClose();
    } catch (e) {
      const err = e as ApiError;
      setError(err.fields.page_settings?.[0] ?? err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title="Page setup" onClose={onClose}>
      <div className="form-grid">
        <label className="field">
          Paper size
          <select value={s.size} onChange={(e) => set("size", e.target.value as PageSettings["size"])}>
            <option value="A4">A4 (210 × 297 mm)</option>
            <option value="Letter">Letter (8.5 × 11 in)</option>
            <option value="Legal">Legal (8.5 × 14 in)</option>
          </select>
        </label>
        <label className="field">
          Orientation
          <select value={s.orientation} onChange={(e) => set("orientation", e.target.value as PageSettings["orientation"])}>
            <option value="portrait">Portrait</option>
            <option value="landscape">Landscape</option>
          </select>
        </label>
      </div>

      <fieldset className="margins">
        <legend>Margins (mm)</legend>
        {(["top", "bottom", "left", "right"] as const).map((side) => (
          <label key={side} className="field">
            {side[0].toUpperCase() + side.slice(1)}
            <input type="number" min={0} max={60} step={1} value={s.margins[side]} onChange={(e) => setMargin(side, e.target.value)} />
          </label>
        ))}
      </fieldset>

      <label className="field">
        Header
        <input value={s.header} maxLength={200} placeholder="Shown at the top of every page" onChange={(e) => set("header", e.target.value)} />
      </label>
      <label className="field">
        Footer
        <input value={s.footer} maxLength={200} placeholder="Shown at the bottom of every page" onChange={(e) => set("footer", e.target.value)} />
      </label>

      <label className="check">
        <input type="checkbox" checked={s.page_numbers} onChange={(e) => set("page_numbers", e.target.checked)} />
        Page numbers
      </label>
      <label className="check">
        <input type="checkbox" checked={s.show_title} onChange={(e) => set("show_title", e.target.checked)} />
        Print the note title at the top
      </label>

      {error && <p className="field-error">{error}</p>}
      <div className="modal-actions">
        <button className="btn" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save"}
        </button>
      </div>
    </Modal>
  );
}

type Preview = { url: string; filename: string } | null;

export function ExportDialog({ note, saveNow, onClose }: { note: Note; saveNow: () => Promise<boolean>; onClose: () => void }) {
  const [extra, setExtra] = useState<string[]>([]);
  const [preview, setPreview] = useState<Preview>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unsaved, setUnsaved] = useState(false);
  const others = useNoteList({ kind: "doc" });
  const request = useRef(0);

  useEffect(() => {
    const id = ++request.current;
    let url: string | null = null;
    setLoading(true);
    setError(null);
    (async () => {
      try {
        // Make sure the PDF includes the latest edits.
        setUnsaved(!(await saveNow()));
        const blob = extra.length
          ? await apiBlob("/notes/export-pdf/", { method: "POST", body: { notes: [note.id, ...extra] } })
          : await apiBlob(`/notes/${note.id}/pdf/`);
        if (id !== request.current) return;
        url = URL.createObjectURL(blob);
        const slug = (note.title || "note").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "note";
        setPreview({ url, filename: `${slug}.pdf` });
      } catch (e) {
        if (id === request.current) setError((e as ApiError).message);
      } finally {
        if (id === request.current) setLoading(false);
      }
    })();
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [note.id, note.title, extra, saveNow]);

  const candidates = (others.data?.pages.flatMap((p) => p.results) ?? []).filter((n) => n.id !== note.id && n.kind === "doc");

  return (
    <Modal title="Export PDF" wide onClose={onClose}>
      <div className="export-layout">
        <div className="pdf-preview">
          {loading && (
            <div className="pdf-preview-status">
              <LoaderCircle className="spin" size={22} /> Preparing PDF…
            </div>
          )}
          {!loading && error && (
            <div className="pdf-preview-status">
              <TriangleAlert size={20} /> {error}
            </div>
          )}
          {!loading && !error && preview && <iframe title="PDF preview" src={preview.url} />}
        </div>

        <div className="export-side">
          {unsaved && (
            <p className="alert alert-warn small">
              <TriangleAlert size={14} /> Your latest edits aren't saved yet, so they may be missing from this PDF.
            </p>
          )}

          {candidates.length > 0 && (
            <div className="combine">
              <h3>Add more notes</h3>
              <p className="muted small">They're added after this note, in the order you tick them.</p>
              <ul>
                {candidates.map((n) => (
                  <li key={n.id}>
                    <label className="check">
                      <input
                        type="checkbox"
                        checked={extra.includes(n.id)}
                        onChange={(e) => setExtra((prev) => (e.target.checked ? [...prev, n.id] : prev.filter((x) => x !== n.id)))}
                      />
                      <span className="ellipsis">{n.title || "Untitled"}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <a
            className={`btn btn-primary ${!preview || loading ? "disabled" : ""}`}
            href={preview?.url}
            download={preview?.filename}
            aria-disabled={!preview || loading}
          >
            <Download size={16} /> Download PDF
          </a>
        </div>
      </div>
    </Modal>
  );
}
