import { useRef, useState, type FormEvent } from "react";
import { NavLink, useMatch, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft, Check, ChevronDown, FileText, Folder as FolderIcon, FolderPlus, Home, LayoutTemplate, LogOut, Monitor, Moon,
  MoreHorizontal, Pencil, Plus, Search, Shapes, Sun, Trash2,
} from "lucide-react";
import { api, ApiError } from "../api";
import { useAuth } from "../auth";
import { noteTitle, refreshLists, useCreateNote, useFolders, useNoteList } from "../notes";
import { getTheme, setTheme, type ThemeChoice } from "../theme";
import type { Folder } from "../types";
import { Dropdown } from "./Dropdown";
import { notify } from "./Toaster";

export function Sidebar({ onSearch }: { onSearch: () => void }) {
  const create = useCreateNote();
  // New notes land in the folder you're looking at.
  const folderId = useMatch("/folders/:id")?.params.id ?? null;
  const pinned = useNoteList({ pinned: true, limit: 10 });
  const pinnedNotes = pinned.data?.pages[0]?.results ?? [];
  const isMac = /Mac|iPhone|iPad/.test(navigator.platform);

  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <WorkspaceMenu />
        <button className="sidebar-search" onClick={onSearch}>
          <Search size={15} /> <span>Search</span>
          <kbd>{isMac ? "⌘" : "Ctrl"} K</kbd>
        </button>
        <Dropdown
          label="New"
          className="btn btn-primary sidebar-new"
          caret={false}
          button={<><Plus size={16} /> New <ChevronDown size={14} className="sidebar-new-caret" /></>}
        >
          {(close) => (
            <div className="menu new-menu">
              <button type="button" onClick={() => { create.mutate({ kind: "doc", folder: folderId }); close(); }}>
                <span className="menu-icon"><FileText size={16} /></span>
                <span><strong>Note</strong><small>Rich text, tables, images</small></span>
              </button>
              <button type="button" onClick={() => { create.mutate({ kind: "board", folder: folderId }); close(); }}>
                <span className="menu-icon"><Shapes size={16} /></span>
                <span><strong>Board</strong><small>Whiteboard, flowcharts, diagrams</small></span>
              </button>
              <NavLink to="/templates" onClick={close} className="menu-link">
                <span className="menu-icon"><LayoutTemplate size={16} /></span>
                <span><strong>From a template</strong><small>Resume, invoice, planner…</small></span>
              </NavLink>
            </div>
          )}
        </Dropdown>
      </div>

      <nav className="sidebar-scroll">
        <div className="nav-group">
          <NavLink to="/" end className="nav-item"><Home size={16} /> Home</NavLink>
          <NavLink to="/docs" end className="nav-item"><FileText size={16} /> Notes</NavLink>
          <NavLink to="/boards" className="nav-item"><Shapes size={16} /> Boards</NavLink>
          <NavLink to="/templates" className="nav-item"><LayoutTemplate size={16} /> Templates</NavLink>
        </div>

        {pinnedNotes.length > 0 && (
          <div className="nav-group">
            <div className="nav-heading">Pinned</div>
            {pinnedNotes.map((n) => (
              <NavLink key={n.id} to={`/n/${n.id}`} className="nav-item">
                {n.kind === "board" ? <Shapes size={16} /> : <FileText size={16} />}
                <span className="ellipsis">{noteTitle(n)}</span>
              </NavLink>
            ))}
          </div>
        )}

        <FolderSection />

        <div className="nav-group">
          <NavLink to="/trash" className="nav-item"><Trash2 size={16} /> Trash</NavLink>
        </div>
      </nav>

      <AccountRow />
    </aside>
  );
}

function WorkspaceMenu() {
  const { me } = useAuth();
  return (
    <div className="workspace-row">
      <div className="logo-mark" aria-hidden="true">N</div>
      <div className="workspace-text">
        <strong>Notes</strong>
        <span className="plan-pill">Private</span>
      </div>
      {me && (
        <a href={me.home_url} className="icon-btn workspace-home" title={`Back to ${me.home_label}`} aria-label={`Back to ${me.home_label}`}>
          <ArrowLeft size={16} />
        </a>
      )}
    </div>
  );
}

function FolderSection() {
  const queryClient = useQueryClient();
  const folders = useFolders();
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createFolder = useMutation({
    mutationFn: (name: string) => api<Folder>("/folders/", { method: "POST", body: { name } }),
    onSuccess: () => {
      setAdding(false);
      setError(null);
      void queryClient.invalidateQueries({ queryKey: ["folders"] });
    },
    onError: (e) => {
      setAdding(false);
      setError((e as ApiError).fields.name?.[0] ?? (e as ApiError).message);
    },
  });

  return (
    <div className="nav-group">
      <div className="nav-heading">
        Folders
        <button className="nav-heading-btn" onClick={() => setAdding(true)} title="New folder" aria-label="New folder">
          <FolderPlus size={14} />
        </button>
      </div>
      {folders.data?.map((f) => <FolderItem key={f.id} folder={f} />)}
      {adding && (
        <NameInput
          placeholder="Folder name"
          onSubmit={(name) => createFolder.mutate(name)}
          onCancel={() => { setAdding(false); setError(null); }}
        />
      )}
      {error && <p className="nav-error">{error}</p>}
      {!adding && folders.data?.length === 0 && (
        <button className="nav-item nav-item-muted" onClick={() => setAdding(true)}>
          <Plus size={16} /> Add a folder
        </button>
      )}
    </div>
  );
}

function FolderItem({ folder }: { folder: Folder }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const active = useMatch(`/folders/${folder.id}`);
  const [renaming, setRenaming] = useState(false);

  async function rename(name: string) {
    await api(`/folders/${folder.id}/`, { method: "PATCH", body: { name } });
    setRenaming(false);
    void queryClient.invalidateQueries({ queryKey: ["folders"] });
  }

  async function remove() {
    await api(`/folders/${folder.id}/`, { method: "DELETE" });
    void queryClient.invalidateQueries({ queryKey: ["folders"] });
    refreshLists(queryClient);
    notify(`Deleted folder “${folder.name}”. Its notes are still in Notes.`);
    if (active) navigate("/docs");
  }

  if (renaming) {
    return <NameInput initial={folder.name} placeholder="Folder name" onSubmit={rename} onCancel={() => setRenaming(false)} />;
  }
  return (
    <div className="nav-row">
      <NavLink to={`/folders/${folder.id}`} className="nav-item">
        <FolderIcon size={16} /> <span className="ellipsis">{folder.name}</span>
      </NavLink>
      <Dropdown label={`${folder.name} options`} button={<MoreHorizontal size={15} />} caret={false} className="icon-btn nav-row-btn">
        {(close) => (
          <div className="menu">
            <button type="button" onClick={() => { setRenaming(true); close(); }}>
              <Pencil size={16} /> Rename
            </button>
            <button type="button" className="danger" onClick={() => { close(); void remove(); }}>
              <Trash2 size={16} /> Delete folder
            </button>
          </div>
        )}
      </Dropdown>
    </div>
  );
}

function NameInput({ initial = "", placeholder, onSubmit, onCancel }: {
  initial?: string;
  placeholder: string;
  onSubmit: (name: string) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(initial);
  // Enter followed by the blur that comes with unmounting must not submit twice.
  const done = useRef(false);
  function finish(submit: boolean) {
    if (done.current) return;
    done.current = true;
    const value = name.trim();
    if (submit && value && value !== initial) onSubmit(value);
    else onCancel();
  }
  function submit(e: FormEvent) {
    e.preventDefault();
    finish(true);
  }
  return (
    <form className="nav-input" onSubmit={submit}>
      <FolderIcon size={16} />
      <input
        autoFocus
        value={name}
        maxLength={120}
        placeholder={placeholder}
        onChange={(e) => setName(e.target.value)}
        onKeyDown={(e) => e.key === "Escape" && finish(false)}
        onBlur={() => finish(true)}
      />
    </form>
  );
}

const THEMES: { key: ThemeChoice; label: string; icon: typeof Sun }[] = [
  { key: "system", label: "System", icon: Monitor },
  { key: "light", label: "Light", icon: Sun },
  { key: "dark", label: "Dark", icon: Moon },
];

function AccountRow() {
  const { me } = useAuth();
  const [theme, setThemeState] = useState(getTheme);
  const name = me?.user.full_name || me?.user.username || "";

  return (
    <div className="sidebar-foot">
      <Dropdown
        label="Account"
        className="account-btn"
        caret={false}
        button={
          <>
            <span className="avatar">{(name[0] ?? "?").toUpperCase()}</span>
            <span className="account-name ellipsis">{name}</span>
            <ChevronDown size={14} />
          </>
        }
      >
        {(close) => (
          <div className="menu account-menu">
            <div className="menu-label ellipsis">{me?.user.email || me?.user.username}</div>
            <a href={me?.home_url ?? "/"} className="menu-link" onClick={close}>
              <ArrowLeft size={16} /> Back to {me?.home_label ?? "Ralfiz BMS"}
            </a>
            <div className="menu-label">Theme</div>
            <div className="theme-switch" role="radiogroup" aria-label="Theme">
              {THEMES.map((t) => (
                <button
                  key={t.key}
                  type="button"
                  role="radio"
                  aria-checked={theme === t.key}
                  className={theme === t.key ? "active" : ""}
                  onClick={() => { setTheme(t.key); setThemeState(t.key); }}
                >
                  <t.icon size={14} /> {t.label} {theme === t.key && <Check size={12} />}
                </button>
              ))}
            </div>
            <div className="menu-sep" />
            <a href={me?.logout_url ?? "/logout/"} className="menu-link" onClick={close}>
              <LogOut size={16} /> Sign out
            </a>
          </div>
        )}
      </Dropdown>
    </div>
  );
}
