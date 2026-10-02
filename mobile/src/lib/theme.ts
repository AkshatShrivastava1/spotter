export const colors = {
  bg: '#0E0F0C',
  surface: '#181A16',
  surface2: '#22251F',
  border: '#2E322A',
  text: '#F2F2EE',
  muted: '#8B8F86',
  accent: '#C6F432', // electric lime: the "go" color
  accentInk: '#0E0F0C',
  protein: '#FF7A59',
  carbs: '#F5B83D',
  fat: '#6EC1FF',
  water: '#4FD1C5',
  danger: '#FF5A5A',
};

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 };
export const radius = { sm: 8, md: 14, lg: 22 };

export const type = {
  display: { fontSize: 40, fontWeight: '800' as const, color: colors.text, letterSpacing: -1 },
  h1: { fontSize: 26, fontWeight: '800' as const, color: colors.text, letterSpacing: -0.5 },
  h2: { fontSize: 18, fontWeight: '700' as const, color: colors.text },
  body: { fontSize: 15, color: colors.text, lineHeight: 21 },
  small: { fontSize: 13, color: colors.muted },
  label: { fontSize: 11, fontWeight: '700' as const, color: colors.muted, letterSpacing: 1.2, textTransform: 'uppercase' as const },
};
