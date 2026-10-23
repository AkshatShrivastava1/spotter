import { Link, useRouter } from 'expo-router';
import { useState } from 'react';
import { Text } from 'react-native';

import { Button, Card, ErrorText, Field, Screen } from '@/components/ui';
import { getApiUrl, login, setApiUrl } from '@/lib/api';
import { colors, type } from '@/lib/theme';

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [url, setUrl] = useState(getApiUrl());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await setApiUrl(url);
      await login(email.trim(), password);
      router.replace('/');
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen>
      <Text style={type.h1}>Welcome back</Text>
      <Text style={type.small}>Log in to pick up where you left off.</Text>
      <Card>
        <Field label="Email" value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address"
          autoComplete="email" />
        <Field label="Password" value={password} onChangeText={setPassword} secureTextEntry autoComplete="password"
          onSubmitEditing={submit} />
      </Card>
      <ErrorText error={error} />
      <Button title="Log in" loading={busy} disabled={!email.trim() || !password} onPress={submit} />
      <Link href="/onboarding" style={{ color: colors.accent, fontWeight: '700', textAlign: 'center' }}>
        New here? Create an account
      </Link>
      <Card>
        <Field label="Server URL (dev)" value={url} onChangeText={setUrl} autoCapitalize="none" />
      </Card>
    </Screen>
  );
}
