<script setup>
import { ArrowLeft, ArrowRight, Check, Circle, FolderKanban } from "lucide-vue-next";

defineProps({
  track: { type: Object, required: true },
  lessons: { type: Array, default: () => [] },
  completedIds: { type: Array, default: () => [] },
});

defineEmits(["back", "open-lesson", "projects"]);
</script>

<template>
  <section class="page course-page">
    <header class="course-header">
      <button type="button" class="text-command" @click="$emit('back')"><ArrowLeft :size="15" /> Curriculum</button>
      <div class="course-number">Track {{ track.order }}</div>
      <h1>{{ track.title }}</h1>
      <p>{{ track.summary }}</p>
      <div class="course-meta">
        <span>{{ track.level }}</span><span>{{ track.hours }} estimated hours</span><span>{{ track.credential }}</span>
      </div>
    </header>

    <div class="course-layout">
      <main class="course-lessons">
        <div class="section-heading">
          <div><span>Required lessons</span><h2>Complete in order</h2></div>
          <strong>{{ lessons.filter((lesson) => completedIds.includes(lesson.id)).length }}/{{ lessons.length }}</strong>
        </div>
        <button
          v-for="(lesson, index) in lessons"
          :key="lesson.id"
          type="button"
          class="course-lesson-row"
          @click="$emit('open-lesson', lesson.id)"
        >
          <Check v-if="completedIds.includes(lesson.id)" :size="18" class="complete-icon" />
          <Circle v-else :size="18" />
          <span class="lesson-number">{{ String(index + 1).padStart(2, '0') }}</span>
          <span class="course-lesson-copy"><strong>{{ lesson.title }}</strong><small>{{ lesson.summary }}</small></span>
          <ArrowRight :size="17" />
        </button>
      </main>

      <aside class="course-projects">
        <FolderKanban :size="24" />
        <span>Applied projects</span>
        <h2>Prove the track with working code</h2>
        <ul>
          <li v-for="project in track.projects" :key="project">{{ project }}</li>
        </ul>
        <button type="button" class="toolbar-button" @click="$emit('projects')">Open project requirements</button>
      </aside>
    </div>
  </section>
</template>

