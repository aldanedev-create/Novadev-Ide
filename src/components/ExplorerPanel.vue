<script setup>
import { computed } from "vue";
import { BookOpen, Check, ChevronRight, Circle, FileCode2, FolderOpen, FolderTree, Package } from "lucide-vue-next";

const props = defineProps({
  tracks: { type: Array, default: () => [] },
  lessons: { type: Array, default: () => [] },
  activeTrackId: { type: String, default: "" },
  activeRoute: { type: String, default: "learn" },
  selectedLessonId: { type: String, default: "" },
  completedIds: { type: Array, default: () => [] },
});

defineEmits(["navigate", "open-track", "open-lesson", "load-lesson"]);

const activeTrack = computed(() => props.tracks.find((track) => track.id === props.activeTrackId) || props.tracks[0]);
const trackLessons = computed(() => {
  const ids = new Set(activeTrack.value?.lessonIds || []);
  return props.lessons.filter((lesson) => ids.has(lesson.id));
});
</script>

<template>
  <aside class="explorer-panel">
    <section class="explorer-section">
      <div class="explorer-heading"><FolderOpen :size="16" /><span>NOVA WORKSPACE</span></div>
      <button type="button" class="explorer-row" :class="{ active: activeRoute === 'editor' }" @click="$emit('navigate', 'editor')">
        <FileCode2 :size="15" /> app.nova
      </button>
      <button type="button" class="explorer-row" :class="{ active: activeRoute === 'preview' }" @click="$emit('navigate', 'preview')">
        <Package :size="15" /> build-ui
      </button>
      <button type="button" class="explorer-row" :class="{ active: activeRoute === 'shell' }" @click="$emit('navigate', 'shell')">
        <ChevronRight :size="15" /> shell
      </button>
    </section>

    <section class="explorer-section track-explorer">
      <div class="explorer-heading"><FolderTree :size="16" /><span>CURRICULUM TRACKS</span></div>
      <button
        v-for="track in tracks"
        :key="track.id"
        type="button"
        class="explorer-row track-explorer-row"
        :class="{ active: activeTrack?.id === track.id }"
        @click="$emit('open-track', track.id)"
      >
        <span>{{ track.order }}</span>{{ track.title }}
      </button>
    </section>

    <section class="explorer-section">
      <div class="explorer-heading"><BookOpen :size="16" /><span>{{ activeTrack?.title || 'LESSONS' }}</span></div>
      <button
        v-for="lesson in trackLessons"
        :key="lesson.id"
        type="button"
        class="lesson-row explorer-lesson-row"
        :class="{ active: selectedLessonId === lesson.id }"
        @click="$emit('open-lesson', lesson.id)"
        @dblclick="$emit('load-lesson', lesson)"
      >
        <Check v-if="completedIds.includes(lesson.id)" :size="14" class="complete-icon" />
        <Circle v-else :size="14" />
        <span>{{ lesson.title }}</span>
      </button>
    </section>
  </aside>
</template>
