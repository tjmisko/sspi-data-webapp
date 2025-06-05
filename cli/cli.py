import click
from cli.commands.collect import collect
from cli.commands.compute import compute
from cli.commands.country import country
from cli.commands.coverage import coverage
from cli.commands.delete import delete
from cli.commands.extrapolate import extrapolate
from cli.commands.interpolate import interpolate
from cli.commands.finalize import finalize
from cli.commands.impute import impute
from cli.commands.metadata import metadata
from cli.commands.panel import panel
from cli.commands.pull import pull
from cli.commands.push import push
from cli.commands.query import query
from cli.commands.save import save
from cli.commands.url import url
from cli.commands.view import view


@click.group()
def cli():
    pass


cli.add_command(collect)
cli.add_command(compute)
cli.add_command(country)
cli.add_command(coverage)
cli.add_command(delete)
cli.add_command(extrapolate)
cli.add_command(interpolate)
cli.add_command(finalize)
cli.add_command(impute)
cli.add_command(metadata)
cli.add_command(panel)
cli.add_command(pull)
cli.add_command(push)
cli.add_command(query)
cli.add_command(save)
cli.add_command(url)
cli.add_command(view)
