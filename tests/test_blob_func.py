import numpy as np
import nodata.scripts.blob as blob
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

def test_rgb_handling():
    outNodata, outCount = blob.test_rgb(3, 0.0, True, 4)
    assert outNodata == 0.0
    assert outCount == 4

def test_rgba_handling():
    outNodata, outCount = blob.test_rgb(4, None, True, 4)
    assert outNodata == None
    assert outCount == 4

def test_rgb_handling_fail():
    with pytest.raises(ValueError):
        blob.test_rgb(3, None, True, 4)


