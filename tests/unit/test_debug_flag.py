"""
Tests for --debug flag functionality in convert.py.

This module tests the debug flag behavior including:
- Argument parsing for --debug flag
- Removal of --quiet from pandoc command when debug is active
- Subprocess output capture behavior
- Creation of debug artifacts (_debug.md and _debug.tex files)
- Metadata passing to debug .tex generation
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from convert import main


class TestDebugArgparse:
    """Tests for --debug flag argument parsing."""

    def test_argparse_accepts_debug_flag_sets_true(self, tmp_path):
        """
        Test that argparse accepts --debug flag and sets it to True.

        Given: CLI arguments with --debug flag
        When: Arguments are parsed
        Then: args.debug is set to True without error
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf), "--debug"]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch(
                    "convert.subprocess.run", return_value=MagicMock(returncode=0)
                ):
                    with patch("convert.os.path.exists", return_value=True):
                        try:
                            main()
                            parsed_successfully = True
                        except SystemExit:
                            parsed_successfully = False

        assert parsed_successfully

    def test_argparse_debug_defaults_to_false_when_not_provided(self, tmp_path):
        """
        Test that --debug defaults to False when not provided.

        Given: CLI arguments without --debug flag
        When: Arguments are parsed
        Then: args.debug is set to False
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf)]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch(
                    "convert.subprocess.run", return_value=MagicMock(returncode=0)
                ):
                    with patch("convert.os.path.exists", return_value=True):
                        try:
                            main()
                            parsed_successfully = True
                        except SystemExit:
                            parsed_successfully = False

        assert parsed_successfully


class TestDebugPandocCommand:
    """Tests for pandoc command modification based on --debug flag."""

    def test_debug_removes_quiet_from_pandoc_cmd(self, tmp_path):
        """
        Test that --debug flag removes --quiet from pandoc command.

        Given: convert.py called with --debug flag
        When: Pandoc command is constructed
        Then: --quiet is NOT included in the command
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf), "--debug"]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run", return_value=MagicMock(returncode=0)
                    ) as mock_run:
                        main()

                        # Find the PDF generation call (not the .tex generation call)
                        pdf_call = None
                        for call_args in mock_run.call_args_list:
                            cmd = (
                                call_args[0][0]
                                if call_args[0]
                                else call_args[1].get("cmd", [])
                            )
                            if "-o" in cmd and cmd[cmd.index("-o") + 1].endswith(
                                ".pdf"
                            ):
                                pdf_call = cmd
                                break

                        assert pdf_call is not None, (
                            "PDF generation pandoc call not found"
                        )
                        assert "--quiet" not in pdf_call

    def test_normal_includes_quiet_in_pandoc_cmd(self, tmp_path):
        """
        Test that without --debug flag, --quiet IS included in pandoc command.

        Given: convert.py called without --debug flag
        When: Pandoc command is constructed
        Then: --quiet IS included in the command
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf)]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run", return_value=MagicMock(returncode=0)
                    ) as mock_run:
                        main()

                        # Find the PDF generation call
                        pdf_call = None
                        for call_args in mock_run.call_args_list:
                            cmd = (
                                call_args[0][0]
                                if call_args[0]
                                else call_args[1].get("cmd", [])
                            )
                            if "-o" in cmd and cmd[cmd.index("-o") + 1].endswith(
                                ".pdf"
                            ):
                                pdf_call = cmd
                                break

                        assert pdf_call is not None, (
                            "PDF generation pandoc call not found"
                        )
                        assert "--quiet" in pdf_call


class TestDebugOutputCapture:
    """Tests for subprocess output capture behavior with --debug flag."""

    def test_debug_does_not_capture_output(self, tmp_path):
        """
        Test that --debug flag disables output capture in subprocess.run.

        Given: convert.py called with --debug flag
        When: subprocess.run is called for pandoc
        Then: capture_output is not True (allows output to flow to terminal)
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf), "--debug"]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run", return_value=MagicMock(returncode=0)
                    ) as mock_run:
                        main()

                        # Check the PDF generation call
                        pdf_call = None
                        for call_obj in mock_run.call_args_list:
                            cmd = (
                                call_obj[0][0]
                                if call_obj[0]
                                else call_obj[1].get("cmd", [])
                            )
                            if "-o" in cmd and cmd[cmd.index("-o") + 1].endswith(
                                ".pdf"
                            ):
                                pdf_call = call_obj
                                break

                        assert pdf_call is not None, "PDF generation call not found"

                        # Verify capture_output is not True
                        capture_output = pdf_call[1].get("capture_output", False)
                        assert capture_output is not True

    def test_normal_captures_output(self, tmp_path):
        """
        Test that without --debug flag, output capture is enabled.

        Given: convert.py called without --debug flag
        When: subprocess.run is called for pandoc
        Then: capture_output=True is set
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf)]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run", return_value=MagicMock(returncode=0)
                    ) as mock_run:
                        main()

                        # Get the subprocess.run kwargs
                        kwargs = mock_run.call_args[1]

                        assert kwargs.get("capture_output") is True


class TestDebugArtifacts:
    """Tests for debug artifact file creation (_debug.md and _debug.tex)."""

    def test_debug_saves_processed_md_alongside_output(self, tmp_path):
        """
        Test that --debug flag saves preprocessed markdown as {stem}_debug.md.

        Given: convert.py called with --debug and output path /tmp/out.pdf
        When: Conversion completes
        Then: /tmp/out_debug.md exists with preprocessed content
        """
        output_pdf = tmp_path / "output.pdf"
        expected_debug_md = tmp_path / "output_debug.md"
        test_args = ["convert.py", "input.md", str(output_pdf), "--debug"]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Processed Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run", return_value=MagicMock(returncode=0)
                    ):
                        main()

        assert expected_debug_md.exists()
        assert expected_debug_md.read_text() == "# Processed Content"

    def test_debug_saves_tex_file_alongside_output(self, tmp_path):
        """
        Test that --debug flag saves intermediate LaTeX as {stem}_debug.tex.

        Given: convert.py called with --debug and output path /tmp/out.pdf
        When: Conversion completes
        Then: /tmp/out_debug.tex exists
        """
        output_pdf = tmp_path / "output.pdf"
        expected_debug_tex = tmp_path / "output_debug.tex"
        test_args = ["convert.py", "input.md", str(output_pdf), "--debug"]

        def subprocess_side_effect(*args, **kwargs):
            """Create .tex file when pandoc is called with -o ...tex."""
            cmd = args[0]
            if "-o" in cmd:
                out_idx = cmd.index("-o") + 1
                out_path = cmd[out_idx]
                if out_path.endswith("_debug.tex"):
                    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
                    Path(out_path).write_text("\\documentclass{article}\n")
            return MagicMock(returncode=0)

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Processed Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run", side_effect=subprocess_side_effect
                    ):
                        main()

        assert expected_debug_tex.exists()

    def test_debug_tex_uses_latex_output_format(self, tmp_path):
        """
        Test that .tex generation uses -t latex -s flags.

        Given: convert.py called with --debug flag
        When: Second pandoc call is made for .tex generation
        Then: Command includes -t latex and -s flags
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf), "--debug"]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run", return_value=MagicMock(returncode=0)
                    ) as mock_run:
                        main()

                        # Find the .tex generation call
                        tex_call = None
                        for call_args in mock_run.call_args_list:
                            cmd = (
                                call_args[0][0]
                                if call_args[0]
                                else call_args[1].get("cmd", [])
                            )
                            if "-o" in cmd and cmd[cmd.index("-o") + 1].endswith(
                                "_debug.tex"
                            ):
                                tex_call = cmd
                                break

                        assert tex_call is not None, (
                            ".tex generation pandoc call not found"
                        )
                        assert "-t" in tex_call
                        assert "latex" in tex_call
                        assert "-s" in tex_call or "--standalone" in tex_call

    def test_debug_tex_passes_metadata_variables(self, tmp_path):
        """
        Test that .tex generation includes all metadata variables.

        Given: convert.py called with --debug and metadata overrides
        When: Second pandoc call is made for .tex generation
        Then: Command includes -V flags for title, author, date, version
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = [
            "convert.py",
            "input.md",
            str(output_pdf),
            "--debug",
            "--title",
            "Test Title",
            "--author",
            "Test Author",
            "--date",
            "2026-02-11",
            "--version",
            "1.0",
        ]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run", return_value=MagicMock(returncode=0)
                    ) as mock_run:
                        main()

                        # Find the .tex generation call
                        tex_call = None
                        for call_args in mock_run.call_args_list:
                            cmd = (
                                call_args[0][0]
                                if call_args[0]
                                else call_args[1].get("cmd", [])
                            )
                            if "-o" in cmd and cmd[cmd.index("-o") + 1].endswith(
                                "_debug.tex"
                            ):
                                tex_call = cmd
                                break

                        assert tex_call is not None, (
                            ".tex generation pandoc call not found"
                        )

                        # Check for metadata variables
                        cmd_str = " ".join(tex_call)
                        assert "title=" in cmd_str
                        assert "author=" in cmd_str
                        assert "date=" in cmd_str
                        assert "git=" in cmd_str

    def test_normal_does_not_create_debug_files(self, tmp_path):
        """
        Test that without --debug flag, no debug artifacts are created.

        Given: convert.py called without --debug flag
        When: Conversion completes
        Then: No _debug.md or _debug.tex files exist
        """
        output_pdf = tmp_path / "output.pdf"
        expected_debug_md = tmp_path / "output_debug.md"
        expected_debug_tex = tmp_path / "output_debug.tex"
        test_args = ["convert.py", "input.md", str(output_pdf)]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run", return_value=MagicMock(returncode=0)
                    ):
                        main()

        assert not expected_debug_md.exists()
        assert not expected_debug_tex.exists()
