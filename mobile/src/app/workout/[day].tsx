import { Link, Stack, useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { Text, TextInput, View } from 'react-native';

import { Button, Card, Chips, CoachBubble, ErrorText, Label, Screen } from '@/components/ui';
import { api, getUnits } from '@/lib/api';
import { colors, type } from '@/lib/theme';
import { Exercise, Plan, PlanDay } from '@/lib/types';

type SetRow = { reps: string; weight: string; done: boolean };
type Prog = { slug: string; name: string; next_time: string; volume_pr: boolean };

const LB = 0.4536;

export default function WorkoutScreen() {
  const { day } = useLocalSearchParams<{ day: string }>();
  const router = useRouter();
  const [pd, setPd] = useState<PlanDay | null>(null);
  const [cues, setCues] = useState<Record<string, string>>({});
  const [last, setLast] = useState<Record<string, string>>({});
  const [rows, setRows] = useState<Record<string, SetRow[]>>({});
  const [unit, setUnit] = useState<'lb' | 'kg'>('lb');
  const [rest, setRest] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ feedback: string; progression: Prog[] } | null>(null);
  const started = useRef(Date.now());

  useEffect(() => {
    (async () => {
      try {
        const u = await getUnits();
        setUnit(u === 'imperial' ? 'lb' : 'kg');
        const k = u === 'imperial' ? LB : 1;
        const plan = await api.get<Plan>('/workouts/plan');
        const d = plan.days.find((x) => x.day === day) ?? plan.days[0];
        setPd(d);
        const init: Record<string, SetRow[]> = {};
        const c: Record<string, string> = {};
        const l: Record<string, string> = {};
        await Promise.all(
          d.exercises.map(async (e) => {
            const [ex, prev] = await Promise.all([
              api.get<Exercise>(`/exercises/${e.slug}`),
              api.get<{ sets: { reps: number; weight_kg: number }[] }>(`/workouts/last/${e.slug}`),
            ]);
            c[e.slug] = ex.cues[0];
            const top = prev.sets[0];
            if (top) l[e.slug] = `Last: ${prev.sets.map((s) => `${Math.round(s.weight_kg / k)}x${s.reps}`).join(', ')} (${u === 'imperial' ? 'lb' : 'kg'})`;
            init[e.slug] = Array.from({ length: e.sets }, () => ({
              reps: '',
              weight: top ? String(Math.round(top.weight_kg / k)) : '',
              done: false,
            }));
          }),
        );
        setCues(c);
        setLast(l);
        setRows(init);
      } catch (e: any) {
        setError(e.message);
      }
    })();
  }, [day]);

  useEffect(() => {
    if (rest <= 0) return;
    const t = setTimeout(() => setRest(rest - 1), 1000);
    return () => clearTimeout(t);
  }, [rest]);

  function update(slug: string, i: number, patch: Partial<SetRow>) {
    setRows((r) => ({ ...r, [slug]: r[slug].map((s, idx) => (idx === i ? { ...s, ...patch } : s)) }));
  }

  async function finish() {
    if (!pd) return;
    setBusy(true);
    setError(null);
    try {
      const exercises = pd.exercises
        .map((e) => ({
          slug: e.slug,
          sets: (rows[e.slug] ?? [])
            .filter((s) => s.reps)
            .map((s) => ({ reps: Number(s.reps), weight_kg: Math.round(Number(s.weight || 0) * (unit === 'lb' ? LB : 1) * 10) / 10 })),
        }))
        .filter((e) => e.sets.length);
      if (!exercises.length) throw new Error('Log at least one set.');
      const r = await api.post<{ feedback: string; progression: Prog[] }>('/workouts/sessions', {
        focus: pd.focus,
        exercises,
        duration_min: Math.round((Date.now() - started.current) / 60000),
      });
      setResult(r);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (result) {
    return (
      <Screen>
        <Text style={type.h1}>Session done.</Text>
        <CoachBubble body={result.feedback} />
        {result.progression.map((p) => (
          <Card key={p.slug}>
            <Text style={[type.body, { fontWeight: '700' }]}>{p.name}{p.volume_pr ? '  · PR' : ''}</Text>
            <Text style={type.small}>{p.next_time}</Text>
          </Card>
        ))}
        <Button title="Done" onPress={() => router.back()} />
      </Screen>
    );
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: pd?.focus ?? 'Workout' }} />
      <ErrorText error={error} />
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <Chips value={unit} onChange={setUnit} options={[{ value: 'lb', label: 'lb' }, { value: 'kg', label: 'kg' }]} />
        {rest > 0 ? (
          <Text style={[type.h2, { color: colors.accent }]}>Rest {Math.floor(rest / 60)}:{String(rest % 60).padStart(2, '0')}</Text>
        ) : null}
      </View>
      {pd?.exercises.map((e) => (
        <Card key={e.slug}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <Text style={type.h2}>{e.name}</Text>
            <Link href={{ pathname: '/exercise/[slug]', params: { slug: e.slug } }} style={{ color: colors.accent }}>Form</Link>
          </View>
          <Text style={type.small}>Target {e.sets} x {e.reps} · rest {Math.round(e.rest_s / 60 * 10) / 10} min</Text>
          {cues[e.slug] ? <Text style={[type.small, { color: colors.text }]}>Cue: {cues[e.slug]}</Text> : null}
          {last[e.slug] ? <Text style={type.small}>{last[e.slug]}</Text> : null}
          {(rows[e.slug] ?? []).map((s, i) => (
            <View key={i} style={{ flexDirection: 'row', gap: 8, alignItems: 'center' }}>
              <View style={{ width: 40 }}><Label>Set {i + 1}</Label></View>
              <TextInput style={[cell, { flex: 1 }]} keyboardType="decimal-pad" placeholder={unit} placeholderTextColor={colors.muted}
                value={s.weight} onChangeText={(v) => update(e.slug, i, { weight: v })} />
              <TextInput style={[cell, { flex: 1 }]} keyboardType="number-pad" placeholder="reps" placeholderTextColor={colors.muted}
                value={s.reps} onChangeText={(v) => update(e.slug, i, { reps: v })} />
              <Button title={s.done ? '✓' : 'Done'} variant={s.done ? 'primary' : 'ghost'} style={{ height: 40, width: 64, paddingHorizontal: 0 }}
                onPress={() => { update(e.slug, i, { done: !s.done }); if (!s.done) setRest(e.rest_s); }} />
            </View>
          ))}
        </Card>
      ))}
      <Button title="Finish workout" onPress={finish} loading={busy} />
    </Screen>
  );
}

const cell = {
  minWidth: 0,
  backgroundColor: colors.surface2, color: colors.text, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 8, fontSize: 16,
};
