import { describe, expect, it } from 'vitest';
import { createDeviceId } from './device-id';

describe('createDeviceId', () => {
  it('uses a browser UUID when secure-context randomUUID is available', () => {
    const uuidCrypto = { randomUUID: () => '00000000-0000-4000-8000-000000000000', getRandomValues: <T extends ArrayBufferView>(values: T) => values } as unknown as Crypto;
    expect(createDeviceId(uuidCrypto)).toBe('00000000-0000-4000-8000-000000000000');
  });

  it('falls back to getRandomValues when randomUUID is unavailable on a LAN HTTP origin', () => {
    const deterministicCrypto = { getRandomValues: (values: Uint8Array) => { values.fill(1); return values; } } as unknown as Crypto;
    const id = createDeviceId(deterministicCrypto);
    expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-8[0-9a-f]{3}-[0-9a-f]{12}$/);
  });
});
