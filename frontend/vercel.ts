const backendOrigin = process.env.RENDER_BACKEND_ORIGIN?.replace(/\/$/, '');

if (!backendOrigin?.startsWith('https://')) {
  throw new Error('RENDER_BACKEND_ORIGIN must be an HTTPS Render backend origin.');
}

/**
 * Vercel runs this file at build time. The browser keeps using relative /api
 * URLs, so its HttpOnly session cookie stays first-party on the Vercel domain.
 * RENDER_BACKEND_ORIGIN is deployment configuration, never a frontend secret.
 */
export const config = {
  outputDirectory: 'dist',
  rewrites: [
    { source: '/api/:path*', destination: `${backendOrigin}/api/:path*` },
    { source: '/(.*)', destination: '/index.html' },
  ],
};
