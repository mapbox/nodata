import glob
import zlib

import numpy
import pytest
import rasterio

from nodata.scripts.alpha import (
    init_worker, finalize_worker, compute_window_rgba, NodataPoolMan)


def dummy_mask(arr, nodata, **kwargs):
    """Return an all-valid mask of the same shape and type as the
    given array"""
    return 255 * numpy.ones_like(arr[0])


def test_dummy_mask():
    assert (
        dummy_mask(numpy.empty((2, 2), dtype='uint8'), 0) == 255).all()


@pytest.fixture(
        scope='function', params=glob.glob('tests/fixtures/alpha/*.tif'))
def worker(request):
    """This provides the global `src` for compute_window_mask"""
    init_worker(request.param, dummy_mask)

    def fin():
        finalize_worker()

    request.addfinalizer(fin)


def test_compute_window_rgba(worker):
    """Get an all-valid rgba for one window"""
    in_window = ((0, 100), (0, 100))
    out_window, data = compute_window_rgba((in_window, 0, {}))
    h, w = rasterio.window_shape(out_window)
    assert in_window == out_window
    assert (numpy.fromstring(
        zlib.decompress(data), 'uint8').reshape((4, h, w))[-1] == 255).all()


@pytest.mark.parametrize(
        "input_path", glob.glob('tests/fixtures/alpha/*.tif'))
def test_pool_man_mask(input_path):
    """NodataPoolMan initializes and computes mask of a file"""
    manager = NodataPoolMan(input_path, dummy_mask, 0)
    assert manager.input_path == input_path
    assert manager.ndv == 0
    result = manager.mask(windows=[((0, 100), (0, 100))])
    window, arr = next(result)
    assert window == ((0, 100), (0, 100))
    assert (arr[-1] == 255).all()
    with pytest.raises(StopIteration):
        next(result)


@pytest.mark.parametrize("keywords", [
    {'padding': 0}])
def test_pool_man_mask_keywords(keywords):
    """NodataPoolMan initializes and computes mask of a file"""
    manager = NodataPoolMan(
        'tests/fixtures/alpha/lossy-curved-edges.tif', dummy_mask, 0)
    result = manager.mask(windows=[((0, 100), (0, 100))], **keywords)
    window, arr = next(result)
    assert window == ((0, 100), (0, 100))
    assert (arr[-1] == 255).all()
    with pytest.raises(StopIteration):
        next(result)
