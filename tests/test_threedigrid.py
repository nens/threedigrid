#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `threedigrid` package."""


import unittest
from click.testing import CliRunner

from threedigrid import threedigrid
from threedigrid import cli

#import ipdb; ipdb.set_trace()


class TestThreedigrid(unittest.TestCase):
    """Tests for `threedigrid` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'threedigrid.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output
