import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { DragHandle } from "@tiptap/extension-drag-handle-react";
import type { Editor } from "@tiptap/react";
import type { Node as PMNode } from "@tiptap/pm/model";
import {
  Copy, GripVertical, Heading1, Heading2, Heading3, Lightbulb, List, ListOrdered, ListTodo, Pilcrow, Plus, Quote, Trash2,
  type LucideIcon,
} from "lucide-react";

type Target = { node: PMNode; pos: number };

const TURN_INTO: { label: string; icon: LucideIcon; run: (e: Editor) => void }[] = [
  { label: "Text", icon: Pilcrow, run: (e) => e.chain().focus().setParagraph().run() },
  { label: "Heading 1", icon: Heading1, run: (e) => e.chain().focus().setHeading({ level: 1 }).run() },
  { label: "Heading 2", icon: Heading2, run: (e) => e.chain().focus().setHeading({ level: 2 }).run() },
  { label: "Heading 3", icon: Heading3, run: (e) => e.chain().focus().setHeading({ level: 3 }).run() },
  { label: "Bullet list", icon: List, run: (e) => e.chain().focus().toggleBulletList().run() },
  { label: "Numbered list", icon: ListOrdered, run: (e) => e.chain().focus().toggleOrderedList().run() },
  { label: "Checklist", icon: ListTodo, run: (e) => e.chain().focus().toggleTaskList().run() },
  { label: "Quote", icon: Quote, run: (e) => e.chain().focus().toggleBlockquote().run() },
  { label: "Callout", icon: Lightbulb, run: (e) => e.chain().focus().setCallout("info").run() },
];

/** Notion-style handle beside each block: "+" opens the block menu on a new line below,
 * the grip drags the block or, when clicked, offers turn into / duplicate / delete. */
export function BlockHandle({ editor }: { editor: Editor }) {
  const target = useRef<Target | null>(null);
  const [menu, setMenu] = useState<{ target: Target; top: number; left: number } | null>(null);

  /** The hovered block as it is in the document now (it may have changed since hovering). */
  function current(): Target | null {
    const t = target.current;
    const node = t && editor.state.doc.nodeAt(t.pos);
    return t && node && node.type === t.node.type ? { node, pos: t.pos } : null;
  }

  function addBelow() {
    const t = current();
    if (!t) return;
    if (t.node.type.name === "paragraph" && t.node.content.size === 0) {
      // Empty line: start the "/" menu right there.
      editor.chain().focus().insertContentAt(t.pos + 1, "/").run();
      return;
    }
    const at = t.pos + t.node.nodeSize;
    editor.chain().insertContentAt(at, { type: "paragraph", content: [{ type: "text", text: "/" }] }).setTextSelection(at + 2).focus().run();
  }

  function openMenu(e: React.MouseEvent) {
    const t = current();
    if (!t) return;
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    // Keep the handle in place while the menu is open (the React DragHandle has no lock command).
    editor.commands.setMeta("lockDragHandle", true);
    setMenu({ target: t, top: rect.bottom + 4, left: rect.left });
  }

  function closeMenu() {
    setMenu(null);
    editor.commands.setMeta("lockDragHandle", false);
  }

  return (
    <>
      <DragHandle
        editor={editor}
        className="block-handle"
        onNodeChange={({ node, pos }) => {
          // Moving onto the handle itself reports no node; keep the block it belongs to.
          if (node) target.current = { node, pos };
        }}
      >
        <button type="button" className="block-handle-btn" onClick={addBelow} title="Add a block below" aria-label="Add a block below">
          <Plus size={16} />
        </button>
        <button type="button" className="block-handle-btn grip" onClick={openMenu} title="Drag to move · click for options" aria-label="Block options">
          <GripVertical size={16} />
        </button>
      </DragHandle>
      {menu && <BlockMenu editor={editor} {...menu} onClose={closeMenu} />}
    </>
  );
}

function BlockMenu({ editor, target, top, left, onClose }: { editor: Editor; target: Target; top: number; left: number; onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const { node, pos } = target;
  const textBlock = node.isTextblock;

  useEffect(() => {
    const onDown = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && onClose();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  const run = (fn: () => void) => () => {
    fn();
    onClose();
  };

  return createPortal(
    <div ref={ref} className="dropdown-panel block-menu" style={{ top: Math.min(top, window.innerHeight - 420), left }} role="menu">
      <div className="menu">
        {textBlock && (
          <>
            <div className="menu-label">Turn into</div>
            {TURN_INTO.map((item) => (
              <button key={item.label} type="button" onClick={run(() => {
                editor.commands.setTextSelection(pos + 1);
                item.run(editor);
              })}>
                <item.icon size={16} /> {item.label}
              </button>
            ))}
            <div className="menu-sep" />
          </>
        )}
        <button type="button" onClick={run(() => editor.chain().focus().insertContentAt(pos + node.nodeSize, node.toJSON()).run())}>
          <Copy size={16} /> Duplicate
        </button>
        <button type="button" className="danger" onClick={run(() => editor.chain().focus().deleteRange({ from: pos, to: pos + node.nodeSize }).run())}>
          <Trash2 size={16} /> Delete
        </button>
      </div>
    </div>,
    document.body,
  );
}
