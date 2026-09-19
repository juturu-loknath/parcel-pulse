import { describe, expect, it } from 'vitest';
import { ApiResponseError, readApiJson, userFacingApiError } from './api';

describe('readApiJson', () => {
  it('turns an empty Vite-style error response into a helpful API error', async () => {
    await expect(readApiJson(new Response(null, { status: 404 }), 'Could not retrieve parcel tracking details.')).rejects.toEqual(
      new ApiResponseError('Could not retrieve parcel tracking details. (HTTP 404).'),
    );
  });

  it('returns a valid successful JSON payload', async () => {
    await expect(readApiJson<{ current_status: string }>(new Response('{"current_status":"BOOKED"}', { status: 200 }), 'Tracking failed.')).resolves.toEqual({ current_status: 'BOOKED' });
  });

  it('does not expose a browser network exception to the user', () => {
    expect(userFacingApiError(new TypeError('Failed to fetch'), 'Could not reach ParcelPulse. Check your connection and try again.')).toBe('Could not reach ParcelPulse. Check your connection and try again.');
    expect(userFacingApiError(new ApiResponseError('No parcel was found. (HTTP 502).'), 'Fallback')).toBe('No parcel was found. (HTTP 502).');
  });
});
