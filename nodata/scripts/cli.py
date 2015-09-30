import click
import nodata

@click.group()
def cli():
    """There's no data like nodata!"""
    pass

@click.command(short_help="Blob + expand valid data area by (inter|extra)polation into nodata areas")
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.option('--bidx', '-b', default=None,
    help="Bands to blob [default = all]")
@click.option('--max-search-distance', '-m', default=4,
    help="Maximum blobbing radius [default = 4]")
@click.option('--nibblemask', '-n', default=False, is_flag=True,
    help="Nibble blobbed nodata areas [default=False]")
@click.option('--compress', '-c', default=None, type=click.Choice(['JPEG', 'LZW', 'DEFLATE', 'None']),
    help="Output compression type ('JPEG', 'LZW', 'DEFLATE') [default = input type]")
@click.option('--mask-threshold', '-d', default=None, type=int,
    help="Alpha pixel threshold upon which to regard data as masked (ie, for lossy you'd want an aggressive threshold of 0) [default=None]")
@click.option('--workers', '-w', default=4, type=int,
    help="Number of workers for multiprocessing [default=4]")
@click.option('--alphafy', '-a', is_flag=True,
    help='If a RGB raster is found, blob + add alpha band where nodata is')
def blob(src_path, dst_path, bidx, max_search_distance, nibblemask, compress, mask_threshold, workers, alphafy):
    """"""
    nodata.blob.blob_nodata(src_path, dst_path, bidx, max_search_distance, nibblemask, compress, mask_threshold, workers, alphafy)

cli.add_command(blob)


@click.command(short_help="Take RGB image and create RGBA with masked Alpha band")
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
def alpha(src_path, dst_path):
    """"""
    from nodata.alphamask import simple_mask, slic_mask
    from .alpha import NodataPoolMan
    import rasterio

    func = simple_mask

    with rasterio.open(src_path, 'r') as src:
        profile = src.profile
        profile['count'] += 1
        profile['transform'] = src.affine
        ndv = src.nodata or (255, 255, 255)  # TODO arg
        windows =  [[window, ij] for ij, window in src.block_windows()]

    ndpm = NodataPoolMan(src_path, func, ndv)
    with rasterio.open(dst_path, 'w', **profile) as dst:
        for win, data in ndpm.add_mask(windows):
            dst.write(data, window=win)

cli.add_command(alpha)
