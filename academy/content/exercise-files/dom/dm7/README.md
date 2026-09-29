# Lab 2.3 - Ralfiz Admin: command palette and resizable sidebar

Build the keyboard and pointer layer of an admin dashboard:

- **Ctrl+K / Cmd+K** toggles a command palette; **/** opens it when you are not typing
- in the palette: type to filter, **↑ ↓** to move, **Enter** to run, **Esc** or a
  backdrop click to close
- running a command dispatches a bubbling **CustomEvent('command')** with
  `detail: { id, label }`; the app listens on document and reacts
- the sidebar can be resized by dragging its edge (pointer events + pointer capture),
  and with the **←/→** keys when the handle is focused

## Run it

Open the `start` folder in VS Code with **Live Server**, or run `npx serve` in it.
The HTML, CSS, command list and render function are ready. Complete TODO(1)-TODO(6)
in `app.js`.

## Acceptance criteria

1. Ctrl+K (Cmd+K on a Mac) opens the palette with the input focused and the browser
   does not react to the shortcut. Pressing it again closes the palette.
2. Typing "or" leaves only Orders. ↑/↓ wrap around; Enter runs the highlighted command.
3. Running "Go to Products" changes the page heading and the status line
   reads "Last command: Go to Products".
4. "Toggle dark mode" switches the theme; the palette itself never touches the page.
5. Dragging the sidebar edge resizes it between 160px and 360px, even if you move fast.
6. Pressing / inside the page search box types a slash instead of opening the palette.
