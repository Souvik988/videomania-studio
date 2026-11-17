/**
 * The speeds the player plays at, forward only, the pitch kept: the viewer's menu (two rows of four: slower, then
 * faster), the full-screen player's.
 */
export const PLAYBACK_SPEEDS = [0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4] as const;

export const SPEED_MIN = PLAYBACK_SPEEDS[0];
export const SPEED_MAX = PLAYBACK_SPEEDS[PLAYBACK_SPEEDS.length - 1];

/** The speed as it is shown: `1.5×`. */
export const speedText = (speed: number) => `${speed}×`;

/** The step of PLAYBACK_SPEEDS nearest to a speed (a speed set some other way, the shuttle's, falls between them). */
export function speedStep(speed: number): number {
  let best = 0;
  for (let i = 1; i < PLAYBACK_SPEEDS.length; i++) {
    if (Math.abs(PLAYBACK_SPEEDS[i] - speed) < Math.abs(PLAYBACK_SPEEDS[best] - speed)) best = i;
  }
  return best;
}
