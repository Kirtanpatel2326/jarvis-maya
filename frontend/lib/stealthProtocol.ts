// frontend/lib/stealthProtocol.ts

export function activateStealthProtocol() {
  if (typeof window === 'undefined') return;

  // 1. Override Document Visibility API
  Object.defineProperty(document, 'hidden', {
    get: () => false,
    configurable: true,
  });

  Object.defineProperty(document, 'visibilityState', {
    get: () => 'visible',
    configurable: true,
  });

  // 2. Block Visibility Change Events from Reaching Monitor Scripts
  window.addEventListener(
    'visibilitychange',
    (e) => {
      e.stopImmediatePropagation();
    },
    true
  );

  // 3. Block Window Blur and Focus-Loss Events
  window.addEventListener(
    'blur',
    (e) => {
      e.stopImmediatePropagation();
    },
    true
  );

  // 4. Spoof Document Focus Checks
  document.hasFocus = () => true;

  console.log('[J.A.R.V.I.S. Stealth] Tab-Switch Detection Blinded (100% Coverage).');
}
