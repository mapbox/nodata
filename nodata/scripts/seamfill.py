import rasterio as rio
from rasterio.fill import fillnodata
import click

import numpy as np
from scipy.ndimage.filters import maximum_filter, minimum_filter

def padWindow(wnd, pad):
    return (
        (wnd[0][0] - pad, wnd[0][1] + pad),
        (wnd[1][0] - pad, wnd[1][1] + pad)
    )

def fillseams(src_path, dst_path, max_search_distance, nibblemask):
    """Usage: ..."""
    with rio.drivers():
        with rio.open(src_path, 'r') as src:
            kwargs = src.meta
            kwargs.update(compress='lzw', transform=kwargs['affine'])
            pad = max_search_distance + 1

            with rio.open(dst_path, 'w', **kwargs) as dst:
                for ji, window in src.block_windows():
                    pWindow = padWindow(window, pad)

                    if src.count == 3:
                        mask = src.read_masks(boundless=True, window=pWindow)[0]
                        alphamask = False
                    else:
                        mask = src.read(src.count, boundless=True, window=pWindow)
                        alphamask = True

                    ras = src.read(boundless=True, window=pWindow)

                    if mask[pad:-pad, pad:-pad].any():
                        ras = [fillnodata(b, mask, max_search_distance)[pad:-pad, pad:-pad] for b in ras]

                        if nibblemask and alphamask == False and 'nodata' in src.meta:
                            ras = nibbleFilledMask(ras, src.meta['nodata'], max_search_distance)
                        elif nibblemask and alphamask:
                            ras[-1] = nibbleFilledMask(ras[-1], None, max_search_distance, True)

                    for i, arr in enumerate(ras, 1):
                        dst.write(arr, i, window=window)

def nibbleFilledMask(filled, nodataval, max_search_distance, is_mask=False):
    filled = np.array(filled)
    if is_mask:
        filled = minimum_filter(filled, size=(max_search_distance * 2 + 1))
    else:
        nmsk = (filled[0] == nodataval) & (filled[1] == nodataval) & (filled[2] == nodataval)
        nmsk = maximum_filter(nmsk, size=(max_search_distance * 2 + 1))
        mskInds = np.where(nmsk == True)
        filled[:, mskInds[0], mskInds[1]] = nodataval

    return filled

def makeNibbled(src_path, dst_path, nibble):
    with rio.drivers():
        with rio.open(src_path, 'r') as src:
            ras = src.read(masked=False)
            kwargs = src.meta
            if 'nodata' in src.meta:
                nodataval = src.meta['nodata']
            else:
                nodataval = 0.0

        # to silence the warning  
        kwargs.update(compress='lzw', transform=kwargs['affine'])

        nibbled = nibbleFilledMask(ras, nodataval, nibble)

        with rio.open(dst_path, 'w', **kwargs) as dst:
            for i, arr in enumerate(nibbled, 1):
                dst.write(arr, i)