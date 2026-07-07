<script setup>
import { computed } from "vue";

const props = defineProps({
  modelValue: { type: String, default: "" },
  fontSize: { type: Number, default: 15 },
  wrapLines: { type: Boolean, default: true },
});

defineEmits(["update:modelValue"]);

const lineCount = computed(() => Math.max(1, props.modelValue.split(/\r?\n/).length));
</script>

<template>
  <div class="code-editor">
    <div class="gutter" aria-hidden="true">
      <span v-for="line in lineCount" :key="line">{{ line }}</span>
    </div>
    <textarea
      :value="modelValue"
      spellcheck="false"
      autocomplete="off"
      autocapitalize="off"
      class="code-input"
      :class="{ nowrap: !wrapLines }"
      :style="{ fontSize: `${fontSize}px` }"
      aria-label="NovaDev source editor"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </div>
</template>
