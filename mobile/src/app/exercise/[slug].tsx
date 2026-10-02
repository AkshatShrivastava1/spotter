import { Stack, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { Text } from 'react-native';

import { Card, ErrorText, Label, Screen } from '@/components/ui';
import { api } from '@/lib/api';
import { colors, type } from '@/lib/theme';
import { Exercise } from '@/lib/types';

export default function ExerciseScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const [ex, setEx] = useState<Exercise | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Exercise>(`/exercises/${slug}`).then(setEx).catch((e) => setError(e.message));
  }, [slug]);

  return (
    <Screen>
      <Stack.Screen options={{ title: ex?.name ?? 'Form guide' }} />
      <ErrorText error={error} />
      {ex && (
        <>
          <Text style={type.h1}>{ex.name}</Text>
          <Text style={type.small}>Works: {ex.muscles.join(', ')} · {ex.rep_range[0]}-{ex.rep_range[1]} reps</Text>
          <Card>
            <Label>Do this</Label>
            {ex.cues.map((c, i) => (
              <Text key={c} style={type.body}><Text style={{ color: colors.accent, fontWeight: '800' }}>{i + 1}. </Text>{c}</Text>
            ))}
          </Card>
          <Card>
            <Label>Watch out for</Label>
            {ex.mistakes.map((m) => <Text key={m} style={type.body}><Text style={{ color: colors.danger }}>✕ </Text>{m}</Text>)}
          </Card>
          <Text style={type.small}>Camera form check (pose tracking) is on the roadmap.</Text>
        </>
      )}
    </Screen>
  );
}
