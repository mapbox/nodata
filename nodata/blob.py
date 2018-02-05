import json
import numpy as np
from numbers import Number

import rasterio as rio
from rasterio.fill import fillnodata
from rasterio.windows import Window
import riomucho

from scipy.ndimage.filters import maximum_filter, minimum_filter


def pad_window(wnd, pad):
    try:
        wnd = wnd.toranges()
    except AttributeError:
        # rasterio < 1.0, already a tuple
        pass

    return (
        (wnd[0][0] - pad, wnd[0][1] + pad),
        (wnd[1][0] - pad, wnd[1][1] + pad)
    )


def test_rgb(count, nodata, alphafy, outCount):
    if count == 3 and alphafy:
        if not isinstance(nodata, Number):
            raise ValueError('3 band imagery must have a defined nodata value')

        return None, nodata, outCount
    elif alphafy:
        return None, None, count
    else:
        return nodata, nodata, count


def fill_nodata(img, mask, fillBands, maxSearchDistance):
    for b in fillBands:
        img[b - 1] = fillnodata(img[b - 1], mask, maxSearchDistance)

    return img


def runNodataFiller(mask, pad):
    nonZero = np.count_nonzero(mask[pad:-pad, pad:-pad])

    if nonZero == 0 or nonZero == mask[pad:-pad, pad:-pad].size:
        return False
    else:
        return True


def handle_RGB(img, mask):
    return np.concatenate([img, mask.reshape(1, mask.shape[-2], mask.shape[-1])])


def blob_worker(srcs, window, ij, globalArgs):
    pad = globalArgs['max_search_distance'] + 1
    padded = pad_window(window, pad)
    padWindow = Window.from_slices(*padded, boundless=True)
    img = srcs[0].read(boundless=True, window=padWindow)

    if isinstance(globalArgs['selectNodata'], Number):
        mask = srcs[0].read_masks(boundless=True, window=padWindow)[0]
        img = handle_RGB(img, mask)
        alphamask = False
    else:
        mask = img[-1]
        alphamask = True

    if globalArgs['maskThreshold'] is not None and alphamask:
        img[-1] = (np.invert(img[-1] < globalArgs['maskThreshold']).astype(img.dtype)
                   * np.iinfo(img.dtype).max)
        mask = img[-1]

    if runNodataFiller(mask, pad):
        img = fill_nodata(
            img, mask, globalArgs['bands'],
            globalArgs['max_search_distance'])[:, pad: -pad, pad: -pad]

        if globalArgs['nibblemask'] \
                and alphamask is False \
                and 'nodata' in srcs[0].meta:

            img = nibble_filled_mask(
                img,
                srcs[0].meta['nodata'],
                globalArgs['max_search_distance'])

        elif globalArgs['nibblemask'] and alphamask:
            img[-1] = nibble_filled_mask(
                img[-1],
                None,
                globalArgs['max_search_distance'],
                True)

    else:
        img = img[:, pad: -pad, pad: -pad]

    return img


def blob_nodata(
        src_path, dst_path, bidx, max_search_distance, nibblemask,
        creation_options, maskThreshold, workers, alphafy):
    """
    """
    with rio.open(src_path) as src:
        windows = [
            [window, ij] for ij, window in src.block_windows()
        ]

        options = src.meta.copy()
        kwds = src.profile.copy()

        outNodata, selectNodata, outCount = test_rgb(src.count, src.nodata, alphafy, 4)

        options.update(**kwds)
        options.update(**creation_options)
        options.update(count=outCount, nodata=outNodata)

        if bidx:
            try:
                bidx = [int(b) for b in json.loads(bidx)]
            except Exception as e:
                raise e

            if bidx and (len(bidx) == 0 or len(bidx) > src.count):
                raise ValueError(
                    "Bands %s differ from source count of %s" %
                    (', '.join([str(b) for b in bidx]), src.count))
        elif alphafy and src.count == 3:
            bidx = list(src.indexes)
            bidx.append(src.indexes[-1] + 1)
        else:
            bidx = list(src.indexes)

        if maskThreshold is not None:
            maskThreshold = np.iinfo(options['dtype']).max - maskThreshold

    with riomucho.RioMucho(
            [src_path], dst_path, blob_worker,
            windows=windows,
            global_args={
                'max_search_distance': max_search_distance,
                'nibblemask': nibblemask,
                'bands': bidx,
                'maskThreshold': maskThreshold,
                'selectNodata': selectNodata
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
    with rio.open(src_path, 'r') as src:
        img = src.read(masked=False)
        kwargs = src.meta
        if 'nodata' in src.meta:
            nodataval = src.meta['nodata']
        else:
            nodataval = 0.0

    kwargs.update(compress='lzw')

    nibbled = nibble_filled_mask(img, nodataval, nibble)

    with rio.open(dst_path, 'w', **kwargs) as dst:
        for i, arr in enumerate(nibbled, 1):
            dst.write(arr, i)
