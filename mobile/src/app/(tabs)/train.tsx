import { Link, useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { Button, Card, ErrorText, Label, Screen } from '@/components/ui';
import { api } from '@/lib/api';
import { colors, type } from '@/lib/theme';
import { Plan } from '@/lib/types';

const TODAY = new Date().toLocaleDateString('en-US', { weekday: 'short' });

export default function TrainScreen() {
  const router = useRouter();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setPlan(await api.get<Plan>('/workouts/plan'));
    } catch (e: any) {
      setError(e.message);
    }
  }, []);
  useFocusEffect(useCallback(() => { load(); }, [load]));

  return (
    <Screen>
      <Text style={type.h1}>Training</Text>
      <ErrorText error={error} />
      {plan && (
        <>
          <Text style={type.h2}>{plan.name}</Text>
          <Text style={type.small}>{plan.notes}</Text>
          {plan.days.map((d) => (
            <Card key={d.day} style={d.day === TODAY ? { borderColor: colors.accent } : undefined}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                <Label>{d.day}{d.day === TODAY ? ' · today' : ''}</Label>
                <Text style={[type.body, { fontWeight: '700' }]}>{d.focus}</Text>
              </View>
              {d.exercises.map((e) => (
                <Link key={e.slug} href={{ pathname: '/exercise/[slug]', params: { slug: e.slug } }} asChild>
                  <Pressable style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                    <Text style={type.body}>{e.name}</Text>
                    <Text style={type.small}>{e.sets} x {e.reps}</Text>
                  </Pressable>
                </Link>
              ))}
              <Button title={d.day === TODAY ? 'Start' : 'Do this one'} variant={d.day === TODAY ? 'primary' : 'ghost'}
                onPress={() => router.push({ pathname: '/workout/[day]', params: { day: d.day } })} />
            </Card>
          ))}
          <Button title="Rebuild plan from my settings" variant="ghost"
            onPress={async () => setPlan(await api.post<Plan>('/workouts/plan/generate'))} />
        </>
      )}
    </Screen>
  );
}
