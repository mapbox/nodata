import rasterio as rio
from rasterio import Affine
import numpy as np
import click


def makehappytiff(dst_path, seams_path):
    kwargs = {'count': 4, 'crs': {'init': u'epsg:3857'}, 'dtype': 'uint8', 'affine': Affine(4.595839562240513, 0.0, -13550756.3744,
       0.0, -4.595839562240513, 6315533.02503), 'driver': u'GTiff', 'transform': Affine(4.595839562240513, 0.0, -13550756.3744,
       0.0, -4.595839562240513, 6315533.02503), 'height': 1065, 'width': 1065, 'nodata': None, 'compress': 'lzw', 'blockxsize': 256, 'tiled': True, 'blockysize': 256}
    imsize = 1065
    testdata = [(np.random.rand(imsize,imsize)*255).astype(np.uint8) for i in range(4)]
    
    for i in range(4):
        testdata[i][0:100,:] = 0
        testdata[i][:,900:] = 0

    with rio.drivers():
        with rio.open(dst_path, 'w', **kwargs) as dst:
            for i, arr in enumerate(testdata, 1):
                dst.write(arr, i)

    if seams_path:
        frto = np.sort(np.random.rand(2) * imsize).astype(int)

        rInds = np.arange(frto[0], frto[1], (frto[1] - frto[0]) / float(imsize)).astype(int)
        inds = np.arange(imsize)

        for i in range(4):
            testdata[i][rInds, inds] = 0
            testdata[i][rInds-1, inds] = 0
            testdata[i][rInds+1, inds] = 0
            testdata[i][inds, rInds] = 0
            testdata[i][inds, rInds-1] = 0
            testdata[i][inds, rInds+1] = 0
        with rio.drivers():
            with rio.open(seams_path, 'w', **kwargs) as dst:
                for i, arr in enumerate(testdata, 1):
                    dst.write(arr, i)


def getnulldiff(in1, in2, threshold):
    with rio.drivers():
        with rio.open(in1, 'r') as src:
            msk1 = src.read_masks()

        with rio.open(in2, 'r') as src:
            msk2 = src.read_masks()


    allmsk1 = ((msk1[0] == 0) & (msk1[1] == 0) & (msk1[1] == 0)).astype(int)
    allmsk2 = ((msk2[0] == 0) & (msk2[1] == 0) & (msk2[1] == 0)).astype(int)
    diff = np.count_nonzero(allmsk1) - np.count_nonzero(allmsk2)
    
    assert diff >= threshold, "input 1 has more than %d nodata pixels than input 2" % (threshold)

if __name__ == '__main__':
    makehappytiff()