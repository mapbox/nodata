import numpy as np

def mask(data, ndv, includeRGB=True):
    '''SIMPLE THRESHOLDING APPROACH'''
    depth, rows, cols = data.shape

    alpha = (np.invert(np.all(np.dstack(data) == ndv, axis=2)).astype(np.uint8) * 255).reshape(1, rows, cols)

    if includeRGB:
        return np.concatenate([data, alpha])
    else:
        return alpha

if __name__ == '__main__':
    mask()