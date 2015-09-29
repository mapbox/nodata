import numpy as np

def mask(data, ndv, pad):
    '''SIMPLE THRESHOLDING APPROACH'''
    depth, rows, cols = data.shape

    alpha = (np.invert(np.all(np.dstack(data) == ndv, axis=2)).astype(np.uint8) * 255).reshape(1, rows, cols)

    return np.concatenate([data, alpha])[:, pad: -pad, pad: -pad]

if __name__ == '__main__':
    mask()