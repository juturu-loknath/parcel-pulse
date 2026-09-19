export class ApiResponseError extends Error {}

export function userFacingApiError(error: unknown, fallbackMessage: string) {
  return error instanceof ApiResponseError ? error.message : fallbackMessage;
}

export const apiBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const apiUrl = (path: string) => `${apiBase}${path}`;

export async function readApiJson<T>(response: Response, fallbackMessage: string): Promise<T> {
  const body = await response.text();
  let payload: unknown = null;

  if (body) {
    try {
      payload = JSON.parse(body);
    } catch {
      throw new ApiResponseError(`${fallbackMessage} The server returned an invalid response (HTTP ${response.status}).`);
    }
  }

  if (!response.ok) {
    const detail = typeof payload === 'object' && payload !== null && 'detail' in payload && typeof payload.detail === 'string' ? payload.detail : fallbackMessage;
    throw new ApiResponseError(`${detail} (HTTP ${response.status}).`);
  }

  if (payload === null) throw new ApiResponseError(`${fallbackMessage} The server returned an empty response.`);
  return payload as T;
}
