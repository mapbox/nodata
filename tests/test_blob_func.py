import numpy as np
import nodata.blob as blob
import pytest

def test_window_padding():
    window = (
        (0, 256),
        (0, 256)
        )
    assert blob.pad_window(window, 128) == ((-128, 384), (-128, 384))
@pytest.fixture
def areaToFill():
    timg = np.zeros((4, 256, 256), dtype=np.uint8())
    rRow, rCol = np.random.randint(2, 254, 2)
    rRowInds = [0, 256]
    rColInds = [0, 256]
    rInd, cInd = np.random.randint(0, 2, 2)
    rRowInds[rInd] = rRow
    rColInds[cInd] = rCol
    for i in range(3):
        timg[i, rRowInds[0]: rRowInds[1], rColInds[0]: rColInds[1]] = 100
    timg[-1, rRowInds[0]: rRowInds[1], rColInds[0]: rColInds[1]] = 255
    return timg

def test_fill_nodata(areaToFill):
    mask = areaToFill[-1].copy()
    notFilledSum = np.sum(np.all(np.dstack(areaToFill) == (0, 0, 0, 0), axis=2))
    filled = blob.fill_nodata(areaToFill, mask, (1, 2, 3, 4), 100)
    filledSum = np.sum(np.all(np.dstack(filled) == (0, 0, 0, 0), axis=2))
    assert notFilledSum > filledSum

def test_handle_rgb():
    img = np.zeros((3, 100,100))
    mask = np.zeros((100, 100))
    assert blob.handle_RGB(img, mask).shape == (4, 100, 100)

def test_rgb_handling_alphafy():
    outNodata, selectNodata, outCount = blob.test_rgb(3, 0.0, True, 4)
    assert outNodata == None
    assert selectNodata == 0.0
    assert outCount == 4

def test_rgb_handling_no_alphafy():
    outNodata, selectNodata, outCount = blob.test_rgb(3, 0.0, False, 4)
    assert outNodata == 0.0
    assert selectNodata == 0.0
    assert outCount == 3

def test_rgba_handling():
    outNodata, selectNodata, outCount = blob.test_rgb(4, None, True, 4)
    assert outNodata == None
    assert selectNodata == None
    assert outCount == 4

def test_rgb_handling_fail():
    with pytest.raises(ValueError):
        blob.test_rgb(3, None, True, 4)

@pytest.fixture
def has_nodata():
    return np.zeros((8, 8), dtype=np.uint8)

@pytest.fixture
def has_somedata():
    tmpnone = np.zeros((8, 8), dtype=np.uint8) + 255
    tmpnone[4, 4] = 0
    return tmpnone

@pytest.fixture
def has_alldata():
    return np.zeros((8, 8), dtype=np.uint8) + 255

def _add_padding(arr, pad, pad_type):
    w, h = arr.shape

    # all_nodata
    outarr = np.zeros(((w + pad * 2), (h + pad * 2)), dtype=np.uint8)

    if pad_type == 'alldata':
        outarr = outarr + 255
    elif pad_type == 'somedata':
        outarr[0, 0] = 255

    outarr[pad:-pad, pad:-pad] = arr

    return outarr


def test_dofill_nodata_nodata(has_nodata):
    arr = _add_padding(has_nodata, 2, pad_type="nodata")
    assert blob.runNodataFiller(arr, 2) is False

def test_dofill_nodata_somedata(has_nodata):
    arr = _add_padding(has_nodata, 2, pad_type="somedata")
    assert blob.runNodataFiller(arr, 2) is True

def test_dofill_nodata_alldata(has_nodata):
    arr = _add_padding(has_nodata, 2, pad_type="alldata")
    assert blob.runNodataFiller(arr, 2) is True

def test_dofill_somedata_nodata(has_somedata):
    arr = _add_padding(has_somedata, 2, pad_type="nodata")
    assert blob.runNodataFiller(arr, 2) is True

def test_dofill_somedata_somedata(has_somedata):
    arr = _add_padding(has_somedata, 2, pad_type="somedata")
    assert blob.runNodataFiller(arr, 2) is True

def test_dofill_somedata_alldata(has_somedata):
    arr = _add_padding(has_somedata, 2, pad_type="alldata")
    assert blob.runNodataFiller(arr, 2) is True

def test_dofill_alldata_nodata(has_alldata):
    arr = _add_padding(has_alldata, 2, pad_type="nodata")
    assert blob.runNodataFiller(arr, 2) is False

def test_dofill_alldata_somedata(has_alldata):
    arr = _add_padding(has_alldata, 2, pad_type="somedata")
    assert blob.runNodataFiller(arr, 2) is False

def test_dofill_alldata_alldata(has_alldata):
    arr = _add_padding(has_alldata, 2, pad_type="alldata")
    assert blob.runNodataFiller(arr, 2) is False
