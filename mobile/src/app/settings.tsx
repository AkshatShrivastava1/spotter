import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { Text } from 'react-native';

import { Button, Card, Chips, ErrorText, Field, Label, Screen } from '@/components/ui';
import { api, getApiUrl, setApiUrl, setUserId } from '@/lib/api';
import { type } from '@/lib/theme';

type Me = {
  name: string; coach_tone: string; home_foods: string[]; target_kcal: number; target_protein_g: number;
  target_water_ml: number; target_steps: number; goal: string; age_band: string;
};

export default function Settings() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [foods, setFoods] = useState('');
  const [url, setUrl] = useState(getApiUrl());
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Me>('/users/me').then((m) => { setMe(m); setFoods(m.home_foods.join(', ')); }).catch((e) => setError(e.message));
  }, []);

  async function save(patch: Record<string, unknown>) {
    try {
      setError(null);
      const m = await api.patch<Me>('/users/me', patch);
      setMe(m);
      setMsg('Saved.');
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <Screen>
      <Card>
        <Label>Server</Label>
        <Field value={url} onChangeText={setUrl} autoCapitalize="none" />
        <Button title="Save server URL" variant="ghost" onPress={async () => { await setApiUrl(url); setMsg('Server updated.'); }} />
      </Card>
      {me && (
        <>
          {me.age_band !== 'child' && <Card>
            <Label>Coach intensity</Label>
            <Chips value={me.coach_tone} onChange={(v) => save({ coach_tone: v })}
              options={[{ value: 'gentle', label: 'Gentle' }, { value: 'firm', label: 'Firm' },
                ...(me.age_band === 'teen' ? [] : [{ value: 'drill', label: 'Drill sergeant' }])]} />
          </Card>}
          {(me.age_band === 'adult' || me.age_band === 'senior') && <Card>
            <Label>Goal</Label>
            <Chips value={me.goal} onChange={(v) => save({ goal: v, recompute_targets: true })}
              options={[{ value: 'lose', label: 'Lose fat' }, { value: 'maintain', label: 'Maintain' }, { value: 'gain', label: 'Build muscle' }]} />
            <Text style={type.small}>
              Targets: {me.target_kcal} kcal · {me.target_protein_g} g protein · {me.target_water_ml} ml water · {me.target_steps} steps
            </Text>
          </Card>}
          <Card>
            <Field label="Home staples" value={foods} onChangeText={setFoods} multiline />
            <Button title="Save foods" variant="ghost"
              onPress={() => save({ home_foods: foods.split(',').map((s) => s.trim()).filter(Boolean) })} />
          </Card>
        </>
      )}
      {msg && <Text style={type.small}>{msg}</Text>}
      <ErrorText error={error} />
      <Button title="Reset app (start over)" variant="danger" onPress={async () => { await setUserId(null); router.replace('/onboarding'); }} />
    </Screen>
  );
}
