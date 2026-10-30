import { useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  Briefcase, Building2, Check, ChevronRight, CloudOff, FileStack, Folder as FolderIcon, LoaderCircle, MoreHorizontal, Pin, PinOff,
  RotateCcw, Target, Trash2, TriangleAlert,
} from "lucide-react";
import { api, ApiError } from "../api";
import type { SaveStatus } from "../autosave";
import { noteTitle, refreshLists, useFolders, useUpdateNoteMeta } from "../notes";
import { Dropdown } from "./Dropdown";
import { notify } from "./Toaster";
import type { Note, NoteLink, NoteSummary } from "../types";

/** Pin, move to a folder and move to trash; used by the editor's ⋯ menu and the note cards. */
export function NoteMenuItems({ note, close, onTrashed }: { note: NoteSummary; close: () => void; onTrashed?: () => void }) {
  const queryClient = useQueryClient();
  const folders = useFolders();
  const update = useUpdateNoteMeta();

  async function moveToTrash() {
    await api(`/notes/${note.id}/`, { method: "DELETE" });
    refreshLists(queryClient);
    notify(`Moved “${noteTitle(note)}” to trash`);
    onTrashed?.();
  }

  return (
    <div className="menu">
      <button type="button" onClick={() => { update.mutate({ id: note.id, pinned: !note.pinned }); close(); }}>
        {note.pinned ? <PinOff size={16} /> : <Pin size={16} />} {note.pinned ? "Unpin" : "Pin to sidebar"}
      </button>
      <div className="menu-label">Move to folder</div>
      <button type="button" className={note.folder ? "" : "active"} onClick={() => { update.mutate({ id: note.id, folder: null }); close(); }}>
        <FileStack size={16} /> No folder
      </button>
      {folders.data?.map((f) => (
        <button key={f.id} type="button" className={note.folder === f.id ? "active" : ""} onClick={() => { update.mutate({ id: note.id, folder: f.id }); close(); }}>
          <FolderIcon size={16} /> <span className="ellipsis">{f.name}</span>
        </button>
      ))}
      <div className="menu-sep" />
      <button type="button" className="danger" onClick={() => { close(); void moveToTrash(); }}>
        <Trash2 size={16} /> Move to trash
      </button>
    </div>
  );
}

/** The editor's ⋯ menu. */
export function NoteMenu({ note }: { note: Note }) {
  const navigate = useNavigate();
  return (
    <Dropdown label="More actions" button={<MoreHorizontal size={18} />} caret={false} align="right">
      {(close) => <NoteMenuItems note={note} close={close} onTrashed={() => navigate("/")} />}
    </Dropdown>
  );
}

/** "Notes ›" or "Folder ›" in front of the title, so you can see and jump to where a note lives.
 * The last crumb (the live title, or the board's title input) comes from the editor. */
export function Breadcrumb({ note, children }: { note: Note; children: ReactNode }) {
  const folders = useFolders();
  const folder = folders.data?.find((f) => f.id === note.folder);
  const section = note.kind === "board" ? { to: "/boards", label: "Boards" } : { to: "/docs", label: "Notes" };
  return (
    <nav className="breadcrumb" aria-label="Location">
      {folder ? (
        <Link to={`/folders/${folder.id}`}><FolderIcon size={14} /> {folder.name}</Link>
      ) : (
        <Link to={section.to}>{section.label}</Link>
      )}
      <ChevronRight size={14} className="breadcrumb-sep" />
      {children}
      {note.pinned && <Pin size={13} className="breadcrumb-pin" aria-label="Pinned" />}
      {note.link && <LinkChip link={note.link} />}
    </nav>
  );
}

const LINK_KINDS = {
  project: { icon: Briefcase, label: "Project" },
  client: { icon: Building2, label: "Client" },
  lead: { icon: Target, label: "Lead" },
};

/** The BMS project, client or lead this note belongs to; opens its page in the BMS. */
export function LinkChip({ link }: { link: NoteLink }) {
  const { icon: Icon, label } = LINK_KINDS[link.kind];
  return (
    <a href={link.url} className="link-chip" title={`${label}: ${link.label} (opens in Ralfiz BMS)`}>
      <Icon size={13} /> <span className="link-chip-kind">{label}</span> <span className="ellipsis">{link.label}</span>
    </a>
  );
}

export function ConflictBanner({ onKeepMine, onLoadTheirs }: { onKeepMine: () => void; onLoadTheirs: () => void }) {
  return (
    <div className="alert alert-warn conflict">
      <TriangleAlert size={16} />
      <span>This note was changed on another device or tab.</span>
      <button className="btn btn-sm" onClick={onKeepMine}>Keep my version</button>
      <button className="btn btn-sm" onClick={onLoadTheirs}>Load the other version</button>
    </div>
  );
}

export function SaveIndicator({ status }: { status: SaveStatus }) {
  const map = {
    saved: { icon: <Check size={14} />, text: "Saved" },
    unsaved: { icon: null, text: "Editing…" },
    saving: { icon: <LoaderCircle size={14} className="spin" />, text: "Saving…" },
    offline: { icon: <CloudOff size={14} />, text: "Offline — will retry" },
    conflict: { icon: <TriangleAlert size={14} />, text: "Not saved" },
  }[status];
  return (
    <span className={`save-status save-${status}`} aria-live="polite">
      {map.icon} {map.text}
    </span>
  );
}

export function TrashActions({ note }: { note: Note }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function restore() {
    try {
      const restored = await api<Note>(`/notes/${note.id}/restore/`, { method: "POST" });
      queryClient.setQueryData(["note", note.id], restored);
      refreshLists(queryClient);
    } catch (e) {
      setError((e as ApiError).message);
    }
  }

  async function deleteForever() {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    await api(`/notes/${note.id}/`, { method: "DELETE" });
    queryClient.removeQueries({ queryKey: ["note", note.id] });
    refreshLists(queryClient);
    navigate("/");
  }

  return (
    <div className="toolbar trash-actions">
      <span className="muted">In trash</span>
      <button className="btn btn-sm" onClick={restore}>
        <RotateCcw size={14} /> Restore
      </button>
      <button className="btn btn-sm btn-danger" onClick={deleteForever}>
        <Trash2 size={14} /> {confirming ? "Click again to delete forever" : "Delete forever"}
      </button>
      {error && <span className="field-error">{error}</span>}
    </div>
  );
}
