import click
import json
import numpy as np

import rasterio as rio
from rasterio.fill import fillnodata
import riomucho

from scipy.ndimage.filters import maximum_filter, minimum_filter

def pad_window(wnd, pad):
    return (
        (wnd[0][0] - pad, wnd[0][1] + pad),
        (wnd[1][0] - pad, wnd[1][1] + pad)
    )

def test_rgb(count, nodata, alphafy, outCount):
    if count == 3 and alphafy:
        if not isinstance(nodata, (int, long, float)):
            raise ValueError('3 band imagery must have a defined nodata value')
        
        return nodata, outCount
    else:
        return None, count

def fill_nodata(img, mask, fillBands, maxSearchDistance):

    for b in fillBands:
        img[b - 1] = fillnodata(img[b - 1], mask, maxSearchDistance)

    return img

def handle_RGB(img, mask):
    return np.concatenate([img, np.array([mask])])

def blob_worker(srcs, window, ij, globalArgs):

    pad = globalArgs['max_search_distance'] + 1

    padWindow = pad_window(window, pad)

    img = srcs[0].read(boundless=True, window=padWindow)

    if isinstance(globalArgs['outNodata'], (int, long, float)):
        mask = srcs[0].read_masks(boundless=True, window=padWindow)[0]
        img = handle_RGB(img, mask)
        alphamask = False
    else:
        mask = img[-1]
        alphamask = True
    
    if globalArgs['maskThreshold'] != None and alphamask:
        img[-1] = (img[-1] > globalArgs['maskThreshold']).astype(img.dtype) * img[-1].max()

    if mask[pad:-pad, pad:-pad].any():

        img = fill_nodata(img, mask, globalArgs['bands'], globalArgs['max_search_distance'])[:, pad: -pad, pad: -pad]

        if globalArgs['nibblemask'] and alphamask == False and 'nodata' in srcs[0].meta:
            img = nibble_filled_mask(
                img,
                srcs[0].meta['nodata'],
                globalArgs['max_search_distance']
                )

        elif globalArgs['nibblemask'] and alphamask:
            img[-1] = nibble_filled_mask(
                img[-1],
                None,
                globalArgs['max_search_distance'],
                True)

    return img


def blob_nodata(src_path, dst_path, bidx, max_search_distance, nibblemask,
        creation_options, maskThreshold, workers, alphafy):

    with rio.open(src_path) as src:
        windows = [
            [window, ij] for ij, window in src.block_windows()
        ]

        options = src.meta.copy()

        outNodata, outCount = test_rgb(src.count, src.nodata, alphafy, 4)

        options.update(
            tiled=True,
            blockxsize=src.block_shapes[0][0],
            blockysize=src.block_shapes[0][1],
            count=outCount,
            nodata=outNodata
            )

        # Update withcreation options like 'compress': 'lzw'.
        options.update(**creation_options)

        if bidx:
            try:
                bidx = [int(b) for b in json.loads(bidx)]
            except Exception as e:
                raise e
        else:
            bidx = src.indexes

        if len(bidx) == 0 or len(bidx) > src.count:
            raise ValueError("Bands %s differ from source count of %s" % (', '.join([str(b) for b in bidx]), src.count))

    with riomucho.RioMucho([src_path], dst_path, blob_worker,
        windows=windows,
        global_args={
            'max_search_distance': max_search_distance,
            'nibblemask': nibblemask,
            'bands': bidx,
            'maskThreshold': maskThreshold,
            'outNodata': outNodata
        }, 
        options=options,
        mode='manual_read') as rm:

        rm.run(workers)


def nibble_filled_mask(filled, nodataval, max_search_distance, is_mask=False):
    filled = np.array(filled)
    if is_mask:
        filled = minimum_filter(filled, size=(max_search_distance * 2 + 1))
    else:
        nmsk = (filled[0] == nodataval) & (filled[1] == nodataval) & (filled[2] == nodataval)
        nmsk = maximum_filter(nmsk, size=(max_search_distance * 2 + 1))
        mskInds = np.where(nmsk == True)
        filled[:, mskInds[0], mskInds[1]] = nodataval

    return filled

def make_nibbled(src_path, dst_path, nibble):
    with rio.drivers():
        with rio.open(src_path, 'r') as src:
            img = src.read(masked=False)
            kwargs = src.meta
            if 'nodata' in src.meta:
                nodataval = src.meta['nodata']
            else:
                nodataval = 0.0

        # to silence the warning  
        kwargs.update(compress='lzw', transform=kwargs['affine'])

        nibbled = nibble_filled_mask(img, nodataval, nibble)

        with rio.open(dst_path, 'w', **kwargs) as dst:
            for i, arr in enumerate(nibbled, 1):
                dst.write(arr, i)
