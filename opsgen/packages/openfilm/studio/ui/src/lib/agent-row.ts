import type { HostAgent } from '@/lib/host';

/**
 * What Settings › Agents offers for an agent that is not found: Locate (the program is somewhere else), and Install,
 * either its official installer run here (`run`) or its install page (`page`). Claude Code waiting in the Claude app
 * gets no installer: the app downloads it once its Code tab is opened. An existing CLI can still be selected.
 */
export function missingActions(agent: Pick<HostAgent, 'setupRequired' | 'install' | 'installer'>, host: { locate: boolean; install: boolean }) {
  if (agent.setupRequired === 'code-tab') return { locate: host.locate, install: null };
  const install: 'run' | 'page' | null = agent.installer && host.install ? 'run' : agent.install ? 'page' : null;
  return { locate: host.locate, install };
}

/**
 * How a connected agent switches account: `here`, one that signs out with its own command (the app signs it out and
 * opens its sign-in); `elsewhere`, in the agent itself or its maker's app, as the row then says. Null for the own key
 * and for one not connected.
 */
export function switchOffer(agent: Pick<HostAgent, 'id' | 'status' | 'signOut'>, host: { switchAccount: boolean }): 'here' | 'elsewhere' | null {
  if (agent.id === 'byok' || agent.status !== 'ready') return null;
  return agent.signOut && host.switchAccount ? 'here' : 'elsewhere';
}

/**
 * The organization an account's line names, unless it only says the email again: a personal Claude account's
 * organization is "<email>'s Organization".
 */
export function accountOrg(account: { org?: string | null; email?: string | null }): string | null {
  if (!account.org) return null;
  return account.email && account.org === `${account.email}'s Organization` ? null : account.org;
}

/**
 * Why one of the person's own models was not saved, in their language: the desktop app names each of its own
 * sentences by a code (agent-roster.mjs probeModel and saveOwnModel), with the address, status or reason it names.
 * The service's own words, and a code with no words here, are shown as the app said them.
 */
export function ownModelError(failure: { error: string; code?: string; url?: string; status?: number; reason?: string }, t: (path: string) => string): string {
  if (!failure.code) return failure.error;
  const path = `settings.agents.ownErrors.${failure.code.replace(/-(\w)/g, (_, c: string) => c.toUpperCase())}`;
  const words = t(path);
  if (words === path) return failure.error;
  return words.replace('{url}', failure.url ?? '').replace('{status}', String(failure.status ?? '')).replace('{reason}', failure.reason ?? '');
}
