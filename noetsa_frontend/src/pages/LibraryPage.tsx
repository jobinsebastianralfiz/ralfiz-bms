import { useState } from "react";
import { useParams } from "react-router-dom";
import { FileText, Folder as FolderIcon, LayoutGrid, List, Plus, Search, Shapes, Trash2 } from "lucide-react";
import { NoteCard } from "../components/NoteCard";
import { useDebounced } from "../hooks";
import { useCreateNote, useFolders, useNoteList, type ListQuery } from "../notes";
import type { NoteKind } from "../types";

type Section = "notes" | "boards" | "folder" | "trash";

const VIEW_KEY = "noetsa:library-view";

function readView(): "grid" | "list" {
  try {
    return localStorage.getItem(VIEW_KEY) === "list" ? "list" : "grid";
  } catch {
    return "grid";
  }
}

/** Notes, Boards, a folder, or Trash: a searchable grid (or list) of cards. */
export function LibraryPage({ section }: { section: Section }) {
  const { id } = useParams();
  const folders = useFolders();
  const folder = section === "folder" ? folders.data?.find((f) => f.id === id) : undefined;
  const create = useCreateNote();
  const [view, setView] = useState(readView);
  const [text, setText] = useState("");
  const q = useDebounced(text.trim(), 250);

  const query: ListQuery = { q: q || undefined };
  if (section === "notes") query.kind = "doc";
  if (section === "boards") query.kind = "board";
  if (section === "folder") query.folder = id;
  if (section === "trash") query.trash = true;
  const list = useNoteList(query);
  const notes = list.data?.pages.flatMap((p) => p.results) ?? [];
  const total = list.data?.pages[0]?.count ?? 0;

  const head = {
    notes: { icon: <FileText size={22} />, title: "Notes", empty: "No notes yet. Write your first one." },
    boards: { icon: <Shapes size={22} />, title: "Boards", empty: "No boards yet. Sketch a flowchart, mind map or whiteboard." },
    folder: { icon: <FolderIcon size={22} />, title: folder?.name ?? "Folder", empty: "This folder is empty. Move notes here from their ⋯ menu, or create one." },
    trash: { icon: <Trash2 size={22} />, title: "Trash", empty: "Trash is empty." },
  }[section];

  function changeView(next: "grid" | "list") {
    setView(next);
    try {
      localStorage.setItem(VIEW_KEY, next);
    } catch {
      // Not remembered in private mode.
    }
  }

  const newKinds: NoteKind[] = section === "boards" ? ["board"] : section === "notes" ? ["doc"] : section === "folder" ? ["doc", "board"] : [];

  return (
    <div className="page library-page">
      <header className="library-head">
        <div className="library-title">
          <span className="library-icon">{head.icon}</span>
          <div>
            <h1>{head.title}</h1>
            {!list.isLoading && <p className="muted small">{total} {total === 1 ? "item" : "items"}{section === "trash" && total > 0 ? " · open the ⋯ menu to restore" : ""}</p>}
          </div>
        </div>
        <div className="library-actions">
          <label className="filter-box">
            <Search size={15} />
            <input placeholder="Filter" value={text} onChange={(e) => setText(e.target.value)} />
          </label>
          <div className="segmented" role="group" aria-label="View">
            <button className={view === "grid" ? "active" : ""} onClick={() => changeView("grid")} aria-label="Grid view" title="Grid view"><LayoutGrid size={15} /></button>
            <button className={view === "list" ? "active" : ""} onClick={() => changeView("list")} aria-label="List view" title="List view"><List size={15} /></button>
          </div>
          {newKinds.map((kind) => (
            <button key={kind} className="btn btn-primary btn-sm" onClick={() => create.mutate({ kind, folder: section === "folder" ? id : null })} disabled={create.isPending}>
              <Plus size={15} /> {kind === "board" ? "New board" : "New note"}
            </button>
          ))}
        </div>
      </header>

      {list.isLoading && <div className="spinner" />}
      {list.isError && <div className="alert alert-error">{(list.error as Error).message}</div>}
      {!list.isLoading && notes.length === 0 && (
        <div className="empty-panel">
          {head.icon}
          <p>{q ? `Nothing matches “${q}”.` : head.empty}</p>
        </div>
      )}

      <div className={view === "grid" ? "card-grid" : "card-list"}>
        {notes.map((n) => <NoteCard key={n.id} note={n} view={view} trash={section === "trash"} />)}
      </div>
      {list.hasNextPage && (
        <button className="btn load-more" onClick={() => list.fetchNextPage()} disabled={list.isFetchingNextPage}>
          {list.isFetchingNextPage ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
