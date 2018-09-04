# -*- coding: utf-8 -*-
"""Console scripts for threedigrid."""

from __future__ import absolute_import
import click
from IPython.terminal.embed import InteractiveShellEmbed

from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.management import help_texts

file_type_choice_map = {'shape': 'to_shape', 'gpkg': 'to_gpkg'}


@click.command()
@click.option('--grid-file', prompt='Path to the admin file',
              help='Path to the admin file', type=click.Path(exists=True))
@click.option('--ipy/--no-ipy', default=False,
              help='Start an interactive ipython session')
def kick_start(grid_file, ipy):
    grid = GridH5Admin(grid_file)

    txt = help_texts.model_overview(grid_file)
    click.secho("""\nOverview of model specifics:\n""", bold=True)
    click.secho(txt)

    if ipy:
        info_txt = '\n\nA GridH5Admin instance for model {} has been ' \
                   'created (variable named grid). Call dir(grid) to ' \
                   'explore.\n'.format(grid.model_name)
        click.secho(info_txt, bg='green', fg='black', bold=True)
        ipshell = InteractiveShellEmbed(exit_msg='Ciao...\n')
        ipshell()


@click.command()
@click.option('--grid-file', prompt='Path to the admin file',
              help='Path to the admin file', type=click.Path(exists=True))
@click.option('--file-type', type=click.Choice(['shape', 'gpkg']))
@click.option('--output-file', prompt='Path to the output file',
              help='Path to the output file',
              type=click.Path(writable=True, resolve_path=True))
@click.option('--model', type=click.Choice(
    ['nodes', 'lines', 'breaches', 'levees']))
@click.option('--subset', default='',
              help='Filter by a subset like 1D_all '
                   '(applies only for models nodes and lines')
def export_to(grid_file, file_type, output_file, model, subset):
    success_msg = 'Successfully created {} '.format(output_file)
    grid = GridH5Admin(grid_file)
    m = getattr(grid, model)
    export_func = file_type_choice_map[file_type]
    if subset:
        getattr(m.subset(subset), export_func)(output_file)
        click.secho(success_msg, fg='green', bold=True)
        return
    getattr(m, export_func)(output_file)
    click.secho(success_msg, fg='green', bold=True)


if __name__ == "__main__":
    kick_start()
