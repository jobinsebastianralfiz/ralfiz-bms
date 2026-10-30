import { mergeAttributes, Node } from "@tiptap/core";
import { TextSelection } from "@tiptap/pm/state";

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    columns: {
      /** Insert a side-by-side layout with 2 or 3 columns. */
      insertColumns: (count: 2 | 3) => ReturnType;
    };
  }
}

/** One column of a `columns` layout; holds ordinary blocks. */
export const Column = Node.create({
  name: "column",
  content: "block+",
  isolating: true,

  parseHTML() {
    return [{ tag: "div[data-column]" }];
  },

  renderHTML({ HTMLAttributes }) {
    return ["div", mergeAttributes(HTMLAttributes, { "data-column": "", class: "column" }), 0];
  },
});

/** Side-by-side columns (2 or 3), e.g. a resume sidebar or a two-column comparison. */
export const Columns = Node.create({
  name: "columns",
  group: "block",
  content: "column{2,3}",
  defining: true,

  parseHTML() {
    return [{ tag: "div[data-columns]" }];
  },

  renderHTML({ HTMLAttributes, node }) {
    return ["div", mergeAttributes(HTMLAttributes, { "data-columns": node.childCount, class: "columns" }), 0];
  },

  addCommands() {
    return {
      insertColumns:
        (count) =>
        ({ chain }) =>
          chain()
            .insertContent({
              type: this.name,
              content: Array.from({ length: count }, () => ({ type: "column", content: [{ type: "paragraph" }] })),
            })
            // The cursor ends up in the last column; start typing in the first one instead.
            .command(({ tr }) => {
              const $pos = tr.selection.$from;
              for (let depth = $pos.depth; depth > 0; depth--) {
                if ($pos.node(depth).type.name === this.name) {
                  tr.setSelection(TextSelection.near(tr.doc.resolve($pos.before(depth) + 3)));
                  break;
                }
              }
              return true;
            })
            .run(),
    };
  },
});
