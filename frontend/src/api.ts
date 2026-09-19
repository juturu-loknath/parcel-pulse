export class ApiResponseError extends Error {}

export function userFacingApiError(error: unknown, fallbackMessage: string) {
  return error instanceof ApiResponseError ? error.message : fallbackMessage;
}

export const apiBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const apiUrl = (path: string) => `${apiBase}${path}`;
export const API_RESPONSE_BODY_TIMEOUT_MS = 120_000;

export async function readApiJson<T>(response: Response, fallbackMessage: string): Promise<T> {
  let timeoutId: ReturnType<typeof setTimeout>;
  const bodyTimeout = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(() => {
      reject(new ApiResponseError(`${fallbackMessage} The server response took too long to read. Please try again.`));
    }, API_RESPONSE_BODY_TIMEOUT_MS);
  });

  let body: string;
  try {
    body = await Promise.race([response.text(), bodyTimeout]);
  } catch (error) {
    if (error instanceof ApiResponseError) throw error;
    throw new ApiResponseError(`${fallbackMessage} The server response could not be read. Please try again.`);
  } finally {
    clearTimeout(timeoutId!);
  }
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
