<script setup>
import { Braces, Boxes, Eye, Play, Save, Share2, Wand2 } from "lucide-vue-next";
import CodeEditor from "../components/CodeEditor.vue";

defineProps({
  code: { type: String, default: "" },
  fileName: { type: String, default: "app.nova" },
  running: { type: Boolean, default: false },
  fontSize: { type: Number, default: 15 },
  wrapLines: { type: Boolean, default: true },
});

defineEmits([
  "update:code",
  "update:fileName",
  "run",
  "tokens",
  "ast",
  "preview",
  "save",
  "share",
  "load-save",
]);
</script>

<template>
  <section class="page editor-page">
    <div class="page-toolbar">
      <div class="file-title-group">
        <input
          class="file-name-input"
          :value="fileName"
          aria-label="Current NovaDev file name"
          @input="$emit('update:fileName', $event.target.value)"
        />
        <span>Write NovaDev, run it, inspect it, or build a UI preview.</span>
      </div>
      <div class="toolbar-actions">
        <button type="button" class="toolbar-button primary" :disabled="running" @click="$emit('run')">
          <Play :size="16" />
          Run
        </button>
        <button type="button" class="toolbar-button" :disabled="running" @click="$emit('preview')">
          <Eye :size="16" />
          Build UI
        </button>
      </div>
    </div>

    <div class="editor-workspace">
      <CodeEditor
        :model-value="code"
        :font-size="fontSize"
        :wrap-lines="wrapLines"
        @update:model-value="$emit('update:code', $event)"
      />

      <aside class="editor-tools" aria-label="Editor tools">
        <button type="button" class="tool-tile" :disabled="running" @click="$emit('run')">
          <Play :size="19" />
          <strong>Run Program</strong>
          <span>Execute prints, variables, functions, loops, and app metadata.</span>
        </button>
        <button type="button" class="tool-tile" :disabled="running" @click="$emit('tokens')">
          <Boxes :size="19" />
          <strong>Inspect Tokens</strong>
          <span>See lexer output for every keyword, number, string, and operator.</span>
        </button>
        <button type="button" class="tool-tile" :disabled="running" @click="$emit('ast')">
          <Braces :size="19" />
          <strong>Inspect AST</strong>
          <span>View parser output as structured syntax tree data.</span>
        </button>
        <button type="button" class="tool-tile" :disabled="running" @click="$emit('preview')">
          <Wand2 :size="19" />
          <strong>Build UI</strong>
          <span>Generate an admin-style preview from pages, tables, and components.</span>
        </button>
        <button type="button" class="tool-tile" @click="$emit('save')">
          <Save :size="19" />
          <strong>Save Browser Draft</strong>
          <span>Keep this code in local storage on this device.</span>
        </button>
        <button type="button" class="tool-tile" @click="$emit('share')">
          <Share2 :size="19" />
          <strong>Share URL</strong>
          <span>Copy a link with this code encoded into the page address.</span>
        </button>
      </aside>
    </div>
  </section>
</template>
