import { useEffect, useState } from "react";
import { useEditorState, type Editor } from "@tiptap/react";
import {
  AlignCenter, AlignJustify, AlignLeft, AlignRight, ArrowDownToLine, ArrowUpToLine, Baseline,
  BetweenHorizontalEnd, BetweenHorizontalStart, BetweenVerticalEnd, BetweenVerticalStart, Bold,
  Columns3, Grid2x2X, Highlighter, ImagePlus, Italic, Link, List, ListOrdered, ListTodo,
  MoreHorizontal, PaintBucket, PanelTop, Plus, Redo2, RemoveFormatting, Rows3, Smile,
  Strikethrough, Subscript, Superscript, Table, TableCellsMerge, TableCellsSplit, Underline, Undo2,
  AlignVerticalJustifyCenter, type LucideIcon,
} from "lucide-react";
import { Dropdown } from "../components/Dropdown";
import { BLOCK_COMMANDS, OPEN_EMOJI_EVENT } from "./commands";
import { ColorGrid, EmojiPicker, HIGHLIGHT_COLORS, LinkForm, TableGridPicker, TEXT_COLORS } from "./pickers";
import { pickImages } from "./uploads";

const FONTS = [
  { label: "Default", value: "" },
  { label: "Arial", value: "Arial, Helvetica, sans-serif" },
  { label: "Georgia", value: "Georgia, serif" },
  { label: "Times New Roman", value: "'Times New Roman', Times, serif" },
  { label: "Verdana", value: "Verdana, sans-serif" },
  { label: "Trebuchet", value: "'Trebuchet MS', sans-serif" },
  { label: "Courier New", value: "'Courier New', monospace" },
];

const SIZES = ["10px", "12px", "14px", "16px", "18px", "20px", "24px", "28px", "32px", "40px", "48px"];

/** Blocks the Insert menu offers (the rest are in the toolbar itself). */
const INSERTABLE = ["Callout", "Toggle", "Drawing", "2 columns", "3 columns", "Quote", "Code block", "Divider", "Page break"];

export function normaliseUrl(href: string) {
  return /^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith("/") ? href : `https://${href}`;
}

const BLOCK_TYPES: { key: string; label: string; className: string; run: (e: Editor) => void }[] = [
  { key: "p", label: "Normal text", className: "bt-p", run: (e) => e.chain().focus().setParagraph().run() },
  { key: "h1", label: "Heading 1", className: "bt-h1", run: (e) => e.chain().focus().setHeading({ level: 1 }).run() },
  { key: "h2", label: "Heading 2", className: "bt-h2", run: (e) => e.chain().focus().setHeading({ level: 2 }).run() },
  { key: "h3", label: "Heading 3", className: "bt-h3", run: (e) => e.chain().focus().setHeading({ level: 3 }).run() },
];

export function blockLabel(e: Editor) {
  for (const level of [1, 2, 3] as const) if (e.isActive("heading", { level })) return `Heading ${level}`;
  return "Normal text";
}

/** "Normal text ▾" picker with a preview of each style. */
export function BlockTypeMenu({ editor, label, compact }: { editor: Editor; label: string; compact?: boolean }) {
  return (
    <Dropdown label="Text style" className={`icon-btn dropdown-btn tb-picker ${compact ? "tb-picker-compact" : "tb-picker-block"}`} button={<span className="ellipsis">{label}</span>}>
      {(close) => (
        <div className="menu block-type-menu">
          {BLOCK_TYPES.map((b) => (
            <button key={b.key} type="button" className={`${b.className} ${label === b.label ? "active" : ""}`} onClick={() => { b.run(editor); close(); }}>
              {b.label}
            </button>
          ))}
        </div>
      )}
    </Dropdown>
  );
}

const ALIGNMENTS: { value: string; label: string; icon: LucideIcon }[] = [
  { value: "left", label: "Align left", icon: AlignLeft },
  { value: "center", label: "Align centre", icon: AlignCenter },
  { value: "right", label: "Align right", icon: AlignRight },
  { value: "justify", label: "Justify", icon: AlignJustify },
];

export function Btn({ label, icon: Icon, active, disabled, onClick }: { label: string; icon: LucideIcon; active?: boolean; disabled?: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      className={`icon-btn ${active ? "active" : ""}`}
      title={label}
      aria-label={label}
      aria-pressed={active}
      disabled={disabled}
      // Keep the editor's selection when clicking toolbar buttons.
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
    >
      <Icon size={16} />
    </button>
  );
}

const Sep = () => <span className="toolbar-sep" />;

function useToolbarState(editor: Editor | null) {
  return useEditorState({
    editor,
    selector: ({ editor: e }) => {
      if (!e) return null;
      const style = e.getAttributes("textStyle");
      return {
        block: blockLabel(e),
        fontFamily: (style.fontFamily as string) ?? "",
        fontSize: (style.fontSize as string) ?? "",
        color: (style.color as string) ?? null,
        highlight: (e.getAttributes("highlight").color as string) ?? null,
        bold: e.isActive("bold"),
        italic: e.isActive("italic"),
        underline: e.isActive("underline"),
        strike: e.isActive("strike"),
        sub: e.isActive("subscript"),
        sup: e.isActive("superscript"),
        align: ALIGNMENTS.find((a) => e.isActive({ textAlign: a.value }))?.value ?? "left",
        bullet: e.isActive("bulletList"),
        ordered: e.isActive("orderedList"),
        task: e.isActive("taskList"),
        link: (e.getAttributes("link").href as string) ?? "",
        inTable: e.isActive("table"),
        canUndo: e.can().undo(),
        canRedo: e.can().redo(),
      };
    },
  });
}

export function Toolbar({ editor }: { editor: Editor | null }) {
  const s = useToolbarState(editor);
  const [emojiSignal, setEmojiSignal] = useState(0);

  useEffect(() => {
    const open = () => setEmojiSignal((n) => n + 1);
    window.addEventListener(OPEN_EMOJI_EVENT, open);
    return () => window.removeEventListener(OPEN_EMOJI_EVENT, open);
  }, []);

  if (!editor || !s) return <div className="toolbar" />;
  const c = () => editor.chain().focus();
  const AlignIcon = ALIGNMENTS.find((a) => a.value === s.align)?.icon ?? AlignLeft;

  return (
    <div className="toolbar-rows">
      <div className="toolbar" role="toolbar" aria-label="Formatting">
        <Btn label="Undo" icon={Undo2} disabled={!s.canUndo} onClick={() => c().undo().run()} />
        <Btn label="Redo" icon={Redo2} disabled={!s.canRedo} onClick={() => c().redo().run()} />
        <Sep />
        <BlockTypeMenu editor={editor} label={s.block} />
        <Dropdown
          label="Font"
          className="icon-btn dropdown-btn tb-picker tb-picker-font"
          button={<span className="ellipsis" style={{ fontFamily: s.fontFamily || undefined }}>{FONTS.find((f) => f.value === s.fontFamily)?.label ?? "Custom font"}</span>}
        >
          {(close) => (
            <div className="menu">
              {FONTS.map((f) => (
                <button key={f.label} type="button" className={s.fontFamily === f.value ? "active" : ""} style={{ fontFamily: f.value || undefined }} onClick={() => {
                  if (f.value) c().setFontFamily(f.value).run();
                  else c().unsetFontFamily().run();
                  close();
                }}>
                  {f.label}
                </button>
              ))}
            </div>
          )}
        </Dropdown>
        <Dropdown label="Font size" className="icon-btn dropdown-btn tb-picker tb-picker-size" button={<span>{s.fontSize ? parseInt(s.fontSize) : "Size"}</span>}>
          {(close) => (
            <div className="menu size-menu">
              <button type="button" className={s.fontSize ? "" : "active"} onClick={() => { c().unsetFontSize().run(); close(); }}>Default</button>
              {SIZES.map((size) => (
                <button key={size} type="button" className={s.fontSize === size ? "active" : ""} onClick={() => { c().setFontSize(size).run(); close(); }}>
                  {parseInt(size)}
                </button>
              ))}
            </div>
          )}
        </Dropdown>
        <Sep />
        <Btn label="Bold" icon={Bold} active={s.bold} onClick={() => c().toggleBold().run()} />
        <Btn label="Italic" icon={Italic} active={s.italic} onClick={() => c().toggleItalic().run()} />
        <Btn label="Underline" icon={Underline} active={s.underline} onClick={() => c().toggleUnderline().run()} />
        <Btn label="Strikethrough" icon={Strikethrough} active={s.strike} onClick={() => c().toggleStrike().run()} />
        <Dropdown
          label="Text colour"
          button={<span className="color-btn"><Baseline size={16} /><i style={{ background: s.color ?? "currentColor" }} /></span>}
        >
          {(close) => (
            <ColorGrid
              colors={TEXT_COLORS}
              current={s.color}
              clearLabel="Default colour"
              onPick={(color) => {
                if (color) c().setColor(color).run();
                else c().unsetColor().run();
                close();
              }}
            />
          )}
        </Dropdown>
        <Dropdown
          label="Highlight"
          button={<span className="color-btn"><Highlighter size={16} /><i style={{ background: s.highlight ?? "transparent" }} /></span>}
        >
          {(close) => (
            <ColorGrid
              colors={HIGHLIGHT_COLORS}
              current={s.highlight}
              clearLabel="No highlight"
              onPick={(color) => {
                if (color) c().setHighlight({ color }).run();
                else c().unsetHighlight().run();
                close();
              }}
            />
          )}
        </Dropdown>
        <Sep />
        <Dropdown label="Alignment" button={<AlignIcon size={16} />}>
          {(close) => (
            <div className="menu">
              {ALIGNMENTS.map((a) => (
                <button
                  key={a.value}
                  type="button"
                  className={s.align === a.value ? "active" : ""}
                  onClick={() => {
                    c().setTextAlign(a.value).run();
                    close();
                  }}
                >
                  <a.icon size={16} /> {a.label}
                </button>
              ))}
            </div>
          )}
        </Dropdown>
        <Btn label="Bullet list" icon={List} active={s.bullet} onClick={() => c().toggleBulletList().run()} />
        <Btn label="Numbered list" icon={ListOrdered} active={s.ordered} onClick={() => c().toggleOrderedList().run()} />
        <Btn label="Checklist" icon={ListTodo} active={s.task} onClick={() => c().toggleTaskList().run()} />
        <Sep />
        <Dropdown label="Link" button={<Link size={16} />} caret={false} active={Boolean(s.link)}>
          {(close) => (
            <LinkForm
              initial={s.link}
              onApply={(href) => {
                c().extendMarkRange("link").setLink({ href: normaliseUrl(href) }).run();
                close();
              }}
              onRemove={() => {
                c().extendMarkRange("link").unsetLink().run();
                close();
              }}
            />
          )}
        </Dropdown>
        <Btn label="Insert image" icon={ImagePlus} onClick={() => pickImages(editor)} />
        <Dropdown label="Insert table" button={<Table size={16} />}>
          {(close) => (
            <TableGridPicker
              onPick={(rows, cols) => {
                c().insertTable({ rows, cols, withHeaderRow: true }).run();
                close();
              }}
            />
          )}
        </Dropdown>
        <Dropdown label="Emoji" button={<Smile size={16} />} caret={false} openSignal={emojiSignal}>
          {(close) => (
            <EmojiPicker
              onPick={(emoji) => {
                c().insertContent(emoji).run();
                close();
              }}
            />
          )}
        </Dropdown>
        <Sep />
        <Dropdown label="Insert" className="icon-btn dropdown-btn tb-insert" button={<><Plus size={16} /> <span>Insert</span></>}>
          {(close) => (
            <div className="menu insert-menu">
              {BLOCK_COMMANDS.filter((b) => INSERTABLE.includes(b.title)).map((b) => (
                <button key={b.title} type="button" onClick={() => { b.run(editor); close(); }}>
                  <span className="menu-icon"><b.icon size={16} /></span>
                  <span><strong>{b.title}</strong><small>{b.description}</small></span>
                </button>
              ))}
            </div>
          )}
        </Dropdown>
        <Dropdown label="More formatting" button={<MoreHorizontal size={16} />} caret={false} align="right">
          {(close) => (
            <div className="menu">
              {[
                { label: "Subscript", icon: Subscript, active: s.sub, run: () => c().toggleSubscript().run() },
                { label: "Superscript", icon: Superscript, active: s.sup, run: () => c().toggleSuperscript().run() },
                { label: "Clear formatting", icon: RemoveFormatting, active: false, run: () => c().unsetAllMarks().clearNodes().run() },
              ].map((item) => (
                <button
                  key={item.label}
                  type="button"
                  className={item.active ? "active" : ""}
                  onClick={() => {
                    item.run();
                    close();
                  }}
                >
                  <item.icon size={16} /> {item.label}
                </button>
              ))}
            </div>
          )}
        </Dropdown>
      </div>
      {s.inTable && <TableToolbar editor={editor} />}
    </div>
  );
}

const V_ALIGN = [
  { value: "top", label: "Top", icon: ArrowUpToLine },
  { value: "middle", label: "Middle", icon: AlignVerticalJustifyCenter },
  { value: "bottom", label: "Bottom", icon: ArrowDownToLine },
];

/** Shown while the cursor is inside a table. */
function TableToolbar({ editor }: { editor: Editor }) {
  const s = useEditorState({
    editor,
    selector: ({ editor: e }) => ({
      canMerge: e.can().mergeCells(),
      canSplit: e.can().splitCell(),
      cellColor: (e.getAttributes("tableCell").backgroundColor ?? e.getAttributes("tableHeader").backgroundColor ?? null) as string | null,
    }),
  });
  const c = () => editor.chain().focus();
  return (
    <div className="toolbar table-toolbar" role="toolbar" aria-label="Table">
      <span className="toolbar-label"><Table size={14} /> Table</span>
      <Btn label="Insert row above" icon={BetweenHorizontalStart} onClick={() => c().addRowBefore().run()} />
      <Btn label="Insert row below" icon={BetweenHorizontalEnd} onClick={() => c().addRowAfter().run()} />
      <Btn label="Delete row" icon={Rows3} onClick={() => c().deleteRow().run()} />
      <Sep />
      <Btn label="Insert column left" icon={BetweenVerticalStart} onClick={() => c().addColumnBefore().run()} />
      <Btn label="Insert column right" icon={BetweenVerticalEnd} onClick={() => c().addColumnAfter().run()} />
      <Btn label="Delete column" icon={Columns3} onClick={() => c().deleteColumn().run()} />
      <Sep />
      <Btn label="Merge cells" icon={TableCellsMerge} disabled={!s.canMerge} onClick={() => c().mergeCells().run()} />
      <Btn label="Split cell" icon={TableCellsSplit} disabled={!s.canSplit} onClick={() => c().splitCell().run()} />
      <Btn label="Header row" icon={PanelTop} onClick={() => c().toggleHeaderRow().run()} />
      <Dropdown label="Cell colour" button={<span className="color-btn"><PaintBucket size={16} /><i style={{ background: s.cellColor ?? "transparent" }} /></span>}>
        {(close) => (
          <ColorGrid
            colors={HIGHLIGHT_COLORS}
            current={s.cellColor}
            clearLabel="No fill"
            onPick={(color) => {
              c().setCellAttribute("backgroundColor", color).run();
              close();
            }}
          />
        )}
      </Dropdown>
      <Dropdown label="Vertical alignment" button={<AlignVerticalJustifyCenter size={16} />}>
        {(close) => (
          <div className="menu">
            {V_ALIGN.map((a) => (
              <button
                key={a.value}
                type="button"
                onClick={() => {
                  c().setCellAttribute("verticalAlign", a.value).run();
                  close();
                }}
              >
                <a.icon size={16} /> {a.label}
              </button>
            ))}
          </div>
        )}
      </Dropdown>
      <Sep />
      <Btn label="Delete table" icon={Grid2x2X} onClick={() => c().deleteTable().run()} />
    </div>
  );
}
