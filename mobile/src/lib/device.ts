import Constants from 'expo-constants';
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import { Pedometer } from 'expo-sensors';
import { Platform } from 'react-native';

import { api } from './api';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

/**
 * Registers this phone for coach push notifications.
 * Needs a physical device and a development build (Expo Go on Android no longer supports remote push).
 * Failing here is fine: the in-app coach inbox still shows every nudge.
 */
export async function registerForPush(): Promise<string | null> {
  try {
    if (Platform.OS === 'web' || !Device.isDevice) return null;
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('coach', {
        name: 'Coach',
        importance: Notifications.AndroidImportance.HIGH,
      });
    }
    const { status } = await Notifications.requestPermissionsAsync();
    if (status !== 'granted') return null;
    const projectId =
      (Constants.expoConfig?.extra as any)?.eas?.projectId ?? (Constants as any).easConfig?.projectId;
    const token = (await Notifications.getExpoPushTokenAsync(projectId ? { projectId } : undefined)).data;
    await api.post('/users/me/push-token', { token });
    return token;
  } catch (e) {
    console.log('[spotter] push registration skipped:', e);
    return null;
  }
}

/** Reads today's steps from the phone (iOS supports ranges; Android falls back to manual entry). */
export async function syncSteps(): Promise<number | null> {
  try {
    if (Platform.OS !== 'ios') return null;
    if (!(await Pedometer.isAvailableAsync())) return null;
    await Pedometer.requestPermissionsAsync();
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    const { steps } = await Pedometer.getStepCountAsync(start, new Date());
    await api.post('/track/steps', { amount: steps });
    return steps;
  } catch (e) {
    console.log('[spotter] step sync skipped:', e);
    return null;
  }
}
