import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from lineunique.cli import Stats, main, unique_lines


class UniqueLinesTests(unittest.TestCase):
    def test_duplicates_keep_first_order(self):
        stats = Stats()
        result = list(unique_lines(["apel\n", "jeruk\n", "apel\n", "pisang\n"], stats=stats))
        self.assertEqual(result, ["apel\n", "jeruk\n", "pisang\n"])
        self.assertEqual(stats, Stats(read=4, written=3, duplicates=1))

    def test_default_preserves_case_and_spaces(self):
        self.assertEqual(list(unique_lines(["apel\n", "APEL\n", " apel \n"])), ["apel\n", "APEL\n", " apel \n"])

    def test_unicode_casefold_matches_equivalent_words(self):
        self.assertEqual(list(unique_lines(["Straße\n", "STRASSE\n"], ignore_case=True)), ["Straße\n"])

    def test_strip_changes_comparison_and_output(self):
        self.assertEqual(list(unique_lines(["  apel\t\n", "apel\n"], strip=True)), ["apel\n"])

    def test_blank_line_is_kept_once_by_default(self):
        self.assertEqual(list(unique_lines(["\n", "\n", " \n"])), ["\n", " \n"])

    def test_drop_empty_skips_whitespace_without_strip(self):
        stats = Stats()
        self.assertEqual(list(unique_lines(["\n", " \t\n", "apel\n"], drop_empty=True, stats=stats)), ["apel\n"])
        self.assertEqual(stats.empty_skipped, 2)

    def test_combined_options_have_consistent_statistics(self):
        stats = Stats()
        result = list(unique_lines([" APEL \n", "apel\n", " \n", "jeruk\n"], ignore_case=True,
                                   strip=True, drop_empty=True, stats=stats))
        self.assertEqual(result, ["APEL\n", "jeruk\n"])
        self.assertEqual(stats.read, stats.written + stats.duplicates + stats.empty_skipped)

    def test_crlf_and_missing_last_newline_become_lf(self):
        self.assertEqual(list(unique_lines(["apel\r\n", "jeruk"])), ["apel\n", "jeruk\n"])


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def invoke(self, *args, input=None):
        return subprocess.run([sys.executable, "-m", "lineunique", *map(str, args)],
                              input=input, capture_output=True, text=True, encoding="utf-8",
                              cwd=Path(__file__).resolve().parents[1], timeout=10,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})

    def test_stdin_stdout_work_without_closing_streams(self):
        incoming, outgoing, errors = io.StringIO("apel\napel\n"), io.StringIO(), io.StringIO()
        self.assertEqual(main([], stdin=incoming, stdout=outgoing, stderr=errors), 0)
        self.assertEqual(outgoing.getvalue(), "apel\n")
        self.assertFalse(incoming.closed)
        self.assertFalse(outgoing.closed)
        self.assertEqual(errors.getvalue(), "")

    def test_stats_are_json_on_stderr_only(self):
        result = self.invoke("--stats", input="apel\napel\n")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "apel\n")
        self.assertEqual(json.loads(result.stderr), {"read": 2, "written": 1, "duplicates": 1, "empty_skipped": 0})

    def test_utf8_bom_crlf_and_output_directory(self):
        source, output = self.root / "input.txt", self.root / "new folder" / "output.txt"
        source.write_bytes("\ufeffcafé\r\ncafé\r\njeruk".encode("utf-8"))
        result = self.invoke(source, "-o", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), "café\njeruk\n".encode("utf-8"))
        self.assertEqual(result.stdout, "")

    def test_existing_output_is_preserved_without_force(self):
        output = self.root / "output.txt"
        output.write_text("lama", encoding="utf-8")
        result = self.invoke("-o", output, input="baru\n")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(output.read_text(encoding="utf-8"), "lama")

    def test_force_replaces_output_and_cleans_temporary_file(self):
        output = self.root / "output.txt"
        output.write_text("lama", encoding="utf-8")
        result = self.invoke("-o", output, "--force", input="baru\nbaru\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_text(encoding="utf-8"), "baru\n")
        self.assertEqual(list(self.root.iterdir()), [output])

    def test_input_is_never_overwritten_even_with_force(self):
        source = self.root / "input.txt"
        source.write_text("apel\napel\n", encoding="utf-8")
        result = self.invoke(source, "-o", source, "--force")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(source.read_text(encoding="utf-8"), "apel\napel\n")

    def test_input_hardlink_is_not_overwritten(self):
        source, target = self.root / "input.txt", self.root / "alias.txt"
        source.write_text("apel\napel\n", encoding="utf-8")
        try:
            os.link(source, target)
        except OSError:
            self.skipTest("Filesystem tidak mendukung hard link.")
        result = self.invoke(source, "-o", target, "--force")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(source.read_text(encoding="utf-8"), "apel\napel\n")

    def test_invalid_utf8_does_not_leave_new_output(self):
        source, output = self.root / "input.txt", self.root / "output.txt"
        source.write_bytes(b"apel\n\xff\xfe\n")
        result = self.invoke(source, "-o", output)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(output.exists())
        self.assertIn("UTF-8", result.stderr)

    def test_invalid_input_does_not_replace_existing_output_with_force(self):
        source, output = self.root / "input.txt", self.root / "output.txt"
        source.write_bytes(b"\xff\n")
        output.write_text("lama", encoding="utf-8")
        result = self.invoke(source, "-o", output, "--force")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(output.read_text(encoding="utf-8"), "lama")

    def test_missing_input_is_reported_without_output(self):
        output = self.root / "output.txt"
        result = self.invoke(self.root / "missing.txt", "-o", output)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(output.exists())

    def test_force_without_file_is_rejected(self):
        result = self.invoke("--force", input="apel\n")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    def test_example_and_statistics(self):
        result = self.invoke("examples/daftar.txt", "--ignore-case", "--strip", "--drop-empty", "--stats")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "apel\njeruk\npisang\n")
        self.assertEqual(json.loads(result.stderr), {"read": 7, "written": 3, "duplicates": 3, "empty_skipped": 1})

    def test_version_and_help_are_available(self):
        self.assertEqual(self.invoke("--version").stdout.strip(), "LineUnique 1.0.0")
        self.assertIn("--ignore-case", self.invoke("--help").stdout)


if __name__ == "__main__":
    unittest.main()
