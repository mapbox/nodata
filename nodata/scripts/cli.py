import click
import nodata

@click.group()
def cli():
    """There's no data like nodata!"""
    pass

@click.command(short_help="Fill seams in imagery / expand valid data area by (inter|extra)polation")
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.option('--max-search-distance', '-m', default=4, help="Maximum filling radius [default = 4]")
@click.option('--nibblemask', '-n', default=False, is_flag=True, help="Nibble filled nodata areas that are (probably) not seams")
def seamfill(src_path, dst_path, max_search_distance, nibblemask):
    """"""
    nodata.seamfill.fillseams(src_path, dst_path, max_search_distance, nibblemask)
    # fillseams(src_path, dst_path, max_search_distance, nibblemask)

cli.add_command(seamfill)