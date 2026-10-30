import { useCallback, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { ChevronDown } from "lucide-react";

type Props = {
  label: string;
  /** Button content; defaults to the label text. */
  button?: ReactNode;
  caret?: boolean;
  active?: boolean;
  children: (close: () => void) => ReactNode;
  /** Lets other code open the dropdown (e.g. the `/` menu opening the emoji picker). */
  openSignal?: number;
  /** Line the panel up with the button's right edge (for buttons near the right of the screen). */
  align?: "left" | "right";
  /** Replaces the default toolbar-button look. */
  className?: string;
};

/** A toolbar button with a floating panel. The panel is portalled to <body> so a
 * horizontally scrolling toolbar can't clip it. */
export function Dropdown({ label, button, caret = true, active, children, openSignal, align = "left", className = "icon-btn dropdown-btn" }: Props) {
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ top: 0, left: 0 });
  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (openSignal) setOpen(true);
  }, [openSignal]);

  useLayoutEffect(() => {
    const panel = panelRef.current;
    if (!open || !buttonRef.current || !panel) return;
    const place = () => {
      const rect = buttonRef.current!.getBoundingClientRect();
      const left = align === "right" ? rect.right - panel.offsetWidth : rect.left;
      setPos({ top: rect.bottom + 6, left: Math.max(8, Math.min(left, window.innerWidth - panel.offsetWidth - 8)) });
    };
    place();
    // Content such as the emoji picker loads after opening and changes the panel's width.
    const observer = new ResizeObserver(place);
    observer.observe(panel);
    return () => observer.disconnect();
  }, [open, align]);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      const target = e.target as Node;
      if (!panelRef.current?.contains(target) && !buttonRef.current?.contains(target)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    const onResize = () => setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    window.addEventListener("resize", onResize);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("resize", onResize);
    };
  }, [open]);

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        className={`${className} ${active || open ? "active" : ""}`}
        title={label}
        aria-label={label}
        aria-haspopup="true"
        aria-expanded={open}
        onMouseDown={(e) => e.preventDefault()}
        onClick={() => setOpen((o) => !o)}
      >
        {button ?? label}
        {caret && <ChevronDown size={12} className="caret" />}
      </button>
      {open &&
        createPortal(
          <div
            ref={panelRef}
            className="dropdown-panel"
            style={{ top: pos.top, left: pos.left }}
            role="dialog"
            aria-label={label}
            // Keep focus (and the text selection) in the editor while picking, except in text fields.
            onMouseDown={(e) => {
              if (!(e.target as HTMLElement).closest("input, textarea, select, em-emoji-picker")) e.preventDefault();
            }}
          >
            {children(close)}
          </div>,
          document.body,
        )}
    </>
  );
}
