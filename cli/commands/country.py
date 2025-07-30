import click
import pycountry


@click.command(help="Finalize clean data for plotting")
@click.argument("country_code", type=str, required=False)
def country(country_code):
    try:
        country = pycountry.countries.search_fuzzy(country_code)[0]
    except LookupError:
        click.echo(f"Country code '{country_code}' not found.")
        return
    except IndexError:
        click.echo(f"Country code '{country_code}' not found.")
        return
    if country:
        if hasattr(country, 'name'):
            click.echo(f"Name: {country.name}")
        if hasattr(country, 'official_name'):
            click.echo(f"Official name: {country.official_name}")
        if hasattr(country, 'common_name'):
            click.echo(f"Common name: {country.common_name}")
        if hasattr(country, 'flag'):
            click.echo(f"Flag: {country.flag}")
        if hasattr(country, 'alpha_2'):
            click.echo(f"Alpha_2 code: {country.alpha_2}")
        if hasattr(country, 'alpha_3'):
            click.echo(f"Alpha_3 code: {country.alpha_3}")
        if hasattr(country, 'numeric'):
            click.echo(f"Numeric code: {country.numeric}")
