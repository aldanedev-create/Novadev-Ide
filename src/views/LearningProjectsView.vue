<script setup>
import { ArrowLeft, ArrowRight, CheckCircle2, FolderKanban } from "lucide-vue-next";

defineProps({
  tracks: { type: Array, default: () => [] },
  lessons: { type: Array, default: () => [] },
  completedIds: { type: Array, default: () => [] },
});

defineEmits(["back", "open-lesson"]);
</script>

<template>
  <section class="page learning-projects-page">
    <header class="projects-header">
      <button type="button" class="text-command" @click="$emit('back')"><ArrowLeft :size="15" /> Curriculum</button>
      <span>Portfolio requirements</span>
      <h1>Build applications that demonstrate NovaDev.</h1>
      <p>Each project should contain editable Nova source, generated frontend and backend code, tests, setup instructions, and a short explanation of project-specific decisions.</p>
    </header>

    <div class="project-requirements">
      <section v-for="track in tracks" :key="track.id" class="project-band">
        <div class="project-band-heading">
          <FolderKanban :size="22" />
          <div><span>Track {{ track.order }}</span><h2>{{ track.title }}</h2></div>
        </div>
        <ul><li v-for="project in track.projects" :key="project">{{ project }}</li></ul>
      </section>
    </div>

    <section class="capstone-band">
      <div><span>Final capstones</span><h2>Complete one guided and one original application</h2></div>
      <button
        v-for="lesson in lessons.filter((item) => item.section === 'Capstone Projects')"
        :key="lesson.id"
        type="button"
        class="capstone-row"
        @click="$emit('open-lesson', lesson.id)"
      >
        <CheckCircle2 v-if="completedIds.includes(lesson.id)" :size="18" />
        <FolderKanban v-else :size="18" />
        <span><strong>{{ lesson.title }}</strong><small>{{ lesson.summary }}</small></span>
        <ArrowRight :size="17" />
      </button>
    </section>
  </section>
</template>
