# NovaDev IDE

NovaDev IDE is the browser learning and coding workspace for NovaDev. It combines a developer learning site with an online editor, shell, lexer inspector, AST inspector, output terminal, and UI builder.

The interface combines a VS Code-style workbench with a structured challenge
curriculum. Developers move through tracks, read a focused lesson, edit starter
code, run checks, inspect tokens/AST output, and build a UI preview from the
same `.nova` source.

## Pages

- `Curriculum` shows six ordered developer tracks and locally saved progress.
- `Track` lists required lessons and applied projects for one learning path.
- `Challenge` combines lesson instructions, a Nova editor, output, and checks.
- `Learning Projects` defines portfolio and capstone requirements.
- `Editor` is the main `.nova` coding page.
- `Build UI` generates a live preview plus `index.html`, `style.css`, and `app.js`.
- `Output` shows program print output and runtime errors.
- `Tokens` shows lexer output.
- `AST` shows parser/project output.
- `Shell` runs one command at a time and keeps session history.
- `Examples` loads complete NovaDev examples into the editor.
- `Settings` controls editor font size, line wrapping, theme, and browser saves.

## Course Content

The 44 lessons now follow six beginner-to-advanced tracks:

- Getting started with source code, tokens, AST output, and runtime execution.
- General programming with variables, strings, lists, objects, operators, control flow, loops, functions, and debugging.
- Object-oriented programming with classes, objects, constructors, methods, `this`, inheritance, and composition.
- App building with `app`, `project`, modes, tables, pages, workflows, routes, auth, SQLite, SQLAlchemy, Vue, Flask, and Tailwind.
- Standard-library topics including Nova math, dates/time, JSON-style data, HTTP/API clients, file read/write/append/delete, SQLite, CLI workflow, and security.
- Advanced development with automations, custom frontend files, custom backend Python modules, packages, API keys, environment variables, third-party APIs, testing, deployment, and capstone projects.

Progress is stored in the browser under `nova-ide-progress-v2`. Lessons that
need local files, packages, secrets, or network access use structural checks
online and explain that the installed NovaDev runtime is required for execution.

The longer teaching outline lives in:

```text
../docs/NOVADEV_DEVELOPER_COURSE.md
```

## Vercel Deployment

This folder is ready for Vercel:

```bash
npm install
npm run build
vercel deploy
```

The Vue frontend calls these serverless endpoints:

- `/api/run`
- `/api/tokens`
- `/api/ast`
- `/api/build-ui`

The API uses a synchronized copy of NovaDev's canonical lexer, parser,
interpreter, ProjectIR, and frontend compiler. It does not use Docker and does
not run unsafe Python blocks online.

Before deploying after a language change, synchronize the runtime:

```bash
python ../scripts/sync_ide_runtime.py
```

## Local Development

```bash
npm install
npm run dev
```

Open the local Vite URL, usually:

```text
http://localhost:5173
```

## Shortcuts

- `Ctrl + Enter` runs the current NovaDev file.
- `Ctrl + B` builds the UI preview.
- `Ctrl + S` saves the current file in browser storage.

## Notes

The online IDE is designed for learning, demos, shell-style testing, lexer/AST inspection, and UI previews. Full local project generation still belongs to the installed NovaDev CLI and package manager.
