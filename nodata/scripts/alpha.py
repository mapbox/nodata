import sys
import zlib

import numpy
import rasterio


base_kwds = None
src = None


def init_worker(path, profile):
    global base_kwds, src
    base_kwds = profile.copy()
    src = rasterio.open(path)


def finalize_worker():
    global base_kwds, src
    src.close()
    src = None
    base_kwds = None


def compute_window_mask(window, nodata, func, **kwargs):
    """Execute the given function with keyword arguments to compute a valid
    data mask.

    Returns the window and mask as deflated bytes.
    """
    global src
    source = src.read(window=window, boundless=True)
    return window, zlib.compress(func(source, nodata, **kwargs))
