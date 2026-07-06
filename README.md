# NovaDev Online IDE

This folder is a standalone Vercel-ready website for running NovaDev code online.

It is built as:

- Vue + Vite frontend
- Python Vercel Functions for NovaDev execution
- Node Vercel Function for share URLs
- Vendored `novadev/` language runtime so the deployment is self-contained

## What It Implements

## IDE Experience

The interface follows the same practical pattern as browser coding tools such as Online Python:

- file tab for the active `.nova` file
- Run, Tokens, AST, Build UI, Share, Save, Load Save, and Download actions
- terminal, problems, tokens, AST, preview, and shell panels
- copy/download output
- light/dark theme toggle
- horizontal split or vertical stacked layout
- font-size and line-wrap settings
- browser autosave while typing
- local browser save/load
- shareable URL hash
- keyboard shortcuts:
  - `Ctrl + Enter` or `F8`: run code
  - `Ctrl + S` or `F10`: save in browser
  - `Ctrl + H` or `F9`: share code

### Phase 1: Safe One-Shot Runner

The browser sends NovaDev source code to Python API functions:

- `/api/run`
- `/api/tokens`
- `/api/ast`

The Python functions import NovaDev directly and execute in safe mode. The runner blocks:

- `allow unsafe_python true`
- raw `python { ... }` blocks
- `custom ...` code blocks
- `input()`

It also enforces source size, output size, and short execution time limits.

### Phase 2: UI Preview And Sharing

The frontend can call:

- `/api/build_ui`
- `/api/share`

`build_ui` generates temporary NovaDev UI files and returns them to the browser as an iframe preview. `share` encodes code into a URL hash, so no database is required.

### Phase 3: Browser Shell Replay

The Shell tab feels like:

```text
nova> let name = "Aldane"
nova> print(name)
Aldane
```

Because Vercel functions are short-lived, the browser shell does not hold a permanent Python process. Instead, it keeps session source in the browser and replays the full session on each command.

## Deploy To Vercel

From this folder:

```bash
npm install
npm run build
vercel
```

When Vercel asks for the project root, use this folder:

```text
nova ide
```

You can also drag/drop or upload this folder to Vercel if your workflow supports that.

## Local Development

Use Vercel's local dev server so the frontend and API functions run together:

```bash
npm install
npx vercel dev
```

Plain Vite development works for the frontend only:

```bash
npm run dev
```

## File Structure

```text
nova ide/
  src/
    App.vue
    api.js
    examples.js
    main.js
    styles.css

  api/
    _common.py
    run.py
    tokens.py
    ast.py
    build_ui.py
    health.py
    share.js

  novadev/
    copied NovaDev Python language runtime

  package.json
  vercel.json
  requirements.txt
```

## Why It Does Not Use Docker

This version is designed for Vercel Functions, so it avoids Docker and avoids a permanent backend process. The safety model is based on:

- direct interpreter calls instead of shell commands
- short `maxDuration`
- source/output size limits
- blocked unsafe NovaDev/Python features
- temporary folders for generated UI previews

For a public production coding site, Docker or a stronger sandbox is still safer for arbitrary user code. This project is a practical Vercel-first prototype.
