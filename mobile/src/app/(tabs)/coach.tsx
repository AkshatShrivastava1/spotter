import Ionicons from '@expo/vector-icons/Ionicons';
import { useFocusEffect } from 'expo-router';
import { useCallback, useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Chip, Chips, ErrorText } from '@/components/ui';
import { api } from '@/lib/api';
import { colors, radius, space, type } from '@/lib/theme';
import { Notification } from '@/lib/types';

type Msg = { id: number | string; role: 'user' | 'coach'; content: string };

const QUICK = ['What should I eat next?', 'How am I doing today?', "I'm craving junk food", 'Give me a meal prep plan for the week'];

export default function CoachScreen() {
  const [tab, setTab] = useState<'chat' | 'inbox'>('chat');
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [inbox, setInbox] = useState<Notification[]>([]);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scroll = useRef<ScrollView>(null);

  const load = useCallback(async () => {
    try {
      setMsgs(await api.get<Msg[]>('/coach/messages'));
      setInbox(await api.get<Notification[]>('/notifications'));
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  async function send(message: string) {
    if (!message.trim()) return;
    setText('');
    setBusy(true);
    setError(null);
    setMsgs((m) => [...m, { id: `tmp-${Date.now()}`, role: 'user', content: message }]);
    try {
      const r = await api.post<{ reply: string }>('/coach/chat', { message });
      setMsgs((m) => [...m, { id: `r-${Date.now()}`, role: 'coach', content: r.reply }]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
      setTimeout(() => scroll.current?.scrollToEnd({ animated: true }), 50);
    }
  }

  async function read(n: Notification) {
    if (n.read) return;
    await api.post(`/notifications/${n.id}/read`);
    setInbox((all) => all.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
  }

  const unread = inbox.filter((n) => !n.read).length;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.bg }} edges={['top']}>
      <View style={{ padding: space.lg, paddingBottom: space.sm, gap: space.md }}>
        <Text style={type.h1}>Coach</Text>
        <Chips value={tab} onChange={setTab} options={[{ value: 'chat', label: 'Chat' }, { value: 'inbox', label: `Nudges${unread ? ` (${unread})` : ''}` }]} />
      </View>

      {tab === 'inbox' ? (
        <ScrollView contentContainerStyle={{ padding: space.lg, gap: space.md, paddingBottom: 120 }}>
          {inbox.length === 0 && <Text style={type.small}>No nudges yet. I&apos;ll check in through the day.</Text>}
          {inbox.map((n) => (
            <Pressable key={n.id} onPress={() => read(n)} style={[bubble, { opacity: n.read ? 0.6 : 1 }]}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                <Text style={[type.body, { fontWeight: '700' }]}>{n.title}</Text>
                {!n.read && <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: colors.accent }} />}
              </View>
              <Text style={type.body}>{n.body}</Text>
              <Text style={type.small}>{new Date(n.created_at + (n.created_at.endsWith('Z') ? '' : 'Z')).toLocaleString()}</Text>
            </Pressable>
          ))}
        </ScrollView>
      ) : (
        <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={90}>
          <ScrollView ref={scroll} contentContainerStyle={{ padding: space.lg, gap: space.sm }}
            onContentSizeChange={() => scroll.current?.scrollToEnd({ animated: false })}>
            {msgs.length === 0 && (
              <Text style={type.small}>Ask me anything: what to eat, how to fix a bad day, why the scale went up, how to do a lift.</Text>
            )}
            {msgs.map((m) => (
              <View key={m.id} style={[m.role === 'user' ? userBubble : bubble, { maxWidth: '88%' }]}>
                <Text style={[type.body, m.role === 'user' && { color: colors.accentInk }]}>{m.content}</Text>
              </View>
            ))}
            {busy && <Text style={type.small}>Coach is typing…</Text>}
            <ErrorText error={error} />
          </ScrollView>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: space.lg, gap: 8 }} style={{ flexGrow: 0 }}>
            {QUICK.map((q) => <Chip key={q} label={q} onPress={() => send(q)} />)}
          </ScrollView>
          <View style={{ flexDirection: 'row', padding: space.lg, gap: 8, alignItems: 'flex-end' }}>
            <TextInput value={text} onChangeText={setText} placeholder="Message your coach" placeholderTextColor={colors.muted}
              multiline style={input} />
            <Pressable onPress={() => send(text)} disabled={busy} style={sendBtn}>
              <Ionicons name="arrow-up" size={22} color={colors.accentInk} />
            </Pressable>
          </View>
        </KeyboardAvoidingView>
      )}
    </SafeAreaView>
  );
}

const bubble = {
  backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1, borderRadius: radius.lg,
  padding: space.md, gap: 6, alignSelf: 'flex-start' as const,
};
const userBubble = { ...bubble, backgroundColor: colors.accent, borderColor: colors.accent, alignSelf: 'flex-end' as const };
const input = {
  flex: 1, backgroundColor: colors.surface2, color: colors.text, borderRadius: radius.md, paddingHorizontal: 14,
  paddingVertical: 12, fontSize: 16, maxHeight: 120,
};
const sendBtn = { width: 46, height: 46, borderRadius: 23, backgroundColor: colors.accent, alignItems: 'center' as const, justifyContent: 'center' as const };
