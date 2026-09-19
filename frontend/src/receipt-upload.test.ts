import { describe, expect, it } from 'vitest';
import { receiptInputAttributes, receiptUploadLabel } from './receipt-upload';

describe('receipt upload options', () => {
  it('uses a normal image picker for gallery selection', () => {
    expect(receiptInputAttributes.gallery).toEqual({ accept: 'image/*' });
    expect(receiptInputAttributes.gallery).not.toHaveProperty('capture');
  });

  it('requests the rear camera only for the camera option', () => {
    expect(receiptInputAttributes.camera).toEqual({ accept: 'image/*', capture: 'environment' });
  });

  it('shows the selected language on the upload choices', () => {
    expect(receiptUploadLabel('en', 'gallery')).toBe('Choose from Gallery');
    expect(receiptUploadLabel('te', 'camera')).toBe('కొత్త ఫోటో తీయండి');
    expect(receiptUploadLabel('both', 'gallery')).toBe('Choose from Gallery / గ్యాలరీ నుండి ఎంచుకోండి');
  });
});
