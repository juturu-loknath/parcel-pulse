import type { AppLanguage } from './receipt-upload';

export const languagePreferenceKey = 'parcelpulse-language';
const languages: readonly AppLanguage[] = ['en', 'te', 'both'];

type StorageLike = Pick<Storage, 'getItem' | 'setItem'>;

export function readLanguagePreference(storage: Pick<StorageLike, 'getItem'> | null | undefined): AppLanguage {
  const saved = storage?.getItem(languagePreferenceKey);
  return languages.includes(saved as AppLanguage) ? saved as AppLanguage : 'en';
}

export function saveLanguagePreference(storage: Pick<StorageLike, 'setItem'>, language: AppLanguage) {
  storage.setItem(languagePreferenceKey, language);
}
