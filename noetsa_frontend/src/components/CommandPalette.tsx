import { useEffect, useRef, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { CornerDownLeft, FileText, Home, LayoutTemplate, LoaderCircle, Plus, Search, Shapes, Trash2 } from "lucide-react";
import { noteTitle, timeAgo, useCreateNote, useNoteList } from "../notes";
import { useDebounced } from "../hooks";

type Item = { key: string; icon: ReactNode; label: string; hint?: string; run: () => void };

/** Ctrl/Cmd+K: jump to any note or board, or run a quick action. */
export function CommandPalette({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate();
  const create = useCreateNote();
  const [text, setText] = useState("");
  const q = useDebounced(text.trim(), 150);
  // Recent items when the box is empty, search results once something is typed.
  const results = useNoteList({ q: q || undefined, limit: 8 });
  const notes = results.data?.pages[0]?.results ?? [];
  const [index, setIndex] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

  const go = (path: string) => () => {
    navigate(path);
    onClose();
  };

  const actions: Item[] = [
    { key: "new-note", icon: <Plus size={16} />, label: "New note", run: () => { create.mutate({ kind: "doc" }); onClose(); } },
    { key: "new-board", icon: <Shapes size={16} />, label: "New board", run: () => { create.mutate({ kind: "board" }); onClose(); } },
    { key: "home", icon: <Home size={16} />, label: "Go to Home", run: go("/") },
    { key: "templates", icon: <LayoutTemplate size={16} />, label: "Browse templates", run: go("/templates") },
    { key: "trash", icon: <Trash2 size={16} />, label: "Open trash", run: go("/trash") },
  ];

  const needle = text.trim().toLowerCase();
  const matchingActions = needle ? actions.filter((a) => a.label.toLowerCase().includes(needle)) : actions;
  const noteItems: Item[] = notes.map((n) => ({
    key: n.id,
    icon: n.kind === "board" ? <Shapes size={16} /> : <FileText size={16} />,
    label: noteTitle(n),
    hint: timeAgo(n.updated_at),
    run: go(`/n/${n.id}`),
  }));
  // Typing usually means "find my note", so results come first; empty box shows actions first.
  const sections: { title: string; items: Item[] }[] = needle
    ? [{ title: "Notes and boards", items: noteItems }, { title: "Actions", items: matchingActions }]
    : [{ title: "Actions", items: matchingActions }, { title: "Recent", items: noteItems }];
  const flat = sections.flatMap((s) => s.items);

  useEffect(() => setIndex(0), [q]);
  useEffect(() => {
    listRef.current?.querySelector(`[data-index="${index}"]`)?.scrollIntoView({ block: "nearest" });
  }, [index]);

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setIndex((i) => Math.min(i + 1, flat.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      flat[index]?.run();
    } else if (e.key === "Escape") {
      onClose();
    }
  }

  let n = -1;
  return (
    <div className="palette-backdrop" onMouseDown={onClose}>
      <div className="palette" role="dialog" aria-modal="true" aria-label="Search" onMouseDown={(e) => e.stopPropagation()}>
        <label className="palette-input">
          {results.isFetching ? <LoaderCircle size={18} className="spin" /> : <Search size={18} />}
          <input
            autoFocus
            placeholder="Search notes and boards, or type a command…"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            role="combobox"
            aria-expanded="true"
            aria-controls="palette-list"
            aria-activedescendant={flat[index] ? `palette-${flat[index].key}` : undefined}
          />
          <kbd>Esc</kbd>
        </label>
        <div className="palette-list" id="palette-list" role="listbox" ref={listRef}>
          {sections.map((section) =>
            section.items.length ? (
              <div key={section.title} className="palette-section">
                <div className="palette-heading">{section.title}</div>
                {section.items.map((item) => {
                  n += 1;
                  const i = n;
                  return (
                    <button
                      key={item.key}
                      id={`palette-${item.key}`}
                      data-index={i}
                      role="option"
                      aria-selected={i === index}
                      className={i === index ? "selected" : ""}
                      onMouseMove={() => setIndex(i)}
                      onClick={item.run}
                    >
                      <span className="palette-icon">{item.icon}</span>
                      <span className="ellipsis">{item.label}</span>
                      {item.hint && <small>{item.hint}</small>}
                      {i === index && <CornerDownLeft size={14} className="palette-enter" />}
                    </button>
                  );
                })}
              </div>
            ) : null,
          )}
          {needle && !results.isFetching && flat.length === 0 && <div className="palette-empty">Nothing matches “{text.trim()}”.</div>}
        </div>
      </div>
    </div>
  );
}
