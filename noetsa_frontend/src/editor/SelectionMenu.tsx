import { useEditorState, type Editor } from "@tiptap/react";
import { BubbleMenu } from "@tiptap/react/menus";
import { NodeSelection } from "@tiptap/pm/state";
import { Baseline, Bold, Code, Highlighter, Italic, Link, Strikethrough, Underline } from "lucide-react";
import { Dropdown } from "../components/Dropdown";
import { BlockTypeMenu, blockLabel, Btn, normaliseUrl } from "./Toolbar";
import { ColorGrid, HIGHLIGHT_COLORS, LinkForm, TEXT_COLORS } from "./pickers";

/** Floating format bar shown over selected text, like Notion and Google Docs. */
export function SelectionMenu({ editor }: { editor: Editor }) {
  const s = useEditorState({
    editor,
    selector: ({ editor: e }) => ({
      block: blockLabel(e),
      bold: e.isActive("bold"),
      italic: e.isActive("italic"),
      underline: e.isActive("underline"),
      strike: e.isActive("strike"),
      code: e.isActive("code"),
      color: (e.getAttributes("textStyle").color as string) ?? null,
      highlight: (e.getAttributes("highlight").color as string) ?? null,
      link: (e.getAttributes("link").href as string) ?? "",
    }),
  });
  const c = () => editor.chain().focus();

  return (
    <BubbleMenu
      editor={editor}
      className="selection-menu"
      options={{ placement: "top", offset: 8, flip: true }}
      shouldShow={({ editor: e, state, from, to }) => {
        if (!e.isEditable || from === to) return false;
        // Images, drawings and code blocks have their own handling.
        if (state.selection instanceof NodeSelection || e.isActive("codeBlock")) return false;
        return state.doc.textBetween(from, to).trim().length > 0;
      }}
    >
      <BlockTypeMenu editor={editor} label={s.block} compact />
      <span className="toolbar-sep" />
      <Btn label="Bold" icon={Bold} active={s.bold} onClick={() => c().toggleBold().run()} />
      <Btn label="Italic" icon={Italic} active={s.italic} onClick={() => c().toggleItalic().run()} />
      <Btn label="Underline" icon={Underline} active={s.underline} onClick={() => c().toggleUnderline().run()} />
      <Btn label="Strikethrough" icon={Strikethrough} active={s.strike} onClick={() => c().toggleStrike().run()} />
      <Btn label="Inline code" icon={Code} active={s.code} onClick={() => c().toggleCode().run()} />
      <span className="toolbar-sep" />
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
      <Dropdown label="Text colour" caret={false} button={<span className="color-btn"><Baseline size={16} /><i style={{ background: s.color ?? "currentColor" }} /></span>}>
        {(close) => (
          <ColorGrid colors={TEXT_COLORS} current={s.color} clearLabel="Default colour" onPick={(color) => {
            if (color) c().setColor(color).run();
            else c().unsetColor().run();
            close();
          }} />
        )}
      </Dropdown>
      <Dropdown label="Highlight" caret={false} button={<span className="color-btn"><Highlighter size={16} /><i style={{ background: s.highlight ?? "transparent" }} /></span>}>
        {(close) => (
          <ColorGrid colors={HIGHLIGHT_COLORS} current={s.highlight} clearLabel="No highlight" onPick={(color) => {
            if (color) c().setHighlight({ color }).run();
            else c().unsetHighlight().run();
            close();
          }} />
        )}
      </Dropdown>
    </BubbleMenu>
  );
}
