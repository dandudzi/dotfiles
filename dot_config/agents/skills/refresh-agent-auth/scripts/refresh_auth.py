#!/usr/bin/env python3
"""Check agent credentials and run their native interactive renewal flows."""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request


KEYCHAIN_ACCOUNT = "linear-operator"
KEYCHAIN_SERVICE = "codex-linear-operator-token"


def run(args, interactive=False):
    return subprocess.run(args, text=True, capture_output=not interactive, check=False)


def check_github():
    result = run(["gh", "auth", "status", "--active", "--hostname", "github.com", "--json", "hosts"])
    try:
        account = json.loads(result.stdout)["hosts"]["github.com"][0]
    except (ValueError, KeyError, IndexError, TypeError):
        if "not logged in" in result.stderr.lower():
            return "missing"
        return "unavailable"
    if account.get("state") == "success":
        return "valid"
    error = account.get("error", "").lower()
    if any(word in error for word in ("no such host", "lookup ", "timeout", "connection refused", "network is unreachable")):
        return "network"
    if any(word in error for word in ("401", "bad credentials", "expired", "invalid token", "not logged in")):
        return "invalid"
    return "unavailable"


def validate_operator(token):
    payload = json.dumps({"query": "query { viewer { id } }"}).encode()
    request = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = json.load(response)
    except urllib.error.HTTPError as error:
        return "invalid" if error.code in (401, 403) else "unavailable"
    except (urllib.error.URLError, TimeoutError, OSError):
        return "network"
    except (ValueError, TypeError):
        return "unavailable"
    if body.get("errors"):
        return "invalid" if any("auth" in str(item.get("message", "")).lower() for item in body["errors"]) else "unavailable"
    return "valid" if body.get("data", {}).get("viewer", {}).get("id") else "unavailable"


def check_operator():
    # Read the current Keychain item, even when this process inherited an older token.
    result = run(["security", "find-generic-password", "-a", KEYCHAIN_ACCOUNT, "-s", KEYCHAIN_SERVICE, "-w"])
    if result.returncode:
        if "could not be found" in result.stderr.lower() and not os.getenv("CODEX_SANDBOX"):
            return "missing"
        return "unavailable"
    token = result.stdout.strip()
    return validate_operator(token) if token else "missing"


def repair_github(status):
    if status in ("invalid", "missing"):
        # gh owns its credential store; never extract or copy its token.
        run(["gh", "auth", "login", "--hostname", "github.com", "--web"], interactive=True)


def repair_operator(status):
    if status in ("invalid", "missing"):
        # A trailing -w makes security prompt on the terminal, avoiding argv secrets.
        run(["security", "add-generic-password", "-U", "-a", KEYCHAIN_ACCOUNT,
             "-s", KEYCHAIN_SERVICE, "-w"], interactive=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "repair"))
    parser.add_argument("--linear-oauth", action="store_true",
                        help="In repair mode, run Codex's interactive Linear MCP OAuth login")
    args = parser.parse_args()
    if args.linear_oauth and args.mode != "repair":
        parser.error("--linear-oauth requires repair")

    github = check_github()
    operator = check_operator()
    print(f"GitHub CLI: {github}")
    print(f"Linear operator Keychain token: {operator}")
    print("Linear MCP OAuth: managed by Codex; check the connection in the active agent")

    if args.mode == "repair":
        repair_github(github)
        repair_operator(operator)
        if args.linear_oauth:
            run(["codex", "mcp", "login", "linear"], interactive=True)
        print(f"GitHub CLI after repair: {check_github()}")
        print(f"Linear operator after repair: {check_operator()}")
        if args.linear_oauth:
            print("Linear MCP OAuth: retry a read-only Linear tool call to verify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
