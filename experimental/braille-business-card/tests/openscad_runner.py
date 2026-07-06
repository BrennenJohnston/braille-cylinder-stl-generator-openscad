"""
OpenSCAD CLI Runner for Cross-Platform STL Validation

This module automates OpenSCAD CLI execution to generate STL files from .scad files
with specified parameters. It handles parameter mapping, command construction, and
error handling for the validation framework.

License: PolyForm Noncommercial 1.0.0
"""

import json
import logging
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OpenSCADResult:
    """Result of an OpenSCAD CLI execution."""

    success: bool
    output_path: Optional[Path]
    stdout: str
    stderr: str
    returncode: int
    duration_seconds: float
    command: str


class OpenSCADNotFoundError(Exception):
    """Raised when OpenSCAD executable cannot be found."""

    pass


class OpenSCADExecutionError(Exception):
    """Raised when OpenSCAD execution fails."""

    pass


class OpenSCADRunner:
    """
    Wrapper for OpenSCAD CLI to generate STL files from .scad scripts.

    Handles:
    - OpenSCAD executable detection across platforms
    - Parameter passing via -D flags or parameter files
    - Command construction and execution
    - Timeout handling
    - Error reporting
    """

    def __init__(
        self,
        openscad_path: Optional[Path] = None,
        default_timeout_seconds: int = 300,
        use_manifold: Optional[bool] = None,
        enforce_version: Optional[str] = None,
    ):
        """
        Initialize OpenSCAD runner.

        Args:
            openscad_path: Path to OpenSCAD executable. If None, auto-detect.
            default_timeout_seconds: Default timeout for OpenSCAD execution
            use_manifold: Use Manifold backend (faster). None=auto-detect, True=force, False=use CGAL
            enforce_version: If set, enforce this exact OpenSCAD version (for CI reproducibility)
        """
        self.openscad_path = openscad_path or self._find_openscad()
        self.default_timeout_seconds = default_timeout_seconds
        self._verify_openscad()
        self.version_string = self.get_version()
        self.use_manifold = use_manifold if use_manifold is not None else self._detect_manifold_support()
        
        # Version enforcement (primarily for CI)
        if enforce_version:
            self._enforce_version(enforce_version)

    def _find_openscad(self) -> Path:
        """
        Auto-detect OpenSCAD executable path based on platform.

        Returns:
            Path to OpenSCAD executable

        Raises:
            OpenSCADNotFoundError: If OpenSCAD cannot be found
        """
        system = platform.system()

        # First check if 'openscad' is in PATH
        openscad_cmd = shutil.which("openscad")
        if openscad_cmd:
            return Path(openscad_cmd)

        # Platform-specific default locations
        if system == "Windows":
            default_paths = [
                Path(r"C:\Program Files\OpenSCAD\openscad.exe"),
                Path(r"C:\Program Files (x86)\OpenSCAD\openscad.exe"),
            ]
        elif system == "Darwin":  # macOS
            default_paths = [
                Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"),
            ]
        elif system == "Linux":
            default_paths = [
                Path("/usr/bin/openscad"),
                Path("/usr/local/bin/openscad"),
                Path("/snap/bin/openscad"),
            ]
        else:
            default_paths = []

        for path in default_paths:
            if path.exists():
                return path

        raise OpenSCADNotFoundError(
            "OpenSCAD executable not found. Searched PATH and default locations.\n"
            "Please install OpenSCAD (https://openscad.org/downloads.html) or\n"
            "add it to PATH."
        )

    def _verify_openscad(self) -> None:
        """
        Verify OpenSCAD executable works and get version.

        Raises:
            OpenSCADNotFoundError: If OpenSCAD doesn't work
        """
        try:
            result = subprocess.run(
                [str(self.openscad_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            version_output = result.stdout or result.stderr
            logger.info(f"Found OpenSCAD: {version_output.strip()}")
        except Exception as e:
            raise OpenSCADNotFoundError(
                f"OpenSCAD executable found at {self.openscad_path} but failed to run: {e}"
            )

    def _detect_manifold_support(self) -> bool:
        """
        Detect if OpenSCAD supports the Manifold backend.
        
        Manifold is available in OpenSCAD nightly builds (2024+) and provides
        significantly faster boolean operations compared to CGAL.

        Returns:
            True if Manifold backend is supported, False otherwise
        """
        try:
            result = subprocess.run(
                [str(self.openscad_path), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            help_output = result.stdout or result.stderr
            has_manifold = "--backend" in help_output and "Manifold" in help_output
            if has_manifold:
                logger.info("Manifold backend detected - enabling for faster rendering")
            return has_manifold
        except Exception:
            return False

    def get_version(self) -> str:
        """
        Get OpenSCAD version string.

        Returns:
            Version string (e.g., "OpenSCAD version 2021.01" or "OpenSCAD version 2026.01.03")
        """
        result = subprocess.run(
            [str(self.openscad_path), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (result.stdout or result.stderr).strip()
    
    def _enforce_version(self, required_version: str) -> None:
        """
        Enforce exact OpenSCAD version for reproducibility.
        
        Args:
            required_version: Required version string (e.g., "2026.01.03")
            
        Raises:
            OpenSCADNotFoundError: If version doesn't match
        """
        if required_version not in self.version_string:
            raise OpenSCADNotFoundError(
                f"OpenSCAD version mismatch!\n"
                f"Required: {required_version}\n"
                f"Found: {self.version_string}\n"
                f"For reproducible testing, please install OpenSCAD {required_version} "
                f"from https://files.openscad.org/snapshots/."
            )
        logger.info(f"✓ OpenSCAD version check passed: {required_version}")
    
    def check_manifold_backend(self, require_manifold: bool = False) -> bool:
        """
        Check if Manifold backend is available and optionally require it.
        
        Args:
            require_manifold: If True, raise error if Manifold is not available
            
        Returns:
            True if Manifold is available
            
        Raises:
            OpenSCADNotFoundError: If require_manifold=True and Manifold not available
        """
        if require_manifold and not self.use_manifold:
            raise OpenSCADNotFoundError(
                f"Manifold backend is required but not available in this OpenSCAD build.\n"
                f"Found: {self.version_string}\n"
                f"Please install an OpenSCAD 2026.01.03+ nightly with Manifold support "
                f"from https://files.openscad.org/snapshots/."
            )
        return self.use_manifold

    def generate_stl(
        self,
        scad_file: Path,
        output_stl: Path,
        parameters: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> OpenSCADResult:
        """
        Generate STL file from OpenSCAD file with parameters.

        Args:
            scad_file: Path to .scad input file
            output_stl: Path to output STL file
            parameters: Dictionary of OpenSCAD variables to set (via -D flags)
            timeout_seconds: Execution timeout (uses default if None)

        Returns:
            OpenSCADResult with execution details

        Raises:
            OpenSCADExecutionError: If OpenSCAD execution fails
        """
        import time

        if not scad_file.exists():
            raise FileNotFoundError(f"OpenSCAD file not found: {scad_file}")

        # Ensure output directory exists
        output_stl.parent.mkdir(parents=True, exist_ok=True)

        # Build command
        cmd = self._build_command(scad_file, output_stl, parameters)
        timeout = timeout_seconds or self.default_timeout_seconds

        logger.info(f"Running OpenSCAD: {scad_file.name} -> {output_stl.name}")
        logger.debug(f"Command: {' '.join(cmd)}")

        # Execute OpenSCAD with proper process management and progress reporting
        start_time = time.time()
        process = None
        try:
            # Use Popen for better process control on Windows
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=scad_file.parent,
            )
            
            # Poll with progress reporting instead of blocking communicate()
            stdout_data = b""
            stderr_data = b""
            last_report_time = start_time
            report_interval = 15  # Report progress every 15 seconds
            
            while True:
                # Check if process has finished
                retcode = process.poll()
                if retcode is not None:
                    # Process finished - read any remaining output
                    remaining_stdout, remaining_stderr = process.communicate(timeout=5)
                    stdout_data += remaining_stdout or b""
                    stderr_data += remaining_stderr or b""
                    break
                
                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    logger.error(f"OpenSCAD timed out after {timeout} seconds - killing process")
                    self._kill_process_tree(process.pid)
                    return OpenSCADResult(
                        success=False,
                        output_path=None,
                        stdout="",
                        stderr=f"Process timed out after {timeout} seconds",
                        returncode=-1,
                        duration_seconds=elapsed,
                        command=" ".join(cmd),
                    )
                
                # Report progress periodically
                if time.time() - last_report_time >= report_interval:
                    logger.info(f"  ... still processing ({int(elapsed)}s elapsed)")
                    last_report_time = time.time()
                
                # Small sleep to avoid busy-waiting
                time.sleep(0.5)
            
            duration = time.time() - start_time
            stdout_str = stdout_data.decode("utf-8", errors="replace") if stdout_data else ""
            stderr_str = stderr_data.decode("utf-8", errors="replace") if stderr_data else ""
            
            success = process.returncode == 0 and output_stl.exists()

            if not success:
                logger.error(f"OpenSCAD failed (returncode={process.returncode})")
                if stderr_str:
                    logger.error(f"stderr: {stderr_str}")

            return OpenSCADResult(
                success=success,
                output_path=output_stl if success else None,
                stdout=stdout_str,
                stderr=stderr_str,
                returncode=process.returncode,
                duration_seconds=duration,
                command=" ".join(cmd),
            )
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"OpenSCAD execution error: {e}")
            if process:
                self._kill_process_tree(process.pid)
            return OpenSCADResult(
                success=False,
                output_path=None,
                stdout="",
                stderr=str(e),
                returncode=-1,
                duration_seconds=duration,
                command=" ".join(cmd),
            )
    
    def _kill_process_tree(self, pid: int) -> None:
        """
        Kill a process and all its children (Windows-compatible).
        
        Args:
            pid: Process ID to kill
        """
        try:
            if platform.system() == "Windows":
                # Use taskkill to kill the entire process tree on Windows
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    timeout=10,
                )
            else:
                # On Unix, use process group
                import os
                import signal
                os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception as e:
            logger.warning(f"Failed to kill process tree {pid}: {e}")

    def _build_command(
        self,
        scad_file: Path,
        output_stl: Path,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Build OpenSCAD command with parameters.

        Args:
            scad_file: Path to .scad file
            output_stl: Path to output STL
            parameters: Dictionary of OpenSCAD variables

        Returns:
            Command as list of strings
        """
        cmd = [
            str(self.openscad_path),
            "-o",
            str(output_stl),
        ]

        # Use Manifold backend if available (much faster for boolean operations)
        if self.use_manifold:
            cmd.extend(["--backend", "Manifold"])

        # Add parameter definitions
        if parameters:
            for key, value in parameters.items():
                cmd.extend(["-D", self._format_parameter(key, value)])

        # Add input file
        cmd.append(str(scad_file))

        return cmd

    def _format_parameter(self, key: str, value: Any) -> str:
        """
        Format parameter for OpenSCAD -D flag.

        Args:
            key: Parameter name
            value: Parameter value

        Returns:
            Formatted parameter string (e.g., 'Line_1="⠓⠑⠇⠇⠕"')
        """
        if isinstance(value, str):
            # Escape quotes and wrap in quotes
            escaped_value = value.replace('"', '\\"')
            return f'{key}="{escaped_value}"'
        elif isinstance(value, bool):
            # OpenSCAD booleans are lowercase true/false
            return f"{key}={str(value).lower()}"
        elif isinstance(value, (int, float)):
            return f"{key}={value}"
        else:
            # For other types, convert to string
            return f'{key}="{str(value)}"'

    def generate_stl_from_json(
        self,
        scad_file: Path,
        output_stl: Path,
        params_json: Path,
        timeout_seconds: Optional[int] = None,
    ) -> OpenSCADResult:
        """
        Generate STL using parameters from JSON file.

        This is a convenience method that loads parameters from a JSON file
        (e.g., test fixture params.json) and calls generate_stl().

        Args:
            scad_file: Path to .scad input file
            output_stl: Path to output STL file
            params_json: Path to JSON file with parameters
            timeout_seconds: Execution timeout

        Returns:
            OpenSCADResult with execution details
        """
        with open(params_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract parameters - handle both direct params and nested structure
        if "parameters" in data:
            parameters = data["parameters"]
        else:
            parameters = data

        return self.generate_stl(
            scad_file=scad_file,
            output_stl=output_stl,
            parameters=parameters,
            timeout_seconds=timeout_seconds,
        )


def main():
    """Example usage and testing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate STL from OpenSCAD file with parameters"
    )
    parser.add_argument("scad_file", type=Path, help="Input .scad file")
    parser.add_argument("output_stl", type=Path, help="Output STL file")
    parser.add_argument(
        "--params-json", type=Path, help="JSON file with parameters"
    )
    parser.add_argument(
        "--timeout", type=int, default=300, help="Timeout in seconds"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        runner = OpenSCADRunner()
        logger.info(f"Using OpenSCAD: {runner.get_version()}")

        if args.params_json:
            result = runner.generate_stl_from_json(
                scad_file=args.scad_file,
                output_stl=args.output_stl,
                params_json=args.params_json,
                timeout_seconds=args.timeout,
            )
        else:
            result = runner.generate_stl(
                scad_file=args.scad_file,
                output_stl=args.output_stl,
                timeout_seconds=args.timeout,
            )

        if result.success:
            logger.info(
                f"✓ STL generated successfully in {result.duration_seconds:.1f}s"
            )
            logger.info(f"  Output: {result.output_path}")
            return 0
        else:
            logger.error("✗ STL generation failed")
            if result.stderr:
                logger.error(f"  Error: {result.stderr}")
            return 1

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
