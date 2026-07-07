<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import ActivityBar from "./components/ActivityBar.vue";
import ExplorerPanel from "./components/ExplorerPanel.vue";
import StatusBar from "./components/StatusBar.vue";
import TitleBar from "./components/TitleBar.vue";
import EditorView from "./views/EditorView.vue";
import ExamplesView from "./views/ExamplesView.vue";
import InspectView from "./views/InspectView.vue";
import LearnView from "./views/LearnView.vue";
import OutputView from "./views/OutputView.vue";
import PreviewView from "./views/PreviewView.vue";
import SettingsView from "./views/SettingsView.vue";
import ShellView from "./views/ShellView.vue";
import { examples, lessons, starterCode } from "./data/lessons";

const routeIds = new Set(["learn", "editor", "preview", "output", "tokens", "ast", "shell", "examples", "settings"]);

function routeFromPath(pathname) {
  const clean = pathname.replace(/^\/+/, "").replace(/\/+$/, "");
  return routeIds.has(clean) ? clean : "learn";
}

const activeRoute = ref(routeFromPath(window.location.pathname));
const selectedLessonId = ref(lessons[0]?.id || "");
const code = ref(starterCode);
const fileName = ref("app.nova");
const output = ref([{ kind: "info", text: "Ready. Run NovaDev code or open a lesson." }]);
const tokens = ref([]);
const astText = ref("");
const preview = ref({ html: "", css: "", js: "", document: "" });
const running = ref(false);
const currentAction = ref("idle");
const sidePanelOpen = ref(true);
const fontSize = ref(15);
const wrapLines = ref(true);
const themeMode = ref(localStorage.getItem("nova-ide-theme") || "dark");
const shellInput = ref("");
const shellSource = ref("");
const shellLines = ref([{ kind: "info", text: "NovaDev 1.x Interactive Shell. Type code below and press Enter." }]);
const shellOutputCount = ref(0);

const currentLesson = computed(() => lessons.find((lesson) => lesson.id === selectedLessonId.value) || lessons[0]);
const lineCount = computed(() => code.value.split(/\r?\n/).length);
const statusText = computed(() => {
  if (running.value) return `Running ${currentAction.value}...`;
  if (activeRoute.value === "preview" && preview.value.document) return "UI preview built";
  if (activeRoute.value === "tokens") return `${tokens.value.length} tokens`;
  return "Ready";
});

function navigate(route) {
  activeRoute.value = route;
  const target = route === "learn" ? "/" : `/${route}`;
  if (window.location.pathname !== target) {
    window.history.pushState({}, "", target);
  }
}

function selectLesson(id) {
  selectedLessonId.value = id;
  navigate("learn");
}

function loadLesson(lesson) {
  selectedLessonId.value = lesson.id;
  fileName.value = `${lesson.id}.nova`;
  code.value = lesson.code;
  output.value = [{ kind: "info", text: `Loaded ${lesson.title}.` }];
  navigate("editor");
}

function setRunning(action, value) {
  currentAction.value = value ? action : "idle";
  running.value = value;
}

function asLines(data) {
  if (Array.isArray(data)) return data.map((line) => String(line));
  if (typeof data === "string") return data.split(/\r?\n/).filter(Boolean);
  return [];
}

async function callApi(endpoint, payload = {}) {
  const response = await fetch(`/api/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code: code.value, fileName: fileName.value, ...payload }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.ok === false) {
    const message = data.error || data.errors?.join("\n") || `Request failed: ${response.status}`;
    throw new Error(message);
  }
  return data;
}

function showApiError(error) {
  output.value = [{ kind: "error", text: error.message || String(error) }];
  navigate("output");
}

async function runCode() {
  setRunning("program", true);
  try {
    const data = await callApi("run");
    const lines = asLines(data.output);
    output.value = lines.length
      ? lines.map((text) => ({ kind: "output", text }))
      : [{ kind: "info", text: "Program finished with no printed output." }];
    navigate("output");
  } catch (error) {
    showApiError(error);
  } finally {
    setRunning("program", false);
  }
}

async function inspectTokens() {
  setRunning("lexer", true);
  try {
    const data = await callApi("tokens");
    tokens.value = data.tokens || [];
    navigate("tokens");
  } catch (error) {
    showApiError(error);
  } finally {
    setRunning("lexer", false);
  }
}

async function inspectAst() {
  setRunning("parser", true);
  try {
    const data = await callApi("ast");
    astText.value = typeof data.ast === "string" ? data.ast : JSON.stringify(data.ast, null, 2);
    navigate("ast");
  } catch (error) {
    showApiError(error);
  } finally {
    setRunning("parser", false);
  }
}

async function buildPreview() {
  setRunning("ui build", true);
  try {
    const data = await callApi("build-ui");
    const files = data.files || {};
    preview.value = {
      html: files["index.html"] || files.html || "",
      css: files["style.css"] || files.css || "",
      js: files["app.js"] || files.js || "",
      document: data.previewHtml || files["index.html"] || files.html || "",
    };
    output.value = [{ kind: "info", text: "UI preview generated from the current NovaDev source." }];
    navigate("preview");
  } catch (error) {
    showApiError(error);
  } finally {
    setRunning("ui build", false);
  }
}

async function runShellLine() {
  const line = shellInput.value.trim();
  if (!line) return;

  shellLines.value.push({ kind: "input", text: line });
  shellInput.value = "";

  if (line === ".clear") {
    resetShell();
    return;
  }

  shellSource.value = `${shellSource.value}${line}\n`;
  setRunning("shell", true);
  try {
    const data = await callApi("run", { code: shellSource.value, fileName: "shell.nova" });
    const lines = asLines(data.output);
    const newLines = lines.slice(shellOutputCount.value);
    shellOutputCount.value = lines.length;
    if (newLines.length) {
      newLines.forEach((text) => shellLines.value.push({ kind: "output", text }));
    }
  } catch (error) {
    shellLines.value.push({ kind: "error", text: error.message || String(error) });
  } finally {
    setRunning("shell", false);
  }
}

function resetShell() {
  shellSource.value = "";
  shellInput.value = "";
  shellOutputCount.value = 0;
  shellLines.value = [{ kind: "info", text: "Shell reset. Variables and functions were cleared." }];
}

function saveLocal() {
  localStorage.setItem("nova-ide-code", code.value);
  localStorage.setItem("nova-ide-file", fileName.value);
  output.value = [{ kind: "info", text: "Saved this NovaDev file in your browser." }];
}

function loadLocal() {
  const saved = localStorage.getItem("nova-ide-code");
  if (!saved) {
    output.value = [{ kind: "info", text: "No browser save was found." }];
    navigate("output");
    return;
  }
  code.value = saved;
  fileName.value = localStorage.getItem("nova-ide-file") || "app.nova";
  output.value = [{ kind: "info", text: "Loaded your browser save." }];
  navigate("editor");
}

async function shareCode() {
  const encoded = btoa(unescape(encodeURIComponent(code.value)));
  const url = `${window.location.origin}/editor?code=${encoded}`;
  await navigator.clipboard?.writeText(url);
  output.value = [{ kind: "info", text: "Share URL copied to clipboard." }];
}

function toggleTheme() {
  themeMode.value = themeMode.value === "dark" ? "light" : "dark";
}

function handleKeydown(event) {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    runCode();
  }
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "b") {
    event.preventDefault();
    buildPreview();
  }
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
    event.preventDefault();
    saveLocal();
  }
}

function handlePopstate() {
  activeRoute.value = routeFromPath(window.location.pathname);
}

onMounted(() => {
  const params = new URLSearchParams(window.location.search);
  const sharedCode = params.get("code");
  if (sharedCode) {
    try {
      code.value = decodeURIComponent(escape(atob(sharedCode)));
      fileName.value = "shared.nova";
      navigate("editor");
    } catch {
      output.value = [{ kind: "error", text: "Could not decode the shared NovaDev code." }];
      navigate("output");
    }
  }
  window.addEventListener("keydown", handleKeydown);
  window.addEventListener("popstate", handlePopstate);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
  window.removeEventListener("popstate", handlePopstate);
});

watch(themeMode, (value) => {
  localStorage.setItem("nova-ide-theme", value);
});
</script>

<template>
  <div class="nova-workbench" :class="themeMode">
    <TitleBar
      :route="activeRoute"
      :running="running"
      :theme-mode="themeMode"
      @run="runCode"
      @build="buildPreview"
      @toggle-theme="toggleTheme"
      @navigate="navigate"
    />

    <main class="workbench-body" :class="{ 'no-explorer': !sidePanelOpen }">
      <ActivityBar :active="activeRoute" @navigate="navigate" />
      <ExplorerPanel
        v-if="sidePanelOpen"
        :lessons="lessons"
        :active-route="activeRoute"
        :selected-lesson-id="selectedLessonId"
        @navigate="navigate"
        @select-lesson="selectLesson"
        @load-lesson="loadLesson"
      />

      <section class="editor-shell">
        <div class="tab-row" role="tablist" aria-label="Open Nova IDE pages">
          <button
            v-for="tab in ['learn', 'editor', 'preview', 'output', 'shell']"
            :key="tab"
            type="button"
            :class="{ active: activeRoute === tab }"
            @click="navigate(tab)"
          >
            {{ tab }}
          </button>
        </div>

        <LearnView
          v-if="activeRoute === 'learn'"
          :lessons="lessons"
          :selected-id="selectedLessonId"
          @select="selectLesson"
          @load="loadLesson"
        />
        <EditorView
          v-else-if="activeRoute === 'editor'"
          v-model:code="code"
          v-model:file-name="fileName"
          :running="running"
          :font-size="fontSize"
          :wrap-lines="wrapLines"
          @run="runCode"
          @tokens="inspectTokens"
          @ast="inspectAst"
          @preview="buildPreview"
          @save="saveLocal"
          @share="shareCode"
          @load-save="loadLocal"
        />
        <PreviewView
          v-else-if="activeRoute === 'preview'"
          :preview="preview"
          :running="running"
          @build="buildPreview"
        />
        <OutputView
          v-else-if="activeRoute === 'output'"
          :lines="output"
          :running="running"
          :current-action="currentAction"
          @run="runCode"
        />
        <InspectView
          v-else-if="activeRoute === 'tokens'"
          kind="tokens"
          :tokens="tokens"
          :running="running"
          @refresh="inspectTokens"
        />
        <InspectView
          v-else-if="activeRoute === 'ast'"
          kind="ast"
          :ast-text="astText"
          :running="running"
          @refresh="inspectAst"
        />
        <ShellView
          v-else-if="activeRoute === 'shell'"
          v-model:input="shellInput"
          :lines="shellLines"
          @submit="runShellLine"
          @reset="resetShell"
          @load-editor="shellSource = code"
        />
        <ExamplesView
          v-else-if="activeRoute === 'examples'"
          :examples="examples"
          :selected-id="selectedLessonId"
          @select="selectLesson"
          @load="loadLesson"
        />
        <SettingsView
          v-else
          v-model:font-size="fontSize"
          v-model:wrap-lines="wrapLines"
          v-model:side-panel-open="sidePanelOpen"
          :theme-mode="themeMode"
          @toggle-theme="toggleTheme"
          @save="saveLocal"
          @load-save="loadLocal"
        />
      </section>
    </main>

    <StatusBar
      :status="statusText"
      :file-name="fileName"
      :route="activeRoute"
      :line-count="lineCount"
      :theme-mode="themeMode"
    />
  </div>
</template>
