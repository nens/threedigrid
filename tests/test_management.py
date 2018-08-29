from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import tempfile

from click.testing import CliRunner

from threedigrid.management import help_texts
from threedigrid.management.commands.kick import kick_start
from threedigrid.management.commands.kick import export_to


test_file_dir = os.path.join(
    os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
grid_admin_h5_file = os.path.join(test_file_dir, "gridadmin.h5")


def test_model_overview():
    # smoke test
    txt = help_texts.model_overview(grid_admin_h5_file)
    assert txt != ''


def test_command_kick_start():
    # smoke test
    runner = CliRunner()
    result = runner.invoke(
        kick_start,
        [u"--grid-file={}".format(grid_admin_h5_file), u"--no-ipy"])
    assert result.exit_code == 0


def test_command_export_to():
    # smoke test

    d = tempfile.mkdtemp()
    test_shp = os.path.join(d, "cmd_exporter_test_lines.shp")

    runner = CliRunner()
    result = runner.invoke(
        export_to,
        [u"--grid-file={}".format(grid_admin_h5_file),
         u"--file-type=shape",
         u"--output-file={}".format(test_shp),
         u"--model=lines",
         u"--subset=1d_all",
         ]
    )
    assert result.exit_code == 0
    assert (os.path.exists(test_shp))
