# js24 · Ralfiz Store: a Vite project with ESLint and Prettier

Set up a real front-end project the way teams do: Vite for the dev server
and build, ESLint for bugs, Prettier for formatting, and `.env` files for
configuration. The finished files are in `solution/`.

You need Node 22.13+ (or 20.19+) and internet access for npm.

## 1. Create the project

```bash
npm create vite@latest ralfiz-store -- --template vanilla
cd ralfiz-store
npm install
npm run dev          # open http://localhost:5173
```

Look around: `package.json` (scripts, `"type": "module"`, `vite` in
devDependencies), `index.html` with `<script type="module">`, `src/main.js`
and `package-lock.json`.

## 2. Add ESLint and Prettier

```bash
npm install -D eslint @eslint/js globals prettier
```

- Copy `solution/eslint.config.js` into the project root.
- Create `.prettierrc`:

```json
{
  "singleQuote": true,
  "semi": true,
  "printWidth": 100
}
```

- Add these scripts to `package.json`:

```json
"lint": "eslint .",
"format": "prettier --write .",
"check": "eslint . && prettier --check ."
```

## 3. Replace the demo app

Delete everything in `src/` and `public/`, then copy `solution/index.html` and
`solution/src/main.js` into place. `main.js` reads two environment
variables and renders six products from DummyJSON.

## 4. Environment files

`.env` (shared defaults, committed). The fake `DB_PASSWORD` line is only here to prove
that Vite does not expose it; never commit a real secret:

```bash
VITE_API_BASE=https://dummyjson.com
VITE_STORE_NAME=Ralfiz Store
DB_PASSWORD=never-exposed-to-the-browser
```

`.env.development` (only for `npm run dev`):

```bash
VITE_STORE_NAME=Ralfiz Store (dev)
```

Restart `npm run dev` after changing `.env` files.

## 5. Build and inspect

```bash
npm run check
npm run build
npm run preview      # open http://localhost:4173
```

Open `dist/assets/index-<hash>.js` and search it.

## Acceptance criteria

- `npm run dev` shows **Ralfiz Store (dev)** with `mode: development` and six product cards.
- `npm run check` finishes with no ESLint errors and
  `All matched files use Prettier code style!`.
- `npm run build` creates `dist/index.html` and one `dist/assets/index-<hash>.js`.
- `npm run preview` shows **Ralfiz Store** with `mode: production`.
- The built JS file contains `dummyjson.com` but **not** `never-exposed-to-the-browser`.
- Change one line in `main.js` and build again: the hash in the file name changes.
