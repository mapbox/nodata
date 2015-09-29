import numpy
import pytest
import rasterio
import zlib

from nodata.scripts.alpha import (
    init_worker, finalize_worker, compute_window_mask)


@pytest.fixture(scope='function')
def worker(request):
    """This provides the global `src` for compute_window_mask"""
    init_worker('tests/fixtures/alpha/lossy-curved-edges.tif', {})

    def fin():
        finalize_worker()

    request.addfinalizer(fin)


def test_all_valid(worker):
    """Get an all-valid mask for one window"""

    def mask_func(arr, nodata):
        """Return an all-valid mask of the same shape and type as the input"""
        return 255 * numpy.ones_like(arr[0])

    in_window = ((0, 100), (0, 100))
    out_window, data = compute_window_mask(in_window, 0, mask_func)
    assert in_window == out_window
    assert (numpy.fromstring(
        zlib.decompress(data), 'uint8').reshape(
            rasterio.window_shape(out_window)) == 255).all()
