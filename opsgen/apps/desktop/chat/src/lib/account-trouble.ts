/**
 * A turn that failed for the account the agent is signed in to, not for the work: signed out, a sign-in that expired
 * or was refused, or an account its organization does not let use the agent (Claude Code: "Your organization has
 * disabled Claude subscription access for Claude Code"). The chat offers Switch account by it, and names the account
 * signed in when the app knows it. Read from the error's words, so a turn kept from before says it too.
 */
import type { RosterAgent } from './desktop-bridge';

const ACCOUNT_TROUBLE = [
  /* Claude Code's subscription turned off by the person's organization */
  /\borganization has disabled\b/i,
  /* signed out: the agents' words ("Not logged in · Please run /login") and the app's ("… is not signed in.") */
  /\bnot (?:signed|logged) in\b/i,
  /\bplease run \/login\b/i,
  /* a sign-in refused or gone */
  /\b(?:session|token|credentials?) (?:has )?expired\b/i,
  /\binvalid (?:api key|token|credentials?|x-api-key)\b/i,
  /\bauthentication (?:failed|required|error)\b/i,
  /\bunauthori[sz]ed\b/i,
  /\b(?:401|403)\b/,
];

export function accountTrouble(error: string | null | undefined): boolean {
  return Boolean(error) && ACCOUNT_TROUBLE.some((re) => re.test(String(error)));
}

/**
 * Whose account it is, as the app's roster says: its organization (unless it only repeats the email, as a personal
 * Claude account's "<email>'s Organization" does) and its email; null when the agent does not tell.
 */
export function accountName(account: RosterAgent['account']): string | null {
  if (!account) return null;
  const org = account.org && !(account.email && account.org === `${account.email}'s Organization`) ? account.org : null;
  const parts = [org, account.email].filter(Boolean);
  return parts.length ? parts.join(' · ') : null;
}
