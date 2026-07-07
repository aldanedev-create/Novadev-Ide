<script setup>
import { computed, ref } from "vue";
import { Code2, Eye, RefreshCw } from "lucide-vue-next";

const props = defineProps({
  preview: {
    type: Object,
    default: () => ({ html: "", css: "", js: "", document: "" }),
  },
  running: { type: Boolean, default: false },
});

defineEmits(["build"]);

const activeFile = ref("index.html");
const files = computed(() => ({
  "index.html": props.preview.html || "",
  "style.css": props.preview.css || "",
  "app.js": props.preview.js || "",
}));
</script>

<template>
  <section class="page preview-page">
    <div class="page-toolbar">
      <div>
        <strong>Build UI Preview</strong>
        <span>Advanced page for generated frontend output.</span>
      </div>
      <button type="button" class="toolbar-button primary" :disabled="running" @click="$emit('build')">
        <RefreshCw :size="16" />
        Rebuild
      </button>
    </div>

    <div v-if="preview.document" class="preview-layout">
      <section class="browser-preview">
        <div class="preview-title">
          <Eye :size="17" />
          Live preview
        </div>
        <iframe title="NovaDev generated UI preview" sandbox="allow-scripts" :srcdoc="preview.document"></iframe>
      </section>

      <section class="generated-files">
        <div class="generated-tabs">
          <button
            v-for="(_, name) in files"
            :key="name"
            type="button"
            :class="{ active: activeFile === name }"
            @click="activeFile = name"
          >
            {{ name }}
          </button>
        </div>
        <pre class="generated-code"><code>{{ files[activeFile] || "No generated code for this file yet." }}</code></pre>
      </section>
    </div>

    <div v-else class="empty-page">
      <Code2 :size="38" />
      <strong>No UI build yet</strong>
      <span>Click Build UI to generate a browser preview from the current NovaDev app.</span>
      <button type="button" class="toolbar-button primary" :disabled="running" @click="$emit('build')">
        <RefreshCw :size="16" />
        Build UI
      </button>
    </div>
  </section>
</template>
