import os
import re
import pytest
import rasterio as rio
import numpy as np

import nodata.alphamask as alphamask


def image_reader(path):
    with rio.open(path) as src:
        return src.read()


def test_cases():
    testdir = 'tests/fixtures/alpha_unit'
    images = [os.path.join(testdir, i) for i in os.listdir(testdir)
              if re.compile('.*.tif').match(i.lower())]

    testdir = 'tests/expected/alpha_simple'
    expected = [os.path.join(testdir, i) for i in os.listdir(testdir)
                if re.compile('.*.tif').match(i.lower())]

    args = [
        (0, 0, 0),
        (0, 0, 0),
        (255, 255, 255),
        (0, 0, 0),
        (255, 255, 255)]

    assert len(args) == len(images) == len(expected)
    return zip(images, expected, args)


@pytest.mark.parametrize(
    'path, expected, args', test_cases())
def test_runner(path, expected, args):
    img = image_reader(path)
    depth, rows, cols = img.shape
    pad = 64
    outputImg = np.concatenate(
        [img, alphamask.simple_mask(img, args).reshape((1, rows, cols))])[:, pad: -pad, pad: -pad]

    expectedImg = image_reader(expected)

    assert outputImg.shape == expectedImg.shape
    assert np.array_equal(outputImg[3], expectedImg[3])  # alpha bands equal
    # assert np.array_equal(outputImg, expectedImg)


def test_alphamask_good_alphaonly():
    rRows, rCols = np.random.randint(3, 300, 2)
    fauxRGB = np.zeros((3, rRows, rCols), dtype=np.uint8) + 255

    # find a random row / col idx and only apply it to one random band
    rRowIdx = np.random.randint(0, rRows - 1, 1)[0]
    rColIdx = np.random.randint(0, rCols - 1, 1)[0]

    cBandIdx = np.random.randint(0, 3, 1)[0]
    fauxRGB[cBandIdx, rRowIdx, rColIdx] = 0

    outputA = alphamask.simple_mask(fauxRGB, (0, 0, 0))

    assert outputA.shape == (rRows, rCols)

    assert np.all(outputA[-1]), "No mask pixels should equal 0"

    # find a random row / col idx and apply it to all bands
    rRowIdx = np.random.randint(0, rRows - 1, 1)[0]
    rColIdx = np.random.randint(0, rCols - 1, 1)[0]

    fauxRGB[:, rRowIdx, rColIdx] = 0

    outputA = alphamask.simple_mask(fauxRGB, (0, 0, 0))

    assert outputA.shape == (rRows, rCols)

    createRowIdx, createColIdx = np.where(outputA == 0)

    assert len(createRowIdx) == 1
    assert rRowIdx == createRowIdx[0]

    assert len(createColIdx) == 1
    assert rColIdx == createColIdx[0]

def test_all_valid():
    all_valid = alphamask.all_valid
    ndv = (255, 255, 255)

    arr = np.random.randint(200, size=(3, 2, 2))
    assert all_valid(arr, ndv)

    arr[:, 1, 1] = 255
    assert not all_valid(arr, ndv)

    arr[:, 1, 1] = 254
    assert not all_valid(arr, ndv, threshold=1)


def test_all_valid_edges():
    all_valid_edges = alphamask.all_valid_edges
    ndv = (255, 255, 255)

    arr = np.random.randint(200, size=(3, 3, 3))
    assert all_valid_edges(arr, ndv)

    arr[:, 0, 0] = 255
    assert not all_valid_edges(arr, ndv)

    arr[:, 0, 0] = 0
    arr[:, 1, 1] = 254  # center nodata doesn't invalidate
    assert all_valid_edges(arr, ndv, threshold=1)


def test_slic_mask_not_any():
    """SLIC doesn't mistake far-from-nodata values as nodata in a noisy
    background."""
    slic_mask = alphamask.slic_mask
    arr = np.random.randint(200, size=(3, 100, 100))
    ndv = (255, 255, 255)

    mask = slic_mask(arr, ndv)
    assert mask.shape == (arr.shape[1], arr.shape[2])
    assert np.all(mask == 255)


@pytest.mark.xfail()
def test_slic_mask_any():
    """SLIC does identify nodata on the edge of a noisy background."""
    import random
    slic_mask = alphamask.slic_mask

    random.seed(1)
    arr = np.random.randint(200, size=(3, 100, 100))
    ndv = (255, 255, 255)

    # set right hand edge to the nodata value
    arr[:, :, -1] = 255

    # set the next column in from the right edge to values near the
    # nodata value to simulate nodata mixed in -- the lossy nodata
    # case.
    random.seed(1)
    arr[:, :, -2] = np.random.randint(252, 255, size=(100,))

    # ensure we have 255 values.
    arr[:, :, 0:5] = 255

    mask = slic_mask(arr, ndv)

    # assert that we do detect lossy nodata in the second to rightmost
    # column.
    assert np.any(mask[:, -2] == 0)
