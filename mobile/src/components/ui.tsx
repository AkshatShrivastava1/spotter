import { ReactNode } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleProp,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  View,
  ViewStyle,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, radius, space, type } from '@/lib/theme';

export function Screen({
  children,
  refreshing,
  onRefresh,
  scroll = true,
}: {
  children: ReactNode;
  refreshing?: boolean;
  onRefresh?: () => void;
  scroll?: boolean;
}) {
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }} edges={['top']}>
      {scroll ? (
        <ScrollView
          contentContainerStyle={{ padding: space.lg, paddingBottom: 120, gap: space.md }}
          keyboardShouldPersistTaps="handled"
          refreshControl={
            onRefresh ? (
              <RefreshControl refreshing={!!refreshing} onRefresh={onRefresh} tintColor={colors.accent} />
            ) : undefined
          }
        >
          {children}
        </ScrollView>
      ) : (
        <View style={{ flex: 1 }}>{children}</View>
      )}
    </SafeAreaView>
  );
}

export function Card({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function Label({ children }: { children: ReactNode }) {
  return <Text style={type.label}>{children}</Text>;
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  loading,
  disabled,
  style,
}: {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'ghost' | 'danger';
  loading?: boolean;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
}) {
  const bg = variant === 'primary' ? colors.accent : variant === 'danger' ? colors.danger : 'transparent';
  const fg = variant === 'primary' ? colors.accentInk : colors.text;
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.btn,
        { backgroundColor: bg, opacity: disabled ? 0.4 : pressed ? 0.8 : 1 },
        variant === 'ghost' && { borderWidth: 1, borderColor: colors.border },
        style,
      ]}
    >
      {loading ? <ActivityIndicator color={fg} /> : <Text style={[styles.btnText, { color: fg }]}>{title}</Text>}
    </Pressable>
  );
}

export function Bar({ value, max, color, height = 8 }: { value: number; max: number; color: string; height?: number }) {
  const pct = max > 0 ? Math.min(value / max, 1) : 0;
  const over = value > max;
  return (
    <View style={{ height, backgroundColor: colors.surface2, borderRadius: height, overflow: 'hidden' }}>
      <View style={{ width: `${pct * 100}%`, height, backgroundColor: over ? colors.danger : color, borderRadius: height }} />
    </View>
  );
}

export function MacroRow({ label, value, target, color, unit = 'g' }: { label: string; value: number; target: number; color: string; unit?: string }) {
  return (
    <View style={{ gap: 6 }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <Text style={[type.small, { color: colors.text, fontWeight: '600' }]}>{label}</Text>
        <Text style={type.small}>
          <Text style={{ color: colors.text }}>{Math.round(value)}</Text> / {target}
          {unit}
        </Text>
      </View>
      <Bar value={value} max={target} color={color} />
    </View>
  );
}

export function Chip({ label, active, onPress }: { label: string; active?: boolean; onPress?: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.chip, active && { backgroundColor: colors.accent, borderColor: colors.accent }]}
    >
      <Text style={{ color: active ? colors.accentInk : colors.text, fontWeight: '600', fontSize: 13 }}>{label}</Text>
    </Pressable>
  );
}

export function Chips<T extends string>({ options, value, onChange }: { options: { value: T; label: string }[]; value: T; onChange: (v: T) => void }) {
  return (
    <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: space.sm }}>
      {options.map((o) => (
        <Chip key={o.value} label={o.label} active={o.value === value} onPress={() => onChange(o.value)} />
      ))}
    </View>
  );
}

export function Field(props: TextInputProps & { label?: string }) {
  const { label, style, ...rest } = props;
  return (
    <View style={{ gap: 6 }}>
      {label ? <Label>{label}</Label> : null}
      <TextInput placeholderTextColor={colors.muted} style={[styles.input, style]} {...rest} />
    </View>
  );
}

export function ErrorText({ error }: { error: string | null }) {
  if (!error) return null;
  return <Text style={{ color: colors.danger, fontSize: 13 }}>{error}</Text>;
}

export function CoachBubble({ title, body }: { title?: string; body: string }) {
  return (
    <View style={styles.coach}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <View style={styles.coachDot} />
        <Text style={[type.label, { color: colors.accent }]}>{title || 'Coach'}</Text>
      </View>
      <Text style={type.body}>{body}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: space.lg,
    gap: space.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  btn: { height: 50, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', paddingHorizontal: space.lg },
  btnText: { fontSize: 16, fontWeight: '700' },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  input: {
    backgroundColor: colors.surface2,
    color: colors.text,
    borderRadius: radius.md,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  coach: {
    backgroundColor: '#1B2112',
    borderColor: '#3A4A16',
    borderWidth: 1,
    borderRadius: radius.lg,
    padding: space.lg,
  },
  coachDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.accent },
});
