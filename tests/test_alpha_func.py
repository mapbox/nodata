import os, re

import pytest
import rasterio as rio
import numpy as np


def image_reader(path):
    with rio.open(path) as src:
        return src.read()

def simple_threshold(data, ndv, pad):
    '''TEST A SIMPLE THRESHOLDING APPROACH'''
    depth, rows, cols = data.shape
    alpha = (np.invert(np.all(np.dstack(data) == ndv, axis=2)).astype(np.uint8) * 255).reshape(1, rows, cols)

    return np.concatenate([data, alpha])[:, pad: -pad, pad: -pad]

@pytest.fixture
def imagesToTest():
    testdir = 'tests/fixtures/alpha_unit'
    return [os.path.join(testdir, i) for i in os.listdir(testdir) if re.compile('.*.tif').match(i.lower())]

@pytest.fixture
def expectedOutput():
    testdir = 'tests/expected/alpha_simple'
    return [os.path.join(testdir, i) for i in os.listdir(testdir) if re.compile('.*.tif').match(i.lower())]

@pytest.fixture
def functionArgs():
    return [
        (0, 0, 0),
        (0, 0, 0),
        (255, 255, 255),
        (0, 0, 0),
        (255, 255, 255)
        ]

def test_runner(imagesToTest, expectedOutput, functionArgs):
    assert len(imagesToTest) == len(expectedOutput), "Test fixture length %s must equal expected length %s" % (len(imagesToTest), len(expectedOutput))
    assert len(imagesToTest) == len(functionArgs), "Test fixture length %s must equal argument length %s" % (len(imagesToTest), len(expectedOutput))

    pad = 64

    for path, expected, args in zip(imagesToTest, expectedOutput, functionArgs):
        img = image_reader(path)

        expectedImg = image_reader(expected)

        outputImg = simple_threshold(img, args, pad)

        assert outputImg.shape == expectedImg.shape

        assert np.array_equal(outputImg, expectedImg)

