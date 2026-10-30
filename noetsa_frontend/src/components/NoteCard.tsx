import { Link } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { FileText, Folder as FolderIcon, MoreHorizontal, Pin, RotateCcw, Shapes, Trash2 } from "lucide-react";
import { api, ApiError } from "../api";
import { noteTitle, refreshLists, timeAgo, useFolders } from "../notes";
import type { NoteSummary } from "../types";
import { Dropdown } from "./Dropdown";
import { NoteMenuItems } from "./NoteChrome";
import { notify } from "./Toaster";

/** A note or board in the Home and library grids (or one row in list view). */
export function NoteCard({ note, view = "grid", trash = false }: { note: NoteSummary; view?: "grid" | "list"; trash?: boolean }) {
  const folders = useFolders();
  const folder = folders.data?.find((f) => f.id === note.folder);
  const board = note.kind === "board";
  const Icon = board ? Shapes : FileText;

  return (
    <div className={`note-card note-card-${view} ${board ? "is-board" : "is-doc"}`}>
      <Link to={`/n/${note.id}`} className="note-card-link">
        {view === "grid" && (
          <div className="note-card-thumb" aria-hidden="true">
            {board ? (
              <div className="thumb-board">
                <Shapes size={26} />
                {note.preview && <span>{note.preview}</span>}
              </div>
            ) : (
              <div className="thumb-doc">
                <b>{noteTitle(note)}</b>
                <span>{note.preview || "Empty page"}</span>
              </div>
            )}
          </div>
        )}
        <div className="note-card-body">
          <div className="note-card-title">
            <Icon size={15} className="note-card-icon" />
            <span className="ellipsis">{noteTitle(note)}</span>
            {note.pinned && !trash && <Pin size={12} className="note-card-pin" aria-label="Pinned" />}
          </div>
          {view === "list" && note.preview && <div className="note-card-preview ellipsis">{note.preview}</div>}
          <div className="note-card-meta">
            {folder && (
              <span className="note-card-folder"><FolderIcon size={12} /> {folder.name}</span>
            )}
            <span>{timeAgo(trash && note.deleted_at ? note.deleted_at : note.updated_at)}</span>
          </div>
        </div>
      </Link>
      <div className="note-card-menu">{trash ? <TrashMenu note={note} /> : <CardMenu note={note} />}</div>
    </div>
  );
}

function CardMenu({ note }: { note: NoteSummary }) {
  return (
    <Dropdown label="Actions" button={<MoreHorizontal size={16} />} caret={false} align="right" className="icon-btn card-menu-btn">
      {(close) => <NoteMenuItems note={note} close={close} />}
    </Dropdown>
  );
}

function TrashMenu({ note }: { note: NoteSummary }) {
  const queryClient = useQueryClient();

  async function restore() {
    try {
      await api(`/notes/${note.id}/restore/`, { method: "POST" });
      refreshLists(queryClient);
      notify(`Restored “${noteTitle(note)}”`);
    } catch (e) {
      notify((e as ApiError).message);
    }
  }

  async function deleteForever() {
    await api(`/notes/${note.id}/`, { method: "DELETE" });
    queryClient.removeQueries({ queryKey: ["note", note.id] });
    refreshLists(queryClient);
    notify(`Deleted “${noteTitle(note)}” forever`);
  }

  return (
    <Dropdown label="Actions" button={<MoreHorizontal size={16} />} caret={false} align="right" className="icon-btn card-menu-btn">
      {(close) => (
        <div className="menu">
          <button type="button" onClick={() => { close(); void restore(); }}>
            <RotateCcw size={16} /> Restore
          </button>
          <button type="button" className="danger" onClick={() => { close(); void deleteForever(); }}>
            <Trash2 size={16} /> Delete forever
          </button>
        </div>
      )}
    </Dropdown>
  );
}
