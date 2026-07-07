<script setup>
import { RotateCcw, Send, TerminalSquare, Upload } from "lucide-vue-next";

defineProps({
  input: { type: String, default: "" },
  lines: { type: Array, default: () => [] },
});

const emit = defineEmits(["update:input", "submit", "reset", "load-editor"]);

function submit() {
  emit("submit");
}
</script>

<template>
  <section class="page shell-page">
    <div class="page-toolbar">
      <div>
        <strong>Nova Shell</strong>
        <span>Run one line at a time, just like <code>python shell.py</code>.</span>
      </div>
      <div class="toolbar-actions">
        <button type="button" class="toolbar-button" @click="$emit('load-editor')">
          <Upload :size="16" />
          Use Editor Code
        </button>
        <button type="button" class="toolbar-button" @click="$emit('reset')">
          <RotateCcw :size="16" />
          Reset
        </button>
      </div>
    </div>

    <div class="shell-layout">
      <div class="shell-window" aria-live="polite">
        <div class="shell-banner">
          <TerminalSquare :size="18" />
          NovaDev 1.x Online Shell
        </div>
        <div v-for="(line, index) in lines" :key="index" class="shell-line" :class="line.kind">
          <span v-if="line.kind === 'input'" class="prompt">nova&gt;</span>
          <span>{{ line.text }}</span>
        </div>
      </div>

      <form class="shell-entry" @submit.prevent="submit">
        <span>nova&gt;</span>
        <input
          :value="input"
          type="text"
          autocomplete="off"
          spellcheck="false"
          placeholder='print("Hello NovaDev")'
          @input="$emit('update:input', $event.target.value)"
        />
        <button type="submit" class="icon-button" title="Run shell line" aria-label="Run shell line">
          <Send :size="17" />
        </button>
      </form>
    </div>
  </section>
</template>
