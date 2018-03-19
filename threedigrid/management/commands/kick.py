# -*- coding: utf-8 -*-
"""Console scripts for threedigrid."""

import click
from IPython.terminal.embed import InteractiveShellEmbed

from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.management.help_texts import model_overview

@click.command()
@click.option('--grid-file', prompt='Path to the admin file',
              help='Path to the admin file', type=click.Path(exists=True))
@click.option('--ipy/--no-ipy', default=False, help='Start an interactive ipython session')
def kick_start(grid_file, ipy):
    """
    :param grid_file: Path to the admin file
    :param ipy: Start an interactive ipython session
    """

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


@click.command()
@click.option('--grid-file', prompt='Path to the admin file',
              help='Path to the admin file', type=click.Path(exists=True))
@click.argument('model')
@click.argument('subset')
def export_to(grid_file, model, subset):
    """

    :param grid_file:  Path to the admin file
    :param model: name of the grid admin model, e.g Nodes/Lines/...
    :param subset:
    :return:
    """
    grid = GridH5Admin(grid_file)
    m = getattr(grid, model)
    s = getattr(m, "subset")(subset)
    click.echo(s.data)


if __name__ == "__main__":
    kick_start()
