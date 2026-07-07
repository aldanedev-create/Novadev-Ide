<script setup>
import { Download, Moon, PanelLeft, Save, Settings2, Sun, Type } from "lucide-vue-next";

defineProps({
  fontSize: { type: Number, default: 15 },
  wrapLines: { type: Boolean, default: true },
  sidePanelOpen: { type: Boolean, default: true },
  themeMode: { type: String, default: "dark" },
});

defineEmits([
  "update:fontSize",
  "update:wrapLines",
  "update:sidePanelOpen",
  "toggle-theme",
  "save",
  "load-save",
]);
</script>

<template>
  <section class="page settings-page">
    <div class="page-toolbar">
      <div>
        <strong>Settings</strong>
        <span>Customize the Nova IDE workspace.</span>
      </div>
    </div>

    <div class="settings-grid">
      <section class="settings-section">
        <div class="settings-heading">
          <Type :size="18" />
          <strong>Editor</strong>
        </div>
        <label class="range-field">
          <span>Font size</span>
          <input
            type="range"
            min="12"
            max="22"
            :value="fontSize"
            @input="$emit('update:fontSize', Number($event.target.value))"
          />
          <output>{{ fontSize }}px</output>
        </label>
        <label class="switch-field">
          <input
            type="checkbox"
            :checked="wrapLines"
            @change="$emit('update:wrapLines', $event.target.checked)"
          />
          <span>Wrap long lines</span>
        </label>
      </section>

      <section class="settings-section">
        <div class="settings-heading">
          <PanelLeft :size="18" />
          <strong>Workspace</strong>
        </div>
        <label class="switch-field">
          <input
            type="checkbox"
            :checked="sidePanelOpen"
            @change="$emit('update:sidePanelOpen', $event.target.checked)"
          />
          <span>Show explorer panel</span>
        </label>
        <button type="button" class="toolbar-button" @click="$emit('toggle-theme')">
          <Sun v-if="themeMode === 'dark'" :size="16" />
          <Moon v-else :size="16" />
          Toggle Theme
        </button>
      </section>

      <section class="settings-section">
        <div class="settings-heading">
          <Settings2 :size="18" />
          <strong>Local Save</strong>
        </div>
        <p>Save your current NovaDev code in this browser, then reload it later.</p>
        <div class="inline-actions">
          <button type="button" class="toolbar-button" @click="$emit('save')">
            <Save :size="16" />
            Save
          </button>
          <button type="button" class="toolbar-button" @click="$emit('load-save')">
            <Download :size="16" />
            Load Save
          </button>
        </div>
      </section>

      <section class="settings-section">
        <div class="settings-heading">
          <Settings2 :size="18" />
          <strong>Shortcuts</strong>
        </div>
        <div class="shortcut-grid">
          <span><kbd>Ctrl</kbd> + <kbd>Enter</kbd></span>
          <span>Run code</span>
          <span><kbd>Ctrl</kbd> + <kbd>B</kbd></span>
          <span>Build UI preview</span>
          <span><kbd>Ctrl</kbd> + <kbd>S</kbd></span>
          <span>Save locally</span>
        </div>
      </section>
    </div>
  </section>
</template>
