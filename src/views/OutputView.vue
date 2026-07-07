<script setup>
import { Play, TerminalSquare } from "lucide-vue-next";

defineProps({
  lines: { type: Array, default: () => [] },
  running: { type: Boolean, default: false },
  currentAction: { type: String, default: "idle" },
});

defineEmits(["run"]);
</script>

<template>
  <section class="page output-page">
    <div class="page-toolbar">
      <div>
        <strong>Program Output</strong>
        <span>{{ running ? `Running ${currentAction}` : "Terminal result from the last run." }}</span>
      </div>
      <button type="button" class="toolbar-button primary" :disabled="running" @click="$emit('run')">
        <Play :size="16" />
        Run Again
      </button>
    </div>

    <pre class="terminal-output"><code><span v-for="(line, index) in lines" :key="index" :class="line.kind">{{ line.text }}
</span></code></pre>

    <div v-if="!lines.length" class="empty-page">
      <TerminalSquare :size="36" />
      <strong>No output yet</strong>
      <span>Run code in the editor to see printed values and errors here.</span>
    </div>
  </section>
</template>
