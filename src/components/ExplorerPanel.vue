<script setup>
import { BookOpen, ChevronRight, FileCode2, FolderOpen, Package } from "lucide-vue-next";

defineProps({
  lessons: { type: Array, default: () => [] },
  activeRoute: { type: String, default: "learn" },
  selectedLessonId: { type: String, default: "" },
});

defineEmits(["navigate", "select-lesson", "load-lesson"]);
</script>

<template>
  <aside class="explorer-panel">
    <section class="explorer-section">
      <div class="explorer-heading">
        <FolderOpen :size="16" />
        <span>NOVA WORKSPACE</span>
      </div>
      <button type="button" class="explorer-row" :class="{ active: activeRoute === 'editor' }" @click="$emit('navigate', 'editor')">
        <FileCode2 :size="15" />
        app.nova
      </button>
      <button type="button" class="explorer-row" :class="{ active: activeRoute === 'preview' }" @click="$emit('navigate', 'preview')">
        <Package :size="15" />
        build-ui
      </button>
      <button type="button" class="explorer-row" :class="{ active: activeRoute === 'shell' }" @click="$emit('navigate', 'shell')">
        <ChevronRight :size="15" />
        shell
      </button>
    </section>

    <section class="explorer-section">
      <div class="explorer-heading">
        <BookOpen :size="16" />
        <span>LEARN NOVADEV</span>
      </div>
      <button
        v-for="lesson in lessons"
        :key="lesson.id"
        type="button"
        class="lesson-row"
        :class="{ active: selectedLessonId === lesson.id }"
        @click="$emit('select-lesson', lesson.id)"
        @dblclick="$emit('load-lesson', lesson)"
      >
        <span>{{ lesson.title }}</span>
        <small>{{ lesson.section }}</small>
      </button>
    </section>
  </aside>
</template>
