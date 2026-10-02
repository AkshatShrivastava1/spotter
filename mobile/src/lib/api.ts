import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

const USER_KEY = 'spotter.userId';
const URL_KEY = 'spotter.apiUrl';

let userId: string | null = null;
let baseUrl: string | null = null;

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
  userId = await AsyncStorage.getItem(USER_KEY);
  baseUrl = (await AsyncStorage.getItem(URL_KEY)) || defaultUrl();
  return userId;
}

export async function setUserId(id: string | null) {
  userId = id;
  if (id) await AsyncStorage.setItem(USER_KEY, id);
  else await AsyncStorage.removeItem(USER_KEY);
}

export async function setApiUrl(url: string) {
  baseUrl = url.replace(/\/$/, '');
  await AsyncStorage.setItem(URL_KEY, baseUrl);
}

export const getApiUrl = () => baseUrl || defaultUrl();
export const getUserId = () => userId;
export const authHeaders = (): Record<string, string> => (userId ? { 'X-User-Id': userId } : {});

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
