export type AppView = 'home' | 'apsrtc';

export function viewFromHash(hash: string): AppView {
  return hash === '#/apsrtc' ? 'apsrtc' : 'home';
}

export function hashForView(view: AppView) {
  return view === 'apsrtc' ? '#/apsrtc' : '';
}
