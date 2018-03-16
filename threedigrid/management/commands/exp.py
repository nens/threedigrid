# -*- coding: utf-8 -*-
"""Console script for threedigrid."""
import click

from threedigrid.admin.gridadmin import GridH5Admin


@click.command()
@click.option('--grid-file', prompt='Path to the admin file',
              help='Path to the admin file', type=click.Path(exists=True))
@click.argument('--model', help='model, e.g nodes, lines,...')
@click.argument('--subset', help='subset')
def export_to(grid_file, model, subset):
    grid = GridH5Admin(grid_file)
    m = getattr(grid, model)
    s = getattr(m, subset)
    click.echo(s)

