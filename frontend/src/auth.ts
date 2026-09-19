import { ApiResponseError, apiUrl, readApiJson } from './api';

export type AuthUser = { id: string; username: string };
// APSRTC may make two payload attempts and retry once (up to ~48 seconds with
// current backend defaults). Keep a finite deadline while allowing proxy and
// processing overhead; an alternate contact receives its own request deadline.
export const API_REQUEST_TIMEOUT_MS = 120_000;

export async function authFetch(path: string, init: RequestInit = {}) {
  const controller = new AbortController();
  const parentSignal = init.signal;
  const abortForParent = () => controller.abort();
  if (parentSignal?.aborted) controller.abort();
  else parentSignal?.addEventListener('abort', abortForParent, { once: true });

  let timeoutId: ReturnType<typeof setTimeout>;
  const timeout = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(() => {
      controller.abort();
      reject(new ApiResponseError('The request took too long. Please try again.'));
    }, API_REQUEST_TIMEOUT_MS);
  });

  try {
    return await Promise.race([
      fetch(apiUrl(path), { ...init, credentials: 'include', headers: { ...(init.headers || {}) }, signal: controller.signal }),
      timeout,
    ]);
  } finally {
    clearTimeout(timeoutId!);
    parentSignal?.removeEventListener('abort', abortForParent);
  }
}

export async function currentUser() {
  const response = await authFetch('/api/auth/me');
  if (response.status === 401) return null;
  return readApiJson<AuthUser>(response, 'Could not verify your sign-in.');
}

export async function signIn(username: string, password: string) {
  const response = await authFetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
  return readApiJson<AuthUser>(response, 'Could not sign in.');
}

export async function signUp(username: string, password: string, signupCode: string) {
  const response = await authFetch('/api/auth/signup', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password, signup_code: signupCode }) });
  return readApiJson<AuthUser>(response, 'Could not create your account.');
}

export function isEasilyGuessedPassword(password: string, username = '') {
  const normalized = password.trim().toLowerCase();
  return normalized.length > 0 && (normalized.length < 8 || ['password', '12345678', 'qwerty', 'parcelpulse'].includes(normalized) || (username.length >= 3 && normalized.includes(username.trim().toLowerCase())));
}

export async function signOut() {
  const response = await authFetch('/api/auth/logout', { method: 'POST' });
  if (!response.ok) await readApiJson(response, 'Could not sign out.');
}
