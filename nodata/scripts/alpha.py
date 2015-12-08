from itertools import izip, repeat
from multiprocessing import cpu_count, Pool
from nodata.alphamask import all_valid_edges
import zlib

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

def compute_window_rgba(args):
    """Execute the given function with keyword arguments to compute a
    valid data mask.

    Returns the window and mask as deflated bytes.
    """
    window, ndv, extra_args = args
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

    # Normalize nodata, if single number -> make a tuple
    if isinstance(ndv, (int, float)):
        ndv = tuple([ndv] * source.shape[0])

    if all_valid_edges(source, ndv, padding=padding):
        # Skip mask_function and fill mask with valid data (255 or dtype max)
        h, w = rasterio.window_shape(read_window)
        nd = numpy.iinfo(source.dtype).max
        mask = (numpy.ones((h, w)) * nd).astype('uint8')
    else:
        # Run the masking function
        mask = mask_function(source, ndv, **extra_args)

    if padding:
        mask = mask[:, padding:-padding, padding:-padding]
    mask3d = mask[numpy.newaxis, :]

    rgba = numpy.concatenate((source, mask3d), axis=0)
    return window, zlib.compress(rgba)


class NodataPoolMan:
    """Nodata processing pool manager

    This class encapsulates the execution of nodata algorithms on
    windows of a dataset.
    """

    def __init__(self, input_path, func, ndv, num_workers=None,
                 max_tasks=100):
        """Create a pool of workers to process window masks"""
        self.input_path = input_path
        self.func = func
        self.ndv = ndv

        # Peek in the source file for metadata. We could even get the
        # ndv value from here in some cases.
        with rasterio.open(input_path) as src:
            self.dtype = src.dtypes[0]
            self.count = src.count

        jobs = num_workers or cpu_count()-1
        if jobs > 1:
            self.pool = Pool(jobs, init_worker,
                             (input_path, func),
                             max_tasks)
        else:
            self.pool = None

        init_worker(input_path, func)

    def _proc_data(self, out_window, data):
        h, w = rasterio.window_shape(out_window)
        b = self.count + 1
        arr = numpy.fromstring(zlib.decompress(data), self.dtype)
        return out_window, arr.reshape((b, h, w))

    def mask(self, windows, **kwargs):
        """Iterate over windows and compute mask arrays.

        The keyword arguments will be passed as keyword arguments to the
        manager's mask algorithm function.

        Yields window, ndarray pairs.
        """
        iterargs = izip(windows, repeat(self.ndv), repeat(kwargs))

        if self.pool:
            for out_window, data in self.pool.imap_unordered(
                    compute_window_rgba, iterargs):
                yield self._proc_data(out_window, data)
        else:
            for args in iterargs:
                out_window, data = compute_window_rgba(args)
                yield self._proc_data(out_window, data)
