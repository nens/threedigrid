# -*- coding: utf-8 -*-
"""Console script for threedigrid."""

from IPython.terminal.embed import InteractiveShellEmbed
from traitlets.config.loader import Config

import click
from admin.gridadmin import GridH5Admin

cfg = Config()

@click.command()
@click.option('--grid-file', prompt='Path to the admin file',
              help='Path to the admin file', type=click.Path(exists=True))
def kick_start(grid_file):
    """Console script for threedigrid."""

    grid = GridH5Admin(grid_file)
    banner = '''
Starting an IPython session...\n\nA GridH5Admin instance for model {} has been created (variable named grid).
Call dir(grid) to explore. \n\nOverview of model specifics: \n
threedicore version: \t{}
has 1D: \t\t{}
has 2D: \t\t{}
has groundwater: \t{}
has levees: \t\t{}
'''.format(
        grid.model_name,
        grid.threedicore_version,
        grid.has_1d,
        grid.has_2d,
        grid.has_groundwater,
        grid.has_levees,)

    ipshell = InteractiveShellEmbed(
        config=cfg,
        banner1=banner,
        exit_msg='\nLeaving IPython, quiting...\n'
    )
    ipshell()


if __name__ == "__main__":
    kick_start()
