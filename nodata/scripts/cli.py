import click
import nodata

@click.group()
def cli():
    """There's no data like nodata!"""
    pass

@click.command(short_help="Fill seams in imagery / expand valid data area by (inter|extra)polation")
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.option('--bidx', '-b', default=None, help="Bands to fill [default = all]")
@click.option('--max-search-distance', '-m', default=4, help="Maximum filling radius [default = 4]")
@click.option('--nibblemask', '-n', default=False, is_flag=True, help="Nibble filled nodata areas that are (probably) not seams")
@click.option('--compress', '-c', default=None, type=click.Choice(['JPEG', 'LZW', 'DEFLATE', None]), help="Output compression type ('JPEG', 'LZW', 'DEFLATE') [default = input type]")
def seamfill(src_path, dst_path, bidx, max_search_distance, nibblemask, compress):
    """"""
    nodata.seamfill.fillseams(src_path, dst_path, bidx, max_search_distance, nibblemask, compress)

cli.add_command(seamfill)