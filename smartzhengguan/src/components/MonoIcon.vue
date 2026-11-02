<template>
  <svg
    class="mono-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="var(--icon-primary)"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    :style="{ '--icon-primary': primary, '--icon-secondary': secondary }"
    aria-hidden="true"
  >
    <template v-if="icon === 'home'">
      <path d="M5 10.5 12 5l7 5.5V20H5z" fill="var(--icon-secondary)" stroke="none" />
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </template>
    <template v-else-if="icon === 'clipboard'">
      <rect x="5" y="4" width="14" height="16" rx="3" fill="var(--icon-secondary)" stroke="none" />
      <rect x="8" y="8" width="8" height="1.6" rx=".8" fill="var(--icon-primary)" stroke="none" opacity=".45" />
      <rect x="8" y="12" width="7" height="1.6" rx=".8" fill="var(--icon-primary)" stroke="none" opacity=".45" />
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" />
    </template>
    <template v-else-if="icon === 'user'">
      <circle cx="12" cy="8" r="4.2" fill="var(--icon-secondary)" stroke="none" />
      <path d="M5 20c1.2-3.9 4.2-6 7-6s5.8 2.1 7 6" fill="var(--icon-secondary)" opacity=".7" stroke="none" />
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c0-4 4-7 8-7s8 3 8 7" />
    </template>
    <template v-else-if="icon === 'users'">
      <circle cx="16.5" cy="8.5" r="3.2" fill="var(--icon-secondary)" opacity=".75" stroke="none" />
      <circle cx="9" cy="7.5" r="4" fill="var(--icon-secondary)" stroke="none" />
      <path d="M4.2 20c.8-3.6 3.8-5.8 6.8-5.8s5.7 1.7 6.6 4.8" fill="var(--icon-secondary)" opacity=".68" stroke="none" />
      <path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2" />
      <circle cx="9.5" cy="7" r="3.5" />
      <path d="M21 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a3.5 3.5 0 0 1 0 6.74" />
    </template>
    <template v-else-if="icon === 'book'">
      <path d="M6 4.5h12.2v14.8H7.2A2.2 2.2 0 0 0 5 21.5V6.8A2.3 2.3 0 0 1 7.3 4.5z" fill="var(--icon-secondary)" stroke="none" />
      <path d="M12 5v13.5" opacity=".45" />
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </template>
    <template v-else-if="icon === 'graduation'">
      <path d="M3.5 10 12 5.6 20.5 10 12 14.3z" fill="var(--icon-secondary)" stroke="none" />
      <path d="M7 14.2v2.8c0 1.8 2.4 3.4 5 3.4s5-1.6 5-3.4v-2.8" fill="var(--icon-secondary)" opacity=".75" stroke="none" />
      <path d="M22 10v6" />
      <path d="M2 10l10-5 10 5-10 5z" />
      <path d="M6 12v5c0 2 3 4 6 4s6-2 6-4v-5" />
    </template>
    <template v-else-if="icon === 'medal'">
      <circle cx="12" cy="8" r="5.5" fill="var(--icon-secondary)" stroke="none" />
      <path d="M10 14.2 8.4 21l3.6-2 3.6 2-1.6-6.8" fill="var(--icon-secondary)" opacity=".78" stroke="none" />
      <circle cx="12" cy="8" r="6" />
      <path d="M15.5 12.9 17 22l-5-3-5 3 1.5-9.1" />
    </template>
    <template v-else-if="icon === 'briefcase'">
      <rect x="3.2" y="7.8" width="17.6" height="11.8" rx="2.6" fill="var(--icon-secondary)" stroke="none" />
      <rect x="9" y="4" width="6" height="3.2" rx="1.2" fill="var(--icon-primary)" opacity=".22" stroke="none" />
      <rect x="2" y="7" width="20" height="14" rx="2" />
      <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
      <path d="M2 13h20" />
    </template>
    <template v-else-if="icon === 'file'">
      <path d="M7 3.5h7l4 4v12A1.8 1.8 0 0 1 16.2 21H7a2 2 0 0 1-2-2V5.5a2 2 0 0 1 2-2z" fill="var(--icon-secondary)" stroke="none" />
      <path d="M14 3.5v4h4" fill="rgba(255,255,255,.55)" stroke="none" />
      <path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z" />
      <path d="M14 2v5h5" />
      <path d="M9 13h6" />
      <path d="M9 17h6" />
    </template>
    <template v-else-if="icon === 'globe'">
      <circle cx="12" cy="12" r="8.5" fill="var(--icon-secondary)" stroke="none" />
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18" />
      <path d="M12 3a15 15 0 0 1 0 18" />
      <path d="M12 3a15 15 0 0 0 0 18" />
    </template>
    <template v-else-if="icon === 'award'">
      <circle cx="12" cy="8" r="4.8" fill="var(--icon-secondary)" stroke="none" />
      <path d="M8.8 13.5 7.6 20l4.4-2.2 4.4 2.2-1.2-6.5" fill="var(--icon-secondary)" opacity=".78" stroke="none" />
      <circle cx="12" cy="8" r="5" />
      <path d="M8.5 13.5 7 21l5-2.5L17 21l-1.5-7.5" />
    </template>
    <template v-else-if="icon === 'wallet'">
      <path d="M4 7.5h15a2 2 0 0 1 2 2v7A2.5 2.5 0 0 1 18.5 19H5.5A2.5 2.5 0 0 1 3 16.5V9a1.5 1.5 0 0 1 1-1.5z" fill="var(--icon-secondary)" stroke="none" />
      <path d="M3 7a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <path d="M3 9h17" />
      <circle cx="16" cy="14" r="1" />
    </template>
    <template v-else-if="icon === 'chart'">
      <rect x="6" y="10" width="3" height="7" rx="1" fill="var(--icon-secondary)" stroke="none" />
      <rect x="11" y="7" width="3" height="10" rx="1" fill="var(--icon-secondary)" opacity=".82" stroke="none" />
      <rect x="16" y="4" width="3" height="13" rx="1" fill="var(--icon-primary)" opacity=".28" stroke="none" />
      <path d="M4 19h16" />
      <rect x="6" y="10" width="3" height="7" rx="1" />
      <rect x="11" y="7" width="3" height="10" rx="1" />
      <rect x="16" y="4" width="3" height="13" rx="1" />
    </template>
    <template v-else-if="icon === 'trend'">
      <path d="M4 17.5h16L18 6.5l-5.2 5-4-3.2L4 12.8z" fill="var(--icon-secondary)" opacity=".72" stroke="none" />
      <path d="M4 16l5-5 4 4 7-8" />
      <path d="M14 7h6v6" />
    </template>
    <template v-else-if="icon === 'upload'">
      <rect x="4" y="16.5" width="16" height="3" rx="1.5" fill="var(--icon-secondary)" stroke="none" />
      <path d="M12 4.5 7.8 8.7h2.4v6.3h3.6V8.7h2.4z" fill="var(--icon-secondary)" stroke="none" />
      <path d="M12 16V4" />
      <path d="M7 9l5-5 5 5" />
      <path d="M4 20h16" />
    </template>
    <template v-else-if="icon === 'edit'">
      <rect x="4.5" y="4.5" width="10.5" height="13" rx="2.2" fill="var(--icon-secondary)" stroke="none" />
      <path d="M15.2 6.2 18.9 9.9 10 18.8l-4 1 1-4z" fill="rgba(255,255,255,.78)" stroke="none" />
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </template>
    <template v-else-if="icon === 'check-circle'">
      <circle cx="12" cy="12" r="8.5" fill="var(--icon-secondary)" stroke="none" />
      <circle cx="12" cy="12" r="9" />
      <path d="m8 12 2.5 2.5L16 9" />
    </template>
    <template v-else-if="icon === 'alert-circle'">
      <circle cx="12" cy="12" r="8.5" fill="var(--icon-secondary)" stroke="none" />
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5" />
      <circle cx="12" cy="16.5" r=".5" fill="var(--icon-primary)" stroke="none" />
    </template>
    <template v-else-if="icon === 'refresh'">
      <path d="M6.5 8.5A7 7 0 0 1 18 6" fill="var(--icon-secondary)" opacity=".7" stroke="none" />
      <path d="M17.5 15.5A7 7 0 0 1 6 18" fill="var(--icon-secondary)" opacity=".55" stroke="none" />
      <path d="M21 12a9 9 0 0 1-15.5 6.4" />
      <path d="M3 12A9 9 0 0 1 18.5 5.6" />
      <path d="M3 17v-4h4" />
      <path d="M21 7v4h-4" />
    </template>
    <template v-else-if="icon === 'clock'">
      <circle cx="12" cy="12" r="8.5" fill="var(--icon-secondary)" stroke="none" />
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </template>
    <template v-else-if="icon === 'star'">
      <path d="m12 4 2.4 4.8 5.3.8-3.8 3.7.9 5.3L12 16.3l-4.8 2.3.9-5.3-3.8-3.7 5.3-.8Z" fill="var(--icon-secondary)" stroke="none" />
      <path d="m12 3 2.8 5.7L21 9.6l-4.5 4.4 1 6.2L12 17.3 6.5 20.2l1-6.2L3 9.6l6.2-.9Z" />
    </template>
    <template v-else-if="icon === 'target'">
      <circle cx="12" cy="12" r="8" fill="var(--icon-secondary)" opacity=".45" stroke="none" />
      <circle cx="12" cy="12" r="4" fill="rgba(255,255,255,.55)" stroke="none" />
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="12" cy="12" r="1.5" fill="var(--icon-primary)" stroke="none" />
    </template>
    <template v-else-if="icon === 'shield'">
      <path d="M12 4 6.2 6.5v4.3c0 4 2.6 6.5 5.8 8.5 3.2-2 5.8-4.5 5.8-8.5V6.5z" fill="var(--icon-secondary)" stroke="none" />
      <path d="M12 3 5 6v5c0 5 3.5 8 7 10 3.5-2 7-5 7-10V6z" />
      <path d="m9.5 11.5 1.8 1.8 3.7-3.8" />
    </template>
    <template v-else-if="icon === 'layers'">
      <path d="m12 4.2 7.2 3.5L12 11 4.8 7.7Z" fill="var(--icon-secondary)" stroke="none" />
      <path d="m4.8 11.7 7.2 3.5 7.2-3.5" opacity=".85" />
      <path d="m4.8 16.2 7.2 3.5 7.2-3.5" opacity=".65" />
      <path d="m12 3 9 4.5-9 4.5-9-4.5Z" />
      <path d="m3 12 9 4.5 9-4.5" />
      <path d="m3 16.5 9 4.5 9-4.5" />
    </template>
    <template v-else-if="icon === 'ratio'">
      <circle cx="7" cy="7" r="2.6" fill="var(--icon-secondary)" stroke="none" />
      <circle cx="17" cy="17" r="2.6" fill="var(--icon-secondary)" stroke="none" />
      <circle cx="7" cy="7" r="3" />
      <circle cx="17" cy="17" r="3" />
      <path d="M6 18 18 6" />
    </template>
    <template v-else-if="icon === 'building'">
      <rect x="4.8" y="3.8" width="14.4" height="16.6" rx="2" fill="var(--icon-secondary)" stroke="none" />
      <rect x="4" y="3" width="16" height="18" rx="2" />
      <path d="M8 7h.01M12 7h.01M16 7h.01M8 11h.01M12 11h.01M16 11h.01M8 15h.01M12 15h.01M16 15h.01" />
    </template>
    <template v-else-if="icon === 'send'">
      <path d="M21 2 11.2 12l3.2 7.3 2.2-5.3 5.3-2.2z" fill="var(--icon-secondary)" stroke="none" />
      <path d="M22 2 11 13" />
      <path d="M22 2 15 22l-4-9-9-4Z" />
    </template>
    <template v-else>
      <circle cx="12" cy="12" r="8.5" fill="var(--icon-secondary)" stroke="none" />
      <circle cx="12" cy="12" r="9" />
      <path d="M8 12h8" />
    </template>
  </svg>
</template>

<script>
export default {
  props: {
    icon: { type: String, default: '' },
    size: { type: [Number, String], default: 18 },
    strokeWidth: { type: [Number, String], default: 1.9 },
    primary: { type: String, default: '#2563EB' },
    secondary: { type: String, default: '#BFDBFE' },
  },
}
</script>

<style scoped>
.mono-icon {
  display: block;
  flex-shrink: 0;
}
</style>
