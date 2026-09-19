import { describe, expect, it } from 'vitest';
import { canStartSavedCheck, isCurrentStatus, savedParcelCopy } from './saved-parcel';

describe('saved parcel helpers', () => {
  it('provides English, Telugu, and bilingual one-tap labels', () => {
    expect(savedParcelCopy('en', 'checkLatest')).toBe('Check latest status');
    expect(savedParcelCopy('te', 'checking')).toContain('తనిఖీ');
    expect(savedParcelCopy('both', 'saveAndCheck')).toContain(' / ');
  });

  it('recognizes an unchanged tracking response', () => {
    const parcel = { current_status: 'IN_TRANSIT', origin: 'Fictional Origin', destination: 'Fictional Destination', events: [{ status: 'IN_TRANSIT' }] };
    expect(isCurrentStatus(parcel, { ...parcel, events: [{ status: 'IN_TRANSIT' }] })).toBe(true);
    expect(isCurrentStatus(parcel, { ...parcel, current_status: 'DELIVERED' })).toBe(false);
  });

  it('prevents a second saved-parcel request while one is active', () => {
    expect(canStartSavedCheck(null)).toBe(true);
    expect(canStartSavedCheck(42)).toBe(false);
  });
});
