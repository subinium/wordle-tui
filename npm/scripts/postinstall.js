#!/usr/bin/env node
const { execSync } = require('child_process');

console.log('Installing TUI Wordle Python package...');

try {
  // Try pip3 first, then pip
  try {
    execSync('pip3 install tui-wordle', { stdio: 'inherit' });
  } catch {
    execSync('pip install tui-wordle', { stdio: 'inherit' });
  }
  console.log('TUI Wordle installed successfully!');
  console.log('Run "wordle" to play!');
} catch (error) {
  console.error('Failed to install Python package.');
  console.error('Please install manually: pip install tui-wordle');
  // Don't fail npm install
}
