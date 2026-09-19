import { apiUrl, readApiJson } from './api';

export type AuthUser = { id: string; username: string };

export async function authFetch(path: string, init: RequestInit = {}) {
  return fetch(apiUrl(path), { ...init, credentials: 'include', headers: { ...(init.headers || {}) } });
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
