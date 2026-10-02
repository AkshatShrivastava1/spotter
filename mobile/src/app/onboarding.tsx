import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Text, View } from 'react-native';

import { Button, Card, Chips, CoachBubble, ErrorText, Field, Label, Screen } from '@/components/ui';
import { api, getApiUrl, setApiUrl, setUserId } from '@/lib/api';
import { colors, type } from '@/lib/theme';

const splitList = (s: string) => s.split(',').map((x) => x.trim()).filter(Boolean);

const STEPS = ['You', 'Goal', 'Food', 'Training', 'Coach'] as const;

export default function Onboarding() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [units, setUnits] = useState<'imperial' | 'metric'>('imperial');
  const [f, setF] = useState({
    name: '', sex: 'male', age: '', heightCm: '', heightFt: '', heightIn: '', weight: '', goalWeight: '',
    goal: 'lose', activity_level: 'moderate',
    diet_type: 'omnivore', home_foods: '', cuisines: '', allergies: '',
    equipment: 'full_gym', training_days_per_week: '4', experience: 'beginner',
    coach_tone: 'firm', wake_time: '07:30', sleep_time: '23:30', apiUrl: getApiUrl(),
    guardian_name: '', guardian_email: '', guardian_consent: '',
  });
  const age = Number(f.age);
  const child = age > 0 && age < 13;
  const youth = age > 0 && age < 18;
  const set = (k: keyof typeof f) => (v: string) => setF((p) => ({ ...p, [k]: v }));

  const toKg = (v: string) => (units === 'imperial' ? Number(v) * 0.4536 : Number(v));
  const heightCm = () =>
    units === 'imperial' ? (Number(f.heightFt) * 12 + Number(f.heightIn || 0)) * 2.54 : Number(f.heightCm);

  const valid = [
    f.name && age >= 6 && heightCm() > 90 && toKg(f.weight) > 10 &&
      (!child || (f.guardian_name.trim() && f.guardian_consent === 'yes')),
    true,
    f.home_foods.trim().length > 0,
    true,
    true,
  ][step];

  async function finish() {
    setBusy(true);
    setError(null);
    try {
      await setApiUrl(f.apiUrl);
      const res = await api.post<{ user: { id: number } }>('/users', {
        name: f.name.trim(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/New_York',
        units,
        sex: f.sex,
        age: Number(f.age),
        height_cm: Math.round(heightCm()),
        weight_kg: Math.round(toKg(f.weight) * 10) / 10,
        goal: youth ? 'maintain' : f.goal,
        goal_weight_kg: !youth && f.goalWeight ? Math.round(toKg(f.goalWeight) * 10) / 10 : null,
        activity_level: f.activity_level,
        coach_tone: f.coach_tone,
        diet_type: f.diet_type,
        home_foods: splitList(f.home_foods),
        cuisines: splitList(f.cuisines),
        allergies: splitList(f.allergies),
        equipment: f.equipment,
        training_days_per_week: Number(f.training_days_per_week),
        experience: f.experience,
        wake_time: f.wake_time,
        sleep_time: f.sleep_time,
        guardian_name: child ? f.guardian_name.trim() : null,
        guardian_email: child ? f.guardian_email.trim() || null : null,
        guardian_consent: child && f.guardian_consent === 'yes',
      });
      await setUserId(String(res.user.id));
      router.replace('/');
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen>
      <Text style={[type.label, { color: colors.accent }]}>
        Step {step + 1} of {STEPS.length} · {STEPS[step]}
      </Text>

      {step === 0 && (
        <>
          <Text style={type.h1}>Let&apos;s meet. I&apos;m Spotter, your coach.</Text>
          <Text style={type.small}>I need a few numbers to set your targets. Only used for coaching.</Text>
          <Card>
            <Field label="First name" value={f.name} onChangeText={set('name')} placeholder="Akshat" />
            <Label>Sex (for metabolism math)</Label>
            <Chips value={f.sex} onChange={set('sex')} options={[{ value: 'male', label: 'Male' }, { value: 'female', label: 'Female' }]} />
            <Field label="Age" keyboardType="number-pad" value={f.age} onChangeText={set('age')} />
            <Chips value={units} onChange={setUnits} options={[{ value: 'imperial', label: 'lb / ft' }, { value: 'metric', label: 'kg / cm' }]} />
            {units === 'imperial' ? (
              <View style={{ flexDirection: 'row', gap: 12 }}>
                <View style={{ flex: 1 }}><Field label="Height ft" keyboardType="number-pad" value={f.heightFt} onChangeText={set('heightFt')} /></View>
                <View style={{ flex: 1 }}><Field label="in" keyboardType="number-pad" value={f.heightIn} onChangeText={set('heightIn')} /></View>
              </View>
            ) : (
              <Field label="Height (cm)" keyboardType="number-pad" value={f.heightCm} onChangeText={set('heightCm')} />
            )}
            <Field label={`Weight (${units === 'imperial' ? 'lb' : 'kg'})`} keyboardType="decimal-pad" value={f.weight} onChangeText={set('weight')} />
          </Card>
          {child && (
            <Card>
              <Label>Parent or guardian</Label>
              <Text style={type.small}>
                Spotter works for kids too, with a grown-up in charge. Kid accounts never see calorie counts, diets or
                weight goals: just moving, water, sleep and good plates.
              </Text>
              <Field label="Parent / guardian name" value={f.guardian_name} onChangeText={set('guardian_name')} />
              <Field label="Parent email (optional)" value={f.guardian_email} onChangeText={set('guardian_email')}
                autoCapitalize="none" keyboardType="email-address" />
              <Chips value={f.guardian_consent} onChange={set('guardian_consent')}
                options={[{ value: 'yes', label: "I'm the parent/guardian and I agree" }]} />
            </Card>
          )}
          {youth && !child && (
            <Text style={type.small}>Teen accounts focus on fueling sport and school, not calorie counting or weight loss.</Text>
          )}
        </>
      )}

      {step === 1 && (
        <>
          <Text style={type.h1}>{youth ? 'Your mission: healthy habits' : 'What are we chasing?'}</Text>
          {youth && (
            <CoachBubble body={child
              ? "We'll work on moving every day, drinking water, sleeping well and eating colourful plates. Growing bodies don't need diets."
              : "We'll focus on fueling your sport and school, getting strong with good technique, and sleep. No diets: you're still growing."} />
          )}
          <Card>
            {!youth && <Chips value={f.goal} onChange={set('goal')} options={[
              { value: 'lose', label: 'Lose fat' }, { value: 'maintain', label: 'Maintain / recomp' }, { value: 'gain', label: 'Build muscle' }]} />}
            {!youth && (
              <Field label={`Goal weight (${units === 'imperial' ? 'lb' : 'kg'}, optional)`} keyboardType="decimal-pad" value={f.goalWeight} onChangeText={set('goalWeight')} />
            )}
            <Label>Activity outside the gym</Label>
            <Chips value={f.activity_level} onChange={set('activity_level')} options={[
              { value: 'sedentary', label: 'Desk all day' }, { value: 'light', label: 'Light' },
              { value: 'moderate', label: 'Moderate' }, { value: 'active', label: 'Active job' }, { value: 'very_active', label: 'Very active' }]} />
          </Card>
        </>
      )}

      {step === 2 && (
        <>
          <Text style={type.h1}>What do you actually eat?</Text>
          <CoachBubble body="I don't hand out generic meal plans. Tell me what you usually cook or eat at home, and I'll build suggestions around that." />
          <Card>
            <Chips value={f.diet_type} onChange={set('diet_type')} options={[
              { value: 'omnivore', label: 'Eat everything' }, { value: 'eggetarian', label: 'Veg + eggs' },
              { value: 'vegetarian', label: 'Vegetarian' }, { value: 'vegan', label: 'Vegan' }, { value: 'pescatarian', label: 'Pescatarian' }]} />
            <Field label="Home staples (comma separated)" value={f.home_foods} onChangeText={set('home_foods')}
              placeholder="dal, roti, rice, eggs, chicken curry, oats" multiline />
            <Field label="Cuisines you like" value={f.cuisines} onChangeText={set('cuisines')} placeholder="North Indian, Mexican" />
            <Field label="Allergies / foods to avoid" value={f.allergies} onChangeText={set('allergies')} placeholder="peanuts" />
          </Card>
        </>
      )}

      {step === 3 && (
        <>
          <Text style={type.h1}>{child ? 'How often do you want to play-train?' : 'How do you train?'}</Text>
          <Card>
            {!child && <Label>Equipment</Label>}
            {!child && <Chips value={f.equipment} onChange={set('equipment')} options={[
              { value: 'full_gym', label: 'Full gym' }, { value: 'home_dumbbells', label: 'Dumbbells at home' }, { value: 'bodyweight', label: 'Bodyweight only' }]} />}
            <Label>Days per week</Label>
            <Chips value={f.training_days_per_week} onChange={set('training_days_per_week')}
              options={['2', '3', '4', '5', '6'].map((d) => ({ value: d, label: d }))} />
            <Label>Experience</Label>
            <Chips value={f.experience} onChange={set('experience')} options={[
              { value: 'beginner', label: 'New / < 1 yr' }, { value: 'intermediate', label: '1-3 yrs' }, { value: 'advanced', label: '3+ yrs' }]} />
          </Card>
        </>
      )}

      {step === 4 && (
        <>
          <Text style={type.h1}>{child ? 'Almost done!' : 'How hard should I push you?'}</Text>
          <Card>
            {!child && <Chips value={f.coach_tone} onChange={set('coach_tone')} options={[
              { value: 'gentle', label: 'Gentle' }, { value: 'firm', label: 'Firm' },
              ...(youth ? [] : [{ value: 'drill', label: 'Drill sergeant' }])]} />}
            {!child && <Text style={type.small}>
              {f.coach_tone === 'gentle' ? 'Encouraging, celebrates small wins.' : f.coach_tone === 'firm'
                ? 'Direct and caring. Calls things out, then gives you the fix.' : 'Blunt tough love. Holds you to your word.'}
            </Text>}
            <View style={{ flexDirection: 'row', gap: 12 }}>
              <View style={{ flex: 1 }}><Field label="Wake time" value={f.wake_time} onChangeText={set('wake_time')} /></View>
              <View style={{ flex: 1 }}><Field label="Bed time" value={f.sleep_time} onChangeText={set('sleep_time')} /></View>
            </View>
            <Text style={type.small}>I time your nudges around these.</Text>
          </Card>
          <Card>
            <Field label="Server URL (dev)" value={f.apiUrl} onChangeText={set('apiUrl')} autoCapitalize="none" />
            <Text style={type.small}>On a phone, use your laptop&apos;s LAN IP, e.g. http://192.168.1.20:8000</Text>
          </Card>
        </>
      )}

      <ErrorText error={error} />
      <View style={{ flexDirection: 'row', gap: 12 }}>
        {step > 0 && <Button title="Back" variant="ghost" onPress={() => setStep(step - 1)} style={{ flex: 1 }} />}
        {step < STEPS.length - 1 ? (
          <Button title="Next" disabled={!valid} onPress={() => setStep(step + 1)} style={{ flex: 2 }} />
        ) : (
          <Button title="Build my plan" loading={busy} onPress={finish} style={{ flex: 2 }} />
        )}
      </View>
    </Screen>
  );
}
