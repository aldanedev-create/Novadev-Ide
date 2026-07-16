<script setup>
import { ArrowRight, BookOpenCheck, FolderKanban, RotateCcw } from "lucide-vue-next";

const props = defineProps({
  tracks: { type: Array, default: () => [] },
  lessons: { type: Array, default: () => [] },
  completedIds: { type: Array, default: () => [] },
});

defineEmits(["open-track", "continue", "projects", "reset-progress"]);

function completedCount(track) {
  return track.lessonIds.filter((id) => props.completedIds.includes(id)).length;
}

function progress(track) {
  return track.lessonIds.length ? Math.round((completedCount(track) / track.lessonIds.length) * 100) : 0;
}
</script>

<template>
  <section class="page curriculum-page">
    <header class="curriculum-header">
      <div>
        <span class="section-kicker">NovaDev Developer Curriculum</span>
        <h1>Learn the language. Build complete applications.</h1>
        <p>Follow ten ordered tracks from first program to Vue/Vite, Express/Node, SQLite/Prisma, automation, professional development, and capstone work.</p>
      </div>
      <div class="curriculum-actions">
        <button type="button" class="toolbar-button primary" @click="$emit('continue')">
          Continue learning
          <ArrowRight :size="16" />
        </button>
        <button type="button" class="toolbar-button" @click="$emit('projects')">
          <FolderKanban :size="16" />
          Capstones
        </button>
        <a class="toolbar-button" href="/book.html" target="_blank" rel="noreferrer">Read the book</a>
      </div>
    </header>

    <div class="curriculum-summary" aria-label="Curriculum summary">
      <span><strong>{{ tracks.length }}</strong> learning tracks</span>
      <span><strong>{{ lessons.length }}</strong> guided lessons</span>
      <span><strong>{{ completedIds.length }}</strong> completed</span>
      <button v-if="completedIds.length" type="button" class="text-command" @click="$emit('reset-progress')">
        <RotateCcw :size="14" /> Reset local progress
      </button>
    </div>

    <div class="track-list">
      <article v-for="track in tracks" :key="track.id" class="track-row">
        <div class="track-order" aria-hidden="true">{{ String(track.order).padStart(2, '0') }}</div>
        <div class="track-copy">
          <div class="track-meta">
            <span>{{ track.level }}</span>
            <span>{{ track.hours }} hours</span>
            <span>{{ track.lessonIds.length }} lessons</span>
          </div>
          <h2>{{ track.title }}</h2>
          <p>{{ track.summary }}</p>
          <div class="progress-line" :aria-label="`${progress(track)} percent complete`">
            <span :style="{ width: `${progress(track)}%` }"></span>
          </div>
          <small>{{ completedCount(track) }} of {{ track.lessonIds.length }} complete</small>
        </div>
        <button type="button" class="track-open" :aria-label="`Open ${track.title}`" @click="$emit('open-track', track.id)">
          <BookOpenCheck :size="20" />
          <span>Open track</span>
          <ArrowRight :size="16" />
        </button>
      </article>
    </div>
  </section>
</template>
