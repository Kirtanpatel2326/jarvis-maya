'use client';

import { useEffect } from 'react';
import { activateStealthProtocol } from '@/lib/stealthProtocol';

export default function StealthInitializer() {
  useEffect(() => {
    activateStealthProtocol();
  }, []);

  return null;
}
