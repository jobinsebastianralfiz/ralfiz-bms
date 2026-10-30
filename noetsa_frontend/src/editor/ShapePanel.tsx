import { useEffect, useMemo, useState } from "react";
import { CaptureUpdateAction, convertToExcalidrawElements, exportToSvg, MIME_TYPES, serializeLibraryAsJSON } from "@excalidraw/excalidraw";
import type { ExcalidrawImperativeAPI } from "@excalidraw/excalidraw/types";
import type { ExcalidrawElement } from "@excalidraw/excalidraw/element/types";
import { ChevronDown, Search, X } from "lucide-react";
import { ensureBoardFont, SHAPE_GROUPS, type Skeleton } from "./boardShapes";
import { STARTERS } from "./boardStarters";

type Item = { id: string; name: string; keywords?: string; build: () => Skeleton[] };

const STARTER_ITEMS: Item[] = STARTERS.map((s) => ({ id: `starter-${s.id}`, name: s.name, keywords: s.description, build: s.build }));
const GROUPS: { name: string; items: Item[] }[] = [
  ...SHAPE_GROUPS.map((g) => ({ name: g.name, items: g.shapes.map((s) => ({ ...s, build: () => s.build(0, 0) })) })),
  { name: "Starter boards", items: STARTER_ITEMS },
];

const COLLAPSED_KEY = "noetsa:shape-groups-collapsed";
// Rendered thumbnails, kept for the whole session ("light:process" -> SVG data URL).
const thumbs = new Map<string, string>();

function toElements(skeletons: Skeleton[]) {
  return convertToExcalidrawElements(skeletons, { regenerateIds: true });
}

async function renderThumb(item: Item, dark: boolean) {
  const key = `${dark ? "dark" : "light"}:${item.id}`;
  const cached = thumbs.get(key);
  if (cached) return cached;
  const svg = await exportToSvg({
    elements: toElements(item.build()),
    appState: { exportBackground: false, exportWithDarkMode: dark },
    files: null,
    exportPadding: 6,
    skipInliningFonts: true,
  });
  // An SVG shown through <img> can't reach the page's fonts, so labels use the system sans.
  const markup = svg.outerHTML.replace(/font-family="[^"]*"/g, 'font-family="system-ui, -apple-system, sans-serif"');
  const url = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(markup)}`;
  thumbs.set(key, url);
  return url;
}

// Where the last shape went, so repeated clicks without moving the view cascade instead of stacking.
let lastDrop = { x: NaN, y: NaN, count: 0 };

/** Adds elements in the middle of the visible canvas (or at `at`) and selects them, as one undo step. */
export function insertElements(api: ExcalidrawImperativeAPI, elements: readonly ExcalidrawElement[], at?: { x: number; y: number }) {
  const st = api.getAppState();
  const zoom = st.zoom.value;
  const minX = Math.min(...elements.map((e) => e.x));
  const minY = Math.min(...elements.map((e) => e.y));
  const maxX = Math.max(...elements.map((e) => e.x + e.width));
  const maxY = Math.max(...elements.map((e) => e.y + e.height));
  let cx = at?.x ?? st.width / 2 / zoom - st.scrollX;
  let cy = at?.y ?? st.height / 2 / zoom - st.scrollY;
  const selected = at ? [] : api.getSceneElements().filter((e) => st.selectedElementIds[e.id]);
  if (selected.length) {
    // Next to the selection, like a diagramming tool: build a flow by clicking shape after shape.
    cx = Math.max(...selected.map((e) => e.x + e.width)) + 60 + (maxX - minX) / 2;
    cy = (Math.min(...selected.map((e) => e.y)) + Math.max(...selected.map((e) => e.y + e.height))) / 2;
  } else if (!at) {
    lastDrop = lastDrop.x === cx && lastDrop.y === cy ? { ...lastDrop, count: lastDrop.count + 1 } : { x: cx, y: cy, count: 0 };
    cx += (lastDrop.count % 8) * 32;
    cy += (lastDrop.count % 8) * 32;
  }
  const dx = cx - (minX + maxX) / 2;
  const dy = cy - (minY + maxY) / 2;
  const moved = elements.map((e) => ({ ...e, x: e.x + dx, y: e.y + dy }));
  const groups = new Set(moved.flatMap((e) => (e.groupIds.length ? [e.groupIds[e.groupIds.length - 1]] : [])));
  api.updateScene({
    elements: [...api.getSceneElementsIncludingDeleted(), ...moved],
    appState: {
      selectedElementIds: Object.fromEntries(moved.filter((e) => !(e.type === "text" && e.containerId)).map((e) => [e.id, true])),
      selectedGroupIds: Object.fromEntries([...groups].map((g) => [g, true])),
    },
    captureUpdate: CaptureUpdateAction.IMMEDIATELY,
  });
  // Bring it into view if it landed off-screen (e.g. placed beside a shape near the edge).
  const left = -st.scrollX;
  const top = -st.scrollY;
  const inView = minX + dx >= left && minY + dy >= top && maxX + dx <= left + st.width / zoom && maxY + dy <= top + st.height / zoom;
  if (!inView && !at) api.scrollToContent(moved, { animate: true });
  return moved;
}

/** Lucidchart-style shape library beside the board. Click adds a shape in the middle of the view; drag drops it where you let go. */
export function ShapePanel({ api, dark, onClose }: { api: ExcalidrawImperativeAPI | null; dark: boolean; onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [collapsed, setCollapsed] = useState<Set<string>>(() => {
    try {
      return new Set(JSON.parse(localStorage.getItem(COLLAPSED_KEY) ?? "[]") as string[]);
    } catch {
      return new Set();
    }
  });
  const [, setRendered] = useState(0);

  // Render thumbnails one by one so the panel shows up straight away.
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      await ensureBoardFont();
      for (const item of GROUPS.flatMap((g) => g.items)) {
        if (cancelled) return;
        try {
          if (!thumbs.has(`${dark ? "dark" : "light"}:${item.id}`)) {
            await renderThumb(item, dark);
            setRendered((n) => n + 1);
          }
        } catch {
          // A missing thumbnail only shows the name.
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [dark]);

  const groups = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return GROUPS;
    return GROUPS.map((g) => ({ ...g, items: g.items.filter((i) => `${i.name} ${i.keywords ?? ""} ${g.name}`.toLowerCase().includes(q)) })).filter((g) => g.items.length);
  }, [query]);

  function toggle(name: string) {
    const next = new Set(collapsed);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    setCollapsed(next);
    try {
      localStorage.setItem(COLLAPSED_KEY, JSON.stringify([...next]));
    } catch {
      // Only a convenience.
    }
  }

  async function add(item: Item) {
    if (!api) return;
    await ensureBoardFont();
    insertElements(api, toElements(item.build()));
    api.setActiveTool({ type: "selection" });
    // On phones the panel covers the board; get out of the way to show what was added.
    if (window.matchMedia("(max-width: 760px)").matches) onClose();
  }

  function drag(e: React.DragEvent, item: Item) {
    const elements = toElements(item.build());
    e.dataTransfer.setData(MIME_TYPES.excalidrawlib, serializeLibraryAsJSON([{ id: item.id, status: "unpublished", elements, created: Date.now() }]));
    e.dataTransfer.effectAllowed = "copy";
  }

  return (
    <aside className="shape-panel" aria-label="Shapes">
      <div className="shape-panel-head">
        <strong>Shapes</strong>
        <button type="button" className="icon-btn" onClick={onClose} title="Hide shapes" aria-label="Hide shapes">
          <X size={16} />
        </button>
      </div>
      <label className="shape-search">
        <Search size={14} />
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search shapes" aria-label="Search shapes" />
      </label>
      <div className="shape-groups">
        {groups.map((g) => {
          const open = query.trim() !== "" || !collapsed.has(g.name);
          return (
            <section key={g.name} className="shape-group">
              <button type="button" className="shape-group-title" onClick={() => toggle(g.name)} aria-expanded={open}>
                <ChevronDown size={14} className={open ? "" : "rotated"} /> {g.name}
              </button>
              {open && (
                <div className={g.name === "Starter boards" ? "shape-grid wide" : "shape-grid"}>
                  {g.items.map((item) => {
                    const src = thumbs.get(`${dark ? "dark" : "light"}:${item.id}`);
                    return (
                      <button
                        key={item.id}
                        type="button"
                        className="shape-tile"
                        draggable
                        onDragStart={(e) => drag(e, item)}
                        onClick={() => add(item)}
                        title={`${item.name}: click to add, or drag onto the board`}
                      >
                        <span className="shape-thumb">{src ? <img src={src} alt="" draggable={false} /> : null}</span>
                        <span className="shape-name">{item.name}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </section>
          );
        })}
        {!groups.length && <p className="muted small shape-empty">No shapes match “{query}”.</p>}
      </div>
    </aside>
  );
}
