"""
Tests for GFM callout/alert support in convert.py.

This module tests the pandoc command construction for GitHub-Flavored Markdown
alert syntax (> [!NOTE], > [!TIP], etc.) including:
- Inclusion of -f markdown+alerts format flag in the PDF pandoc command
- Inclusion of --lua-filter=callout.lua flag in the PDF pandoc command
- Inclusion of -f markdown+alerts in the debug .tex generation command
- Inclusion of --lua-filter=callout.lua in the debug .tex generation command
- Existence of the assets/callout.lua file itself
"""

import os
import shutil
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from convert import main


def _find_pdf_call(mock_run):
    """Extract the pandoc command list for the PDF generation call.

    Args:
        mock_run: The mock object for convert.subprocess.run.

    Returns:
        The command list (list[str]) for the PDF pandoc call, or None if not
        found.
    """
    for call_args in mock_run.call_args_list:
        cmd = call_args[0][0] if call_args[0] else call_args[1].get("cmd", [])
        if "-o" in cmd and cmd[cmd.index("-o") + 1].endswith(".pdf"):
            return cmd
    return None


def _find_tex_call(mock_run):
    """Extract the pandoc command list for the debug .tex generation call.

    Args:
        mock_run: The mock object for convert.subprocess.run.

    Returns:
        The command list (list[str]) for the .tex pandoc call, or None if not
        found.
    """
    for call_args in mock_run.call_args_list:
        cmd = call_args[0][0] if call_args[0] else call_args[1].get("cmd", [])
        if "-o" in cmd and cmd[cmd.index("-o") + 1].endswith(".tex"):
            return cmd
    return None


class TestCalloutAlertsFormatFlag:
    """Tests for -f markdown+alerts flag in the pandoc PDF command."""

    def test_pandoc_cmd_includes_alerts_format_flag(self, tmp_path):
        """
        Test that the PDF pandoc command includes -f markdown+alerts.

        Given: convert.py called with a standard input file
        When: The pandoc command for PDF generation is constructed
        Then: The command contains -f followed by markdown+alerts as consecutive
              arguments
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf)]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run",
                        return_value=MagicMock(returncode=0),
                    ) as mock_run:
                        main()

                        pdf_call = _find_pdf_call(mock_run)
                        assert pdf_call is not None, (
                            "PDF generation pandoc call not found"
                        )

                        # -f and markdown+alerts must appear as consecutive args
                        assert "-f" in pdf_call, (
                            "-f flag not found in PDF pandoc command"
                        )
                        f_index = pdf_call.index("-f")
                        assert f_index + 1 < len(pdf_call), (
                            "-f flag has no following argument"
                        )
                        assert pdf_call[f_index + 1] == "markdown+alerts", (
                            f"Expected 'markdown+alerts' after -f, "
                            f"got '{pdf_call[f_index + 1]}'"
                        )

    def test_pandoc_cmd_alerts_format_value_is_exact(self, tmp_path):
        """
        Test that the format value is exactly 'markdown+alerts', not a prefix.

        Given: convert.py called with a standard input file
        When: The pandoc command for PDF generation is constructed
        Then: The argument immediately following -f equals 'markdown+alerts'
              exactly (not 'markdown' or 'markdown+alerts+something')
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf)]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run",
                        return_value=MagicMock(returncode=0),
                    ) as mock_run:
                        main()

                        pdf_call = _find_pdf_call(mock_run)
                        assert pdf_call is not None, (
                            "PDF generation pandoc call not found"
                        )

                        f_indices = [i for i, arg in enumerate(pdf_call) if arg == "-f"]
                        assert len(f_indices) >= 1, (
                            "-f flag not found in PDF pandoc command"
                        )

                        format_values = [
                            pdf_call[i + 1] for i in f_indices if i + 1 < len(pdf_call)
                        ]
                        assert "markdown+alerts" in format_values, (
                            f"No -f markdown+alerts found; format values seen: "
                            f"{format_values}"
                        )


class TestCalloutLuaFilter:
    """Tests for --lua-filter=callout.lua flag in the pandoc PDF command."""

    def test_pandoc_cmd_includes_lua_filter(self, tmp_path):
        """
        Test that the PDF pandoc command includes a --lua-filter= pointing to
        callout.lua.

        Given: convert.py called with a standard input file
        When: The pandoc command for PDF generation is constructed
        Then: The command contains a --lua-filter=... argument whose value ends
              with 'callout.lua'
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf)]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run",
                        return_value=MagicMock(returncode=0),
                    ) as mock_run:
                        main()

                        pdf_call = _find_pdf_call(mock_run)
                        assert pdf_call is not None, (
                            "PDF generation pandoc call not found"
                        )

                        lua_filter_args = [
                            arg for arg in pdf_call if arg.startswith("--lua-filter=")
                        ]
                        assert len(lua_filter_args) >= 1, (
                            "--lua-filter= flag not found in PDF pandoc command"
                        )

                        callout_filters = [
                            arg
                            for arg in lua_filter_args
                            if arg.endswith("callout.lua")
                        ]
                        assert len(callout_filters) >= 1, (
                            "No --lua-filter pointing to callout.lua found; "
                            f"lua-filter args present: {lua_filter_args}"
                        )

    def test_pandoc_cmd_lua_filter_points_to_asset_path(self, tmp_path):
        """
        Test that the --lua-filter= value uses the get_asset_path resolution
        for callout.lua (i.e. the path contains 'assets/callout.lua' or simply
        ends with 'callout.lua' under the script directory).

        Given: convert.py called with a standard input file
        When: The pandoc command for PDF generation is constructed
        Then: The --lua-filter= value is an absolute path ending in callout.lua
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf)]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run",
                        return_value=MagicMock(returncode=0),
                    ) as mock_run:
                        main()

                        pdf_call = _find_pdf_call(mock_run)
                        assert pdf_call is not None, (
                            "PDF generation pandoc call not found"
                        )

                        callout_filter_arg = next(
                            (
                                arg
                                for arg in pdf_call
                                if arg.startswith("--lua-filter=")
                                and arg.endswith("callout.lua")
                            ),
                            None,
                        )
                        assert callout_filter_arg is not None, (
                            "--lua-filter=<path>/callout.lua not found in PDF "
                            "pandoc command"
                        )

                        filter_path = callout_filter_arg.split("=", 1)[1]
                        assert os.path.isabs(filter_path), (
                            f"Expected absolute path for lua-filter, got: {filter_path}"
                        )
                        assert filter_path.endswith("callout.lua"), (
                            f"Expected path ending in callout.lua, got: {filter_path}"
                        )


class TestDebugTexCalloutSupport:
    """Tests for callout flags in the debug .tex generation pandoc command."""

    def test_debug_tex_cmd_includes_alerts_format_flag(self, tmp_path):
        """
        Test that the debug .tex pandoc command includes -f markdown+alerts.

        Given: convert.py called with --debug flag
        When: The second pandoc call (for .tex generation) is constructed
        Then: The command contains -f followed by markdown+alerts
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf), "--debug"]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run",
                        return_value=MagicMock(returncode=0),
                    ) as mock_run:
                        main()

                        tex_call = _find_tex_call(mock_run)
                        assert tex_call is not None, (
                            ".tex generation pandoc call not found; "
                            "ensure --debug triggers a second pandoc call "
                            "with a .tex output path"
                        )

                        assert "-f" in tex_call, (
                            "-f flag not found in .tex pandoc command"
                        )
                        f_index = tex_call.index("-f")
                        assert f_index + 1 < len(tex_call), (
                            "-f flag has no following argument in .tex command"
                        )
                        assert tex_call[f_index + 1] == "markdown+alerts", (
                            f"Expected 'markdown+alerts' after -f in .tex command, "
                            f"got '{tex_call[f_index + 1]}'"
                        )

    def test_debug_tex_cmd_includes_lua_filter(self, tmp_path):
        """
        Test that the debug .tex pandoc command includes --lua-filter=callout.lua.

        Given: convert.py called with --debug flag
        When: The second pandoc call (for .tex generation) is constructed
        Then: The command contains a --lua-filter= argument ending with callout.lua
        """
        output_pdf = tmp_path / "output.pdf"
        test_args = ["convert.py", "input.md", str(output_pdf), "--debug"]

        with patch("sys.argv", test_args):
            with patch("convert.process_markdown", return_value="# Content"):
                with patch("convert.os.path.exists", return_value=True):
                    with patch(
                        "convert.subprocess.run",
                        return_value=MagicMock(returncode=0),
                    ) as mock_run:
                        main()

                        tex_call = _find_tex_call(mock_run)
                        assert tex_call is not None, (
                            ".tex generation pandoc call not found; "
                            "ensure --debug triggers a second pandoc call "
                            "with a .tex output path"
                        )

                        lua_filter_args = [
                            arg for arg in tex_call if arg.startswith("--lua-filter=")
                        ]
                        assert len(lua_filter_args) >= 1, (
                            "--lua-filter= flag not found in .tex pandoc command"
                        )

                        callout_filters = [
                            arg
                            for arg in lua_filter_args
                            if arg.endswith("callout.lua")
                        ]
                        assert len(callout_filters) >= 1, (
                            "No --lua-filter pointing to callout.lua found in "
                            ".tex command; lua-filter args present: "
                            f"{lua_filter_args}"
                        )


class TestCalloutLuaAsset:
    """Tests for the existence of the callout.lua asset file."""

    def test_callout_lua_asset_exists(self):
        """
        Test that assets/callout.lua exists on disk.

        Given: The converter project repository
        When: The assets directory is inspected
        Then: assets/callout.lua is present (required for --lua-filter to work)

        Note: This test is expected to FAIL in the RED phase because callout.lua
        has not yet been created. It serves as a sentinel that drives creation
        of the file in the GREEN phase.
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate from tests/unit/ up to the project root
        project_root = os.path.dirname(os.path.dirname(script_dir))
        callout_lua_path = os.path.join(project_root, "assets", "callout.lua")

        assert os.path.isfile(callout_lua_path), (
            f"assets/callout.lua not found at {callout_lua_path}. "
            "The file must be created as part of GFM callout support."
        )


# Check for pandoc availability at module level for skip decorator
_has_pandoc = shutil.which("pandoc") is not None


@pytest.mark.skipif(not _has_pandoc, reason="pandoc not installed")
class TestCalloutLuaFilterBehavior:
    """Tests for the actual output of callout.lua when run through pandoc."""

    @pytest.fixture()
    def lua_filter_path(self):
        """Return absolute path to assets/callout.lua."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        return os.path.join(project_root, "assets", "callout.lua")

    def _run_pandoc(self, markdown: str, lua_filter: str, fmt: str = "markdown+alerts"):
        """Run pandoc with the lua filter and return LaTeX output."""
        result = subprocess.run(
            ["pandoc", "-f", fmt, f"--lua-filter={lua_filter}", "-t", "latex"],
            input=markdown,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"pandoc failed: {result.stderr}"
        return result.stdout

    def test_note_callout_produces_cosaicallout_environment(self, lua_filter_path):
        """
        Given: Markdown with > [!NOTE] callout
        When: Processed through pandoc with callout.lua
        Then: Output contains \\begin{cosaicallout}{note} and \\end{cosaicallout}
        """
        md = "> [!NOTE]\n> This is a note.\n"
        output = self._run_pandoc(md, lua_filter_path)
        assert "\\begin{cosaicallout}{note}" in output
        assert "\\end{cosaicallout}" in output
        assert "This is a note." in output

    def test_all_five_alert_types_produce_correct_environments(self, lua_filter_path):
        """
        Given: Markdown with all 5 GFM alert types
        When: Processed through pandoc with callout.lua
        Then: Each type produces its own cosaicallout environment
        """
        types = ["NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"]
        for alert_type in types:
            md = f"> [!{alert_type}]\n> Content for {alert_type.lower()}.\n"
            output = self._run_pandoc(md, lua_filter_path)
            assert f"\\begin{{cosaicallout}}{{{alert_type.lower()}}}" in output, (
                f"[!{alert_type}] did not produce cosaicallout environment"
            )

    def test_regular_blockquote_unchanged(self, lua_filter_path):
        """
        Given: A regular blockquote without [!TYPE] marker
        When: Processed through pandoc with callout.lua
        Then: Output uses standard \\begin{quote} environment
        """
        md = "> This is a regular quote.\n"
        output = self._run_pandoc(md, lua_filter_path)
        assert "\\begin{quote}" in output
        assert "cosaicallout" not in output

    def test_unknown_alert_type_unchanged(self, lua_filter_path):
        """
        Given: A blockquote with unsupported [!UNKNOWN] marker
        When: Processed through pandoc with callout.lua
        Then: Output preserves as regular blockquote (no cosaicallout)
        """
        md = "> [!UNKNOWN]\n> This should stay a blockquote.\n"
        output = self._run_pandoc(md, lua_filter_path)
        assert "cosaicallout" not in output

    def test_callout_with_multiline_content(self, lua_filter_path):
        """
        Given: A [!WARNING] callout with multiple paragraphs
        When: Processed through pandoc with callout.lua
        Then: All content is wrapped in the cosaicallout environment
        """
        md = "> [!WARNING]\n> First paragraph.\n>\n> Second paragraph.\n"
        output = self._run_pandoc(md, lua_filter_path)
        assert "\\begin{cosaicallout}{warning}" in output
        assert "First paragraph." in output
        assert "Second paragraph." in output
        assert "\\end{cosaicallout}" in output
