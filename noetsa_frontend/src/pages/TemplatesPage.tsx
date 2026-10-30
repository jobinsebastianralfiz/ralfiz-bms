import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { EditorContent, useEditor } from "@tiptap/react";
import { LayoutTemplate, LoaderCircle, Trash2 } from "lucide-react";
import { api, ApiError } from "../api";
import { Modal } from "../components/Modal";
import { notify } from "../components/Toaster";
import { buildExtensions } from "../editor/extensions";
import { CATEGORY_LABELS, useTemplates, useUseTemplate } from "../templates";
import type { Note, TemplateCategory, TemplateDetail } from "../types";
import { pageWidthMm } from "./PdfDialogs";

type Filter = "all" | "mine" | TemplateCategory;

export function TemplatesPage() {
  const templates = useTemplates();
  const [filter, setFilter] = useState<Filter>("all");
  const [open, setOpen] = useState<string | null>(null);

  const all = templates.data ?? [];
  const shown = all.filter((t) => (filter === "all" ? true : filter === "mine" ? !t.builtin : t.category === filter));
  const hasMine = all.some((t) => !t.builtin);
  const filters: { key: Filter; label: string }[] = [
    { key: "all", label: "All" },
    ...(Object.keys(CATEGORY_LABELS) as TemplateCategory[]).map((key) => ({ key, label: CATEGORY_LABELS[key] })),
    ...(hasMine ? [{ key: "mine" as Filter, label: "My templates" }] : []),
  ];

  return (
    <div className="page templates-page">
      <h1>
        <LayoutTemplate size={24} /> Templates
      </h1>
      <p className="muted">Start a resume, invoice, letter or plan from a ready-made layout. Everything stays editable.</p>

      <div className="chips" role="tablist">
        {filters.map((f) => (
          <button key={f.key} role="tab" aria-selected={filter === f.key} className={`chip ${filter === f.key ? "active" : ""}`} onClick={() => setFilter(f.key)}>
            {f.label}
          </button>
        ))}
      </div>

      {templates.isLoading && <div className="spinner" />}
      {templates.isError && <div className="alert alert-error">{(templates.error as Error).message}</div>}

      <div className="template-grid">
        {shown.map((t) => (
          <button key={t.id} className="template-card" onClick={() => setOpen(t.id)}>
            <div className="template-thumb" aria-hidden="true">
              <span className="thumb-title">{t.name}</span>
              <span className="thumb-text">{t.preview}</span>
            </div>
            <div className="template-info">
              <div className="template-name">
                <span>{t.name}</span>
                {!t.builtin && <span className="badge">Mine</span>}
              </div>
              <p className="muted small">{t.description || CATEGORY_LABELS[t.category]}</p>
            </div>
          </button>
        ))}
      </div>

      {open && <TemplatePreview id={open} onClose={() => setOpen(null)} />}
    </div>
  );
}

function TemplatePreview({ id, onClose }: { id: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const detail = useQuery({ queryKey: ["template", id], queryFn: () => api<TemplateDetail>(`/templates/${id}/`) });
  const use = useUseTemplate();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const t = detail.data;

  async function remove() {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    await api(`/templates/${id}/`, { method: "DELETE" });
    await queryClient.invalidateQueries({ queryKey: ["templates"] });
    notify("Template deleted");
    onClose();
  }

  return (
    <Modal title={t?.name ?? "Template"} wide onClose={onClose}>
      <div className="export-layout">
        <div className="template-preview">
          {detail.isLoading && <div className="pdf-preview-status"><LoaderCircle className="spin" size={22} /></div>}
          {t && <ReadOnlyDoc template={t} />}
        </div>
        <div className="export-side">
          {t && (
            <>
              <p className="muted">{t.description}</p>
              <p className="small muted">
                {CATEGORY_LABELS[t.category]} · {t.page_settings.size} {t.page_settings.orientation}
              </p>
              {!t.builtin && (
                <button className="btn btn-sm btn-danger" onClick={remove}>
                  <Trash2 size={14} /> {confirmDelete ? "Click again to delete" : "Delete template"}
                </button>
              )}
            </>
          )}
          <button className="btn btn-primary" disabled={!t || use.isPending} onClick={() => use.mutate(id)}>
            {use.isPending ? "Creating…" : "Use this template"}
          </button>
        </div>
      </div>
    </Modal>
  );
}

/** The template rendered by the real editor (read-only) on a page-width sheet, scaled to fit. */
function ReadOnlyDoc({ template }: { template: TemplateDetail }) {
  const editor = useEditor({ extensions: buildExtensions(), content: template.content, editable: false });
  const m = template.page_settings.margins;
  return (
    <div className="template-sheet-wrap">
      <div
        className="template-sheet prose"
        style={{ width: `${pageWidthMm(template.page_settings)}mm`, padding: `${m.top}mm ${m.right}mm ${m.bottom}mm ${m.left}mm` }}
      >
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}

/** "Save as template" from a note. */
export function SaveTemplateDialog({ note, saveNow, onClose }: { note: Note; saveNow: () => Promise<boolean>; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(note.title || "");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<TemplateCategory>("personal");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      await saveNow();
      await api("/templates/", { method: "POST", body: { note: note.id, name: name.trim(), description, category } });
      await queryClient.invalidateQueries({ queryKey: ["templates"] });
      notify("Saved as a template");
      onClose();
    } catch (e) {
      const err = e as ApiError;
      setError(err.fields.name?.[0] ?? err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title="Save as template" onClose={onClose}>
      <p className="muted small">New notes made from it start with this note's content and page setup.</p>
      <label className="field">
        Name
        <input value={name} maxLength={120} onChange={(e) => setName(e.target.value)} autoFocus />
      </label>
      <label className="field">
        Description
        <input value={description} maxLength={240} placeholder="Optional" onChange={(e) => setDescription(e.target.value)} />
      </label>
      <label className="field">
        Category
        <select value={category} onChange={(e) => setCategory(e.target.value as TemplateCategory)}>
          {(Object.keys(CATEGORY_LABELS) as TemplateCategory[]).map((key) => (
            <option key={key} value={key}>{CATEGORY_LABELS[key]}</option>
          ))}
        </select>
      </label>
      {error && <p className="field-error">{error}</p>}
      <div className="modal-actions">
        <button className="btn" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={save} disabled={saving || !name.trim()}>
          {saving ? "Saving…" : "Save template"}
        </button>
      </div>
    </Modal>
  );
}
