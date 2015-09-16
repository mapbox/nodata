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

def make_windows(width, height, blocksize):
    for x in range(0, width, blocksize):
       for y in range(0, height, blocksize):
           yield (
               (y, min((y + blocksize), height)),
               (x, min((x + blocksize), width))
               )

def seam_filler(srcs, window, ij, globalArgs):
    pad = globalArgs['max_search_distance'] + 1

    padWindow = pad_window(window, pad)

    img = srcs[0].read(boundless=True, window=padWindow)

    if srcs[0].count == 3:
        mask = srcs[0].read_masks(boundless=True, window=padWindow)[0]
        alphamask = False
    else:
        mask = img[-1].copy()
        alphamask = True

    if globalArgs['maskThreshold'] != None and alphamask:
        img[-1] = (img[-1] > globalArgs['maskThreshold']).astype(img.dtype) * img[-1].max()

    if mask[pad:-pad, pad:-pad].any():
        for b in globalArgs['bands']:
            img[b - 1] = fillnodata(img[b - 1], mask, globalArgs['max_search_distance'])

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

    return img[:, pad: -pad, pad: -pad]

def fillseams(src_path, dst_path, bidx, max_search_distance, nibblemask, compress, maskThreshold):

    with rio.open(src_path) as src:
        windows = [
            [window, ij] for ij, window in src.block_windows()
        ]

        options = src.meta.copy()

        if compress:
            options.update(compress=compress)

        if bidx:
            try:
                bidx = [int(b) for b in json.loads(bidx)]
            except Exception as e:
                raise e
        else:
            bidx = src.indexes

        if len(bidx) == 0 or len(bidx) > src.count:
            raise ValueError("Bands %s differ from source count of %s" % (', '.join([str(b) for b in bidx]), src.count))

    with riomucho.RioMucho([src_path], dst_path, seam_filler,
        windows=windows,
        global_args={
            'max_search_distance': max_search_distance,
            'nibblemask': nibblemask,
            'bands': bidx,
            'maskThreshold': maskThreshold
        }, 
        options=options,
        mode='manual_read') as rm:

        rm.run(4)


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