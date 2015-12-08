import click

from rasterio.rio.options import creation_options

from nodata.blob import blob_nodata


@click.group()
def cli():
    """There's no data like nodata!"""
    pass


@click.command(
    short_help="Blob + expand valid data area by (inter|extra)polation into"
               "nodata areas")
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.option('--bidx', '-b', default=None,
    help="Bands to blob [default = all]")
@click.option('--max-search-distance', '-m', default=4,
    help="Maximum blobbing radius [default = 4]")
@click.option('--nibblemask', '-n', default=False, is_flag=True,
    help="Nibble blobbed nodata areas [default=False]")
@creation_options
@click.option('--mask-threshold', '-d', default=None, type=int,
    help="Alpha pixel threshold upon which to regard data as masked "
         "(ie, for lossy you'd want an aggressive threshold of 0) "
         "[default=None]")
@click.option('--jobs', '-j', default=4, type=int,
    help="Number of workers for multiprocessing [default=4]")
@click.option('--alphafy', '-a', is_flag=True,
    help='If a RGB raster is found, blob + add alpha band where nodata is')
def blob(src_path, dst_path, bidx, max_search_distance, nibblemask,
        creation_options, mask_threshold, jobs, alphafy):
    """"""
    blob_nodata(
        src_path, dst_path, bidx, max_search_distance, nibblemask,
        creation_options, mask_threshold, jobs, alphafy)


cli.add_command(blob)


@click.command(short_help="Take RGB image and create RGBA with masked Alpha band")
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.option('--ndv', type=int, default=None)
@click.option('--mode', type=click.Choice(['exact', 'slic']), default='exact')
@click.option('--padding', type=int, default=0)
@click.option('--jobs', '-j', type=int, default=None)
def alpha(src_path, dst_path, ndv, mode, padding, jobs):
    """"""
    from nodata.alphamask import simple_mask, slic_mask
    from .alpha import NodataPoolMan
    import rasterio

    if mode == 'exact':
        func = simple_mask
    elif mode == 'slic':
        func = slic_mask

    with rasterio.open(src_path, 'r') as src:
        profile = src.profile
        source_ndv = src.nodata
        windows = [window for ij, window in src.block_windows()]

    ndv = ndv or source_ndv
    if not ndv:
        raise click.UsageError("Dataset nodata is not defined, must supply --ndv")

    ndpm = NodataPoolMan(src_path, func, ndv, num_workers=jobs)

    profile['count'] += 1
    profile['transform'] = src.affine
    with rasterio.open(dst_path, 'w', **profile) as dst:
        for win, data in ndpm.mask(windows, padding=padding):
            dst.write(data, window=win)

cli.add_command(alpha)
