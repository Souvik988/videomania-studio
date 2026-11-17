/** Real model menu and preference store; the fake bridge never starts an agent or sends a prompt. */
import React from 'react';
import { createRoot } from 'react-dom/client';
import { ModelPopover } from '../chat/src/components/ModelPopover';
import { agentModelSummary, agentOptions, effectivePrefs, useLocalAgents } from '../chat/src/state/local-agent-store';
import { createLocalAgentTurn, runLocalAgentTurn } from '../chat/src/lib/local-agent-run';
import type { LocalAgentId } from '../chat/src/lib/desktop-bridge';
import '../shell/shell.css';
import '../chat/src/chat.css';

const agent = (new URLSearchParams(location.search).get('agent') ?? 'opencode') as LocalAgentId;
const effortId = agent === 'cursor' ? 'reasoning' : agent === 'copilot' ? 'reasoning_effort' : 'effort';
const roster = [{ id: agent, name: agent, shown: true, status: 'ready' as const }];
const calls: Array<string | undefined> = [];
const sent: unknown[] = [];
let onEvent: (event: any) => void = () => {};
const options = (model = 'plain') => [
  { id: 'model', name: 'Model', category: 'model', currentValue: model, options: [
    { value: 'plain', name: 'Plain model' }, { value: 'reasoning', name: 'Reasoning model' }, { value: 'default', name: 'Auto' },
    ...(agent === 'cursor' ? [{ value: 'grok', name: 'Grok 4.7' }] : []),
  ] },
  ...(model === 'reasoning' ? [{ id: effortId, name: 'Effort', category: 'thought_level', currentValue: 'default', options: [
    { value: 'default', name: 'Default' }, { value: 'low', name: 'Low' }, { value: 'high', name: 'High' }, { value: 'max', name: 'Max' },
  ] }] : []),
  ...(model === 'grok' ? [{ id: 'reasoning_effort', name: 'Effort', category: 'thought_level', currentValue: 'high', options: [
    { value: 'low', name: 'Low' }, { value: 'medium', name: 'Medium' }, { value: 'high', name: 'High' },
  ] }] : []),
  ...(['reasoning', 'grok'].includes(model) ? [{ id: 'fast', name: 'Fast', category: 'model_config', currentValue: 'false', options: [
    { value: 'false', name: 'Off' }, { value: 'true', name: 'Fast' },
  ] }] : []),
];
let sessionOptions = options();
(window as any).openfilmDesktop = {
  agents: { list: async () => roster, onChange: () => () => {} },
  localAgents: {
    onEvent: (receive: typeof onEvent) => { onEvent = receive; return () => {}; },
    start: async () => ({ ok: true, key: 'fake-session', info: { configOptions: sessionOptions } }),
    setOption: async (_key: string, id: string, value: string) => {
      sent.push([id, value]);
      const option = sessionOptions.find((o) => o.id === id);
      if (!option?.options.some((o) => o.value === value)) return { ok: false, error: 'Invalid params' };
      sessionOptions = id === 'model' ? (option.currentValue === value ? sessionOptions : options(value))
        : sessionOptions.map((o) => o.id === id ? { ...o, currentValue: value } : o);
      return { ok: true, result: { configOptions: sessionOptions } };
    },
    prompt: async () => { sent.push(['prompt']); return { ok: true, stopReason: 'end_turn' }; },
    probe: async (_agent: string, model?: string) => {
      calls.push(model);
      await new Promise((done) => setTimeout(done, model === 'reasoning' ? 150 : 10));
      return { ok: true, info: { configOptions: options(model) } };
    },
  },
};
const legacy = agent === 'cursor' && new URLSearchParams(location.search).has('legacy');
const legacyModel = 'reasoning[reasoning_effort=high]';
useLocalAgents.setState({ picked: agent,
  prefs: legacy ? { cursor: { model: legacyModel } } : {},
  options: legacy ? { cursor: [{ id: 'model', name: 'Model', category: 'model', currentValue: legacyModel, options: [{ value: legacyModel, name: 'Reasoning model' }] }] } : {},
  roster, hydrated: true });
(window as any).modelOptionsFixture = {
  agent, effortId, calls, sent,
  desync: () => { sessionOptions = options('default'); },
  stale: () => {
    const state = useLocalAgents.getState();
    useLocalAgents.setState({ prefs: { ...state.prefs, [agent]: { ...state.prefs[agent], fast: 'true', context: '256k', reasoning_effort: 'high' } } });
  },
  send: async () => {
    const state = useLocalAgents.getState();
    sent.length = 0;
    return runLocalAgentTurn({ agent, projectId: 'fixture', conversation: 'fixture', cwd: '/fake', text: 'not sent to any agent',
      turn: createLocalAgentTurn(`local:fixture-${Date.now()}`, agent),
      options: effectivePrefs(state.prefs, agent, roster, state.options[agent]),
      onOptions: (next) => useLocalAgents.getState().noteOptions(agent, next),
    });
  },
  publish: () => {
    onEvent({ key: 'fake-session', kind: 'update', update: { sessionUpdate: 'config_option_update', configOptions: sessionOptions.map((o) =>
      o.category === 'thought_level' ? { ...o, options: [...o.options, { value: 'xhigh', name: 'Extra high' }] } : o) } });
  },
  state: () => {
    const state = useLocalAgents.getState();
    const visible = agentOptions(state, agent);
    const prefs = effectivePrefs(state.prefs, agent, state.roster, visible);
    return { options: state.options[agent], prefs, visible, summary: agentModelSummary(visible, prefs), rawPrefs: state.prefs[agent] };
  },
  model: (model: string) => useLocalAgents.getState().setPref(agent, 'model', model),
};

createRoot(document.getElementById('root')!).render(
  <div className="of-chat" style={{ padding: 40, width: 480 }}>
    <div data-model-picker><ModelPopover /></div>
    <div id="of-chat-layer" className="of-chat" />
  </div>,
);
