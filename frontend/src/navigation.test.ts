import { describe, expect, it } from 'vitest';
import { hashForView, viewFromHash } from './navigation';

describe('courier selection navigation', () => {
  it('opens the home screen for a fresh or unknown URL fragment', () => {
    expect(viewFromHash('')).toBe('home');
    expect(viewFromHash('#/future-carrier')).toBe('home');
  });

  it('maps the APSRTC card to a refresh-safe route', () => {
    expect(hashForView('apsrtc')).toBe('#/apsrtc');
    expect(viewFromHash('#/apsrtc')).toBe('apsrtc');
  });
});
