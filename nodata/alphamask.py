import numpy as np
import skimage.measure as measure
import scipy.ndimage.measurements as sci_meas
from skimage.segmentation import slic
from scipy.ndimage.morphology import binary_fill_holes


def _diff_nodata(image, ndv):
    return np.sum([np.abs(im.astype(float) - n) for im, n in zip(image, ndv)], axis=0)


def _hacky_make_image(labeled_img, u_labels, measures, m_key, dtype=np.int16):
    out = np.zeros(labeled_img.shape, dtype=dtype).ravel()
    if m_key is None:
        measures = [{"key": m} for m in measures]
        m_key = "key"

    def value_grab(a, b):
        out[b] = measures[a[0] - 1][m_key]
        return None

    sci_meas.labeled_comprehension(labeled_img, labeled_img, u_labels, value_grab, float, 0, pass_positions=True)

    return out.reshape(labeled_img.shape)


def all_valid(data, ndv, threshold=0):
    """Test if all the data in the entire array are valid data
    within the specified threshold"""
    diff = _diff_nodata(data, ndv)
    return np.all(diff > (threshold * data.shape[0]))


def _edges(arr):
    left = arr[0, :]
    right = arr[-1, :]
    top = arr[:, 0]
    bottom = arr[:, -1]
    edges = np.concatenate([left, right, top, bottom])
    return edges


def all_valid_edges(data, ndv, threshold=0):
    """Test if all the data on the edges are valid data
    within the specified threshold"""
    diff = _diff_nodata(data, ndv)
    edges = _edges(diff)
    return np.all(edges > (threshold * data.shape[0]))


def simple_mask(data, ndv):
    '''Exact nodata masking'''
    depth, rows, cols = data.shape
    nd = np.iinfo(data.dtype).max
    alpha = np.invert(np.all(np.dstack(data) == ndv, axis=2)).astype(data.dtype) * nd
    return alpha


def slic_mask(arr, nodata, n_clusters=50, threshold=5, debug=False):
    """
    Uses @dnomadb algorithm, roughly:
        - cluster image using SLIC (k-means)
        - pull out contiguous regions and find aggregate stats
        - select regions that are likely ndv
        - fill inclusions
    """
    assert arr.shape[0] == len(nodata)
    near_nodata = _diff_nodata(arr, nodata)
    clusters = slic(near_nodata, n_clusters)
    labeled = measure.label(clusters) + 1
    measures = measure.regionprops(labeled, intensity_image=near_nodata, cache=True)
    mean_intensity = _hacky_make_image(labeled, np.unique(labeled), measures, 'mean_intensity')
    mask = binary_fill_holes(np.invert(binary_fill_holes(mean_intensity >= threshold)))
    nd = np.iinfo(arr.dtype).max
    mask = np.invert(mask) * nd
    if debug:
        d = dict([(m.label, m.mean_intensity) for m in measures])
        return mask.astype('uint8'), labeled.astype('uint32'), mean_intensity.astype('uint32'), d
    else:
        return mask.astype('uint8')
