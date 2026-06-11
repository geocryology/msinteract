"""
Tests for InputRunOptions.

The example file at ``src/msinteract/data/MESH_input_run_options.ini`` is
used as a read-only fixture.  Any test that modifies the file works on a
temporary copy so the source file is never altered.
"""

import datetime
import shutil
import os
import pytest

from msinteract.run_options import InputRunOptions, set_run_option_flag

# ---------------------------------------------------------------------------
# Path to the bundled example file
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "src", "msinteract", "data",
)
EXAMPLE_FILE = os.path.join(DATA_DIR, "MESH_input_run_options.ini")


# ---------------------------------------------------------------------------
# Fixture: temporary writable copy of the example file
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_ini(tmp_path):
    """Return a path to a writable copy of the example .ini file."""
    dest = tmp_path / "MESH_input_run_options.ini"
    shutil.copy(EXAMPLE_FILE, dest)
    return str(dest)


# ---------------------------------------------------------------------------
# get_flag / __getitem__
# ---------------------------------------------------------------------------

class TestGetFlag:
    def test_simple_integer_flag(self):
        opts = InputRunOptions(EXAMPLE_FILE)
        assert opts.get_flag("SHDFILEFLAG") == "2"

    def test_multi_token_flag(self):
        opts = InputRunOptions(EXAMPLE_FILE)
        value = opts.get_flag("BASINFORCINGFLAG")
        assert "met" in value

    def test_flag_with_start_date_option(self):
        opts = InputRunOptions(EXAMPLE_FILE)
        value = opts.get_flag("BASINFORCINGFLAG")
        assert "start_date=" in value

    def test_case_insensitive_lookup(self):
        opts = InputRunOptions(EXAMPLE_FILE)
        assert opts.get_flag("shdfileflag") == opts.get_flag("SHDFILEFLAG")

    def test_getitem_operator(self):
        opts = InputRunOptions(EXAMPLE_FILE)
        assert opts["SHDFILEFLAG"] == "2"

    def test_getitem_matches_get_flag(self):
        opts = InputRunOptions(EXAMPLE_FILE)
        assert opts["RUNMODE"] == opts.get_flag("RUNMODE")

    def test_missing_flag_raises_key_error(self):
        opts = InputRunOptions(EXAMPLE_FILE)
        with pytest.raises(KeyError):
            opts.get_flag("NONEXISTENTFLAG")

    def test_all_declared_flags_readable(self):
        """Every flag that appears in the file should be retrievable."""
        opts = InputRunOptions(EXAMPLE_FILE)
        expected_flags = [
            "BASINFORCINGFLAG",
            "SHDFILEFLAG",
            "INPUTPARAMSFORMFLAG",
            "SOILINIFLAG",
            "NRSOILAYEREADFLAG",
            "RUNMODE",
            "DIAGNOSEMODE",
            "TIMESTEPFLAG",
        ]
        for flag in expected_flags:
            value = opts.get_flag(flag)
            assert isinstance(value, str), f"{flag} should return a string"


# ---------------------------------------------------------------------------
# set_flag / __setitem__
# ---------------------------------------------------------------------------

class TestSetFlag:
    def test_set_integer_flag(self, tmp_ini):
        opts = InputRunOptions(tmp_ini)
        opts.set_flag("SHDFILEFLAG", "3")
        assert InputRunOptions(tmp_ini).get_flag("SHDFILEFLAG") == "3"

    def test_set_string_flag(self, tmp_ini):
        opts = InputRunOptions(tmp_ini)
        opts.set_flag("RUNMODE", "runsvs route")
        assert InputRunOptions(tmp_ini).get_flag("RUNMODE") == "runsvs route"

    def test_setitem_operator(self, tmp_ini):
        opts = InputRunOptions(tmp_ini)
        opts["TIMESTEPFLAG"] = "30"
        assert InputRunOptions(tmp_ini)["TIMESTEPFLAG"] == "30"

    def test_set_flag_preserves_other_flags(self, tmp_ini):
        opts = InputRunOptions(tmp_ini)
        original_runmode = opts.get_flag("RUNMODE")
        opts.set_flag("SHDFILEFLAG", "99")
        assert InputRunOptions(tmp_ini).get_flag("RUNMODE") == original_runmode

    def test_set_flag_case_insensitive(self, tmp_ini):
        opts = InputRunOptions(tmp_ini)
        opts.set_flag("shdfileflag", "5")
        assert InputRunOptions(tmp_ini).get_flag("SHDFILEFLAG") == "5"

    def test_set_missing_flag_raises_key_error(self, tmp_ini):
        opts = InputRunOptions(tmp_ini)
        with pytest.raises(KeyError):
            opts.set_flag("NONEXISTENTFLAG", "1")

    def test_roundtrip_set_then_get(self, tmp_ini):
        opts = InputRunOptions(tmp_ini)
        opts.set_flag("NRSOILAYEREADFLAG", "7")
        assert InputRunOptions(tmp_ini).get_flag("NRSOILAYEREADFLAG") == "7"

    def test_module_level_helper(self, tmp_ini):
        set_run_option_flag(tmp_ini, "SOILINIFLAG", "2")
        assert InputRunOptions(tmp_ini).get_flag("SOILINIFLAG") == "2"


# ---------------------------------------------------------------------------
# get_output_directory
# ---------------------------------------------------------------------------

class TestGetOutputDirectory:
    def test_example_file_output_directory(self):
        opts = InputRunOptions(EXAMPLE_FILE)
        assert opts.get_output_directory() == "output"

    def test_returns_string(self):
        opts = InputRunOptions(EXAMPLE_FILE)
        assert isinstance(opts.get_output_directory(), str)

    def test_directory_has_no_whitespace(self):
        opts = InputRunOptions(EXAMPLE_FILE)
        dirname = opts.get_output_directory()
        assert ' ' not in dirname and '\t' not in dirname


# ---------------------------------------------------------------------------
# get_start_date / get_end_date  (all-zero → None)
# ---------------------------------------------------------------------------

class TestGetDatesAllZero:
    def test_start_date_is_none_when_zero(self):
        opts = InputRunOptions(EXAMPLE_FILE)
        assert opts.get_start_date() is None

    def test_end_date_is_none_when_zero(self):
        opts = InputRunOptions(EXAMPLE_FILE)
        assert opts.get_end_date() is None


# ---------------------------------------------------------------------------
# set_start_date / set_end_date
# ---------------------------------------------------------------------------

class TestSetDates:
    def test_set_start_date_and_read_back(self, tmp_ini):
        target = datetime.datetime(2012, 6, 1, 0, 0)  # 2012, day 153
        opts = InputRunOptions(tmp_ini)
        opts.set_start_date(target)
        result = InputRunOptions(tmp_ini).get_start_date()
        assert result == target

    def test_set_end_date_and_read_back(self, tmp_ini):
        target = datetime.datetime(2015, 1, 1, 0, 0)  # 2015, day 1
        opts = InputRunOptions(tmp_ini)
        opts.set_end_date(target)
        result = InputRunOptions(tmp_ini).get_end_date()
        assert result == target

    def test_set_start_date_to_none(self, tmp_ini):
        # First set a non-zero date, then reset to None
        opts = InputRunOptions(tmp_ini)
        opts.set_start_date(datetime.datetime(2012, 6, 1))
        opts.set_start_date(None)
        assert InputRunOptions(tmp_ini).get_start_date() is None

    def test_set_end_date_to_none(self, tmp_ini):
        opts = InputRunOptions(tmp_ini)
        opts.set_end_date(datetime.datetime(2015, 1, 1))
        opts.set_end_date(None)
        assert InputRunOptions(tmp_ini).get_end_date() is None

    def test_set_date_preserves_flags(self, tmp_ini):
        opts = InputRunOptions(tmp_ini)
        original_flag = opts.get_flag("SHDFILEFLAG")
        opts.set_start_date(datetime.datetime(2010, 3, 15, 6, 30))
        assert InputRunOptions(tmp_ini).get_flag("SHDFILEFLAG") == original_flag

    def test_set_date_with_hour_and_minute(self, tmp_ini):
        target = datetime.datetime(2020, 11, 30, 18, 30)
        opts = InputRunOptions(tmp_ini)
        opts.set_end_date(target)
        result = InputRunOptions(tmp_ini).get_end_date()
        assert result.year == 2020
        assert result.hour == 18
        assert result.minute == 30

    def test_set_date_leap_year(self, tmp_ini):
        # 2016 is a leap year; day 60 is Feb 29
        target = datetime.datetime(2016, 2, 29, 0, 0)
        opts = InputRunOptions(tmp_ini)
        opts.set_start_date(target)
        result = InputRunOptions(tmp_ini).get_start_date()
        assert result == target

    def test_start_and_end_dates_independent(self, tmp_ini):
        start = datetime.datetime(2012, 6, 1)
        end = datetime.datetime(2015, 1, 1)
        opts = InputRunOptions(tmp_ini)
        opts.set_start_date(start)
        opts.set_end_date(end)
        reloaded = InputRunOptions(tmp_ini)
        assert reloaded.get_start_date() == start
        assert reloaded.get_end_date() == end
