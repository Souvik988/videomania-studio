/**
 * Deleting layers inside a page (the Layers panel's delete, the picture's Delete key and menu): the page is shared by
 * every clip of it and is the agent's, so it is never written. What goes is the layer in this clip: an override of
 * `display: none` (applied with priority, it takes the layer out of the page's flow as if it were not written), the
 * one entry its clip keeps for it. Every other change pointing only at it or at what is inside it goes too — its own
 * moves and styles, those of the layers inside it, the component properties made of them — so nothing is left that
 * changes nothing. It is one edit of film.html: an undo puts it all back.
 *
 * Pure: no React, no DOM, so `node --test` runs it.
 */

import type { FilmOverride } from './film.ts';
import type { ComponentProp } from './component-props.ts';
import type { OverrideTarget } from './film-overrides.ts';

/** The style that deletes a layer. */
const DELETED_STYLE = { display: 'none' } as const;

const same = (o: { at?: string; n?: number }, t: OverrideTarget) => o.at === t.at && (o.n ?? null) === (t.n ?? null);

/**
 * The clip's overrides with `targets` deleted: each one's entries replaced by one `display: none` entry (where its
 * first entry was, else last), and the entries `gone` says point only at deleted layers (one answer per entry of
 * `all`, studio/server/stage.js `within`) left out. The clip's own entry (its fades) is kept. Null: none left.
 */
export function withDeleted(
  all: readonly FilmOverride[] | undefined, targets: readonly OverrideTarget[], gone: readonly boolean[] = [],
): FilmOverride[] | null {
  const list = all ?? [];
  const out: FilmOverride[] = [];
  const placed = new Set<OverrideTarget>();
  const entry = (t: OverrideTarget): FilmOverride => (
    { at: t.at, ...(t.n != null ? { n: t.n } : {}), style: { ...DELETED_STYLE } }
  );
  list.forEach((o, i) => {
    const t = o.at === undefined ? undefined : targets.find((x) => same(o, x));
    if (t) {
      if (!placed.has(t)) { placed.add(t); out.push(entry(t)); }
      return;
    }
    if (o.at !== undefined && gone[i]) return;
    out.push(o);
  });
  for (const t of targets) if (!placed.has(t)) out.push(entry(t));
  return out.length ? out : null;
}

/** The component properties left once the ones `gone` says name only deleted layers (one answer per property) go. */
export function propsWithoutDeleted(list: readonly ComponentProp[], gone: readonly boolean[]): ComponentProp[] {
  return list.filter((p, i) => p.type === 'var' || !gone[i]);
}

/** What `within` is asked of a clip: where each override and each property points (a variable points at no layer). */
export function pointersOf(overrides: readonly FilmOverride[] | undefined, props: readonly ComponentProp[]): {
  overrides: (OverrideTarget | null)[];
  props: (OverrideTarget | null)[];
} {
  const of = (o: { at?: string; n?: number }) => (o.at ? { at: o.at, ...(o.n != null ? { n: o.n } : {}) } : null);
  return { overrides: (overrides ?? []).map(of), props: props.map((p) => (p.type === 'var' ? null : of(p))) };
}
