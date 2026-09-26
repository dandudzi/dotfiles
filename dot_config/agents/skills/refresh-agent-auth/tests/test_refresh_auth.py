import importlib.util
import json
import pathlib
import subprocess
import unittest
from io import BytesIO
from unittest.mock import patch


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "refresh_auth.py"
spec = importlib.util.spec_from_file_location("refresh_auth", SCRIPT)
auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)


class RefreshAuthTests(unittest.TestCase):
    def test_network_failure_does_not_trigger_github_login(self):
        response = {"hosts": {"github.com": [{"state": "error", "error": "lookup api.github.com: no such host"}]}}
        with patch.object(auth, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(response), "")) as run:
            self.assertEqual(auth.check_github(), "network")
            auth.repair_github("network")
            self.assertEqual(run.call_count, 1)

    def test_expired_github_credential_uses_native_login(self):
        response = {"hosts": {"github.com": [{"state": "error", "error": "HTTP 401: Bad credentials"}]}}
        with patch.object(auth, "run", side_effect=[
            subprocess.CompletedProcess([], 0, json.dumps(response), ""),
            subprocess.CompletedProcess([], 0, "", ""),
        ]) as run:
            self.assertEqual(auth.check_github(), "invalid")
            auth.repair_github("invalid")
            self.assertEqual(run.call_args_list[1].args[0], ["gh", "auth", "login", "--hostname", "github.com", "--web"])

    def test_operator_uses_keychain_value_instead_of_environment(self):
        with patch.object(auth, "run", return_value=subprocess.CompletedProcess([], 0, "keychain-value\n", "")) as run:
            with patch.object(auth, "validate_operator", return_value="valid") as validate:
                with patch.dict("os.environ", {"LINEAR_OPERATOR_ACCESS_TOKEN": "stale-value"}):
                    self.assertEqual(auth.check_operator(), "valid")
                validate.assert_called_once_with("keychain-value")
                self.assertEqual(run.call_args.args[0][:2], ["security", "find-generic-password"])

    def test_operator_repair_prompts_keychain_without_secret_argument(self):
        with patch.object(auth, "run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run:
            auth.repair_operator("invalid")
            args = run.call_args.args[0]
            self.assertEqual(args[-1], "-w")
            self.assertIn("-U", args)
            self.assertNotIn("LINEAR_OPERATOR_ACCESS_TOKEN", args)

    def test_operator_probe_uses_bearer_and_returns_only_status(self):
        with patch.object(auth.urllib.request, "urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value = BytesIO(b'{"data":{"viewer":{"id":"user"}}}')
            self.assertEqual(auth.validate_operator("private-token"), "valid")
            request = urlopen.call_args.args[0]
            self.assertEqual(request.get_header("Authorization"), "Bearer private-token")


if __name__ == "__main__":
    unittest.main()
