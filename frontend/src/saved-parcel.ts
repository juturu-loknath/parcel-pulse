import type { AppLanguage } from './receipt-upload';

type SavedParcelCopyKey = 'checkLatest' | 'checking' | 'alreadyUpToDate' | 'reloadSaved' | 'missingContact' | 'saveAndCheck' | 'remove';

const copy: Record<SavedParcelCopyKey, Record<'en' | 'te', string>> = {
  checkLatest: { en: 'Check latest status', te: 'తాజా స్థితిని తనిఖీ చేయండి' },
  checking: { en: 'Checking status…', te: 'స్థితిని తనిఖీ చేస్తున్నాము…' },
  alreadyUpToDate: { en: 'Already up to date', te: 'ఇప్పటికే తాజాగా ఉంది' },
  reloadSaved: { en: 'Reload saved parcels', te: 'సేవ్ చేసిన పార్సెల్‌లను మళ్లీ లోడ్ చేయండి' },
  missingContact: { en: 'Enter a sender or receiver mobile number to check this parcel.', te: 'ఈ పార్సెల్‌ను తనిఖీ చేయడానికి పంపినవారి లేదా అందుకునేవారి మొబైల్ నంబర్ నమోదు చేయండి.' },
  saveAndCheck: { en: 'Save and check status', te: 'సేవ్ చేసి స్థితిని తనిఖీ చేయండి' },
  remove: { en: 'Remove parcel', te: 'పార్సెల్‌ను తొలగించండి' },
};

export function savedParcelCopy(language: AppLanguage, key: SavedParcelCopyKey) {
  const value = copy[key];
  if (language === 'en') return value.en;
  if (language === 'te') return value.te;
  return `${value.en} / ${value.te}`;
}

export type ParcelSnapshot = Pick<
  { current_status: string; origin?: string; destination?: string; events: unknown[] },
  'current_status' | 'origin' | 'destination' | 'events'
>;

export function isCurrentStatus(previous: ParcelSnapshot, next: ParcelSnapshot) {
  return previous.current_status === next.current_status
    && previous.origin === next.origin
    && previous.destination === next.destination
    && JSON.stringify(previous.events) === JSON.stringify(next.events);
}

export function canStartSavedCheck(checkingId: number | null) {
  return checkingId === null;
}
