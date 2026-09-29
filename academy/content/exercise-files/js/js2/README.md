# Lesson 0.2 lab: set up like a professional

## Task
Create a new project folder `ralfiz-setup` with Node.js, npm scripts,
Prettier, ESLint and git, then finish the small program in `start/index.js`.

## Setup
```bash
node -v                     # 22 or newer
mkdir ralfiz-setup && cd ralfiz-setup
npm init -y
npm pkg set type=module scripts.start="node index.js"
npm install --save-dev --save-exact prettier
echo '{ "singleQuote": true }' > .prettierrc
npm install --save-dev eslint @eslint/js globals
# copy solution/eslint.config.js here (or run: npm init @eslint/config@latest)
git init
echo "node_modules" > .gitignore
```
Copy `start/index.js` into the folder and solve the TODOs.

## Commands
- `npm start`: run the program
- `npx eslint .`: lint (should print nothing when clean)
- `npx prettier . --write`: format every file

## Acceptance criteria
- `npm start` prints three environment lines (Node.js version, platform,
  folder) and then `R-1001: 3 x Notebook = 360 (incl. GST 424.80)` and
  `R-1002: 4 x Gel pen = 100 (incl. GST 118.00)`.
- `npx eslint .` reports no problems.
- Running Prettier a second time changes no files.
- `git status` does not list node_modules, and you have at least one commit.
