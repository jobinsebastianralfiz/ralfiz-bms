import { useEffect, useRef, useState, type FormEvent } from "react";
import { Ban } from "lucide-react";

export const TEXT_COLORS = [
  "#000000", "#434343", "#666666", "#999999", "#cccccc", "#ffffff",
  "#c0392b", "#e67e22", "#f1c40f", "#27ae60", "#16a085", "#2980b9",
  "#4f46e5", "#8e44ad", "#d81b60", "#795548", "#1e3a8a", "#065f46",
];

export const HIGHLIGHT_COLORS = [
  "#fff59d", "#ffe0b2", "#ffcdd2", "#f8bbd0", "#e1bee7", "#d1c4e9",
  "#c5cae9", "#bbdefb", "#b2ebf2", "#c8e6c9", "#dcedc8", "#eeeeee",
];

export function ColorGrid({
  colors,
  current,
  onPick,
  clearLabel,
}: {
  colors: string[];
  current?: string | null;
  onPick: (color: string | null) => void;
  clearLabel: string;
}) {
  return (
    <div className="color-picker">
      <button type="button" className="color-clear" onClick={() => onPick(null)}>
        <Ban size={14} /> {clearLabel}
      </button>
      <div className="color-grid">
        {colors.map((c) => (
          <button
            key={c}
            type="button"
            className={`swatch ${current?.toLowerCase() === c ? "selected" : ""}`}
            style={{ background: c }}
            title={c}
            aria-label={`Colour ${c}`}
            onClick={() => onPick(c)}
          />
        ))}
      </div>
      <label className="color-custom">
        Custom
        <input type="color" value={current && current.startsWith("#") ? current : "#000000"} onChange={(e) => onPick(e.target.value)} />
      </label>
    </div>
  );
}

const GRID = 8;

/** Hover to choose the table size, like Word's Insert Table grid. */
export function TableGridPicker({ onPick }: { onPick: (rows: number, cols: number) => void }) {
  const [hover, setHover] = useState({ rows: 0, cols: 0 });
  return (
    <div className="table-grid-picker">
      <div className="table-grid" onMouseLeave={() => setHover({ rows: 0, cols: 0 })}>
        {Array.from({ length: GRID * GRID }, (_, i) => {
          const row = Math.floor(i / GRID) + 1;
          const col = (i % GRID) + 1;
          const on = row <= hover.rows && col <= hover.cols;
          return (
            <button
              key={i}
              type="button"
              className={on ? "on" : ""}
              aria-label={`${row} by ${col} table`}
              onMouseEnter={() => setHover({ rows: row, cols: col })}
              onFocus={() => setHover({ rows: row, cols: col })}
              onClick={() => onPick(row, col)}
            />
          );
        })}
      </div>
      <div className="muted small center">{hover.rows ? `${hover.rows} × ${hover.cols} table` : "Choose a size"}</div>
    </div>
  );
}

/** emoji-mart is loaded on first use to keep it out of the main bundle. */
export function EmojiPicker({ onPick }: { onPick: (emoji: string) => void }) {
  const host = useRef<HTMLDivElement>(null);
  const onPickRef = useRef(onPick);
  onPickRef.current = onPick;
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([import("emoji-mart"), import("@emoji-mart/data")])
      .then(([{ Picker }, data]) => {
        if (cancelled || !host.current) return;
        const picker = new Picker({
          data: data.default,
          theme: "auto",
          previewPosition: "none",
          skinTonePosition: "search",
          autoFocus: true,
          onEmojiSelect: (e: { native: string }) => onPickRef.current(e.native),
        });
        host.current.replaceChildren(picker as unknown as Node);
      })
      .catch(() => setFailed(true));
    return () => {
      cancelled = true;
    };
  }, []);

  if (failed) return <div className="muted small">Couldn't load emojis. Check your connection.</div>;
  return (
    <div ref={host} className="emoji-host">
      <div className="spinner" />
    </div>
  );
}

export function LinkForm({ initial, onApply, onRemove }: { initial: string; onApply: (url: string) => void; onRemove: () => void }) {
  const [url, setUrl] = useState(initial);
  function submit(e: FormEvent) {
    e.preventDefault();
    if (url.trim()) onApply(url.trim());
  }
  return (
    <form className="link-form" onSubmit={submit}>
      <input autoFocus type="text" inputMode="url" placeholder="Paste or type a link" value={url} onChange={(e) => setUrl(e.target.value)} />
      <button className="btn btn-primary btn-sm">Apply</button>
      {initial && (
        <button type="button" className="btn btn-sm" onClick={onRemove}>
          Remove
        </button>
      )}
    </form>
  );
}
