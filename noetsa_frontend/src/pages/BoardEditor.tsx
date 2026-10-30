import "../editor/excalidrawSetup";
import { useCallback, useEffect, useRef, useState } from "react";
import { convertToExcalidrawElements, Excalidraw, hashElementsVersion, useHandleLibrary } from "@excalidraw/excalidraw";
import type { AppState, BinaryFileData, BinaryFiles, ExcalidrawImperativeAPI, LibraryItems } from "@excalidraw/excalidraw/types";
import type { ExcalidrawElement } from "@excalidraw/excalidraw/element/types";
import "@excalidraw/excalidraw/index.css";
import { FilePlus2, Shapes } from "lucide-react";
import { api, API_BASE, ApiError } from "../api";
import { useAutosave } from "../autosave";
import { Breadcrumb, ConflictBanner, NoteMenu, SaveIndicator, TrashActions } from "../components/NoteChrome";
import { notify } from "../components/Toaster";
import { CLEAN_DEFAULTS } from "../editor/boardStyle";
import { insertElements, ShapePanel } from "../editor/ShapePanel";
import { ensureBoardFont } from "../editor/boardShapes";
import { STARTERS, type Starter } from "../editor/boardStarters";
import { useResolvedTheme } from "../theme";
import type { Note } from "../types";

/** What a board stores. Images live in the asset store; `files` maps Excalidraw file ids to asset ids. */
type BoardScene = {
  type: "excalidraw";
  version: 2;
  elements: ExcalidrawElement[];
  appState: { viewBackgroundColor?: string; gridModeEnabled?: boolean };
  files: Record<string, { asset: string; mimeType: string }>;
};

const LIBRARY_KEY = "noetsa:board-library";
const PANEL_KEY = "noetsa:shape-panel";

function panelOpenByDefault() {
  try {
    const saved = localStorage.getItem(PANEL_KEY);
    if (saved) return saved === "open";
  } catch {
    // Fall through to the screen-size default.
  }
  return window.matchMedia("(min-width: 761px)").matches;
}

function readScene(note: Note): BoardScene {
  const c = (note.content ?? {}) as Partial<BoardScene>;
  return {
    type: "excalidraw",
    version: 2,
    elements: Array.isArray(c.elements) ? c.elements : [],
    appState: c.appState ?? {},
    files: c.files ?? {},
  };
}

function blobToDataURL(blob: Blob) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

// Shape libraries are kept per browser for now (Excalidraw's "Library" panel).
const libraryAdapter = {
  load: () => {
    try {
      const raw = localStorage.getItem(LIBRARY_KEY);
      return raw ? { libraryItems: JSON.parse(raw) as LibraryItems } : null;
    } catch {
      return null;
    }
  },
  save: ({ libraryItems }: { libraryItems: LibraryItems }) => {
    try {
      localStorage.setItem(LIBRARY_KEY, JSON.stringify(libraryItems));
    } catch {
      notify("Couldn't save your shape library in this browser.");
    }
  },
};

export function BoardEditor({ note, onReload }: { note: Note; onReload: () => void }) {
  const trashed = Boolean(note.deleted_at);
  const dark = useResolvedTheme() === "dark";
  const [title, setTitle] = useState(note.title);
  const { status, conflict, schedule, keepMine, discardMine } = useAutosave(note);
  const [excalidraw, setExcalidraw] = useState<ExcalidrawImperativeAPI | null>(null);
  const initial = useRef(readScene(note));
  // Excalidraw file id -> asset; grows as pasted images finish uploading.
  const fileMap = useRef<BoardScene["files"]>({ ...initial.current.files });
  const uploading = useRef(new Set<string>());
  const lastKey = useRef<string | null>(null);
  const excalidrawRef = useRef<ExcalidrawImperativeAPI | null>(null);
  excalidrawRef.current = excalidraw;
  const empty = initial.current.elements.length === 0;
  const [panelOpen, setPanelOpen] = useState(() => !trashed && panelOpenByDefault());
  // A new, empty board offers starter boards until something is drawn.
  const [showStarters, setShowStarters] = useState(empty && !trashed);

  function togglePanel() {
    setPanelOpen((open) => {
      try {
        localStorage.setItem(PANEL_KEY, open ? "closed" : "open");
      } catch {
        // Only a convenience.
      }
      return !open;
    });
  }

  async function applyStarter(starter: Starter) {
    setShowStarters(false);
    if (!excalidraw) return;
    await ensureBoardFont();
    const placed = insertElements(excalidraw, convertToExcalidrawElements(starter.build(), { regenerateIds: true }), { x: 0, y: 0 });
    excalidraw.updateScene({ appState: { selectedElementIds: {}, selectedGroupIds: {} } });
    excalidraw.scrollToContent(placed, { fitToViewport: true, viewportZoomFactor: 0.85 });
  }

  useHandleLibrary({ excalidrawAPI: excalidraw, adapter: libraryAdapter });

  const save = useCallback(
    (elements: readonly ExcalidrawElement[], appState: AppState, force = false) => {
      const key = `${hashElementsVersion(elements)}:${appState.viewBackgroundColor}:${appState.gridModeEnabled}:${Object.keys(fileMap.current).length}`;
      if (!force && key === lastKey.current) return;
      const first = lastKey.current === null;
      lastKey.current = key;
      // The first onChange after mount just reports the loaded scene; nothing to save.
      if (first && !force) return;
      const live = elements.filter((el) => !el.isDeleted);
      const used = new Set<string>(live.flatMap((el) => (el.type === "image" && el.fileId ? [el.fileId] : [])));
      const scene: BoardScene = {
        type: "excalidraw",
        version: 2,
        elements: live,
        appState: { viewBackgroundColor: appState.viewBackgroundColor, gridModeEnabled: appState.gridModeEnabled },
        files: Object.fromEntries(Object.entries(fileMap.current).filter(([id]) => used.has(id))),
      };
      schedule({ content: scene });
    },
    [schedule],
  );

  /** Upload images Excalidraw holds only as data URLs, so the board stores a small reference instead. */
  const uploadNewImages = useCallback(
    (elements: readonly ExcalidrawElement[], files: BinaryFiles) => {
      for (const el of elements) {
        if (el.type !== "image" || el.isDeleted || !el.fileId) continue;
        const id = el.fileId;
        const file = files[id];
        if (fileMap.current[id] || uploading.current.has(id) || !file) continue;
        uploading.current.add(id);
        void (async () => {
          try {
            const blob = await (await fetch(file.dataURL)).blob();
            const form = new FormData();
            form.append("file", blob, `board-image.${file.mimeType.split("/")[1] ?? "png"}`);
            const asset = await api<{ id: string }>("/assets/", { method: "POST", body: form });
            fileMap.current[id] = { asset: asset.id, mimeType: file.mimeType };
            if (excalidrawRef.current) {
              save(excalidrawRef.current.getSceneElementsIncludingDeleted(), excalidrawRef.current.getAppState(), true);
            }
          } catch (e) {
            notify(`Couldn't save an image: ${(e as ApiError).message}`);
          } finally {
            uploading.current.delete(id);
          }
        })();
      }
    },
    [save],
  );

  // Fetch the board's images from the asset store and hand them to Excalidraw.
  useEffect(() => {
    if (!excalidraw) return;
    const entries = Object.entries(initial.current.files);
    if (!entries.length) return;
    let cancelled = false;
    void Promise.all(
      entries.map(async ([id, ref]): Promise<BinaryFileData | null> => {
        try {
          const res = await fetch(`${API_BASE}/assets/${ref.asset}/`, { credentials: "same-origin" });
          if (!res.ok) return null;
          return { id: id as BinaryFileData["id"], mimeType: ref.mimeType as BinaryFileData["mimeType"], dataURL: (await blobToDataURL(await res.blob())) as BinaryFileData["dataURL"], created: Date.now() };
        } catch {
          return null;
        }
      }),
    ).then((loaded) => {
      if (!cancelled) excalidraw.addFiles(loaded.filter((f): f is BinaryFileData => f !== null));
    });
    return () => {
      cancelled = true;
    };
  }, [excalidraw]);

  return (
    <div className="editor-page board-page">
      <header className="doc-topbar board-bar">
        {trashed ? (
          <TrashActions note={note} />
        ) : (
          <Breadcrumb note={note}>
            <input
              className="board-title"
              placeholder="Untitled board"
              aria-label="Board title"
              value={title}
              maxLength={200}
              onChange={(e) => {
                setTitle(e.target.value);
                schedule({ title: e.target.value });
              }}
            />
          </Breadcrumb>
        )}
        <div className="editor-bar-right">
          {!trashed && <SaveIndicator status={status} />}
          {!trashed && (
            <button type="button" className={`btn btn-sm btn-ghost-strong${panelOpen ? " active" : ""}`} onClick={togglePanel} aria-pressed={panelOpen}>
              <Shapes size={15} /> <span className="hide-sm">Shapes</span>
            </button>
          )}
          {!trashed && <NoteMenu note={note} />}
        </div>
      </header>

      {conflict && (
        <ConflictBanner
          onKeepMine={keepMine}
          onLoadTheirs={() => {
            if (discardMine()) onReload();
          }}
        />
      )}

      <div className="board-canvas">
        {panelOpen && !trashed && <ShapePanel api={excalidraw} dark={dark} onClose={togglePanel} />}
        <div className="board-stage">
        {showStarters && (
          <div className="board-starters" role="dialog" aria-label="Start this board">
            <div className="board-starters-card">
              <h2>Start your board</h2>
              <p className="muted">Pick a ready-made layout, or start from a blank canvas.</p>
              <div className="board-starters-grid">
                <button type="button" className="starter-option blank" onClick={() => setShowStarters(false)}>
                  <FilePlus2 size={22} />
                  <strong>Blank board</strong>
                  <span>Draw from scratch</span>
                </button>
                {STARTERS.map((s) => (
                  <button key={s.id} type="button" className="starter-option" onClick={() => applyStarter(s)} disabled={!excalidraw}>
                    <strong>{s.name}</strong>
                    <span>{s.description}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
        <Excalidraw
          excalidrawAPI={setExcalidraw}
          initialData={{
            elements: initial.current.elements,
            // Crisp diagram style and right-angle connectors; new boards start with the grid on.
            appState: {
              ...CLEAN_DEFAULTS,
              currentItemArrowType: "elbow",
              ...(empty && initial.current.appState.gridModeEnabled === undefined ? { gridModeEnabled: true } : {}),
              ...initial.current.appState,
            },
            scrollToContent: true,
          }}
          onChange={(elements, appState, files) => {
            if (trashed) return;
            if (showStarters && elements.some((el) => !el.isDeleted)) setShowStarters(false);
            uploadNewImages(elements, files);
            save(elements, appState);
          }}
          theme={dark ? "dark" : "light"}
          name={title || "Untitled board"}
          viewModeEnabled={trashed}
          UIOptions={{ canvasActions: { saveToActiveFile: false } }}
        />
        </div>
      </div>
    </div>
  );
}
