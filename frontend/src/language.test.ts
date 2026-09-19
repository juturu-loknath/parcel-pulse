import { describe, expect, it } from 'vitest';
import { languagePreferenceKey, readLanguagePreference, saveLanguagePreference } from './language';

function storageWith(value: string | null) {
  const values = new Map<string, string>();
  if (value !== null) values.set(languagePreferenceKey, value);
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, next: string) => values.set(key, next),
  };
}

describe('language preference', () => {
  it('defaults a new user to English', () => {
    expect(readLanguagePreference(storageWith(null))).toBe('en');
  });

  it('preserves a valid saved preference instead of replacing it', () => {
    expect(readLanguagePreference(storageWith('te'))).toBe('te');
    expect(readLanguagePreference(storageWith('both'))).toBe('both');
  });

  it('persists an explicitly selected language', () => {
    const storage = storageWith(null);
    saveLanguagePreference(storage, 'te');
    expect(readLanguagePreference(storage)).toBe('te');
  });
});
