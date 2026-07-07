<script setup>
import { FileCode2, Play } from "lucide-vue-next";

defineProps({
  examples: { type: Array, default: () => [] },
  selectedId: { type: String, default: "" },
});

defineEmits(["load", "select"]);
</script>

<template>
  <section class="page examples-page">
    <div class="page-toolbar">
      <div>
        <strong>Example Projects</strong>
        <span>Load complete NovaDev examples into the editor.</span>
      </div>
    </div>

    <div class="examples-grid">
      <article
        v-for="example in examples"
        :key="example.id"
        class="example-card"
        :class="{ active: example.id === selectedId }"
      >
        <div class="example-card-header">
          <FileCode2 :size="19" />
          <div>
            <strong>{{ example.title }}</strong>
            <span>{{ example.section }} · {{ example.level }}</span>
          </div>
        </div>
        <p>{{ example.summary }}</p>
        <div class="chip-list">
          <span v-for="concept in example.concepts" :key="concept">{{ concept }}</span>
        </div>
        <div class="example-actions">
          <button type="button" class="toolbar-button" @click="$emit('select', example.id)">Open Lesson</button>
          <button type="button" class="toolbar-button primary" @click="$emit('load', example)">
            <Play :size="15" />
            Load Code
          </button>
        </div>
      </article>
    </div>
  </section>
</template>
