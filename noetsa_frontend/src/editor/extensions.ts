import StarterKit from "@tiptap/starter-kit";
import { Placeholder } from "@tiptap/extensions";
import { TaskItem, TaskList } from "@tiptap/extension-list";
import { Table, TableCell, TableHeader, TableRow } from "@tiptap/extension-table";
import Image from "@tiptap/extension-image";
import { TextStyleKit } from "@tiptap/extension-text-style";
import Highlight from "@tiptap/extension-highlight";
import TextAlign from "@tiptap/extension-text-align";
import Subscript from "@tiptap/extension-subscript";
import Superscript from "@tiptap/extension-superscript";
import { Details, DetailsContent, DetailsSummary } from "@tiptap/extension-details";
import { Callout } from "./callout";
import { CodeBlock } from "./codeBlock";
import { Column, Columns } from "./columns";
import { Drawing } from "./drawing";
import { PageBreak } from "./pageBreak";
import { SlashCommand } from "./slash";


/** Word-style cell options: background colour and vertical alignment, stored as cell attributes. */
const cellAttributes = {
  backgroundColor: {
    default: null,
    parseHTML: (el: HTMLElement) => el.style.backgroundColor || null,
    renderHTML: (attrs: { backgroundColor?: string | null }) =>
      attrs.backgroundColor ? { style: `background-color: ${attrs.backgroundColor}` } : {},
  },
  verticalAlign: {
    default: null,
    parseHTML: (el: HTMLElement) => el.style.verticalAlign || null,
    renderHTML: (attrs: { verticalAlign?: string | null }) =>
      attrs.verticalAlign ? { style: `vertical-align: ${attrs.verticalAlign}` } : {},
  },
};

const StyledTableCell = TableCell.extend({
  addAttributes() {
    return { ...this.parent?.(), ...cellAttributes };
  },
});

const StyledTableHeader = TableHeader.extend({
  addAttributes() {
    return { ...this.parent?.(), ...cellAttributes };
  },
});

export function buildExtensions() {
  return [
    StarterKit.configure({
      link: { openOnClick: false, autolink: true, defaultProtocol: "https" },
      // Replaced by the syntax-highlighting version below (same node name and JSON).
      codeBlock: false,
    }),
    CodeBlock,
    Placeholder.configure({
      includeChildren: true,
      placeholder: ({ node }) => {
        if (node.type.name === "heading") return `Heading ${node.attrs.level}`;
        if (node.type.name === "detailsSummary") return "Toggle title";
        return "Write, or type / for blocks…";
      },
    }),
    TaskList,
    TaskItem.configure({ nested: true }),
    Table.configure({ resizable: true, cellMinWidth: 60 }),
    TableRow,
    StyledTableHeader,
    StyledTableCell,
    // Images live in our asset store; base64 pastes are converted to uploads instead.
    Image.configure({
      allowBase64: false,
      resize: { enabled: true, directions: ["bottom-right", "bottom-left"], minWidth: 60, alwaysPreserveAspectRatio: true },
    }),
    TextStyleKit,
    Highlight.configure({ multicolor: true }),
    TextAlign.configure({ types: ["heading", "paragraph"] }),
    Subscript,
    Superscript,
    PageBreak,
    Callout,
    Columns,
    Column,
    Details.configure({ persist: true, HTMLAttributes: { class: "details" } }),
    DetailsSummary,
    DetailsContent,
    Drawing,
    SlashCommand,
  ];
}
