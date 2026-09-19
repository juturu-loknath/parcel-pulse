import { describe, expect, it } from 'vitest';
import { isEasilyGuessedPassword } from './auth';

describe('signup password guidance', () => {
  it('warns about clearly guessable passwords without rejecting them', () => {
    expect(isEasilyGuessedPassword('a')).toBe(true);
    expect(isEasilyGuessedPassword('password')).toBe(true);
    expect(isEasilyGuessedPassword('tulip-secret', 'tulip')).toBe(true);
  });

  it('does not warn for a non-obvious password', () => {
    expect(isEasilyGuessedPassword('pigeon-river-amber')).toBe(false);
  });
});
