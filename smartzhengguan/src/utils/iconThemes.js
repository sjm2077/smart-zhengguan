const ICON_THEMES = {
  home: { primary: '#4F46E5', secondary: '#C7D2FE', surface: '#EEF2FF' },
  clipboard: { primary: '#84CC16', secondary: '#D9F99D', surface: '#F3FCE8' },
  user: { primary: '#84CC16', secondary: '#D9F99D', surface: '#F3FCE8' },
  users: { primary: '#3B82F6', secondary: '#BFDBFE', surface: '#ECF4FF' },
  book: { primary: '#3B82F6', secondary: '#BAE6FD', surface: '#ECF7FF' },
  graduation: { primary: '#2563EB', secondary: '#BFDBFE', surface: '#EEF4FF' },
  medal: { primary: '#65A30D', secondary: '#D9F99D', surface: '#F4FBE8' },
  briefcase: { primary: '#0F6CBD', secondary: '#B6E0FE', surface: '#EDF8FF' },
  file: { primary: '#2F7DE1', secondary: '#BFDBFE', surface: '#ECF4FF' },
  globe: { primary: '#0F9D8A', secondary: '#B8F0E8', surface: '#ECFCF8' },
  award: { primary: '#F59E0B', secondary: '#FDE68A', surface: '#FFF7E8' },
  wallet: { primary: '#F59E0B', secondary: '#FCD34D', surface: '#FFF7E8' },
  chart: { primary: '#2563EB', secondary: '#93C5FD', surface: '#EEF4FF' },
  trend: { primary: '#14B8A6', secondary: '#99F6E4', surface: '#ECFEFB' },
  upload: { primary: '#06B6D4', secondary: '#A5F3FC', surface: '#ECFEFF' },
  edit: { primary: '#2F7DE1', secondary: '#BFDBFE', surface: '#ECF4FF' },
  'check-circle': { primary: '#16A34A', secondary: '#BBF7D0', surface: '#EEFDF3' },
  'alert-circle': { primary: '#F59E0B', secondary: '#FDE68A', surface: '#FFF7E8' },
  refresh: { primary: '#F59E0B', secondary: '#FCD34D', surface: '#FFF7E8' },
  clock: { primary: '#F59E0B', secondary: '#FDE68A', surface: '#FFF7E8' },
  star: { primary: '#F59E0B', secondary: '#FDE68A', surface: '#FFF7E8' },
  target: { primary: '#8B5CF6', secondary: '#DDD6FE', surface: '#F5F3FF' },
  shield: { primary: '#16A34A', secondary: '#BBF7D0', surface: '#EEFDF3' },
  layers: { primary: '#4F46E5', secondary: '#C7D2FE', surface: '#EEF2FF' },
  ratio: { primary: '#8B5CF6', secondary: '#DDD6FE', surface: '#F5F3FF' },
  building: { primary: '#3B82F6', secondary: '#BFDBFE', surface: '#ECF4FF' },
  send: { primary: '#06B6D4', secondary: '#A5F3FC', surface: '#ECFEFF' },
}

const DEFAULT_THEME = { primary: '#2563EB', secondary: '#BFDBFE', surface: '#EEF4FF' }

export function getIconTheme(icon) {
  return ICON_THEMES[icon] || DEFAULT_THEME
}
