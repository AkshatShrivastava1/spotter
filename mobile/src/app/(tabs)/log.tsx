import Ionicons from '@expo/vector-icons/Ionicons';
import * as ImagePicker from 'expo-image-picker';
import { useEffect, useState } from 'react';
import { Image, Pressable, Text, TextInput, View } from 'react-native';

import { Button, Card, Chips, CoachBubble, ErrorText, Field, Label, Screen } from '@/components/ui';
import { api, getProfile, imagePart, isYouth } from '@/lib/api';
import { colors, radius, type } from '@/lib/theme';
import { FoodItem, MealType, ParseResult } from '@/lib/types';

function defaultMealType(): MealType {
  const h = new Date().getHours();
  if (h < 11) return 'breakfast';
  if (h < 16) return 'lunch';
  if (h < 18) return 'snack';
  return 'dinner';
}

type LogResult = { feedback: string; recovery: { over_kcal: number; trim_next_days_kcal: number; extra_steps_today: number } | null };

export default function LogScreen() {
  const [mealType, setMealType] = useState<MealType>(defaultMealType());
  const [text, setText] = useState('');
  const [photo, setPhoto] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [items, setItems] = useState<FoodItem[] | null>(null);
  const [question, setQuestion] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LogResult | null>(null);
  const [youth, setYouth] = useState(false);

  useEffect(() => {
    getProfile().then((p) => setYouth(isYouth(p.age_band))).catch(() => {});
  }, []);

  function reset() {
    setText('');
    setPhoto(null);
    setItems(null);
    setQuestion('');
    setResult(null);
  }

  async function estimateText() {
    setBusy(true);
    setError(null);
    try {
      const r = await api.post<ParseResult>('/food/parse', { text });
      setItems(r.items);
      setQuestion(r.clarifying_question);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function pick(camera: boolean) {
    const opts: ImagePicker.ImagePickerOptions = { mediaTypes: ['images'], quality: 0.6 };
    if (camera) await ImagePicker.requestCameraPermissionsAsync();
    const res = camera ? await ImagePicker.launchCameraAsync(opts) : await ImagePicker.launchImageLibraryAsync(opts);
    if (res.canceled) return;
    const asset = res.assets[0];
    setPhoto(asset);
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append('file', await imagePart(asset.uri, asset.mimeType ?? 'image/jpeg', asset.fileName ?? 'meal.jpg'));
      form.append('note', text);
      const r = await api.upload<ParseResult>('/food/photo', form);
      setItems(r.items);
      setQuestion(r.clarifying_question);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  function edit(i: number, key: keyof FoodItem, value: string) {
    setItems((prev) => prev!.map((it, idx) => (idx === i ? { ...it, [key]: key === 'name' || key === 'quantity' ? value : Number(value) || 0 } : it)));
  }

  async function save() {
    if (!items?.length) return;
    setBusy(true);
    setError(null);
    try {
      const r = await api.post<LogResult>('/meals', {
        meal_type: mealType,
        items,
        description: text,
        source: photo ? 'photo' : 'text',
      });
      setResult(r);
      setItems(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const total = (items ?? []).reduce(
    (a, i) => ({ kcal: a.kcal + i.kcal, p: a.p + i.protein_g, c: a.c + i.carbs_g, f: a.f + i.fat_g }),
    { kcal: 0, p: 0, c: 0, f: 0 },
  );

  if (result) {
    return (
      <Screen>
        <Text style={type.h1}>Logged.</Text>
        <CoachBubble body={result.feedback} />
        {result.recovery && result.recovery.over_kcal > 0 && (
          <Card>
            <Label>Recovery plan</Label>
            <Text style={type.body}>
              {result.recovery.over_kcal} kcal over. Next 2 days trimmed by {result.recovery.trim_next_days_kcal} kcal each
              {result.recovery.extra_steps_today ? `, plus ${result.recovery.extra_steps_today.toLocaleString()} extra steps today` : ''}.
              No skipping meals, no punishment cardio.
            </Text>
          </Card>
        )}
        <Button title="Log another" onPress={reset} />
      </Screen>
    );
  }

  return (
    <Screen>
      <Text style={type.h1}>What did you eat?</Text>
      <Chips value={mealType} onChange={setMealType} options={[
        { value: 'breakfast', label: 'Breakfast' }, { value: 'lunch', label: 'Lunch' },
        { value: 'dinner', label: 'Dinner' }, { value: 'snack', label: 'Snack' }]} />

      {!items && (
        <>
          <Field value={text} onChangeText={setText} multiline style={{ minHeight: 90, textAlignVertical: 'top' }}
            placeholder="e.g. 3 rotis, a bowl of dal, some bhindi and a glass of chaas" />
          <Button title="Estimate" onPress={estimateText} loading={busy} disabled={!text.trim()} />
          <View style={{ flexDirection: 'row', gap: 12 }}>
            <Pressable style={photoBtn} onPress={() => pick(true)}>
              <Ionicons name="camera" size={22} color={colors.text} />
              <Text style={type.small}>Snap meal</Text>
            </Pressable>
            <Pressable style={photoBtn} onPress={() => pick(false)}>
              <Ionicons name="image" size={22} color={colors.text} />
              <Text style={type.small}>From library</Text>
            </Pressable>
          </View>
          <Text style={type.small}>Tip: add a note with the photo (&quot;cooked in 2 tbsp ghee&quot;) and the estimate gets much better.</Text>
        </>
      )}

      {photo && <Image source={{ uri: photo.uri }} style={{ width: '100%', height: 200, borderRadius: radius.lg }} />}

      {items && (
        <Card>
          <Label>Check my estimate</Label>
          {items.length === 0 && <Text style={type.small}>Couldn&apos;t find food in that. Try describing it.</Text>}
          {items.map((it, i) => (
            <View key={i} style={{ gap: 6, borderBottomColor: colors.border, borderBottomWidth: 1, paddingBottom: 10 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text style={[type.body, { fontWeight: '700', flex: 1 }]}>{it.name}</Text>
                {it.confidence === 'low' && <Text style={{ color: colors.carbs, fontSize: 12, marginRight: 8 }}>low confidence</Text>}
                <Pressable onPress={() => setItems(items.filter((_, idx) => idx !== i))}>
                  <Ionicons name="close" size={18} color={colors.muted} />
                </Pressable>
              </View>
              <TextInput value={it.quantity} onChangeText={(v) => edit(i, 'quantity', v)} style={qtyInput} placeholderTextColor={colors.muted} />
              <View style={{ flexDirection: 'row', gap: 8 }}>
                {(youth ? (['protein_g', 'carbs_g', 'fat_g'] as const) : (['kcal', 'protein_g', 'carbs_g', 'fat_g'] as const)).map((k) => (
                  <View key={k} style={{ flex: 1 }}>
                    <Text style={type.small}>{k === 'kcal' ? 'kcal' : k[0].toUpperCase() + ' g'}</Text>
                    <TextInput keyboardType="numeric" value={String(Math.round(it[k]))} onChangeText={(v) => edit(i, k, v)} style={numInput} />
                  </View>
                ))}
              </View>
            </View>
          ))}
          <Text style={[type.h2]}>
            {youth ? '' : `${Math.round(total.kcal)} kcal · `}P{Math.round(total.p)} C{Math.round(total.c)} F{Math.round(total.f)}
          </Text>
          {!!question && <CoachBubble body={question} />}
          <ErrorText error={error} />
          <View style={{ flexDirection: 'row', gap: 12 }}>
            <Button title="Redo" variant="ghost" onPress={reset} style={{ flex: 1 }} />
            <Button title="Log it" onPress={save} loading={busy} disabled={!items.length} style={{ flex: 2 }} />
          </View>
        </Card>
      )}
      {!items && <ErrorText error={error} />}
    </Screen>
  );
}

const photoBtn = {
  flex: 1, height: 70, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border,
  backgroundColor: colors.surface, alignItems: 'center' as const, justifyContent: 'center' as const, gap: 4,
};
const numInput = {
  backgroundColor: colors.surface2, color: colors.text, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 6, fontSize: 15,
};
const qtyInput = { ...numInput, color: colors.muted };
