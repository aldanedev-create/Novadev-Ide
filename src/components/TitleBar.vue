<script setup>
import { Boxes, Braces, Eye, Moon, Play, Settings, Sun } from "lucide-vue-next";

defineProps({
  route: { type: String, default: "learn" },
  running: { type: Boolean, default: false },
  themeMode: { type: String, default: "dark" },
});

defineEmits(["run", "build", "toggle-theme", "navigate"]);
</script>

<template>
  <header class="title-bar">
    <div class="brand-mark" aria-label="NovaDev">ND</div>
    <div class="title-copy">
      <strong>NovaDev IDE</strong>
      <span>Learn, code, run, inspect, and build UI in one workspace.</span>
    </div>
    <div class="title-actions">
      <button type="button" class="toolbar-button primary" :disabled="running" @click="$emit('run')">
        <Play :size="16" />
        Run
      </button>
      <button type="button" class="toolbar-button" :disabled="running" @click="$emit('build')">
        <Eye :size="16" />
        Build UI
      </button>
      <button type="button" class="icon-button" title="Inspect tokens" aria-label="Inspect tokens" @click="$emit('navigate', 'tokens')">
        <Boxes :size="18" />
      </button>
      <button type="button" class="icon-button" title="Inspect AST" aria-label="Inspect AST" @click="$emit('navigate', 'ast')">
        <Braces :size="18" />
      </button>
      <button type="button" class="icon-button" title="Settings" aria-label="Settings" @click="$emit('navigate', 'settings')">
        <Settings :size="18" />
      </button>
      <button type="button" class="icon-button" title="Toggle theme" aria-label="Toggle theme" @click="$emit('toggle-theme')">
        <Sun v-if="themeMode === 'dark'" :size="18" />
        <Moon v-else :size="18" />
      </button>
    </div>
  </header>
</template>
