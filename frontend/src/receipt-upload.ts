export type AppLanguage = 'en' | 'te' | 'both';
export type ReceiptUploadOption = 'gallery' | 'camera';

const labels: Record<ReceiptUploadOption, Record<'en' | 'te', string>> = {
  gallery: { en: 'Choose from Gallery', te: 'గ్యాలరీ నుండి ఎంచుకోండి' },
  camera: { en: 'Take a Photo', te: 'కొత్త ఫోటో తీయండి' },
};

export const receiptInputAttributes = {
  gallery: { accept: 'image/*' },
  camera: { accept: 'image/*', capture: 'environment' },
} as const;

export function receiptUploadLabel(language: AppLanguage, option: ReceiptUploadOption) {
  const label = labels[option];
  if (language === 'en') return label.en;
  if (language === 'te') return label.te;
  return `${label.en} / ${label.te}`;
}
