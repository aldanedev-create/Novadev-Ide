<script setup>
import { ArrowLeft, ArrowRight, Check, Circle, Code2, FlaskConical, Play } from "lucide-vue-next";

const bookUrl = import.meta.env.VITE_NOVADEV_BOOK_URL || "/book.html";

defineProps({
  lesson: { type: Object, required: true },
  track: { type: Object, required: true },
  code: { type: String, default: "" },
  output: { type: Array, default: () => [] },
  checks: { type: Array, default: () => [] },
  completed: { type: Boolean, default: false },
  running: { type: Boolean, default: false },
  localOnly: { type: Boolean, default: false },
  hasPrevious: { type: Boolean, default: false },
  hasNext: { type: Boolean, default: false },
});

defineEmits(["update:code", "back", "run", "check", "editor", "previous", "next"]);
</script>

<template>
  <section class="page challenge-page">
    <div class="challenge-toolbar">
      <button type="button" class="text-command" @click="$emit('back')"><ArrowLeft :size="15" /> {{ track.title }}</button>
      <span :class="['completion-status', { complete: completed }]">
        <Check v-if="completed" :size="15" /><Circle v-else :size="15" />
        {{ completed ? 'Completed' : 'In progress' }}
      </span>
    </div>

    <div class="challenge-workspace">
      <article class="challenge-instructions">
        <header>
          <span>{{ lesson.section }} · {{ lesson.level }}</span>
          <h1>{{ lesson.title }}</h1>
          <p>{{ lesson.summary }}</p>
          <a class="text-command book-reference" :href="bookUrl" target="_blank" rel="noreferrer">Read the canonical book chapter <ArrowRight :size="14" /></a>
        </header>

        <section>
          <h2>Lesson</h2>
          <p>{{ lesson.explanation }}</p>
        </section>
        <section v-if="lesson.outcomes?.length">
          <h2>Objectives</h2>
          <ul><li v-for="outcome in lesson.outcomes" :key="outcome">{{ outcome }}</li></ul>
        </section>
        <section class="challenge-task">
          <h2>Challenge</h2>
          <p>{{ lesson.exercise }}</p>
          <small v-if="localOnly">This lesson uses local system capabilities. The online checker validates its NovaDev structure without executing local file, package, secret, or network operations.</small>
        </section>
        <section v-if="lesson.projectUse">
          <h2>Production use</h2>
          <p>{{ lesson.projectUse }}</p>
        </section>
      </article>

      <section class="challenge-code-panel">
        <div class="challenge-code-header">
          <span><Code2 :size="16" /> {{ lesson.id }}.nova</span>
          <button type="button" class="icon-button" title="Open in full editor" aria-label="Open in full editor" @click="$emit('editor')"><ArrowRight :size="17" /></button>
        </div>
        <textarea
          :value="code"
          class="challenge-code-input"
          spellcheck="false"
          aria-label="NovaDev challenge editor"
          @input="$emit('update:code', $event.target.value)"
        ></textarea>
        <div class="challenge-actions">
          <button type="button" class="toolbar-button" :disabled="running || localOnly" @click="$emit('run')"><Play :size="16" /> Run code</button>
          <button type="button" class="toolbar-button primary" :disabled="running" @click="$emit('check')"><FlaskConical :size="16" /> Check lesson</button>
        </div>
        <div class="challenge-results" aria-live="polite">
          <div class="result-heading"><strong>Tests and output</strong><span>{{ checks.filter((item) => item.passed).length }}/{{ checks.length || 0 }} checks</span></div>
          <p v-for="(line, index) in output" :key="`${line.kind}-${index}`" :class="line.kind">{{ line.text }}</p>
          <p v-for="check in checks" :key="check.label" :class="check.passed ? 'success' : 'error'">
            <Check v-if="check.passed" :size="14" /><Circle v-else :size="14" /> {{ check.label }}
          </p>
          <p v-if="!output.length && !checks.length" class="info">Run the starter code, then check your solution.</p>
        </div>
        <footer class="challenge-navigation">
          <button type="button" class="toolbar-button" :disabled="!hasPrevious" @click="$emit('previous')"><ArrowLeft :size="15" /> Previous</button>
          <button type="button" class="toolbar-button" :disabled="!hasNext" @click="$emit('next')">Next <ArrowRight :size="15" /></button>
        </footer>
      </section>
    </div>
  </section>
</template>
