"""End-to-end checks for Maven decisions in the active Codex execpolicy."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


RULES = Path(__file__).with_name("default.rules")

CASES: tuple[tuple[str | None, tuple[str, ...]], ...] = (
    # Installed Maven metadata is safe; Maven Wrapper metadata can bootstrap code.
    ("allow", ("mvn", "--version")),
    ("allow", ("mvn", "--help")),
    ("allow", ("rtk", "mvn", "--version")),
    ("allow", ("rtk", "--verbose", "mvn", "--version")),
    ("allow", ("rtk", "proxy", "mvn", "--version")),
    (None, ("./mvnw", "--version")),
    (None, ("rtk", "./mvnw", "--version")),
    # Routine project work remains sandbox-governed rather than unconditionally allowed.
    (None, ("mvn", "validate")),
    (None, ("mvn", "test")),
    (None, ("mvn", "clean", "verify")),
    (None, ("mvn", "dependency:resolve")),
    (None, ("mvn", "help:effective-pom")),
    (None, ("mvn", "release:clean")),
    (None, ("rtk", "mvn", "test")),
    # Local repository, dependency-cache, project-generation, and execution mutations prompt.
    ("prompt", ("mvn", "install")),
    ("prompt", ("mvnw", "install")),
    ("prompt", ("./mvnw", "install")),
    ("prompt", ("mvn", "clean", "install")),
    ("prompt", ("mvn", "install:install-file", "-Dfile=library.jar")),
    ("prompt", ("mvn", "dependency:purge-local-repository")),
    ("prompt", ("mvn", "dependency:get", "-Dartifact=g:a:1")),
    ("prompt", ("mvn", "dependency:go-offline")),
    ("prompt", ("mvn", "archetype:generate")),
    ("prompt", ("mvn", "wrapper:wrapper")),
    ("prompt", ("mvn", "versions:set", "-DnewVersion=2")),
    ("prompt", ("mvn", "dependency:add", "-Dartifact=g:a:1")),
    ("prompt", ("mvn", "dependency:remove", "-Dartifact=g:a")),
    ("prompt", ("mvn", "spring-boot:run")),
    ("prompt", ("mvn", "quarkus:dev")),
    ("prompt", ("mvn", "exec:java")),
    ("prompt", ("mvn", "--encrypt-password", "secret")),
    ("prompt", ("mvn", "-emp", "secret")),
    ("prompt", ("rtk", "mvn", "clean", "install")),
    ("prompt", ("rtk", "test", "mvn", "dependency:purge-local-repository")),
    ("prompt", ("rtk", "--verbose", "proxy", "mvn", "wrapper:wrapper")),
    # Publication and release automation are blocked for all wrapper spellings.
    ("forbidden", ("mvn", "deploy")),
    ("forbidden", ("mvnw", "deploy")),
    ("forbidden", ("./mvnw", "deploy")),
    ("forbidden", ("mvn", "clean", "deploy")),
    ("forbidden", ("mvn", "test", "deploy")),
    ("forbidden", ("mvn", "install", "deploy")),
    ("forbidden", ("mvn", "site-deploy")),
    ("forbidden", ("mvn", "deploy:deploy")),
    ("forbidden", ("mvn", "deploy:deploy-file", "-Dfile=library.jar")),
    ("forbidden", ("mvn", "release:prepare")),
    ("forbidden", ("mvn", "release:prepare-with-pom")),
    ("forbidden", ("mvn", "release:perform")),
    ("forbidden", ("mvn", "release:stage")),
    ("forbidden", ("mvn", "release:rollback")),
    ("forbidden", ("rtk", "mvn", "deploy:deploy-file")),
    ("forbidden", ("rtk", "./mvnw", "clean", "deploy")),
    ("forbidden", ("rtk", "--verbose", "proxy", "mvn", "release:perform")),
    ("forbidden", ("rtk", "proxy", "--skip-env", "mvn", "site-deploy")),
)

# Native prefix rules cannot inspect arbitrary goal positions or versioned plugin tokens.
KNOWN_NATIVE_LIMITATIONS: tuple[tuple[str, ...], ...] = (
    ("mvn", "-q", "deploy"),
    ("mvn", "-V", "deploy"),
    ("mvn", "--show-version", "deploy"),
    ("mvn", "-f", "module/pom.xml", "deploy"),
    ("mvn", "clean", "verify", "deploy"),
    ("mvn", "org.apache.maven.plugins:maven-deploy-plugin:3.1.4:deploy-file"),
)


def decision(command: tuple[str, ...]) -> str | None:
    completed = subprocess.run(
        (
            "rtk",
            "codex",
            "execpolicy",
            "check",
            "--pretty",
            "--rules",
            str(RULES),
            *command,
        ),
        check=True,
        text=True,
        capture_output=True,
    )
    payload_start = completed.stdout.find("{")
    if payload_start < 0:
        raise RuntimeError(f"No JSON output for {' '.join(command)}: {completed.stdout}")
    return json.loads(completed.stdout[payload_start:]).get("decision")


def main() -> int:
    failures: list[str] = []
    for expected, command in CASES:
        actual = decision(command)
        if actual != expected:
            failures.append(
                f"{' '.join(command)}: expected {expected or 'unmatched'}, "
                f"got {actual or 'unmatched'}"
            )

    for command in KNOWN_NATIVE_LIMITATIONS:
        actual = decision(command)
        if actual is not None:
            failures.append(
                f"documented limitation {' '.join(command)} unexpectedly became {actual}"
            )

    if failures:
        print("Maven execpolicy failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        f"Maven execpolicy: {len(CASES)} decisions passed; "
        f"{len(KNOWN_NATIVE_LIMITATIONS)} native limitations remain documented"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
