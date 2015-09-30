import glob
import zlib

import numpy
import pytest
import rasterio

from nodata.scripts.alpha import (
    all_valid, init_worker, finalize_worker, compute_window_mask,
    NodataPoolMan)


def test_all_valid():
    assert (
        all_valid(numpy.empty((2, 2), dtype='uint8'), 0) == 255).all()


@pytest.fixture(
        scope='function', params=glob.glob('tests/fixtures/alpha/*.tif'))
def worker(request):
    """This provides the global `src` for compute_window_mask"""
    init_worker(request.param, all_valid)

    def fin():
        finalize_worker()

    request.addfinalizer(fin)


def test_compute_window_mask(worker):
    """Get an all-valid mask for one window"""
    in_window = ((0, 100), (0, 100))
    out_window, data = compute_window_mask((in_window, 0, {}))
    assert in_window == out_window
    assert (numpy.fromstring(
        zlib.decompress(data), 'uint8').reshape(
            rasterio.window_shape(out_window)) == 255).all()


@pytest.mark.parametrize("input_path", glob.glob('tests/fixtures/alpha/*.tif'))
def test_pool_man(input_path):
    """NodataPoolMan initializes and computes mask of a file"""
    manager = NodataPoolMan(input_path, all_valid, 0)
    assert manager.input_path == input_path
    assert manager.nodata == 0
    result = manager.mask(windows=[((0, 100), (0, 100))])
    window, arr = next(result)
    assert window == ((0, 100), (0, 100))
    assert (arr == 255).all()
    with pytest.raises(StopIteration):
        next(result)
