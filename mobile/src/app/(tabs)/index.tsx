import { Link, useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { Bar, Button, Card, CoachBubble, ErrorText, Label, MacroRow, Screen } from '@/components/ui';
import { api, getUserId } from '@/lib/api';
import { syncSteps } from '@/lib/device';
import { colors, type } from '@/lib/theme';
import { Today } from '@/lib/types';

const WATER_STEP = 250;

export default function TodayScreen() {
  const router = useRouter();
  const [t, setT] = useState<Today | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [checkinDue, setCheckinDue] = useState(false);

  const load = useCallback(async () => {
    if (!getUserId()) return;
    try {
      setError(null);
      await syncSteps();
      setT(await api.get<Today>('/today'));
      const c = await api.get<{ due: boolean }>('/checkin');
      setCheckinDue(c.due && new Date().getDay() === 0);
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  async function addWater(ml: number) {
    await api.post('/track/water', { amount: ml });
    load();
  }

  if (!t) {
    return (
      <Screen>
        <Text style={type.h1}>Today</Text>
        <ErrorText error={error} />
        {error && <Button title="Settings" variant="ghost" onPress={() => router.push('/settings')} />}
      </Screen>
    );
  }

  const left = t.remaining.kcal;
  const hour = Number(t.local_time.slice(0, 2));
  const greeting = hour < 5 ? 'Up late' : hour < 12 ? 'Morning' : hour < 17 ? 'Afternoon' : 'Evening';

  return (
    <Screen refreshing={refreshing} onRefresh={async () => { setRefreshing(true); await load(); setRefreshing(false); }}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <View>
          <Text style={type.small}>{greeting}, {t.name}</Text>
          <Text style={type.h1}>Today</Text>
        </View>
        <View style={{ flexDirection: 'row', gap: 16, alignItems: 'center' }}>
          {t.streak > 0 && <Text style={{ color: colors.accent, fontWeight: '800' }}>{t.streak} day streak</Text>}
          <Link href="/settings" style={{ color: colors.muted }}>Settings</Link>
        </View>
      </View>

      {checkinDue && (
        <Pressable onPress={() => router.push('/checkin')}>
          <CoachBubble title="Weekly check-in" body="It's Sunday. Let's sit down and review your week: weight averages, photos, and next week's plan. Tap to start." />
        </Pressable>
      )}

      {t.coach_card && (
        <Pressable onPress={() => router.push('/coach')}>
          <CoachBubble title={t.coach_card.title} body={t.coach_card.body} />
        </Pressable>
      )}

      {t.show_calories ? (
        <Card>
          <Label>Calories</Label>
          <View style={{ flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between' }}>
            <View>
              <Text style={[type.display, left < 0 && { color: colors.danger }]}>{Math.abs(left)}</Text>
              <Text style={type.small}>{left >= 0 ? 'kcal left' : 'kcal over'}</Text>
            </View>
            <Text style={type.small}>
              {t.eaten.kcal} eaten / {t.target.kcal} target
              {t.kcal_adjustment ? `\n(${t.kcal_adjustment} balance adj.)` : ''}
            </Text>
          </View>
          <Bar value={t.eaten.kcal} max={t.target.kcal} color={colors.accent} height={12} />
          <MacroRow label="Protein" value={t.eaten.protein_g} target={t.target.protein_g} color={colors.protein} />
          <MacroRow label="Carbs" value={t.eaten.carbs_g} target={t.target.carbs_g} color={colors.carbs} />
          <MacroRow label="Fat" value={t.eaten.fat_g} target={t.target.fat_g} color={colors.fat} />
        </Card>
      ) : (
        <Card>
          <Label>Fuel</Label>
          <Text style={type.body}>Build each plate with protein, carbs for energy, and a fruit or veggie.</Text>
          <MacroRow label="Protein (for strong muscles)" value={t.eaten.protein_g} target={t.target.protein_g} color={colors.protein} />
          <Text style={type.small}>Goal today: 60 minutes of active play or sport.</Text>
        </Card>
      )}

      <View style={{ flexDirection: 'row', gap: 12 }}>
        <Card style={{ flex: 1 }}>
          <Label>Water</Label>
          <Text style={type.h2}>{(t.water_ml / 1000).toFixed(2)} L</Text>
          <Bar value={t.water_ml} max={t.target.water_ml} color={colors.water} />
          <View style={{ flexDirection: 'row', gap: 8 }}>
            <Button title="+250" variant="ghost" onPress={() => addWater(WATER_STEP)} style={{ flex: 1, height: 38 }} />
            <Button title="+500" variant="ghost" onPress={() => addWater(500)} style={{ flex: 1, height: 38 }} />
          </View>
        </Card>
        <Card style={{ flex: 1 }}>
          <Label>Steps</Label>
          <Text style={type.h2}>{t.steps.toLocaleString()}</Text>
          <Bar value={t.steps} max={t.target.steps} color={colors.text} />
          <Text style={type.small}>of {t.target.steps.toLocaleString()}</Text>
        </Card>
      </View>

      <Card>
        <Label>Training</Label>
        {t.todays_workout ? (
          <>
            <Text style={type.h2}>{t.todays_workout.focus}{t.workout_done ? '  ✓ done' : ''}</Text>
            <Text style={type.small}>{t.todays_workout.exercises.map((e) => e.name).join(' · ')}</Text>
            {!t.workout_done && (
              <Button title="Start workout" onPress={() => router.push({ pathname: '/workout/[day]', params: { day: t.todays_workout!.day } })} />
            )}
          </>
        ) : (
          <Text style={type.body}>Rest day. Hit your steps and stretch for 10 minutes.</Text>
        )}
      </Card>

      <Card>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
          <Label>Meals</Label>
          <Link href="/log" style={{ color: colors.accent, fontWeight: '700' }}>+ Log</Link>
        </View>
        {t.meals.length === 0 && <Text style={type.small}>Nothing logged yet.</Text>}
        {t.meals.map((m) => (
          <View key={m.id} style={{ gap: 2, paddingVertical: 4 }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text style={[type.body, { fontWeight: '700', textTransform: 'capitalize' }]}>{m.meal_type}</Text>
              <Text style={type.small}>{m.kcal} kcal · P{m.protein_g}</Text>
            </View>
            <Text style={type.small} numberOfLines={1}>{m.description}</Text>
          </View>
        ))}
      </Card>
      <ErrorText error={error} />
    </Screen>
  );
}
