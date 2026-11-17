/**
 * How the app runs a Node program of its own (an agent's adapter, the app's own agent) on Electron as Node: this file
 * first, through `--import`, then the program as the main module, as Node would start it (a program that runs only
 * when it is the main one, `import.meta.main` or `require.main === module`, runs). ELECTRON_RUN_AS_NODE is what made
 * Electron a Node; it is taken out of the environment before the program starts, so what the program starts (the
 * person's agent, and every command that agent runs) does not have it. An Electron app the agent runs, or its tests,
 * would start as Node too.
 *
 * On Windows, what the program starts opens no console window (hidden-windows.mjs).
 *
 *   electron --import <this file's URL> <program> [args…]
 */
import childProcess from 'node:child_process';
import { hideChildWindows } from './hidden-windows.mjs';

delete process.env.ELECTRON_RUN_AS_NODE;
if (process.platform === 'win32') hideChildWindows(childProcess);
