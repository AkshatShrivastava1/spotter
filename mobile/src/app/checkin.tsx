import * as ImagePicker from 'expo-image-picker';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { Image, Text, View } from 'react-native';

import { Button, Card, Chips, CoachBubble, ErrorText, Field, Label, Screen } from '@/components/ui';
import { api, fromKg, getProfile, imagePart, isYouth, unitLabel, Units } from '@/lib/api';
import { colors, radius, type } from '@/lib/theme';
import { Checkin, CheckinQuestion, Trend } from '@/lib/types';

type Status = { due: boolean; questions: CheckinQuestion[]; trend: Trend; week: Record<string, number> };

export default function CheckinScreen() {
  const router = useRouter();
  const [status, setStatus] = useState<Status | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [photos, setPhotos] = useState<{ id: number; uri: string; pose: string }[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Checkin | null>(null);
  const [units, setUnits] = useState<Units>('imperial');
  const [youth, setYouth] = useState(false);

  useEffect(() => {
    api.get<Status>('/checkin').then(setStatus).catch((e) => setError(e.message));
    getProfile().then((p) => { setUnits(p.units); setYouth(isYouth(p.age_band)); }).catch(() => {});
  }, []);

  async function addPhoto(pose: string) {
    await ImagePicker.requestCameraPermissionsAsync();
    const r = await ImagePicker.launchCameraAsync({ mediaTypes: ['images'], quality: 0.6 }).catch(() =>
      ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.6 }),
    );
    if (r.canceled) return;
    const a = r.assets[0];
    try {
      const form = new FormData();
      form.append('file', await imagePart(a.uri, a.mimeType ?? 'image/jpeg', a.fileName ?? `${pose}.jpg`));
      form.append('pose', pose);
      const saved = await api.upload<{ id: number }>('/progress-photos', form);
      setPhotos((p) => [...p.filter((x) => x.pose !== pose), { id: saved.id, uri: a.uri, pose }]);
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const parsed: Record<string, string | number> = {};
      for (const q of status!.questions) {
        const v = answers[q.key];
        if (v) parsed[q.key] = q.type === 'scale' ? Number(v) : v;
      }
      setResult(await api.post<Checkin>('/checkin', { answers: parsed, photo_ids: photos.map((p) => p.id) }));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (result) {
    return (
      <Screen>
        <Text style={type.h1}>Your week, reviewed</Text>
        <CoachBubble body={result.coach_review} />
        {result.kcal_change !== 0 && (
          <Card><Text style={type.body}>New daily target: {result.kcal_change > 0 ? '+' : ''}{result.kcal_change} kcal.</Text></Card>
        )}
        <Button title="Done" onPress={() => router.back()} />
      </Screen>
    );
  }

  if (!status) return <Screen><ErrorText error={error} /></Screen>;
  const t = status.trend;
  const w = status.week;

  return (
    <Screen>
      <Text style={type.h1}>How was your week?</Text>
      <Card>
        <Label>The numbers</Label>
        {!youth && <Text style={type.body}>
          Avg weight: {fromKg(t.this_week_avg, units)} {unitLabel(units)} (last week {fromKg(t.last_week_avg, units)})
        </Text>}
        <Text style={type.body}>Logged {w.days_logged}/7 days · protein hit {w.days_protein_hit}x · {w.workouts} workouts · {Number(w.avg_steps).toLocaleString()} avg steps</Text>
      </Card>

      {!youth && <Card>
        <Label>Progress photos</Label>
        <Text style={type.small}>Same spot, same light, same time of day. Front and side.</Text>
        <View style={{ flexDirection: 'row', gap: 12 }}>
          {['front', 'side'].map((pose) => {
            const p = photos.find((x) => x.pose === pose);
            return (
              <View key={pose} style={{ flex: 1, gap: 6 }}>
                {p ? <Image source={{ uri: p.uri }} style={{ width: '100%', aspectRatio: 3 / 4, borderRadius: radius.md }} />
                  : <View style={{ width: '100%', aspectRatio: 3 / 4, borderRadius: radius.md, backgroundColor: colors.surface2 }} />}
                <Button title={p ? `Retake ${pose}` : `Take ${pose}`} variant="ghost" onPress={() => addPhoto(pose)} />
              </View>
            );
          })}
        </View>
      </Card>}

      {status.questions.map((q) => (
        <Card key={q.key}>
          <Text style={type.body}>{q.q}</Text>
          {q.type === 'scale' ? (
            <Chips value={answers[q.key] ?? ''} onChange={(v) => setAnswers((a) => ({ ...a, [q.key]: v }))}
              options={['1', '2', '3', '4', '5'].map((n) => ({ value: n, label: n }))} />
          ) : (
            <Field value={answers[q.key] ?? ''} onChangeText={(v) => setAnswers((a) => ({ ...a, [q.key]: v }))} multiline />
          )}
        </Card>
      ))}
      <ErrorText error={error} />
      <Button title="Review my week" onPress={submit} loading={busy} />
    </Screen>
  );
}
