<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import ActivityBar from "./components/ActivityBar.vue";
import ExplorerPanel from "./components/ExplorerPanel.vue";
import StatusBar from "./components/StatusBar.vue";
import TitleBar from "./components/TitleBar.vue";
import CourseView from "./views/CourseView.vue";
import CurriculumView from "./views/CurriculumView.vue";
import EditorView from "./views/EditorView.vue";
import ExamplesView from "./views/ExamplesView.vue";
import InspectView from "./views/InspectView.vue";
import LearningProjectsView from "./views/LearningProjectsView.vue";
import LessonChallengeView from "./views/LessonChallengeView.vue";
import OutputView from "./views/OutputView.vue";
import PreviewView from "./views/PreviewView.vue";
import SettingsView from "./views/SettingsView.vue";
import ShellView from "./views/ShellView.vue";
import { examples, lessons, starterCode } from "./data/lessons";
import {
  curriculumTracks,
  evaluateLessonSource,
  lessonsForTrack,
  localOnlyLessons,
  trackById,
  trackForLesson,
} from "./data/curriculum";

const toolRoutes = new Set(["editor", "preview", "output", "tokens", "ast", "shell", "examples", "settings"]);

function parseRoute(pathname) {
  const parts = pathname.split("/").filter(Boolean);
  if (!parts.length) return { route: "learn" };
  if (parts[0] === "learn" && parts.length === 1) return { route: "learn" };
  if (parts[0] === "learn" && parts.length === 2) return { route: "course", trackId: parts[1] };
  if (parts[0] === "learn" && parts.length >= 3) return { route: "lesson", trackId: parts[1], lessonId: parts[2] };
  if (parts[0] === "projects") return { route: "projects" };
  if (toolRoutes.has(parts[0])) return { route: parts[0] };
  return { route: "learn" };
}

function readProgress() {
  try {
    const value = JSON.parse(localStorage.getItem("nova-ide-progress-v2") || "[]");
    return Array.isArray(value) ? value.filter((id) => lessons.some((lesson) => lesson.id === id)) : [];
  } catch {
    return [];
  }
}

const initialRoute = parseRoute(window.location.pathname);
const initialLesson = lessons.find((lesson) => lesson.id === initialRoute.lessonId) || lessons[0];
const activeRoute = ref(initialRoute.route);
const selectedLessonId = ref(initialLesson?.id || "");
const activeTrackId = ref(initialRoute.trackId || trackForLesson(selectedLessonId.value).id);
const completedIds = ref(readProgress());
const code = ref(initialRoute.route === "lesson" ? initialLesson.code : starterCode);
const fileName = ref(initialRoute.route === "lesson" ? `${initialLesson.id}.nova` : "app.nova");
const output = ref([{ kind: "info", text: "Ready. Run NovaDev code or open a lesson." }]);
const challengeOutput = ref([]);
const challengeChecks = ref([]);
const tokens = ref([]);
const astText = ref("");
const preview = ref({ html: "", css: "", js: "", document: "", files: {} });
const running = ref(false);
const currentAction = ref("idle");
const sidePanelOpen = ref(true);
const fontSize = ref(15);
const wrapLines = ref(true);
const themeMode = ref(localStorage.getItem("nova-ide-theme") || "dark");
const shellInput = ref("");
const shellSource = ref("");
const shellLines = ref([{ kind: "info", text: "NovaDev 1.1 Interactive Shell. Type code below and press Enter." }]);
const shellOutputCount = ref(0);
const bookUrl = import.meta.env.VITE_NOVADEV_BOOK_URL || "/book.html";

const currentLesson = computed(() => lessons.find((lesson) => lesson.id === selectedLessonId.value) || lessons[0]);
const currentTrack = computed(() => trackById(activeTrackId.value || trackForLesson(currentLesson.value.id).id));
const currentTrackLessons = computed(() => lessonsForTrack(currentTrack.value, lessons));
const currentLessonIndex = computed(() => currentTrackLessons.value.findIndex((lesson) => lesson.id === currentLesson.value.id));
const lessonIsLocalOnly = computed(() => localOnlyLessons.has(currentLesson.value.id));
const lineCount = computed(() => code.value.split(/\r?\n/).length);
const visibleTabs = computed(() => {
  const tabs = [{ id: "learn", label: "curriculum" }];
  if (activeRoute.value === "course") tabs.push({ id: "course", label: "track" });
  if (activeRoute.value === "lesson") tabs.push({ id: "lesson", label: "challenge" });
  tabs.push(
    { id: "projects", label: "projects" },
    { id: "editor", label: "editor" },
    { id: "preview", label: "build UI" },
    { id: "output", label: "output" },
    { id: "shell", label: "shell" },
  );
  return tabs;
});
const statusText = computed(() => {
  if (running.value) return `Running ${currentAction.value}...`;
  if (activeRoute.value === "preview" && preview.value.document) return "UI preview built";
  if (activeRoute.value === "tokens") return `${tokens.value.length} tokens`;
  if (activeRoute.value === "lesson") return `${completedIds.value.length}/${lessons.length} lessons completed`;
  return "Ready";
});

function pushPath(path) {
  if (window.location.pathname !== path) window.history.pushState({}, "", path);
}

function navigate(route) {
  if (route === "course") return openTrack(activeTrackId.value);
  if (route === "lesson") return openLesson(selectedLessonId.value);
  activeRoute.value = route;
  const path = route === "learn" ? "/" : route === "projects" ? "/projects" : `/${route}`;
  pushPath(path);
}

function openTrack(id) {
  const track = trackById(id);
  activeTrackId.value = track.id;
  activeRoute.value = "course";
  pushPath(`/learn/${track.id}`);
}

function openLesson(id) {
  const lesson = lessons.find((item) => item.id === id);
  if (!lesson) return;
  const changed = selectedLessonId.value !== lesson.id;
  selectedLessonId.value = lesson.id;
  activeTrackId.value = trackForLesson(lesson.id).id;
  if (changed || !code.value.trim()) code.value = lesson.code;
  fileName.value = `${lesson.id}.nova`;
  challengeOutput.value = [];
  challengeChecks.value = [];
  activeRoute.value = "lesson";
  pushPath(`/learn/${activeTrackId.value}/${lesson.id}`);
}

function continueLearning() {
  const next = lessons.find((lesson) => !completedIds.value.includes(lesson.id)) || lessons[0];
  openLesson(next.id);
}

function resetProgress() {
  if (!window.confirm("Reset all locally saved NovaDev curriculum progress?")) return;
  completedIds.value = [];
}

function loadLesson(lesson) {
  selectedLessonId.value = lesson.id;
  activeTrackId.value = trackForLesson(lesson.id).id;
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
  if (!response.ok || data.ok === false) throw new Error(data.error || data.errors?.join("\n") || `Request failed: ${response.status}`);
  return data;
}

function showApiError(error) {
  output.value = [{ kind: "error", text: error.message || String(error) }];
  navigate("output");
}

async function executeCode(navigateToOutput = true) {
  setRunning("program", true);
  try {
    const data = await callApi("run");
    const lines = asLines(data.output);
    const result = lines.length ? lines.map((text) => ({ kind: "output", text })) : [{ kind: "info", text: `Program finished. Last value: ${data.lastValue ?? "nil"}` }];
    if (navigateToOutput) {
      output.value = result;
      navigate("output");
    } else {
      challengeOutput.value = result;
    }
    return true;
  } catch (error) {
    const result = [{ kind: "error", text: error.message || String(error) }];
    if (navigateToOutput) {
      output.value = result;
      navigate("output");
    } else {
      challengeOutput.value = result;
    }
    return false;
  } finally {
    setRunning("program", false);
  }
}

async function runCode() {
  return executeCode(true);
}

async function runChallenge() {
  return executeCode(false);
}

async function checkChallenge() {
  setRunning("lesson checks", true);
  try {
    let runtimePassed = true;
    if (!lessonIsLocalOnly.value) {
      try {
        const data = await callApi("run");
        const lines = asLines(data.output);
        challengeOutput.value = lines.length ? lines.map((text) => ({ kind: "output", text })) : [{ kind: "info", text: "NovaDev parsed and ran the solution." }];
      } catch (error) {
        runtimePassed = false;
        challengeOutput.value = [{ kind: "error", text: error.message || String(error) }];
      }
    }
    const checks = evaluateLessonSource(currentLesson.value.id, code.value);
    if (!lessonIsLocalOnly.value) checks.unshift({ label: "Program parses and runs", passed: runtimePassed });
    challengeChecks.value = checks;
    if (checks.every((check) => check.passed)) {
      completedIds.value = [...new Set([...completedIds.value, currentLesson.value.id])];
      challengeOutput.value.push({ kind: "success", text: "Lesson complete. Progress saved in this browser." });
    }
  } finally {
    setRunning("lesson checks", false);
  }
}

function openAdjacent(direction) {
  const index = currentLessonIndex.value + direction;
  const lesson = currentTrackLessons.value[index];
  if (lesson) openLesson(lesson.id);
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
  setRunning("UI build", true);
  try {
    const data = await callApi("build-ui");
    const files = data.files || {};
    preview.value = {
      html: files["index.html"] || "",
      css: files["style.css"] || "",
      js: files["app.js"] || "",
      document: data.previewHtml || files["index.html"] || "",
      files,
    };
    output.value = [{ kind: "info", text: `Generated ${Object.keys(files).length} frontend files from the current NovaDev source.` }];
    navigate("preview");
  } catch (error) {
    showApiError(error);
  } finally {
    setRunning("UI build", false);
  }
}

async function runShellLine() {
  const line = shellInput.value.trim();
  if (!line) return;
  shellLines.value.push({ kind: "input", text: line });
  shellInput.value = "";
  if (line === ".clear") return resetShell();
  shellSource.value = `${shellSource.value}${line}\n`;
  setRunning("shell", true);
  try {
    const data = await callApi("run", { code: shellSource.value, fileName: "shell.nova" });
    const lines = asLines(data.output);
    const newLines = lines.slice(shellOutputCount.value);
    shellOutputCount.value = lines.length;
    newLines.forEach((text) => shellLines.value.push({ kind: "output", text }));
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
    return navigate("output");
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

function applyBrowserRoute() {
  const state = parseRoute(window.location.pathname);
  activeRoute.value = state.route;
  if (state.trackId) activeTrackId.value = trackById(state.trackId).id;
  if (state.lessonId && lessons.some((lesson) => lesson.id === state.lessonId)) {
    selectedLessonId.value = state.lessonId;
    activeTrackId.value = trackForLesson(state.lessonId).id;
  }
}

function handleKeydown(event) {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    activeRoute.value === "lesson" ? runChallenge() : runCode();
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
  window.addEventListener("popstate", applyBrowserRoute);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
  window.removeEventListener("popstate", applyBrowserRoute);
});

watch(themeMode, (value) => localStorage.setItem("nova-ide-theme", value));
watch(completedIds, (value) => localStorage.setItem("nova-ide-progress-v2", JSON.stringify(value)), { deep: true });
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
        :tracks="curriculumTracks"
        :lessons="lessons"
        :active-track-id="activeTrackId"
        :active-route="activeRoute"
        :selected-lesson-id="selectedLessonId"
        :completed-ids="completedIds"
        @navigate="navigate"
        @open-track="openTrack"
        @open-lesson="openLesson"
        @load-lesson="loadLesson"
      />

      <section class="editor-shell">
        <div class="tab-row" role="tablist" aria-label="Open Nova IDE pages">
          <button v-for="tab in visibleTabs" :key="tab.id" type="button" :class="{ active: activeRoute === tab.id }" @click="navigate(tab.id)">
            {{ tab.label }}
          </button>
          <a class="book-tab" :href="bookUrl" target="_blank" rel="noreferrer">book</a>
        </div>

        <CurriculumView
          v-if="activeRoute === 'learn'"
          :tracks="curriculumTracks"
          :lessons="lessons"
          :completed-ids="completedIds"
          @open-track="openTrack"
          @continue="continueLearning"
          @projects="navigate('projects')"
          @reset-progress="resetProgress"
        />
        <CourseView
          v-else-if="activeRoute === 'course'"
          :track="currentTrack"
          :lessons="currentTrackLessons"
          :completed-ids="completedIds"
          @back="navigate('learn')"
          @open-lesson="openLesson"
          @projects="navigate('projects')"
        />
        <LessonChallengeView
          v-else-if="activeRoute === 'lesson'"
          v-model:code="code"
          :lesson="currentLesson"
          :track="currentTrack"
          :output="challengeOutput"
          :checks="challengeChecks"
          :completed="completedIds.includes(currentLesson.id)"
          :running="running"
          :local-only="lessonIsLocalOnly"
          :has-previous="currentLessonIndex > 0"
          :has-next="currentLessonIndex >= 0 && currentLessonIndex < currentTrackLessons.length - 1"
          @back="openTrack(currentTrack.id)"
          @run="runChallenge"
          @check="checkChallenge"
          @editor="loadLesson(currentLesson)"
          @previous="openAdjacent(-1)"
          @next="openAdjacent(1)"
        />
        <LearningProjectsView
          v-else-if="activeRoute === 'projects'"
          :tracks="curriculumTracks"
          :lessons="lessons"
          :completed-ids="completedIds"
          @back="navigate('learn')"
          @open-lesson="openLesson"
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
        <PreviewView v-else-if="activeRoute === 'preview'" :preview="preview" :running="running" @build="buildPreview" />
        <OutputView v-else-if="activeRoute === 'output'" :lines="output" :running="running" :current-action="currentAction" @run="runCode" />
        <InspectView v-else-if="activeRoute === 'tokens'" kind="tokens" :tokens="tokens" :running="running" @refresh="inspectTokens" />
        <InspectView v-else-if="activeRoute === 'ast'" kind="ast" :ast-text="astText" :running="running" @refresh="inspectAst" />
        <ShellView
          v-else-if="activeRoute === 'shell'"
          v-model:input="shellInput"
          :lines="shellLines"
          @submit="runShellLine"
          @reset="resetShell"
          @load-editor="shellSource = code"
        />
        <ExamplesView v-else-if="activeRoute === 'examples'" :examples="examples" :selected-id="selectedLessonId" @select="openLesson" @load="loadLesson" />
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

    <StatusBar :status="statusText" :file-name="fileName" :route="activeRoute" :line-count="lineCount" :theme-mode="themeMode" />
  </div>
</template>
