import { forwardRef, Fragment, useEffect, useImperativeHandle, useState } from "react";
import { Extension } from "@tiptap/core";
import { ReactRenderer } from "@tiptap/react";
import Suggestion, { type SuggestionKeyDownProps, type SuggestionProps } from "@tiptap/suggestion";
import { filterCommands, type BlockCommand } from "./commands";

type MenuHandle = { onKeyDown: (event: KeyboardEvent) => boolean };
type MenuProps = SuggestionProps<BlockCommand, BlockCommand>;

const SlashMenu = forwardRef<MenuHandle, MenuProps>(function SlashMenu({ items, command }, ref) {
  const [selected, setSelected] = useState(0);
  useEffect(() => setSelected(0), [items]);

  useImperativeHandle(ref, () => ({
    onKeyDown(event) {
      if (!items.length) return false;
      if (event.key === "ArrowDown") {
        setSelected((s) => (s + 1) % items.length);
        return true;
      }
      if (event.key === "ArrowUp") {
        setSelected((s) => (s - 1 + items.length) % items.length);
        return true;
      }
      if (event.key === "Enter") {
        command(items[selected]);
        return true;
      }
      return false;
    },
  }));

  useEffect(() => {
    document.querySelector(".slash-menu [aria-selected=true]")?.scrollIntoView({ block: "nearest" });
  }, [selected]);

  if (!items.length) return <div className="slash-menu"><div className="slash-empty">No matching blocks</div></div>;
  return (
    <div className="slash-menu" role="listbox">
      {items.map((item, i) => (
        <Fragment key={item.title}>
        {(i === 0 || items[i - 1].group !== item.group) && <div className="slash-group">{item.group}</div>}
        <button
          role="option"
          aria-selected={i === selected}
          className={i === selected ? "selected" : ""}
          onMouseEnter={() => setSelected(i)}
          onMouseDown={(e) => {
            e.preventDefault(); // keep editor focus
            command(item);
          }}
        >
          <span className="slash-icon"><item.icon size={18} /></span>
          <span>
            <strong>{item.title}</strong>
            <small>{item.description}</small>
          </span>
        </button>
        </Fragment>
      ))}
    </div>
  );
});

function place(el: HTMLElement, rect: DOMRect | null | undefined) {
  if (!rect) return;
  const menuHeight = Math.min(el.offsetHeight || 320, 320);
  const below = rect.bottom + 6 + menuHeight < window.innerHeight;
  el.style.left = `${Math.max(8, Math.min(rect.left, window.innerWidth - 288))}px`;
  el.style.top = below ? `${rect.bottom + 6}px` : `${Math.max(8, rect.top - menuHeight - 6)}px`;
}

/** Typing `/` opens a menu of blocks to insert (headings, lists, table, image, emoji…). */
export const SlashCommand = Extension.create({
  name: "slashCommand",

  addProseMirrorPlugins() {
    return [
      Suggestion<BlockCommand, BlockCommand>({
        editor: this.editor,
        char: "/",
        // "/2 col" should still match; once nothing matches and a space was typed it's just text.
        allowSpaces: true,
        items: ({ query }) => filterCommands(query),
        command: ({ editor, range, props }) => {
          editor.chain().focus().deleteRange(range).run();
          props.run(editor);
        },
        render: () => {
          let renderer: ReactRenderer<MenuHandle, MenuProps> | null = null;
          return {
            onStart: (props) => {
              renderer = new ReactRenderer(SlashMenu, { props, editor: props.editor });
              renderer.element.classList.add("slash-popup");
              document.body.appendChild(renderer.element);
              place(renderer.element, props.clientRect?.());
            },
            onUpdate: (props) => {
              renderer?.updateProps(props);
              if (!renderer) return;
              const giveUp = !props.items.length && props.query.includes(" ");
              renderer.element.style.display = giveUp ? "none" : "";
              place(renderer.element, props.clientRect?.());
            },
            onKeyDown: ({ event }: SuggestionKeyDownProps) => {
              if (renderer?.element.style.display === "none") return false;
              if (event.key === "Escape") {
                renderer?.element.remove();
                return true;
              }
              return renderer?.ref?.onKeyDown(event) ?? false;
            },
            onExit: () => {
              renderer?.element.remove();
              renderer?.destroy();
              renderer = null;
            },
          };
        },
      }),
    ];
  },
});
