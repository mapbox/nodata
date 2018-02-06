from itertools import repeat
from multiprocessing import cpu_count, Pool
import sys
import zlib
try:
    from itertools import izip
except ImportError:
    izip = zip  # py3 use builtin zip

import numpy
import rasterio


# We're compelled to use global variables for the source dataset and masking
# algorithm function. The worker initialization and finalization functions
# make sure that the globals of a worker process are set up and cleaned up
# properly.

src_dataset = None
mask_function = None


def init_worker(path, func):
    global mask_function, src_dataset
    mask_function = func
    src_dataset = rasterio.open(path)


def finalize_worker():
    global mask_function, src_dataset
    src_dataset.close()
    mask_function = None
    src_dataset = None


# The following function is executed by worker processes.

def compute_window_mask(args):
    """Execute the given function with keyword arguments to compute a
    valid data mask.

    Returns the window and mask as deflated bytes.
    """
    window, nodata, extra_args = args
    global mask_function, src_dataset

    padding = int(extra_args.get('padding', 0))

    if padding:
        start, stop = zip(*window)
        start = [v - 10 for v in start]
        stop = [v + 10 for v in stop]
        read_window = zip(*[start, stop])
    else:
        read_window = window

    source = src_dataset.read(window=read_window, boundless=True)
    result = mask_function(source, nodata, **extra_args)

    if padding:
        result = result[:, padding:-padding, padding:-padding]

    return window, zlib.compress(result.tobytes())


def all_valid(arr, nodata, **kwargs):
    """Return an all-valid mask of the same shape and type as the
    given array"""
    return 255 * numpy.ones_like(arr[0])


class NodataPoolMan:
    """Nodata processing pool manager

    This class encapsulates the execution of nodata algorithms on
    windows of a dataset.
    """

    def __init__(self, input_path, func, nodata, num_workers=None,
            max_tasks=100):
        """Create a pool of workers to process window masks"""
        self.input_path = input_path
        self.func = func
        self.nodata = nodata

        # Peek in the source file for metadata. We could even get the
        # nodata value from here in some cases.
        with rasterio.open(input_path) as src:
            self.dtype = src.dtypes[0]

        self.pool = Pool(
            num_workers or cpu_count()-1, init_worker, (input_path, func),
            max_tasks)

    def mask(self, windows, **kwargs):
        """Iterate over windows and compute mask arrays.

        The keyword arguments will be passed as keyword arguments to the
        manager's mask algorithm function.

        Yields window, ndarray pairs.
        """
        iterargs = izip(windows, repeat(self.nodata), repeat(kwargs))
        for out_window, data in self.pool.imap_unordered(
                compute_window_mask, iterargs):

            out_data = numpy.fromstring(
                        zlib.decompress(data), self.dtype).reshape(
                            [int(x) for x in rasterio.windows.shape(out_window)])

            yield out_window, out_data
