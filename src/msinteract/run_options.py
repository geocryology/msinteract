import re
import os
import datetime
from typing import Optional


class InputRunOptions:
    """
    Class to manage reading and updating run option flags in MESH-SVS2 input files.

    The file format is documented in ``input_run_options_documentation.pdf``.
    Key formatting rules:
    - Control-flag count and diagnostic-point count use Fortran ``(i5)``
      fixed-format: the integer is right-justified in the first five characters
      of the line.
    - The output-directory name is left-justified in exactly ten characters
      (padded with spaces; clipped if longer than ten).
    - Simulation run-time lines contain four free-format integers:
      year, day-of-year, hour (0-23), minute.
    - All-zero run times mean "start from / run until the end of driving data".
    """

    def __init__(self, file_path):
        self.file_path = file_path

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __getitem__(self, key):
        return self.get_flag(key)

    def __setitem__(self, key, value):
        """Set a control flag using dict-style write access (``obj["FLAG"] = "val"``)."""
        self.set_flag(key, value)

    # ------------------------------------------------------------------
    # Internal I/O helpers
    # ------------------------------------------------------------------

    def _read_lines(self):
        with open(self.file_path, 'r') as f:
            return f.readlines()

    def _write_lines(self, lines):
        with open(self.file_path, 'w') as f:
            f.writelines(lines)

    def _find_section(self, lines, pattern):
        """Return the index of the first line matching *pattern* (case-insensitive)."""
        for i, line in enumerate(lines):
            if re.search(pattern, line, re.IGNORECASE):
                return i
        return -1

    # ------------------------------------------------------------------
    # Control flags
    # ------------------------------------------------------------------

    def _get_control_flags_range(self, lines):
        """Return ``(start_idx, count)`` for the control-flags block.

        *start_idx* is the index of the first flag line.
        *count* is the number of flags declared in the section header.
        """
        header_idx = self._find_section(lines, r'#{5}.*control.*flag.*#{5}')
        if header_idx == -1:
            raise ValueError("Could not find '##### Control Flags #####' section")

        # The header is followed immediately by a '----#' separator line and
        # then the count line (Fortran i5 format: integer in first 5 chars).
        for i in range(header_idx + 1, min(header_idx + 6, len(lines))):
            if lines[i].rstrip().endswith('----#') or lines[i].strip() == '----#':
                count_line = lines[i + 1]
                try:
                    count = int(count_line[:5])
                except ValueError as exc:
                    raise ValueError(
                        f"Could not parse flag count from line: {count_line!r}"
                    ) from exc
                return i + 2, count

        raise ValueError("Could not locate '----#' separator in Control Flags section")

    def get_flag(self, key):
        """Return the value string for the control flag *key*.

        Lookup is case-insensitive.  Raises :class:`KeyError` when not found.
        """
        lines = self._read_lines()
        start_idx, count = self._get_control_flags_range(lines)
        key_upper = key.upper()

        for i in range(start_idx, start_idx + count):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            parts = stripped.split(None, 1)
            if parts and parts[0].upper() == key_upper:
                return parts[1].strip() if len(parts) > 1 else ""

        raise KeyError(f"Flag {key!r} not found in {self.file_path!r}")

    def set_flag(self, key, value):
        """Update the value of control flag *key* in-place.

        The flag name and its original leading/trailing whitespace are
        preserved; only the value portion is replaced.
        Raises :class:`KeyError` when the flag is not found.
        """
        lines = self._read_lines()
        start_idx, count = self._get_control_flags_range(lines)
        key_upper = key.upper()

        for i in range(start_idx, start_idx + count):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            parts = stripped.split(None, 1)
            if parts and parts[0].upper() == key_upper:
                # Preserve everything up to and including the key name plus its
                # original inter-column whitespace, then append the new value.
                m = re.match(r'^(\s*\S+\s+)', line)
                if m:
                    prefix = m.group(1)
                else:
                    prefix = parts[0] + '  '
                lines[i] = prefix + value + '\n'
                self._write_lines(lines)
                return

        raise KeyError(f"Flag {key!r} not found in {self.file_path!r}")

    # ------------------------------------------------------------------
    # Output directory
    # ------------------------------------------------------------------

    def get_output_directory(self):
        """Return the output directory name (stripped of padding spaces).

        The model reads exactly ten characters; names longer than ten
        characters are silently clipped by MESH.
        """
        lines = self._read_lines()
        header_idx = self._find_section(lines, r'#{5}.*output.*director.*#{5}')
        if header_idx == -1:
            raise ValueError("Could not find '##### Output Directory #####' section")

        for i in range(header_idx + 1, min(header_idx + 5, len(lines))):
            if re.match(r'\s*-{9}#', lines[i]):
                dir_line = lines[i + 1]
                return dir_line[:10].strip()

        raise ValueError("Could not locate '---------#' separator in Output Directory section")

    # ------------------------------------------------------------------
    # Simulation run times
    # ------------------------------------------------------------------

    def _find_run_times_lines(self, lines):
        """Return ``(start_line_idx, stop_line_idx)`` for the two time lines."""
        header_idx = self._find_section(lines, r'#{5}.*simulation.*run.*time.*#{5}')
        if header_idx == -1:
            raise ValueError("Could not find '##### Simulation Run Times #####' section")

        for i in range(header_idx + 1, min(header_idx + 6, len(lines))):
            if '---#---#---#---#' in lines[i]:
                return i + 1, i + 2

        raise ValueError(
            "Could not locate '---#---#---#---#' separator in Simulation Run Times section"
        )

    @staticmethod
    def _parse_time_line(line):
        """Parse ``year doy hour minute`` from a simulation time line.

        The comment (everything from ``#`` onward) is stripped before
        parsing so it does not interfere with the integer read.
        """
        comment_idx = line.find('#')
        data = line[:comment_idx] if comment_idx != -1 else line
        parts = data.split()
        if len(parts) < 4:
            raise ValueError(f"Expected 4 integers in run-time line, got: {line!r}")
        return int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])

    @staticmethod
    def _time_to_datetime(year, doy, hour, minute):
        """Convert ``(year, doy, hour, minute)`` to :class:`datetime.datetime`.

        Returns ``None`` when all four fields are zero (meaning MESH will
        use the first / last frame of the driving data).
        """
        if year == 0 and doy == 0 and hour == 0 and minute == 0:
            return None
        base = datetime.datetime(year, 1, 1)
        return base + datetime.timedelta(days=doy - 1, hours=hour, minutes=minute)

    @staticmethod
    def _datetime_to_time(dt):
        """Convert :class:`datetime.datetime` (or ``None``) to ``(year, doy, hour, minute)``."""
        if dt is None:
            return 0, 0, 0, 0
        return dt.year, dt.timetuple().tm_yday, dt.hour, dt.minute

    @staticmethod
    def _format_time_line(year, doy, hour, minute, comment=""):
        """Format a run-time line, preserving any original comment."""
        # Each field is right-justified in 4 characters to maintain
        # compatibility with older MESH versions that use (i4,i4,i4,i4).
        nums = f"{year:4d}{doy:4d}{hour:4d}{minute:4d}"
        if comment:
            return f"{nums} {comment}\n"
        return f"{nums}\n"

    def get_start_date(self) -> Optional[datetime.datetime]:
        """Return the simulation start date as :class:`datetime.datetime`.

        Returns ``None`` when all fields are zero (i.e. start from first
        frame of driving data).
        """
        lines = self._read_lines()
        start_idx, _ = self._find_run_times_lines(lines)
        year, doy, hour, minute = self._parse_time_line(lines[start_idx])
        return self._time_to_datetime(year, doy, hour, minute)

    def get_end_date(self) -> Optional[datetime.datetime]:
        """Return the simulation end/stop date as :class:`datetime.datetime`.

        Returns ``None`` when all fields are zero (i.e. run until driving
        data is exhausted).
        """
        lines = self._read_lines()
        _, stop_idx = self._find_run_times_lines(lines)
        year, doy, hour, minute = self._parse_time_line(lines[stop_idx])
        return self._time_to_datetime(year, doy, hour, minute)

    def set_start_date(self, start_date: datetime.datetime):
        """Write the simulation start date.

        Pass ``None`` to reset to all-zeros (start from first frame of
        driving data).
        """
        lines = self._read_lines()
        start_idx, _ = self._find_run_times_lines(lines)
        year, doy, hour, minute = self._datetime_to_time(start_date)
        comment = self._extract_comment(lines[start_idx])
        lines[start_idx] = self._format_time_line(year, doy, hour, minute, comment)
        self._write_lines(lines)

    def set_end_date(self, end_date: datetime.datetime):
        """Write the simulation end/stop date.

        Pass ``None`` to reset to all-zeros (run until driving data ends).
        """
        lines = self._read_lines()
        _, stop_idx = self._find_run_times_lines(lines)
        year, doy, hour, minute = self._datetime_to_time(end_date)
        comment = self._extract_comment(lines[stop_idx])
        lines[stop_idx] = self._format_time_line(year, doy, hour, minute, comment)
        self._write_lines(lines)

    @staticmethod
    def _extract_comment(line):
        """Return the ``# …`` comment portion of a line, or empty string."""
        m = re.search(r'#.*$', line)
        return m.group(0).rstrip() if m else ""


# ---------------------------------------------------------------------------
# Module-level helper (used by conversion.py)
# ---------------------------------------------------------------------------

def set_run_option_flag(file_path, key, value):
    """Set a single run-option flag in *file_path*.

    Convenience wrapper around :meth:`InputRunOptions.set_flag` kept for
    backwards compatibility with code that calls this function directly.
    """
    InputRunOptions(file_path).set_flag(key, value)