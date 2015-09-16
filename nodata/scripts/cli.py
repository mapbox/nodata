import click
import nodata

@click.group()
def cli():
    """There's no data like nodata!"""
    pass

@click.command(short_help="Fill seams in imagery / expand valid data area by (inter|extra)polation")
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.option('--bidx', '-b', default=None,
    help="Bands to fill [default = all]")
@click.option('--max-search-distance', '-m', default=4,
    help="Maximum filling radius [default = 4]")
@click.option('--nibblemask', '-n', default=False, is_flag=True,
    help="Nibble filled nodata areas that are (probably) not seams")
@click.option('--compress', '-c', default=None, type=click.Choice(['JPEG', 'LZW', 'DEFLATE', None]),
    help="Output compression type ('JPEG', 'LZW', 'DEFLATE') [default = input type]")
@click.option('--mask-threshold', '-d', default=None, type=int,
    help="Alpha pixel threshold upon which to regard data as masked (ie, for lossy you'd want an aggressive threshold of 0) [default=None]")
def blob(src_path, dst_path, bidx, max_search_distance, nibblemask, compress, mask_threshold):
    """"""
    nodata.blob.blob_nodata(src_path, dst_path, bidx, max_search_distance, nibblemask, compress, mask_threshold)

cli.add_command(blob)