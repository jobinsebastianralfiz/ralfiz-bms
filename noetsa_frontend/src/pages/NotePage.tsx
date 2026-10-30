import { useRef, useState } from "react";
import { EditorContent, useEditor, type Editor } from "@tiptap/react";
import { BookmarkPlus, FileDown, FileText, MoveHorizontal, Settings2 } from "lucide-react";
import { useAutosave } from "../autosave";
import { Breadcrumb, ConflictBanner, NoteMenu, SaveIndicator, TrashActions } from "../components/NoteChrome";
import { Dropdown } from "../components/Dropdown";
import { buildExtensions } from "../editor/extensions";
import { BlockHandle } from "../editor/BlockHandle";
import { SelectionMenu } from "../editor/SelectionMenu";
import { Toolbar } from "../editor/Toolbar";
import { imageFiles, insertImages } from "../editor/uploads";
import type { Note } from "../types";
import { ExportDialog, PageSetupDialog, pageWidthMm } from "./PdfDialogs";
import { SaveTemplateDialog } from "./TemplatesPage";

/** An on/off view preference remembered per browser. */
function useStoredToggle(key: string, fallback: boolean) {
  const [on, setOn] = useState(() => {
    try {
      const value = localStorage.getItem(key);
      return value === null ? fallback : value === "1";
    } catch {
      return fallback;
    }
  });
  function toggle() {
    setOn((current) => {
      try {
        localStorage.setItem(key, current ? "0" : "1");
      } catch {
        // Private mode: the choice just isn't remembered.
      }
      return !current;
    });
  }
  return [on, toggle] as const;
}

export function DocEditor({ note, onReload }: { note: Note; onReload: () => void }) {
  const trashed = Boolean(note.deleted_at);
  const [title, setTitle] = useState(note.title);
  const { status, conflict, schedule, keepMine, discardMine, saveNow } = useAutosave(note);
  const [pageView, togglePageView] = useStoredToggle("noetsa:page-view", false);
  // Page view keeps the paper width, so full width only applies outside it.
  const [fullWidth, toggleFullWidth] = useStoredToggle("noetsa:full-width", true);
  const [dialog, setDialog] = useState<"setup" | "export" | "template" | null>(null);

  const editorRef = useRef<Editor | null>(null);
  const editor = useEditor({
    extensions: buildExtensions(),
    content: note.content ?? "",
    editable: !trashed,
    onUpdate: ({ editor }) => schedule({ content: editor.getJSON() }),
    editorProps: {
      // Pasted or dropped image files are uploaded to the asset store, then inserted.
      handlePaste: (_view, event) => {
        const files = imageFiles(event.clipboardData?.files);
        if (!files.length || !editorRef.current) return false;
        event.preventDefault();
        void insertImages(editorRef.current, files);
        return true;
      },
      handleDrop: (view, event, _slice, moved) => {
        const files = imageFiles(event.dataTransfer?.files);
        if (moved || !files.length || !editorRef.current) return false;
        event.preventDefault();
        const pos = view.posAtCoords({ left: event.clientX, top: event.clientY })?.pos;
        void insertImages(editorRef.current, files, pos);
        return true;
      },
    },
  });
  editorRef.current = editor;

  return (
    <div className="editor-page">
      <header className="doc-header">
        <div className="doc-topbar">
          <Breadcrumb note={note}>
            <span className="ellipsis breadcrumb-current">{title || "Untitled"}</span>
          </Breadcrumb>
          <div className="editor-bar-right">
            {!trashed && <SaveIndicator status={status} />}
            {!trashed && (
              <>
                <button className="btn btn-sm btn-ghost-strong" onClick={() => setDialog("export")}>
                  <FileDown size={15} /> <span className="hide-sm">Export PDF</span>
                </button>
                <Dropdown label="Page layout" button={<FileText size={17} />} caret={false} active={pageView} align="right">
                  {(close) => (
                    <div className="menu">
                      <button type="button" className={pageView ? "active" : ""} onClick={() => { togglePageView(); close(); }}>
                        <FileText size={16} /> {pageView ? "Hide page view" : "Show page view"}
                      </button>
                      {!pageView && (
                        <button type="button" className={fullWidth ? "active" : ""} onClick={() => { toggleFullWidth(); close(); }}>
                          <MoveHorizontal size={16} /> {fullWidth ? "Narrow width" : "Full width"}
                        </button>
                      )}
                      <button type="button" onClick={() => { setDialog("setup"); close(); }}>
                        <Settings2 size={16} /> Page setup…
                      </button>
                      <button type="button" onClick={() => { setDialog("template"); close(); }}>
                        <BookmarkPlus size={16} /> Save as template…
                      </button>
                    </div>
                  )}
                </Dropdown>
                <NoteMenu note={note} />
              </>
            )}
          </div>
        </div>
        {trashed ? <TrashActions note={note} /> : <div className="doc-toolbar"><Toolbar editor={editor} /></div>}
      </header>

      {conflict && <ConflictBanner onKeepMine={keepMine} onLoadTheirs={() => {
            if (discardMine()) onReload();
          }} />}

      <div className={`editor-scroll ${pageView ? "page-view" : fullWidth ? "full-width" : ""}`}>
        <div className="editor-doc" style={pageView ? pageSheetStyle(note) : undefined}>
          <input
            className="title-input"
            placeholder="Untitled"
            value={title}
            readOnly={trashed}
            maxLength={200}
            onChange={(e) => {
              setTitle(e.target.value);
              schedule({ title: e.target.value });
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                editor?.commands.focus("start");
              }
            }}
          />
          <EditorContent editor={editor} className="prose" />
          {editor && !trashed && <BlockHandle editor={editor} />}
          {editor && !trashed && <SelectionMenu editor={editor} />}
        </div>
      </div>

      {dialog === "setup" && <PageSetupDialog note={note} onClose={() => setDialog(null)} />}
      {dialog === "export" && <ExportDialog note={note} saveNow={saveNow} onClose={() => setDialog(null)} />}
      {dialog === "template" && <SaveTemplateDialog note={note} saveNow={saveNow} onClose={() => setDialog(null)} />}
    </div>
  );
}

/** Page view: a white sheet with the note's paper width and margins (pagination itself shows in the PDF preview). */
function pageSheetStyle(note: Note) {
  const s = note.page_settings;
  const m = s.margins;
  return {
    width: `${pageWidthMm(s)}mm`,
    maxWidth: "none",
    padding: `${Math.max(m.top, 8)}mm ${Math.max(m.right, 8)}mm ${Math.max(m.bottom, 8)}mm ${Math.max(m.left, 8)}mm`,
  };
}
