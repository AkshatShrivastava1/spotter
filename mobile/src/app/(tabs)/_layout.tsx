import Ionicons from '@expo/vector-icons/Ionicons';
import { Tabs } from 'expo-router/js-tabs';
import type { ColorValue } from 'react-native';

import { colors } from '@/lib/theme';

type IconName = React.ComponentProps<typeof Ionicons>['name'];
const icon = (name: IconName) =>
  function TabIcon({ color, size }: { color: ColorValue; size: number }) {
    return <Ionicons name={name} color={color as string} size={size} />;
  };

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: { backgroundColor: colors.surface, borderTopColor: colors.border },
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.muted,
      }}
    >
      <Tabs.Screen name="index" options={{ title: 'Today', tabBarIcon: icon('flash') }} />
      <Tabs.Screen name="log" options={{ title: 'Log food', tabBarIcon: icon('restaurant') }} />
      <Tabs.Screen name="coach" options={{ title: 'Coach', tabBarIcon: icon('chatbubble-ellipses') }} />
      <Tabs.Screen name="train" options={{ title: 'Train', tabBarIcon: icon('barbell') }} />
      <Tabs.Screen name="progress" options={{ title: 'Progress', tabBarIcon: icon('stats-chart') }} />
    </Tabs>
  );
}
