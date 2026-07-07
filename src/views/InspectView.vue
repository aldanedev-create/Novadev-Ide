<script setup>
import { Boxes, Braces } from "lucide-vue-next";

defineProps({
  kind: { type: String, required: true },
  tokens: { type: Array, default: () => [] },
  astText: { type: String, default: "" },
  running: { type: Boolean, default: false },
});

defineEmits(["refresh"]);
</script>

<template>
  <section class="page inspect-page">
    <div class="page-toolbar">
      <div>
        <strong>{{ kind === "tokens" ? "Lexer Tokens" : "AST Inspector" }}</strong>
        <span>{{ kind === "tokens" ? `${tokens.length} tokens` : "Parser output" }}</span>
      </div>
      <button type="button" class="toolbar-button primary" :disabled="running" @click="$emit('refresh')">
        <Boxes v-if="kind === 'tokens'" :size="16" />
        <Braces v-else :size="16" />
        Refresh
      </button>
    </div>

    <table v-if="kind === 'tokens' && tokens.length" class="token-table">
      <thead>
        <tr>
          <th>Type</th>
          <th>Value</th>
          <th>Line</th>
          <th>Column</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(token, index) in tokens" :key="`${token.type}-${index}`">
          <td>{{ token.type }}</td>
          <td>{{ token.value }}</td>
          <td>{{ token.line }}</td>
          <td>{{ token.column }}</td>
        </tr>
      </tbody>
    </table>

    <pre v-else-if="kind === 'ast'" class="terminal-output">{{ astText || "Parse source to inspect the AST." }}</pre>

    <div v-else class="empty-page">
      <Boxes v-if="kind === 'tokens'" :size="36" />
      <Braces v-else :size="36" />
      <strong>{{ kind === "tokens" ? "No tokens yet" : "No AST yet" }}</strong>
      <span>Run the inspector from the toolbar to see how NovaDev understands your code.</span>
      <button type="button" class="toolbar-button primary" @click="$emit('refresh')">Run Inspector</button>
    </div>
  </section>
</template>
