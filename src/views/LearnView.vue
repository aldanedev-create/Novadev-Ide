<script setup>
import { ArrowRight, BookOpen, Play } from "lucide-vue-next";

defineProps({
  lessons: { type: Array, default: () => [] },
  selectedId: { type: String, default: "" },
});

defineEmits(["select", "load"]);
</script>

<template>
  <section class="page learn-page">
    <aside class="lesson-index">
      <div class="lesson-index-title">
        <BookOpen :size="18" />
        <strong>Course</strong>
      </div>
      <button
        v-for="lesson in lessons"
        :key="lesson.id"
        type="button"
        class="lesson-index-row"
        :class="{ active: selectedId === lesson.id }"
        @click="$emit('select', lesson.id)"
      >
        <span>{{ lesson.title }}</span>
        <small>{{ lesson.section }}</small>
      </button>
    </aside>

    <article v-for="lesson in lessons" v-show="lesson.id === selectedId" :key="lesson.id" class="lesson-content">
      <header class="lesson-hero">
        <span>{{ lesson.section }} · {{ lesson.level }}</span>
        <h1>{{ lesson.title }}</h1>
        <p>{{ lesson.summary }}</p>
        <button type="button" class="toolbar-button primary" @click="$emit('load', lesson)">
          <Play :size="16" />
          Open in Editor
        </button>
      </header>

      <section class="lesson-section">
        <h2>What You Learn</h2>
        <div class="chip-list">
          <span v-for="concept in lesson.concepts" :key="concept">{{ concept }}</span>
        </div>
      </section>

      <section v-if="lesson.outcomes?.length" class="lesson-section">
        <h2>Developer Outcomes</h2>
        <ul class="lesson-list">
          <li v-for="outcome in lesson.outcomes" :key="outcome">{{ outcome }}</li>
        </ul>
      </section>

      <section v-if="lesson.explanation" class="lesson-section lesson-explanation">
        <h2>Explanation</h2>
        <p>{{ lesson.explanation }}</p>
      </section>

      <section class="lesson-section two-column">
        <div>
          <h2>Example Code</h2>
          <pre class="code-sample"><code>{{ lesson.code }}</code></pre>
        </div>
        <div>
          <h2>Practice</h2>
          <p>{{ lesson.exercise }}</p>
          <button type="button" class="toolbar-button" @click="$emit('load', lesson)">
            Try It
            <ArrowRight :size="16" />
          </button>
        </div>
      </section>

      <section v-if="lesson.projectUse" class="lesson-section lesson-explanation">
        <h2>Where Developers Use This</h2>
        <p>{{ lesson.projectUse }}</p>
      </section>
    </article>
  </section>
</template>
