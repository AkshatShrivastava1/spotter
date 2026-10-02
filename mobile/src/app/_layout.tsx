import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { getUserId, loadSession } from '@/lib/api';
import { registerForPush, syncSteps } from '@/lib/device';
import { colors } from '@/lib/theme';

export default function RootLayout() {
  const [ready, setReady] = useState(false);
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    loadSession().then(() => setReady(true));
  }, []);

  useEffect(() => {
    if (!ready) return;
    const onboarding = segments[0] === 'onboarding';
    if (!getUserId() && !onboarding) router.replace('/onboarding');
    if (getUserId() && !onboarding) {
      registerForPush();
      syncSteps();
    }
  }, [ready, segments, router]);

  if (!ready) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.bg, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.bg },
          headerTintColor: colors.text,
          headerShadowVisible: false,
          contentStyle: { backgroundColor: colors.bg },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="onboarding" options={{ headerShown: false }} />
        <Stack.Screen name="checkin" options={{ title: 'Weekly check-in', presentation: 'modal' }} />
        <Stack.Screen name="settings" options={{ title: 'Settings' }} />
        <Stack.Screen name="workout/[day]" options={{ title: 'Workout' }} />
        <Stack.Screen name="exercise/[slug]" options={{ title: 'Form guide' }} />
      </Stack>
    </SafeAreaProvider>
  );
}
