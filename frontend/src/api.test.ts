import { afterEach, describe, expect, it, vi } from 'vitest';
import { API_RESPONSE_BODY_TIMEOUT_MS, ApiResponseError, readApiJson, userFacingApiError } from './api';

afterEach(() => {
  vi.useRealTimers();
});

describe('readApiJson', () => {
  it('turns an empty Vite-style error response into a helpful API error', async () => {
    await expect(readApiJson(new Response(null, { status: 404 }), 'Could not retrieve parcel tracking details.')).rejects.toEqual(
      new ApiResponseError('Could not retrieve parcel tracking details. (HTTP 404).'),
    );
  });

  it('returns a valid successful JSON payload', async () => {
    await expect(readApiJson<{ current_status: string }>(new Response('{"current_status":"BOOKED"}', { status: 200 }), 'Tracking failed.')).resolves.toEqual({ current_status: 'BOOKED' });
  });

  it('reports an unreadable response body without exposing a browser exception', async () => {
    const unreadableResponse = {
      status: 200,
      text: async () => { throw new TypeError('Body stream failed'); },
    } as unknown as Response;

    await expect(readApiJson(unreadableResponse, 'Could not read that receipt.')).rejects.toEqual(
      new ApiResponseError('Could not read that receipt. The server response could not be read. Please try again.'),
    );
  });

  it('ends a stalled response-body read with a friendly timeout error', async () => {
    vi.useFakeTimers();
    expect(API_RESPONSE_BODY_TIMEOUT_MS).toBe(120_000);
    const stalledResponse = {
      status: 200,
      text: () => new Promise<string>(() => undefined),
    } as unknown as Response;

    const pending = readApiJson(stalledResponse, 'Could not read that receipt.');
    const timeoutError = expect(pending).rejects.toEqual(
      new ApiResponseError('Could not read that receipt. The server response took too long to read. Please try again.'),
    );
    await vi.advanceTimersByTimeAsync(API_RESPONSE_BODY_TIMEOUT_MS);
    await timeoutError;
  });

  it('does not expose a browser network exception to the user', () => {
    expect(userFacingApiError(new TypeError('Failed to fetch'), 'Could not reach ParcelPulse. Check your connection and try again.')).toBe('Could not reach ParcelPulse. Check your connection and try again.');
    expect(userFacingApiError(new ApiResponseError('No parcel was found. (HTTP 502).'), 'Fallback')).toBe('No parcel was found. (HTTP 502).');
  });
});
