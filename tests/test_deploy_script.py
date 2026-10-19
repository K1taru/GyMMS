"""Exercise deployment trust boundaries and failure recovery on a fake host."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/deploy.sh"
IMAGE = "ghcr.io/k1taru/gymms@sha256:" + "a" * 64
FAKE_HOST = r'''#!/usr/bin/env python3
import json, os, pathlib, sys
command, args = pathlib.Path(sys.argv[0]).name, sys.argv[1:]
with open(os.environ["COMMAND_LOG"], "a") as log:
    log.write(json.dumps([command, *args]) + "\n")
stage = os.environ.get("FAIL_STAGE", "")
if command == "docker":
    if "imagetools" in args:
        print(json.dumps({"digest": "invalid" if stage == "digest" else "sha256:" + "a" * 64}))
    if (stage == "pull" and args[0] == "pull" or
        stage == "migration" and "run" in args or
        stage == "health" and "up" in args and "web" in args or
        stage == "backup" and "db" in args and "exec" in args):
        sys.exit(1)
    if "exec" in args and "db" in args:
        print("fake database archive")
if command == "cosign":
    if stage == "signature":
        sys.exit(1)
    print(json.dumps([{"optional": {"run_number": "bad" if stage == "sequence" else "42"}}]))
if command == "jq":
    value = json.load(sys.stdin)
    print(value["digest"] if isinstance(value, dict) else value[0]["optional"]["run_number"])
'''


class DeploymentScriptTests(unittest.TestCase):
    def run_release(self, stage="", previous=None, blocked=False, config_mode=0o600):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            host = root / "host with spaces"
            host.mkdir()
            (host / "media").mkdir()
            (host / ".env").touch()
            compose = root / "compose.yml"
            compose.touch()
            state = root / "state"
            state.mkdir()
            if previous:
                (state / "current").write_text(previous + "\n")
            if blocked:
                (state / "blocked").touch()
            config = root / "deploy.conf"
            settings = {"GYMMS_DEPLOY_PATH": str(host), "GYMMS_PROJECT_NAME": "gymms",
                        "GYMMS_GITHUB_REPOSITORY": "K1taru/GyMMS",
                        "GYMMS_COMPOSE_FILE": str(compose), "GYMMS_STATE_DIR": str(state)}
            config.write_text("\n".join(f"{key}={shlex.quote(value)}" for key, value in settings.items()))
            config.chmod(config_mode)
            binaries = root / "bin"
            binaries.mkdir()
            for command in ("docker", "cosign", "jq"):
                executable = binaries / command
                executable.write_text(FAKE_HOST)
                executable.chmod(0o700)
            log = root / "commands.jsonl"
            result = subprocess.run(
                ["bash", str(SCRIPT), str(config)],
                env={**os.environ, "PATH": f"{binaries}:{os.environ['PATH']}",
                     "COMMAND_LOG": str(log), "FAIL_STAGE": stage},
                capture_output=True, text=True,
            )
            commands = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
            return (result, commands, (state / "blocked").exists(),
                    (state / "current").read_text().strip() if (state / "current").exists() else None,
                    len(list(state.glob("backup-*/media.tar.gz"))))

    def test_success_verifies_before_pull_and_preserves_release_order(self):
        result, commands, blocked, current, archives = self.run_release()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(blocked)
        self.assertEqual(current, "42 " + IMAGE)
        self.assertEqual(archives, 1)
        steps = [" ".join(command) for command in commands]
        markers = ("cosign verify", "docker pull", "stop web", "pg_dump", "run --rm",
                   "180 web", "180 payment-worker", "migrate --check", "check_readiness")
        positions = [next(i for i, command in enumerate(steps) if marker in command) for marker in markers]
        self.assertEqual(positions, sorted(positions))
        verify = next(command for command in commands if command[0] == "cosign")
        self.assertIn("https://github.com/K1taru/GyMMS/.github/workflows/ci-cd.yml@refs/heads/main", verify)
        self.assertIn("https://token.actions.githubusercontent.com", verify)
        self.assertIn("release=production", verify)
        self.assertIn(IMAGE, verify)
        self.assertFalse(any("git" == command[0] or "build" in command for command in commands))
        for command in commands:
            if command[0] == "docker" and ("up" in command or "run" in command):
                self.assertIn("--build=false" if "run" in command else "--no-build", command)
                self.assertIn("never", command)

    def test_untrusted_signature_digest_or_sequence_never_pull_or_stop(self):
        for stage in ("signature", "digest", "sequence"):
            with self.subTest(stage=stage):
                result, commands, blocked, _, _ = self.run_release(stage)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(blocked)
                self.assertFalse(any("pull" in command or "stop" in command for command in commands))

    def test_failed_pull_keeps_running_services(self):
        result, commands, blocked, current, _ = self.run_release("pull")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(blocked)
        self.assertIsNone(current)
        self.assertFalse(any("stop" in command for command in commands))

    def test_failed_backup_migration_or_health_blocks_future_deployment(self):
        for stage in ("backup", "migration", "health"):
            with self.subTest(stage=stage):
                result, commands, blocked, current, _ = self.run_release(stage)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(blocked)
                self.assertIsNone(current)
                self.assertFalse(any("up" in command and "payment-worker" in command for command in commands))
                if stage == "backup":
                    self.assertFalse(any("run" in command for command in commands))

    def test_blocked_host_requires_explicit_recovery(self):
        result, commands, blocked, _, _ = self.run_release(blocked=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(blocked)
        self.assertEqual(commands, [])

    def test_unchanged_release_is_noop(self):
        result, commands, blocked, current, _ = self.run_release(previous="42 " + IMAGE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(blocked)
        self.assertEqual(current, "42 " + IMAGE)
        self.assertFalse(any("pull" in command or "stop" in command for command in commands))

    def test_previously_signed_release_cannot_replace_a_newer_release(self):
        result, commands, blocked, current, _ = self.run_release(previous="43 old-image")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(blocked)
        self.assertEqual(current, "43 old-image")
        self.assertFalse(any("pull" in command or "stop" in command for command in commands))

    def test_group_writable_configuration_is_rejected(self):
        result, commands, _, _, _ = self.run_release(config_mode=0o660)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(commands, [])


if __name__ == "__main__":
    unittest.main()
