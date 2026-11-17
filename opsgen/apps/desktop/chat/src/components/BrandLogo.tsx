'use client';

import React from 'react';

/* The OpsGen mark: a frame with a play triangle and a spark at its corner (the agent at work). */
export function BrandLogo({ size = 18, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="currentColor" className={`block shrink-0 ${className ?? ''}`.trim()} role="img" aria-label="OpsGen">
      <path fillRule="evenodd" d="M24 10H66Q90 10 90 34V66Q90 90 66 90H34Q10 90 10 66V24Q10 10 24 10ZM34 24Q24 24 24 34V66Q24 76 34 76H66Q76 76 76 66V40Q76 24 60 24Z" />
      <path d="M42 37L64 50L42 63Z" />
      <path d="M84 4L87 13L96 16L87 19L84 28L81 19L72 16L81 13Z" />
    </svg>
  );
}
