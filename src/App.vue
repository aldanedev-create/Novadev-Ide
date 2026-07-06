<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  Boxes,
  Braces,
  Columns3,
  Code2,
  Copy,
  Download,
  FileCode2,
  Keyboard,
  Layers3,
  MonitorPlay,
  Moon,
  Play,
  RotateCcw,
  Rows3,
  Save,
  Settings,
  Share2,
  Sparkles,
  Sun,
  Terminal,
} from "lucide-vue-next";
import { buildUi, createShare, getAst, getTokens, runNova } from "./api";
import { examples, starterCode } from "./examples";

const code = ref(starterCode);
const activeExample = ref(examples[0].id);
const activePanel = ref("output");
const output = ref("");
const tokenRows = ref([]);
const astText = ref("");
const preview = ref(null);
const running = ref(false);
const status = ref("Ready");
const shareMessage = ref("");
const fileName = ref("main.nova");
const savedAt = ref("");
const dirty = ref(false);
const showSettings = ref(false);
const layoutMode = ref("horizontal");
const themeMode = ref("dark");
const fontSize = ref(14);
const wrapLines = ref(true);
const shellInput = ref("");
const shellSource = ref("");
const shellLines = ref([
  { kind: "system", text: "NovaDev browser shell uses safe session replay on Vercel." },
]);
const previousShellOutput = ref("");

const currentExample = computed(() => examples.find((item) => item.id === activeExample.value) || examples[0]);

const editorStyle = computed(() => ({
  fontSize: `${fontSize.value}px`,
}));

const codeStats = computed(() => {
  const lines = code.value ? code.value.split(/\r?\n/).length : 0;
  const bytes = new Blob([code.value]).size;
  return `${lines} lines / ${bytes.toLocaleString()} bytes`;
});

const problemsCount = computed(() => (output.value.trim().startsWith("error:") ? 1 : 0));

const panelTitle = computed(() => {
  const titles = {
    output: "Terminal",
    problems: "Problems",
    tokens: "Lexer Tokens",
    ast: "AST Inspector",
    preview: "Generated UI Preview",
    shell: "Browser Shell",
  };
  return titles[activePanel.value] || "Output";
});

const previewSrcdoc = computed(() => {
  if (!preview.value) {
    return "";
  }
  const style = `<style>${preview.value.css || ""}</style>`;
  const script = `<${"script"}>${preview.value.js || ""}</${"script"}>`;
  return (preview.value.html || "")
    .replace('<link rel="stylesheet" href="style.css">', style)
    .replace(`<${"script"} defer src="app.js"></${"script"}>`, script);
});

function setPanel(panel) {
  activePanel.value = panel;
}

function setStatus(text) {
  status.value = text;
}

function loadExample(example) {
  activeExample.value = example.id;
  code.value = example.code;
  fileName.value = `${example.id}.nova`;
  output.value = "";
  tokenRows.value = [];
  astText.value = "";
  preview.value = null;
  shareMessage.value = "";
  setPanel("output");
  setStatus(`Loaded ${example.title}`);
}

function setLayout(mode) {
  layoutMode.value = mode;
  localStorage.setItem("novadev.ide.layout", mode);
}

function toggleTheme() {
  themeMode.value = themeMode.value === "dark" ? "light" : "dark";
  localStorage.setItem("novadev.ide.theme", themeMode.value);
}

function saveLocal() {
  localStorage.setItem(
    "novadev.ide.session",
    JSON.stringify({
      code: code.value,
      fileName: fileName.value,
      savedAt: new Date().toISOString(),
    }),
  );
  dirty.value = false;
  savedAt.value = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  setStatus("Saved in this browser");
}

function loadLocal() {
  const raw = localStorage.getItem("novadev.ide.session");
  if (!raw) {
    setStatus("No browser save found");
    return;
  }
  try {
    const session = JSON.parse(raw);
    code.value = session.code || starterCode;
    fileName.value = session.fileName || "main.nova";
    activeExample.value = "";
    dirty.value = false;
    savedAt.value = session.savedAt
      ? new Date(session.savedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      : "";
    setStatus("Loaded browser save");
  } catch {
    setStatus("Could not load browser save");
  }
}

function resetEditor() {
  const ok = window.confirm("Reset the current NovaDev file to the selected example?");
  if (!ok) {
    return;
  }
  loadExample(currentExample.value);
}

function downloadText(name, text, type = "text/plain") {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

function downloadCode() {
  downloadText(fileName.value || "main.nova", code.value, "text/plain");
  setStatus("Downloaded source file");
}

function downloadOutput() {
  downloadText("novadev-output.txt", output.value || "", "text/plain");
  setStatus("Downloaded output");
}

async function copyOutput() {
  await navigator.clipboard?.writeText(output.value || "");
  setStatus("Copied output");
}

function formatRunResult(result) {
  if (!result.ok) {
    return `error: ${result.error || "NovaDev failed"}`;
  }
  const text = result.output || "";
  if (text.trim()) {
    return text.trimEnd();
  }
  if (result.lastValue !== null && result.lastValue !== undefined) {
    return String(result.lastValue);
  }
  return "Program finished with no output.";
}

async function runCode() {
  running.value = true;
  setStatus("Running NovaDev safely...");
  setPanel("output");
  try {
    const result = await runNova(code.value);
    output.value = formatRunResult(result);
    setStatus(result.ok ? "Run complete" : "Run failed");
  } catch (error) {
    output.value = `error: ${error.message}`;
    setStatus("Run failed");
  } finally {
    running.value = false;
  }
}

async function inspectTokens() {
  running.value = true;
  setStatus("Tokenizing source...");
  setPanel("tokens");
  try {
    const result = await getTokens(code.value);
    if (result.ok) {
      tokenRows.value = result.tokens;
      setStatus(`Lexer produced ${result.tokens.length} tokens`);
    } else {
      tokenRows.value = [];
      output.value = `error: ${result.error}`;
      setPanel("output");
      setStatus("Tokenize failed");
    }
  } finally {
    running.value = false;
  }
}

async function inspectAst() {
  running.value = true;
  setStatus("Parsing AST...");
  setPanel("ast");
  try {
    const result = await getAst(code.value);
    if (result.ok) {
      astText.value = JSON.stringify(result.ast, null, 2);
      setStatus("AST ready");
    } else {
      astText.value = "";
      output.value = `error: ${result.error}`;
      setPanel("output");
      setStatus("AST failed");
    }
  } finally {
    running.value = false;
  }
}

async function buildPreview() {
  running.value = true;
  setStatus("Building UI preview...");
  setPanel("preview");
  try {
    const result = await buildUi(code.value);
    if (result.ok) {
      preview.value = result.files;
      setStatus("UI preview built");
    } else {
      preview.value = null;
      output.value = `error: ${result.error}`;
      setPanel("output");
      setStatus("Preview failed");
    }
  } finally {
    running.value = false;
  }
}

function fallbackShareUrl() {
  const encoded = btoa(unescape(encodeURIComponent(code.value)))
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
  return `${window.location.origin}${window.location.pathname}#code=${encoded}`;
}

async function shareCode() {
  setStatus("Creating share URL...");
  shareMessage.value = "";
  let url = fallbackShareUrl();
  try {
    const result = await createShare(code.value);
    if (result.ok && result.url) {
      url = result.url;
    }
  } catch {
    // The hash fallback still works when the Node share function is unavailable locally.
  }

  await navigator.clipboard?.writeText(url);
  shareMessage.value = "Share URL copied to clipboard.";
  setStatus("Share URL ready");
}

function handleShortcut(event) {
  const key = event.key.toLowerCase();
  if (event.key === "F8" || (event.ctrlKey && key === "enter")) {
    event.preventDefault();
    runCode();
  } else if (event.key === "F9" || (event.ctrlKey && key === "h")) {
    event.preventDefault();
    shareCode();
  } else if (event.key === "F10" || (event.ctrlKey && key === "s")) {
    event.preventDefault();
    saveLocal();
  }
}

async function runShellLine() {
  const line = shellInput.value.trim();
  if (!line) {
    return;
  }
  shellInput.value = "";
  shellLines.value.push({ kind: "prompt", text: `nova> ${line}` });

  if (line === ".clear") {
    shellSource.value = "";
    previousShellOutput.value = "";
    shellLines.value = [{ kind: "system", text: "Shell cleared." }];
    return;
  }

  if (line === ".load-editor") {
    shellSource.value = code.value;
    previousShellOutput.value = "";
    shellLines.value.push({ kind: "system", text: "Loaded editor code into shell session." });
    return;
  }

  const nextSource = `${shellSource.value}\n${line}`.trim();
  const result = await runNova(nextSource);

  if (!result.ok) {
    shellLines.value.push({ kind: "error", text: result.error || "NovaDev shell failed" });
    return;
  }

  shellSource.value = nextSource;
  const nextOutput = (result.output || "").trimEnd();
  let display = "";
  if (nextOutput && nextOutput.startsWith(previousShellOutput.value)) {
    display = nextOutput.slice(previousShellOutput.value.length).trim();
  } else {
    display = nextOutput.trim();
  }
  previousShellOutput.value = nextOutput;

  if (!display && result.lastValue !== null && result.lastValue !== undefined) {
    display = String(result.lastValue);
  }
  if (display) {
    shellLines.value.push({ kind: "output", text: display });
  }
}

function resetShell() {
  shellInput.value = "";
  shellSource.value = "";
  previousShellOutput.value = "";
  shellLines.value = [{ kind: "system", text: "NovaDev browser shell reset." }];
}

function decodeSharedCode() {
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const encoded = hash.get("code");
  if (!encoded) {
    return;
  }
  try {
    const padded = encoded.padEnd(encoded.length + ((4 - (encoded.length % 4)) % 4), "=");
    const normalized = padded.replaceAll("-", "+").replaceAll("_", "/");
    code.value = decodeURIComponent(escape(atob(normalized)));
    activeExample.value = "";
    setStatus("Loaded shared code");
  } catch {
    setStatus("Could not load shared code");
  }
}

onMounted(decodeSharedCode);

watch(code, () => {
  dirty.value = true;
  localStorage.setItem(
    "novadev.ide.autosave",
    JSON.stringify({
      code: code.value,
      fileName: fileName.value,
    }),
  );
});

onMounted(() => {
  const savedTheme = localStorage.getItem("novadev.ide.theme");
  const savedLayout = localStorage.getItem("novadev.ide.layout");
  if (savedTheme === "light" || savedTheme === "dark") {
    themeMode.value = savedTheme;
  }
  if (savedLayout === "vertical" || savedLayout === "horizontal") {
    layoutMode.value = savedLayout;
  }
  window.addEventListener("keydown", handleShortcut);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleShortcut);
});
</script>

<template>
  <main class="ide-shell" :class="[`theme-${themeMode}`, `layout-${layoutMode}`]">
    <aside class="sidebar">
      <a class="brand" href="/" aria-label="NovaDev IDE">
        <span class="brand-mark">ND</span>
        <span>
          <strong>NovaDev IDE</strong>
          <small>Vercel online runner</small>
        </span>
      </a>

      <section class="phase-list" aria-label="Build phases">
        <div class="phase-card">
          <span><Play :size="16" /> Phase 1</span>
          <p>Run safe NovaDev code, inspect tokens, and inspect AST.</p>
        </div>
        <div class="phase-card">
          <span><MonitorPlay :size="16" /> Phase 2</span>
          <p>Build UI previews and share source through encoded URLs.</p>
        </div>
        <div class="phase-card">
          <span><Terminal :size="16" /> Phase 3</span>
          <p>Browser shell replay designed for Vercel serverless limits.</p>
        </div>
      </section>

      <section class="examples">
        <div class="sidebar-heading">
          <span>Examples</span>
          <Sparkles :size="16" />
        </div>
        <button
          v-for="example in examples"
          :key="example.id"
          class="example-button"
          :class="{ active: activeExample === example.id }"
          type="button"
          @click="loadExample(example)"
        >
          <strong>{{ example.title }}</strong>
          <small>{{ example.phase }}</small>
        </button>
      </section>

      <section v-if="showSettings" class="settings-card">
        <div class="sidebar-heading">
          <span>Editor Settings</span>
          <Keyboard :size="16" />
        </div>
        <label>
          <span>Font size</span>
          <input v-model.number="fontSize" type="range" min="12" max="22" />
          <strong>{{ fontSize }}px</strong>
        </label>
        <label class="toggle-row">
          <span>Line wrap</span>
          <input v-model="wrapLines" type="checkbox" />
        </label>
        <div class="shortcut-list">
          <span>Ctrl + Enter / F8 Run</span>
          <span>Ctrl + S / F10 Save</span>
          <span>Ctrl + H / F9 Share</span>
        </div>
      </section>
    </aside>

    <section class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">Safe NovaDev Online</p>
          <h1>Write, Run, Inspect, Preview</h1>
        </div>
        <div class="topbar-actions">
          <button type="button" title="Toggle theme" @click="toggleTheme">
            <Sun v-if="themeMode === 'dark'" :size="17" />
            <Moon v-else :size="17" />
            {{ themeMode === "dark" ? "Light" : "Dark" }}
          </button>
          <button type="button" title="Horizontal layout" :class="{ active: layoutMode === 'horizontal' }" @click="setLayout('horizontal')">
            <Columns3 :size="17" /> Split
          </button>
          <button type="button" title="Vertical layout" :class="{ active: layoutMode === 'vertical' }" @click="setLayout('vertical')">
            <Rows3 :size="17" /> Stack
          </button>
          <button type="button" title="Editor settings" @click="showSettings = !showSettings">
            <Settings :size="17" /> Settings
          </button>
          <div class="status-pill" aria-live="polite">{{ status }}</div>
        </div>
      </header>

      <section class="editor-region" :class="{ stacked: layoutMode === 'vertical' }">
        <div class="editor-panel">
          <div class="file-tabs">
            <button class="file-tab active" type="button">
              <FileCode2 :size="16" />
              <input v-model="fileName" aria-label="Current NovaDev file name" />
              <span v-if="dirty" class="dirty-dot" title="Unsaved changes" />
            </button>
            <span class="file-meta">{{ codeStats }}</span>
          </div>

          <div class="editor-header">
            <div>
              <p>{{ currentExample.phase || "Custom" }}</p>
              <h2>{{ currentExample.title || "Custom NovaDev File" }}</h2>
            </div>
            <div class="editor-header-actions">
              <button class="icon-button" type="button" title="Save in this browser" @click="saveLocal">
                <Save :size="18" />
              </button>
              <button class="icon-button" type="button" title="Download source file" @click="downloadCode">
                <Download :size="18" />
              </button>
              <button class="icon-button" type="button" title="Reset to current example" @click="resetEditor">
                <RotateCcw :size="18" />
              </button>
            </div>
          </div>

          <textarea
            v-model="code"
            class="code-editor"
            spellcheck="false"
            aria-label="NovaDev code editor"
            :style="editorStyle"
            :wrap="wrapLines ? 'soft' : 'off'"
          />

          <div class="toolbar">
            <button class="primary" type="button" :disabled="running" @click="runCode">
              <Play :size="17" /> Run
            </button>
            <button type="button" :disabled="running" @click="inspectTokens">
              <Boxes :size="17" /> Tokens
            </button>
            <button type="button" :disabled="running" @click="inspectAst">
              <Braces :size="17" /> AST
            </button>
            <button type="button" :disabled="running" @click="buildPreview">
              <MonitorPlay :size="17" /> Build UI
            </button>
            <button type="button" @click="shareCode">
              <Share2 :size="17" /> Share
            </button>
            <button type="button" @click="saveLocal">
              <Save :size="17" /> Save
            </button>
            <button type="button" @click="loadLocal">
              <RotateCcw :size="17" /> Load Save
            </button>
            <button type="button" @click="downloadCode">
              <Download :size="17" /> Download
            </button>
          </div>
          <p class="share-message">
            <Copy :size="14" />
            {{ shareMessage || (savedAt ? `Last browser save ${savedAt}` : "Autosaves in this browser while you type.") }}
          </p>
        </div>

        <div class="result-panel">
          <nav class="tabs" aria-label="Output panels">
            <button :class="{ active: activePanel === 'output' }" type="button" @click="setPanel('output')">
              <Terminal :size="16" /> Output
            </button>
            <button :class="{ active: activePanel === 'problems' }" type="button" @click="setPanel('problems')">
              <Sparkles :size="16" /> Problems {{ problemsCount }}
            </button>
            <button :class="{ active: activePanel === 'tokens' }" type="button" @click="setPanel('tokens')">
              <Boxes :size="16" /> Tokens
            </button>
            <button :class="{ active: activePanel === 'ast' }" type="button" @click="setPanel('ast')">
              <Braces :size="16" /> AST
            </button>
            <button :class="{ active: activePanel === 'preview' }" type="button" @click="setPanel('preview')">
              <MonitorPlay :size="16" /> Preview
            </button>
            <button :class="{ active: activePanel === 'shell' }" type="button" @click="setPanel('shell')">
              <Code2 :size="16" /> Shell
            </button>
          </nav>

          <div class="result-header">
            <strong>{{ panelTitle }}</strong>
            <div class="result-actions">
              <button type="button" @click="copyOutput"><Copy :size="15" /> Copy</button>
              <button type="button" @click="downloadOutput"><Download :size="15" /> Download</button>
            </div>
          </div>

          <section v-if="activePanel === 'output'" class="panel-body">
            <pre class="terminal-output">{{ output || "Run NovaDev code to see output here." }}</pre>
          </section>

          <section v-else-if="activePanel === 'problems'" class="panel-body">
            <div v-if="problemsCount" class="problem-card">
              <strong>Runtime or syntax issue</strong>
              <pre>{{ output }}</pre>
            </div>
            <div v-else class="empty-state">
              <Sparkles :size="28" />
              <p>No problems detected from the last run.</p>
            </div>
          </section>

          <section v-else-if="activePanel === 'tokens'" class="panel-body">
            <table v-if="tokenRows.length" class="token-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Value</th>
                  <th>Line</th>
                  <th>Column</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(token, index) in tokenRows" :key="`${token.type}-${index}`">
                  <td>{{ token.type }}</td>
                  <td>{{ token.value }}</td>
                  <td>{{ token.line }}</td>
                  <td>{{ token.column }}</td>
                </tr>
              </tbody>
            </table>
            <p v-else class="empty-state">Tokenize source to inspect lexer output.</p>
          </section>

          <section v-else-if="activePanel === 'ast'" class="panel-body">
            <pre class="json-output">{{ astText || "Parse source to inspect the AST." }}</pre>
          </section>

          <section v-else-if="activePanel === 'preview'" class="panel-body preview-body">
            <iframe
              v-if="previewSrcdoc"
              class="preview-frame"
              title="NovaDev generated UI preview"
              sandbox="allow-scripts"
              :srcdoc="previewSrcdoc"
            />
            <div v-else class="empty-state">
              <FileCode2 :size="28" />
              <p>Build UI from an app/page/table example to preview generated files.</p>
            </div>
          </section>

          <section v-else class="panel-body shell-body">
            <div class="shell-log">
              <p
                v-for="(line, index) in shellLines"
                :key="index"
                :class="['shell-line', line.kind]"
              >
                {{ line.text }}
              </p>
            </div>
            <form class="shell-form" @submit.prevent="runShellLine">
              <span>nova&gt;</span>
              <input
                v-model="shellInput"
                autocomplete="off"
                spellcheck="false"
                placeholder='let name = "Aldane"'
                aria-label="NovaDev shell input"
              />
              <button type="submit"><Play :size="16" /> Enter</button>
              <button type="button" @click="resetShell"><RotateCcw :size="16" /> Clear</button>
            </form>
          </section>
        </div>
      </section>

      <section class="details-band">
        <article>
          <Layers3 :size="22" />
          <h3>Vercel Fit</h3>
          <p>Each run is a short Python function request. There is no Docker container and no permanent process.</p>
        </article>
        <article>
          <Terminal :size="22" />
          <h3>Safe Runner</h3>
          <p>Code size, output size, timeout, and unsafe Python bridge checks are enforced before execution.</p>
        </article>
        <article>
          <Share2 :size="22" />
          <h3>Shareable</h3>
          <p>Source code can be encoded into a URL, so examples can be shared without a database.</p>
        </article>
      </section>
    </section>
  </main>
</template>
