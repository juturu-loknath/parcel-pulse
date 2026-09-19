import { describe, expect, it } from 'vitest';
import { homeCopy } from './home-copy';

describe('courier home copy', () => {
  it('has English, Telugu, and bilingual home labels', () => {
    expect(homeCopy('en', 'chooseService')).toBe('Choose your parcel service');
    expect(homeCopy('te', 'home')).toBe('హోమ్');
    expect(homeCopy('both', 'apsrtcAvailable')).toContain(' / ');
  });
});
