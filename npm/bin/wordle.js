#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');

// Try to run the Python wordle command
const proc = spawn('wordle', process.argv.slice(2), {
  stdio: 'inherit',
  shell: true,
});

proc.on('error', (err) => {
  if (err.code === 'ENOENT') {
    console.error('Error: wordle command not found.');
    console.error('Please ensure Python package is installed:');
    console.error('  pip install tui-wordle');
    process.exit(1);
  }
  throw err;
});

proc.on('close', (code) => {
  process.exit(code);
});
