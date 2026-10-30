import { lazy, Suspense, useEffect, useState } from "react";
import { mergeAttributes, Node } from "@tiptap/core";
import { NodeViewWrapper, ReactNodeViewRenderer, type ReactNodeViewProps } from "@tiptap/react";
import { LoaderCircle, PenLine } from "lucide-react";
import type { DrawingScene } from "./DrawingDialog";

// Excalidraw is large; it loads only when a drawing is opened.
const DrawingDialog = lazy(() => import("./DrawingDialog").then((m) => ({ default: m.DrawingDialog })));

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    drawing: {
      /** Insert an empty drawing and open the drawing editor. */
      insertDrawing: () => ReturnType;
    };
  }
}

// Set by insertDrawing so the freshly inserted block opens its editor straight away
// (an empty drawing loaded from a saved note must not pop open by itself).
let openNextDrawing = false;

function DrawingView({ node, updateAttributes, deleteNode, editor, selected }: ReactNodeViewProps) {
  const src = node.attrs.src as string | null;
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (openNextDrawing) {
      openNextDrawing = false;
      setEditing(true);
    }
  }, []);

  const open = () => editor.isEditable && setEditing(true);

  return (
    <NodeViewWrapper className={`drawing-block ${selected ? "is-selected" : ""}`} data-drag-handle="">
      {src ? (
        <figure className="drawing-figure" onDoubleClick={open}>
          <img src={src} alt="Drawing" style={node.attrs.width ? { width: `${node.attrs.width}px` } : undefined} draggable={false} />
          {editor.isEditable && (
            <button type="button" className="btn btn-sm drawing-edit" onClick={open}>
              <PenLine size={14} /> Edit drawing
            </button>
          )}
        </figure>
      ) : (
        <button type="button" className="drawing-empty" onClick={open} disabled={!editor.isEditable}>
          <PenLine size={20} />
          <span><strong>Drawing</strong> Click to sketch, draw shapes or a quick diagram</span>
        </button>
      )}
      {editing && (
        <Suspense fallback={<div className="drawing-loading"><LoaderCircle className="spin" size={22} /></div>}>
          <DrawingDialog
            scene={node.attrs.scene as DrawingScene | null}
            onCancel={() => {
              setEditing(false);
              // A drawing that was never saved leaves nothing behind.
              if (!src && !node.attrs.scene) deleteNode();
            }}
            onSave={(saved) => {
              updateAttributes(saved);
              setEditing(false);
            }}
          />
        </Suspense>
      )}
    </NodeViewWrapper>
  );
}

/** A sketch inside a note. The Excalidraw scene is kept for editing, and a PNG of it in the
 * asset store is what the note, the list preview and the PDF show. */
export const Drawing = Node.create({
  name: "drawing",
  group: "block",
  atom: true,
  draggable: true,

  addAttributes() {
    return {
      src: { default: null },
      scene: { default: null, rendered: false },
      width: { default: null },
    };
  },

  parseHTML() {
    return [{ tag: "figure[data-drawing]" }];
  },

  renderHTML({ HTMLAttributes }) {
    const { src, width } = HTMLAttributes;
    return ["figure", { "data-drawing": "" }, ["img", mergeAttributes({ src, alt: "Drawing" }, width ? { style: `width: ${width}px` } : {})]];
  },

  addNodeView() {
    return ReactNodeViewRenderer(DrawingView);
  },

  addCommands() {
    return {
      insertDrawing:
        () =>
        ({ commands }) => {
          openNextDrawing = true;
          const ok = commands.insertContent({ type: this.name });
          if (!ok) openNextDrawing = false;
          return ok;
        },
    };
  },
});
