<script setup>
import { Boxes, Braces, Eye, FileCode2, GraduationCap, Play, Settings, TerminalSquare } from "lucide-vue-next";

defineProps({
  active: { type: String, default: "learn" },
});

defineEmits(["navigate"]);

const items = [
  { id: "learn", label: "Learn", icon: GraduationCap },
  { id: "editor", label: "Editor", icon: FileCode2 },
  { id: "preview", label: "Build UI", icon: Eye },
  { id: "output", label: "Output", icon: Play },
  { id: "tokens", label: "Tokens", icon: Boxes },
  { id: "ast", label: "AST", icon: Braces },
  { id: "shell", label: "Shell", icon: TerminalSquare },
  { id: "settings", label: "Settings", icon: Settings },
];
</script>

<template>
  <nav class="activity-bar" aria-label="Nova IDE navigation">
    <button
      v-for="item in items"
      :key="item.id"
      type="button"
      class="activity-button"
      :class="{ active: active === item.id }"
      :title="item.label"
      :aria-label="item.label"
      @click="$emit('navigate', item.id)"
    >
      <component :is="item.icon" :size="21" />
    </button>
  </nav>
</template>
