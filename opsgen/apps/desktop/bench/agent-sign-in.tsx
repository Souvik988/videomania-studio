/** Settings with a simulated agent bridge; no real terminal or sign-in is opened. */
import React from 'react';
import { createRoot } from 'react-dom/client';
import { AgentsSection } from '../../../packages/openfilm/studio/ui/src/components/settings/AgentsSection';
import '../shell/shell.css';

createRoot(document.getElementById('root')!).render(<div style={{ padding: 24, maxWidth: 900 }}><AgentsSection /></div>);
