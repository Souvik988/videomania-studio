/** Startup/model refresh fixture: no agent process or model request is started. */
import React from 'react';
import { createRoot } from 'react-dom/client';
import { ModelPopover } from '../chat/src/components/ModelPopover';
import { useLocalAgents } from '../chat/src/state/local-agent-store';
import type { RosterAgent } from '../chat/src/lib/desktop-bridge';
import '../shell/shell.css';
import '../chat/src/chat.css';

localStorage.setItem('openfilm.language', 'en');
localStorage.setItem('openfilm.local-agents.v2', JSON.stringify({ picked: 'codex', prefs: {}, options: {} }));
let roster: RosterAgent[] = [
  { id: 'codex', name: 'Codex', shown: true, status: 'checking' },
  { id: 'opencode', name: 'OpenCode', shown: true, status: 'ready' },
  { id: 'cursor', name: 'Cursor', shown: false, status: 'checking' },
];
const initial = structuredClone(roster);
const listeners = new Set<(list: RosterAgent[]) => void>();
const calls: string[] = [];
let release: (list: RosterAgent[]) => void = () => {};
let released = false;
const oldList = new Promise<RosterAgent[]>((done) => { release = done; });
const publish = () => { for (const listener of listeners) listener(roster); };
(window as any).openfilmDesktop = {
  agents: {
    list: async () => released ? roster : oldList,
    onChange: (listener: (list: RosterAgent[]) => void) => { listeners.add(listener); return () => listeners.delete(listener); },
  },
  localAgents: {
    probe: async (id: string) => {
      calls.push(id);
      const revision = roster.find((a) => a.id === id)?.configurationRevision ?? 0;
      const name = `${id === 'codex' ? 'Codex' : 'OpenCode'} ${revision ? 'Updated' : 'Ready'} Model`;
      return { ok: true, info: { configOptions: [{ id: 'model', category: 'model', name: 'Model', currentValue: 'model', options: [{ name, value: 'model' }] }] } };
    },
  },
};
(window as any).agentStartupFixture = {
  checking: () => publish(),
  ready: () => { roster = roster.map((a) => a.id === 'codex' ? { ...a, status: 'ready' } : a); publish(); },
  release: () => { released = true; release(initial); },
  refresh: () => { roster = roster.map((a) => ({ ...a, configurationRevision: 1 })); publish(); },
  calls,
  state: () => useLocalAgents.getState().roster,
};
createRoot(document.getElementById('root')!).render(
  <div className="of-chat" style={{ padding: 40, width: 520 }}>
    <div data-model-picker><ModelPopover /></div><div id="of-chat-layer" className="of-chat" />
  </div>,
);
