import { mergeAttributes, Node } from "@tiptap/core";
import { NodeViewContent, NodeViewWrapper, ReactNodeViewRenderer, type ReactNodeViewProps } from "@tiptap/react";
import { useState } from "react";

/** Variants; must match CALLOUTS in notes/render.py. */
export const CALLOUTS = {
  info: { emoji: "💡", label: "Info" },
  note: { emoji: "📝", label: "Note" },
  success: { emoji: "✅", label: "Success" },
  warning: { emoji: "⚠️", label: "Warning" },
  danger: { emoji: "🚫", label: "Important" },
} as const;

export type CalloutVariant = keyof typeof CALLOUTS;

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    callout: {
      /** Wrap the current block(s) in a callout. */
      setCallout: (variant?: CalloutVariant) => ReturnType;
    };
  }
}

function CalloutView({ node, updateAttributes, editor }: ReactNodeViewProps) {
  const variant = (node.attrs.variant in CALLOUTS ? node.attrs.variant : "info") as CalloutVariant;
  const [open, setOpen] = useState(false);
  return (
    <NodeViewWrapper className={`callout callout-${variant}`} data-callout={variant}>
      <span className="callout-icon-wrap" contentEditable={false}>
        <button
          type="button"
          className="callout-icon"
          title="Change callout style"
          disabled={!editor.isEditable}
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => setOpen((o) => !o)}
        >
          {CALLOUTS[variant].emoji}
        </button>
        {open && (
          <span className="callout-picker" onMouseLeave={() => setOpen(false)}>
            {(Object.keys(CALLOUTS) as CalloutVariant[]).map((key) => (
              <button
                key={key}
                type="button"
                className={`callout-swatch callout-${key}`}
                title={CALLOUTS[key].label}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => {
                  updateAttributes({ variant: key });
                  setOpen(false);
                }}
              >
                {CALLOUTS[key].emoji}
              </button>
            ))}
          </span>
        )}
      </span>
      <NodeViewContent className="callout-content" />
    </NodeViewWrapper>
  );
}

/** A coloured box with an icon, for tips, warnings and highlights. */
export const Callout = Node.create({
  name: "callout",
  group: "block",
  content: "block+",
  defining: true,

  addAttributes() {
    return {
      variant: {
        default: "info",
        parseHTML: (el) => el.getAttribute("data-callout") || "info",
        renderHTML: (attrs) => ({ "data-callout": attrs.variant }),
      },
    };
  },

  parseHTML() {
    return [{ tag: "div[data-callout]" }];
  },

  renderHTML({ HTMLAttributes }) {
    return ["div", mergeAttributes(HTMLAttributes, { class: "callout" }), 0];
  },

  addNodeView() {
    return ReactNodeViewRenderer(CalloutView);
  },

  addCommands() {
    return {
      setCallout:
        (variant = "info") =>
        ({ commands }) =>
          commands.wrapIn(this.name, { variant }),
    };
  },
});
