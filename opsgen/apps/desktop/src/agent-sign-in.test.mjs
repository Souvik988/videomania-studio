import { test } from 'node:test';
import assert from 'node:assert/strict';
import { signInScript, terminalTabOpenScript, powerShellWindowLaunch } from './agents.mjs';

test('a tracked Mac login returns its exact terminal tab, and checks do not reopen Terminal', () => {
  const script = signInScript('/bin/qwen', [], { cwd: '/tmp/login', track: true });
  assert.match(script, /set loginTab to do script/);
  assert.match(script, /return tty of loginTab/);
  const check = terminalTabOpenScript('/dev/ttys012');
  assert.match(check, /^if application "Terminal" is not running then return "closed"/);
  assert.match(check, /if tty of terminalTab is "\/dev\/ttys012" then return "open"/);
  assert.doesNotMatch(check, /activate|do script/);
  assert.throws(() => terminalTabOpenScript('"\nactivate'), /Invalid terminal tty/);
});

test('tracking a Windows login waits for its console instead of the short lived launcher', () => {
  const file = 'C:\\Users\\someone\\Temp\\qwen login.ps1';
  const plain = powerShellWindowLaunch(file);
  const tracked = powerShellWindowLaunch(file, { wait: true });
  assert.doesNotMatch(plain.args[3], /\/wait/);
  assert.match(tracked.args[3], /^"start "" \/wait /);
  assert.match(tracked.args[3], /-NoExit.*-File "C:\\Users\\someone\\Temp\\qwen login.ps1""$/);
});

test('on Windows the tracked launcher exits when its sign-in window closes', { skip: process.platform !== 'win32' }, async () => {
  const { spawn } = await import('node:child_process');
  const { mkdtempSync, writeFileSync, existsSync } = await import('node:fs');
  const { tmpdir } = await import('node:os');
  const { join } = await import('node:path');
  const dir = mkdtempSync(join(tmpdir(), 'of-login-window '));
  const mark = join(dir, 'opened');
  const file = join(dir, 'sign-in.ps1');
  writeFileSync(file, `\ufeffSet-Content -LiteralPath '${mark.replace(/'/g, "''")}' -Value opened\r\nStart-Sleep -Seconds 1\r\n[Environment]::Exit(0)\r\n`, 'utf8');
  const how = powerShellWindowLaunch(file, { wait: true });
  const child = spawn(how.cmd, how.args, { cwd: dir, detached: true, stdio: 'ignore', ...how.options });
  const exited = new Promise((resolve, reject) => { child.once('exit', resolve); child.once('error', reject); });
  for (let i = 0; i < 100 && !existsSync(mark); i++) await new Promise((done) => setTimeout(done, 50));
  assert.ok(existsSync(mark));
  assert.equal(child.exitCode, null, 'the launcher remains alive while its terminal is open');
  assert.equal(await exited, 0);
});
