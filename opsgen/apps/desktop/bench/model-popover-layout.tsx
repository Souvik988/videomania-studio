/** Real agent menu with local options only; no agents or model requests. */
import React from 'react';
import { createRoot } from 'react-dom/client';
import { ModelPopover } from '../chat/src/components/ModelPopover';
import { useLocalAgents } from '../chat/src/state/local-agent-store';
import type { LocalAgentSessionInfo, RosterAgent } from '../chat/src/lib/desktop-bridge';
import '../shell/shell.css';
import '../chat/src/chat.css';

const roster: RosterAgent[] = [
  { id: 'codex', name: 'Codex', shown: true, status: 'ready' },
  { id: 'claude', name: 'Claude Code', shown: true, status: 'missing' },
  { id: 'cursor', name: 'Cursor', shown: true, status: 'ready' },
  { id: 'codebuddy', name: 'CodeBuddy', shown: true, status: 'ready' },
];
const options = (extra = 0): NonNullable<LocalAgentSessionInfo['configOptions']> => [
  { id: 'model', name: 'Model', category: 'model', currentValue: 'deepseek', options: [
    { value: 'deepseek', name: 'Deepseek-V4.1-Flash' },
    { value: 'long', name: 'A model with a much longer display name' },
  ] },
  { id: 'effort', name: 'Effort', category: 'thought_level', currentValue: 'low', options: [
    { value: 'low', name: 'Low' }, { value: 'high', name: 'High' }, { value: 'max', name: 'Max' },
    ...Array.from({ length: extra }, (_, i) => ({ value: `extra-${i}`, name: `Extra effort ${i + 1}` })),
  ] },
];
useLocalAgents.setState({ picked: 'codebuddy', prefs: {}, options: { codebuddy: options() }, roster, hydrated: true });
(window as any).modelPopoverFixture = {
  grow: (extra: number) => useLocalAgents.getState().noteOptions('codebuddy', options(extra)),
};

createRoot(document.getElementById('root')!).render(
  <>
    <div className="of-chat" data-model-picker style={{ position: 'fixed', right: 16, bottom: 8, height: 'auto' }}>
      <ModelPopover placement="top" align="end" />
    </div>
    <div id="of-chat-layer" className="of-chat" />
  </>,
);
