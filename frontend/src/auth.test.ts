import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiResponseError } from './api';
import { API_REQUEST_TIMEOUT_MS, authFetch, isEasilyGuessedPassword } from './auth';

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('signup password guidance', () => {
  it('warns about clearly guessable passwords without rejecting them', () => {
    expect(isEasilyGuessedPassword('a')).toBe(true);
    expect(isEasilyGuessedPassword('password')).toBe(true);
    expect(isEasilyGuessedPassword('tulip-secret', 'tulip')).toBe(true);
  });

  it('does not warn for a non-obvious password', () => {
    expect(isEasilyGuessedPassword('pigeon-river-amber')).toBe(false);
  });

  it('aborts and reports a friendly error when fetch never resolves', async () => {
    vi.useFakeTimers();
    expect(API_REQUEST_TIMEOUT_MS).toBe(120_000);
    let requestSignal: AbortSignal | undefined;
    const fetchMock = vi.fn((_: string, init?: RequestInit) => {
      requestSignal = init?.signal ?? undefined;
      return new Promise<Response>(() => undefined);
    });
    vi.stubGlobal('fetch', fetchMock);

    const pending = authFetch('/api/track');
    const timeoutError = expect(pending).rejects.toEqual(new ApiResponseError('The request took too long. Please try again.'));
    await vi.advanceTimersByTimeAsync(API_REQUEST_TIMEOUT_MS);

    await timeoutError;
    expect(fetchMock).toHaveBeenCalledWith('/api/track', expect.objectContaining({ credentials: 'include' }));
    expect(requestSignal?.aborted).toBe(true);
  });
});
