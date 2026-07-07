<script setup>
defineProps({
  status: { type: String, default: "Ready" },
  fileName: { type: String, default: "app.nova" },
  route: { type: String, default: "learn" },
  lineCount: { type: Number, default: 1 },
  themeMode: { type: String, default: "dark" },
});
</script>

<template>
  <footer class="status-bar">
    <span>{{ status }}</span>
    <span>{{ fileName }}</span>
    <span>{{ lineCount }} lines</span>
    <span>{{ route }}</span>
    <span>{{ themeMode }}</span>
  </footer>
</template>
