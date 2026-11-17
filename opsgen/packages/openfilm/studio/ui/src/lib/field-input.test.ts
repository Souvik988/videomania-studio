import { test } from 'node:test';
import assert from 'node:assert/strict';
import { applyFieldInput, parseFieldInput } from './field-input.ts';
import { formatTimecode, frameAt } from './timecode.ts';

test('a typed number, arithmetic and px', () => {
  assert.deepEqual(parseFieldInput('240'), { set: 240 });
  assert.deepEqual(parseFieldInput('1440/2'), { set: 720 });
  assert.deepEqual(parseFieldInput('100 + 20 * 2'), { set: 140 }, 'times before plus');
  assert.deepEqual(parseFieldInput('(100+20)*2'), { set: 240 });
  assert.deepEqual(parseFieldInput('24px'), { set: 24 });
  assert.deepEqual(parseFieldInput('(-20)'), { set: -20 }, 'a negative value is typed in brackets');
  assert.deepEqual(parseFieldInput('0-20'), { set: -20 });
  assert.deepEqual(parseFieldInput('1,5'), { set: 1.5 }, 'a decimal comma');
});

test('a change of the value there: + - * /', () => {
  assert.deepEqual(parseFieldInput('+20'), { rel: '+', by: 20 });
  assert.deepEqual(parseFieldInput('-20'), { rel: '-', by: 20 });
  assert.deepEqual(parseFieldInput('−5'), { rel: '-', by: 5 }, 'a typographic minus');
  assert.deepEqual(parseFieldInput('*2'), { rel: '*', by: 2 });
  assert.deepEqual(parseFieldInput('/4'), { rel: '/', by: 4 });
  assert.equal(applyFieldInput({ rel: '+', by: 20 }, 100), 120);
  assert.equal(applyFieldInput({ rel: '-', by: 20 }, 100), 80);
  assert.equal(applyFieldInput({ rel: '*', by: 2 }, 100), 200);
  assert.equal(applyFieldInput({ rel: '/', by: 4 }, 100), 25);
  assert.equal(applyFieldInput({ set: 7 }, 100), 7);
  assert.equal(parseFieldInput('/0'), null);
  assert.deepEqual(parseFieldInput('*50%', { percent: 'self' }), { rel: '*', by: 0.5 }, 'a scale in % is a fraction');
});

test('% is a share of what the field measures against', () => {
  assert.deepEqual(parseFieldInput('50%', { percent: 1920 }), { set: 960 });
  assert.deepEqual(parseFieldInput('+10%', { percent: 1080 }), { rel: '+', by: 108 });
  assert.deepEqual(parseFieldInput('50%', { percent: 'self' }), { set: 50 }, 'a field in % takes its own unit');
  assert.equal(parseFieldInput('50%'), null, 'no measure, no %');
});

test('time: seconds, frames, ms and timecodes', () => {
  const time = { time: true };
  assert.deepEqual(parseFieldInput('2.5s', time), { set: 2.5 });
  assert.deepEqual(parseFieldInput('12f', time), { set: 0.4 });
  assert.deepEqual(parseFieldInput('250ms', time), { set: 0.25 });
  assert.deepEqual(parseFieldInput('2', time), { set: 2 }, 'a bare number is seconds');
  assert.deepEqual(parseFieldInput('00:00:02:15', time), { set: 2.5 });
  assert.deepEqual(parseFieldInput('01:00:00', time), { set: 60 }, 'MM:SS:FF');
  assert.deepEqual(parseFieldInput('1:15', time), { set: 1.5 }, 'SS:FF');
  assert.deepEqual(parseFieldInput('+6f', time), { rel: '+', by: 0.2 });
  assert.deepEqual(parseFieldInput('1s + 15f', time), { set: 1.5 });
  assert.equal(parseFieldInput('12f'), null, 'frames only in a time field');
  assert.equal(parseFieldInput('00:02:15'), null, 'a timecode only in a time field');
});

test('a typed timecode lands on the frame that shows it, at every rate', () => {
  /* at 29.97 the 17th second starts 17 ms after 17 s: 17 + 0 / 29.97 was the frame shown as 00:00:16:29 */
  const at = (raw: string, fps: number) => (parseFieldInput(raw, { time: true, fps }) as { set: number }).set;
  assert.equal(formatTimecode(at('00:00:17:00', 29.97) * 1000, { fps: 29.97 }), '00:00:17:00');
  for (const fps of [23.976, 24, 25, 29.97, 30, 59.94, 60]) {
    for (let frame = 0; frame < 120 * fps; frame += 1) {
      const shown = formatTimecode((frame * 1000) / (fps === Math.round(fps) ? fps : (Math.round(fps) * 1000) / 1001), { fps });
      assert.equal(formatTimecode(at(shown, fps) * 1000, { fps }), shown, `${shown} at ${fps}`);
    }
  }
  /* frames count at the real rate too: 30 frames at 29.97 are a whole frame past 1 s */
  assert.equal(frameAt(at('30f', 29.97) * 1000, 29.97), 30);
});

test('the field\'s own unit marks, and what is not understood', () => {
  assert.deepEqual(parseFieldInput('45°', { units: ['°', 'deg'] }), { set: 45 });
  assert.deepEqual(parseFieldInput('90deg', { units: ['°', 'deg'] }), { set: 90 });
  assert.deepEqual(parseFieldInput('1.5×', { units: ['×', 'x'] }), { set: 1.5 });
  assert.equal(parseFieldInput(''), null);
  assert.equal(parseFieldInput('abc'), null);
  assert.equal(parseFieldInput('12em'), null);
  assert.equal(parseFieldInput('2+'), null);
  assert.equal(parseFieldInput('(2'), null);
  assert.equal(parseFieldInput('+'), null);
});
