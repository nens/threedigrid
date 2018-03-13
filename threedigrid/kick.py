# -*- coding: utf-8 -*-
"""Console script for threedigrid."""

from IPython.terminal.embed import InteractiveShellEmbed

import click
from admin.gridadmin import GridH5Admin
from threedigrid.help_texts import model_overview

@click.command()
@click.option('--grid-file', prompt='Path to the admin file',
              help='Path to the admin file', type=click.Path(exists=True))
@click.option('--ipy/--no-ipy', default=False, help='Start an interactive ipdb session')
def kick_start(grid_file, ipy):
    """Console script for threedigrid."""

    grid = GridH5Admin(grid_file)

    txt = model_overview(grid_file)
    click.secho("""\nOverview of model specifics:\n""", bold=True)
    click.secho(txt)

    if ipy:
        info_txt = '\n\nA GridH5Admin instance for model {} has been created (variable named grid). ' \
                   'Call dir(grid) to explore.\n'.format(grid.model_name)
        click.secho(info_txt, bg='green', fg='black', bold=True)
        ipshell = InteractiveShellEmbed(exit_msg='Ciao...\n')
        ipshell()

if __name__ == "__main__":
    kick_start()
