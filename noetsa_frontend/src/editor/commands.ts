import type { Editor } from "@tiptap/react";
import {
  ChevronRightSquare, CodeXml, Columns2, Columns3, Heading1, Heading2, Heading3, ImagePlus, Lightbulb, List, ListOrdered,
  ListTodo, Minus, PenLine, Pilcrow, Quote, SeparatorHorizontal, Smile, Table, type LucideIcon,
} from "lucide-react";
import { pickImages } from "./uploads";

export const OPEN_EMOJI_EVENT = "noetsa:open-emoji";

export type BlockCommand = {
  title: string;
  description: string;
  icon: LucideIcon;
  keywords: string;
  group: "Basic" | "Lists" | "Insert" | "Layout";
  run: (editor: Editor) => void;
};

/** Blocks offered by the `/` menu and the block "+" button. */
export const BLOCK_COMMANDS: BlockCommand[] = [
  { group: "Basic", title: "Text", description: "Plain paragraph", icon: Pilcrow, keywords: "paragraph normal", run: (e) => e.chain().focus().setParagraph().run() },
  { group: "Basic", title: "Heading 1", description: "Large section title", icon: Heading1, keywords: "h1 title", run: (e) => e.chain().focus().setHeading({ level: 1 }).run() },
  { group: "Basic", title: "Heading 2", description: "Medium section title", icon: Heading2, keywords: "h2 subtitle", run: (e) => e.chain().focus().setHeading({ level: 2 }).run() },
  { group: "Basic", title: "Heading 3", description: "Small section title", icon: Heading3, keywords: "h3", run: (e) => e.chain().focus().setHeading({ level: 3 }).run() },
  { group: "Basic", title: "Callout", description: "Coloured box for tips and warnings", icon: Lightbulb, keywords: "note tip warning info box alert", run: (e) => e.chain().focus().setCallout("info").run() },
  { group: "Basic", title: "Quote", description: "Highlighted quotation", icon: Quote, keywords: "blockquote", run: (e) => e.chain().focus().toggleBlockquote().run() },
  { group: "Basic", title: "Toggle", description: "Collapsible section", icon: ChevronRightSquare, keywords: "details collapse expand accordion fold", run: (e) => e.chain().focus().setDetails().updateAttributes("details", { open: true }).run() },
  { group: "Lists", title: "Bullet list", description: "Simple bulleted list", icon: List, keywords: "ul unordered", run: (e) => e.chain().focus().toggleBulletList().run() },
  { group: "Lists", title: "Numbered list", description: "List with numbers", icon: ListOrdered, keywords: "ol ordered", run: (e) => e.chain().focus().toggleOrderedList().run() },
  { group: "Lists", title: "Checklist", description: "Tasks you can tick off", icon: ListTodo, keywords: "todo task checkbox", run: (e) => e.chain().focus().toggleTaskList().run() },
  { group: "Insert", title: "Table", description: "Rows and columns, like Word", icon: Table, keywords: "grid spreadsheet", run: (e) => e.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run() },
  { group: "Insert", title: "Image", description: "Upload a picture", icon: ImagePlus, keywords: "photo picture upload", run: (e) => pickImages(e) },
  { group: "Insert", title: "Drawing", description: "Sketch shapes and diagrams in the note", icon: PenLine, keywords: "draw sketch whiteboard diagram excalidraw canvas", run: (e) => e.chain().focus().insertDrawing().run() },
  { group: "Insert", title: "Emoji", description: "Insert an emoji", icon: Smile, keywords: "smiley icon", run: () => window.dispatchEvent(new Event(OPEN_EMOJI_EVENT)) },
  { group: "Insert", title: "Code block", description: "Code with syntax colours", icon: CodeXml, keywords: "pre snippet programming", run: (e) => e.chain().focus().toggleCodeBlock().run() },
  { group: "Layout", title: "2 columns", description: "Two blocks side by side", icon: Columns2, keywords: "columns layout side grid", run: (e) => e.chain().focus().insertColumns(2).run() },
  { group: "Layout", title: "3 columns", description: "Three blocks side by side", icon: Columns3, keywords: "columns layout side grid", run: (e) => e.chain().focus().insertColumns(3).run() },
  { group: "Layout", title: "Divider", description: "Horizontal line", icon: Minus, keywords: "hr rule separator", run: (e) => e.chain().focus().setHorizontalRule().run() },
  { group: "Layout", title: "Page break", description: "Start a new page when printed (Ctrl+Enter)", icon: SeparatorHorizontal, keywords: "new page pdf print", run: (e) => e.chain().focus().setPageBreak().run() },
];

export function filterCommands(query: string) {
  const q = query.toLowerCase().trim();
  if (!q) return BLOCK_COMMANDS;
  return BLOCK_COMMANDS.filter((c) => `${c.title} ${c.keywords}`.toLowerCase().includes(q));
}
