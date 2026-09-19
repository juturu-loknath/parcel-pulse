import type { AppLanguage } from './receipt-upload';

type HomeCopyKey = 'welcome' | 'chooseService' | 'apsrtcAvailable' | 'comingSoon' | 'openApsrtc' | 'home';

const copy: Record<HomeCopyKey, Record<'en' | 'te', string>> = {
  welcome: { en: 'Welcome to simple parcel tracking.', te: 'సులభమైన పార్సెల్ ట్రాకింగ్‌కు స్వాగతం.' },
  chooseService: { en: 'Choose your parcel service', te: 'మీ పార్సెల్ సేవను ఎంచుకోండి' },
  apsrtcAvailable: { en: 'Tracking available now', te: 'ట్రాకింగ్ ఇప్పుడు అందుబాటులో ఉంది' },
  comingSoon: { en: 'More parcel services coming soon.', te: 'మరిన్ని పార్సెల్ సేవలు త్వరలో అందుబాటులోకి వస్తాయి.' },
  openApsrtc: { en: 'Open APSRTC Logistics', te: 'APSRTC లాజిస్టిక్స్ తెరవండి' },
  home: { en: 'Home', te: 'హోమ్' },
};

export function homeCopy(language: AppLanguage, key: HomeCopyKey) {
  const value = copy[key];
  if (language === 'en') return value.en;
  if (language === 'te') return value.te;
  return `${value.en} / ${value.te}`;
}
