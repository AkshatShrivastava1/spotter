import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

const TOKEN_KEY = 'spotter.token';
const LEGACY_USER_KEY = 'spotter.userId'; // pre-login builds stored a bare user id
const URL_KEY = 'spotter.apiUrl';

let token: string | null = null;
let baseUrl: string | null = null;
let onAuthLost: (() => void) | null = null;

/** Called when the server rejects our token (expired / logged out elsewhere). */
export const setOnAuthLost = (fn: (() => void) | null) => {
  onAuthLost = fn;
};

function defaultUrl(): string {
  // EXPO_PUBLIC_API_URL wins (set it to your laptop's LAN IP when testing on a phone),
  // then app.json extra.apiUrl.
  return (
    process.env.EXPO_PUBLIC_API_URL ||
    (Constants.expoConfig?.extra as { apiUrl?: string } | undefined)?.apiUrl ||
    'http://localhost:8000'
  );
}

export async function loadSession(): Promise<string | null> {
  token = await AsyncStorage.getItem(TOKEN_KEY);
  await AsyncStorage.removeItem(LEGACY_USER_KEY);
  baseUrl = (await AsyncStorage.getItem(URL_KEY)) || defaultUrl();
  return token;
}

export async function setToken(t: string | null) {
  token = t;
  if (t) await AsyncStorage.setItem(TOKEN_KEY, t);
  else await AsyncStorage.removeItem(TOKEN_KEY);
}

export async function logout() {
  await setToken(null);
}

export async function setApiUrl(url: string) {
  baseUrl = url.replace(/\/$/, '');
  await AsyncStorage.setItem(URL_KEY, baseUrl);
}

export const getApiUrl = () => baseUrl || defaultUrl();
export const isLoggedIn = () => !!token;
export const authHeaders = (): Record<string, string> => (token ? { Authorization: `Bearer ${token}` } : {});

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(method: string, path: string, body?: unknown, form?: FormData): Promise<T> {
  const headers: Record<string, string> = { ...authHeaders() };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  let res: Response;
  try {
    res = await fetch(`${getApiUrl()}${path}`, {
      method,
      headers,
      body: form ?? (body !== undefined ? JSON.stringify(body) : undefined),
    });
  } catch {
    throw new ApiError(0, `Can't reach the Spotter server at ${getApiUrl()}. Check it's running and the URL in Settings.`);
  }
  if (res.status === 401 && token && !path.startsWith('/auth/')) {
    await setToken(null);
    onAuthLost?.();
  }
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const j = await res.json();
      msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail ?? j);
    } catch {}
    throw new ApiError(res.status, msg);
  }
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(p: string) => request<T>('GET', p),
  post: <T>(p: string, body?: unknown) => request<T>('POST', p, body ?? {}),
  patch: <T>(p: string, body: unknown) => request<T>('PATCH', p, body),
  del: <T>(p: string) => request<T>('DELETE', p),
  upload: <T>(p: string, form: FormData) => request<T>('POST', p, undefined, form),
};

/** Build a multipart image part that works on iOS/Android (uri) and web (blob). */
export async function imagePart(uri: string, mimeType = 'image/jpeg', name = 'photo.jpg'): Promise<Blob | any> {
  if (uri.startsWith('blob:') || uri.startsWith('data:')) {
    return await (await fetch(uri)).blob();
  }
  return { uri, type: mimeType, name };
}

export type Units = 'imperial' | 'metric';
const KG_TO_LB = 2.20462;
export const unitLabel = (u: Units) => (u === 'imperial' ? 'lb' : 'kg');
export const fromKg = (kg: number | null | undefined, u: Units) =>
  kg == null ? '–' : (u === 'imperial' ? kg * KG_TO_LB : kg).toFixed(1);
export const toKg = (v: number, u: Units) => (u === 'imperial' ? v / KG_TO_LB : v);
export const getUnits = async (): Promise<Units> => (await api.get<{ units: Units }>('/users/me')).units;

export type AgeBand = 'child' | 'teen' | 'adult' | 'senior';
export type Profile = { units: Units; age_band: AgeBand; age: number };
export const getProfile = () => api.get<Profile>('/users/me');
export const isYouth = (b?: AgeBand) => b === 'child' || b === 'teen';

type AuthResponse = { access_token: string; user: { id: number; name: string } };

export async function login(email: string, password: string) {
  const r = await api.post<AuthResponse>('/auth/login', { email, password });
  await setToken(r.access_token);
  return r.user;
}

export async function signup(body: Record<string, unknown>) {
  const r = await api.post<AuthResponse>('/auth/signup', body);
  await setToken(r.access_token);
  return r.user;
}
