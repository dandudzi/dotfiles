#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const os = require('node:os');

const CACHE_TTL_MS = 300_000; // 5 minutes

function getCachePath() {
  const cacheDir = path.join(os.homedir(), '.claude', 'ccline');
  return path.join(cacheDir, '.api_usage_cache.json');
}

function readCache() {
  try {
    const data = JSON.parse(fs.readFileSync(getCachePath(), 'utf8'));
    if (Date.now() - data.cached_at < CACHE_TTL_MS) {
      return data;
    }
    return null;
  } catch {
    return null;
  }
}

function writeCache(fiveHourUtilization) {
  const cachePath = getCachePath();
  const cacheDir = path.dirname(cachePath);
  fs.mkdirSync(cacheDir, { recursive: true });
  fs.writeFileSync(cachePath, JSON.stringify({
    five_hour_utilization: fiveHourUtilization,
    cached_at: Date.now()
  }));
}

function readStaleCache() {
  try {
    const data = JSON.parse(fs.readFileSync(getCachePath(), 'utf8'));
    return data;
  } catch {
    return null;
  }
}

async function getOAuthToken() {
  // Try macOS Keychain first
  if (process.platform === 'darwin') {
    try {
      const user = os.userInfo().username;
      // Command is hardcoded — no user input, safe from injection
      const raw = cp.execSync(
        `security find-generic-password -a "${user}" -w -s "Claude Code-credentials"`,
        { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }
      ).trim();
      const creds = JSON.parse(raw);
      if (creds.claudeAiOauth?.accessToken) {
        return creds.claudeAiOauth.accessToken;
      }
    } catch {
      // Fall through to file-based credentials
    }
  }

  // Fallback: read credentials file
  const configDir = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
  const credPath = path.join(configDir, '.credentials.json');
  const raw = fs.readFileSync(credPath, 'utf8');
  const creds = JSON.parse(raw);
  if (creds.claudeAiOauth?.accessToken) {
    return creds.claudeAiOauth.accessToken;
  }
  throw new Error('No OAuth token found in credentials');
}

async function fetchUsage(token) {
  const res = await fetch('https://api.anthropic.com/api/oauth/usage', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'anthropic-beta': 'oauth-2025-04-20'
    }
  });
  if (!res.ok) {
    throw new Error(`API request failed: ${res.status}`);
  }
  return res.json();
}

function formatOutput(utilization) {
  const pct = Math.round(utilization);
  let color;
  if (pct >= 90) {
    color = '\x1b[91m'; // bright red
  } else if (pct >= 50) {
    color = '\x1b[33m'; // yellow
  } else {
    color = '\x1b[97m'; // white
  }
  return `${color}${pct}%\x1b[0m`;
}

async function main() {
  try {
    const token = await getOAuthToken();

    // Check cache first
    const cached = readCache();
    if (cached) {
      process.stdout.write(formatOutput(cached.five_hour_utilization));
      return;
    }

    // Fetch from API
    let data;
    try {
      data = await fetchUsage(token);
    } catch (err) {
      // On API failure, try stale cache
      const stale = readStaleCache();
      if (stale) {
        process.stdout.write(formatOutput(stale.five_hour_utilization));
        return;
      }
      throw err;
    }

    const utilization = data.five_hour?.utilization ?? 0;
    writeCache(utilization);
    process.stdout.write(formatOutput(utilization));
  } catch (err) {
    process.stderr.write(`Error: ${err.message}\n`);
    process.exit(1);
  }
}

// Run main when executed directly, export for testing
if (require.main === module) {
  main();
}

module.exports = { getOAuthToken, fetchUsage, formatOutput, readCache, writeCache };
