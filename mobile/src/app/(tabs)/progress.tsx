import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import { Image, Text, View } from 'react-native';

import { Button, Card, CoachBubble, ErrorText, Field, Label, Screen } from '@/components/ui';
import { api, authHeaders, fromKg, getApiUrl, getProfile, isYouth, toKg, unitLabel, Units } from '@/lib/api';
import { colors, radius, type } from '@/lib/theme';
import { Checkin, Trend } from '@/lib/types';


export default function ProgressScreen() {
  const router = useRouter();
  const [trend, setTrend] = useState<Trend | null>(null);
  const [photos, setPhotos] = useState<{ id: number; day: string; pose: string }[]>([]);
  const [history, setHistory] = useState<Checkin[]>([]);
  const [weight, setWeight] = useState('');
  const [units, setUnits] = useState<Units>('imperial');
  const [youth, setYouth] = useState(false);
  const lb = (kg: number | null | undefined) => fromKg(kg, units);
  const u = unitLabel(units);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const prof = await getProfile();
      setUnits(prof.units);
      setYouth(isYouth(prof.age_band));
      if (isYouth(prof.age_band)) {
        setHistory(await api.get<Checkin[]>('/checkin/history'));
        return;
      }
      setTrend(await api.get<Trend>('/weight/trend'));
      setPhotos(await api.get('/progress-photos'));
      setHistory(await api.get<Checkin[]>('/checkin/history'));
    } catch (e: any) {
      setError(e.message);
    }
  }, []);
  useFocusEffect(useCallback(() => { load(); }, [load]));

  async function logWeight() {
    try {
      setTrend(await api.post<Trend>('/track/weight', { amount: toKg(Number(weight), units) }));
      setWeight('');
    } catch (e: any) {
      setError(e.message);
    }
  }

  const weeks = trend?.weekly.filter((w) => w.avg_kg != null) ?? [];
  const vals = weeks.map((w) => w.avg_kg as number);
  const min = Math.min(...vals) - 0.5;
  const max = Math.max(...vals) + 0.5;
  const today = trend?.daily.at(-1);
  const loggedToday = today?.day === new Date().toLocaleDateString('en-CA');

  return (
    <Screen>
      <Text style={type.h1}>Progress</Text>
      <ErrorText error={error} />
      {youth ? (
        <>
          <CoachBubble title="Your progress" body="For you, progress means moving more, getting stronger at your exercises, drinking water and sleeping well. We don't track weight or photos on kid and teen accounts." />
          <Button title="Weekly check-in" onPress={() => router.push('/checkin')} />
          {history.map((c) => (
            <Card key={c.id}>
              <Label>Week ending {c.week_end}</Label>
              <Text style={type.body}>{c.coach_review}</Text>
            </Card>
          ))}
        </>
      ) : (
      <>

      <Card>
        <Label>Daily weigh-in</Label>
        {loggedToday ? (
          <Text style={type.body}>Logged today: {lb(today!.kg)} {u}. Same time tomorrow: after the bathroom, before food.</Text>
        ) : (
          <View style={{ flexDirection: 'row', gap: 8, alignItems: 'flex-end' }}>
            <View style={{ flex: 1 }}>
              <Field keyboardType="decimal-pad" placeholder={u} value={weight} onChangeText={setWeight} />
            </View>
            <Button title="Log" onPress={logWeight} disabled={!weight} />
          </View>
        )}
      </Card>

      <Card>
        <Label>Weekly average (what actually matters)</Label>
        <View style={{ flexDirection: 'row', gap: 24 }}>
          <View>
            <Text style={type.small}>This week</Text>
            <Text style={type.h1}>{lb(trend?.this_week_avg)}</Text>
          </View>
          <View>
            <Text style={type.small}>Last week</Text>
            <Text style={[type.h1, { color: colors.muted }]}>{lb(trend?.last_week_avg)}</Text>
          </View>
          {trend?.change_kg != null && (
            <View>
              <Text style={type.small}>Change</Text>
              <Text style={[type.h1, { color: colors.accent }]}>{trend.change_kg > 0 ? '+' : ''}{lb(trend.change_kg)}</Text>
            </View>
          )}
        </View>
        {weeks.length > 1 && (
          <View style={{ flexDirection: 'row', alignItems: 'flex-end', gap: 6, height: 110 }}>
            {weeks.map((w) => (
              <View key={w.week_end} style={{ flex: 1, alignItems: 'center', gap: 4 }}>
                <Text style={{ color: colors.muted, fontSize: 10 }}>{lb(w.avg_kg)}</Text>
                <View style={{
                  width: '100%', borderRadius: 6, backgroundColor: colors.surface2,
                  height: 20 + 70 * (((w.avg_kg as number) - min) / (max - min || 1)),
                }} />
              </View>
            ))}
          </View>
        )}
        <Text style={type.small}>{trend?.verdict}</Text>
      </Card>

      <CoachBubble title="Weekly check-in" body="Every Sunday we review your week together: weight trend, photos, how you felt, and I adjust your plan." />
      <Button title="Start weekly check-in" onPress={() => router.push('/checkin')} />

      {photos.length > 0 && (
        <Card>
          <Label>Progress photos</Label>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
            {photos.slice(0, 9).map((p) => (
              <View key={p.id} style={{ width: '31%', gap: 2 }}>
                <Image source={{ uri: `${getApiUrl()}/progress-photos/${p.id}/image`, headers: authHeaders() }}
                  style={{ width: '100%', aspectRatio: 3 / 4, borderRadius: radius.sm, backgroundColor: colors.surface2 }} />
                <Text style={{ color: colors.muted, fontSize: 10 }}>{p.day} · {p.pose}</Text>
              </View>
            ))}
          </View>
        </Card>
      )}

      {history.map((c) => (
        <Card key={c.id}>
          <Label>Week ending {c.week_end}</Label>
          <Text style={type.body}>{c.coach_review}</Text>
        </Card>
      ))}
      </>
      )}
    </Screen>
  );
}
