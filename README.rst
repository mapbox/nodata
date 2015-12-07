|Circle CI|

nodata
======

.. figure:: https://cloud.githubusercontent.com/assets/5084513/9670961/4f04da04-5244-11e5-93e5-86b69694f82f.jpg
   :alt: miles-davis7

   miles-davis7

Usage
-----

Nodata blobbing
~~~~~~~~~~~~~~~

::

            UNBLOBBED         BLOBBED

    ALPHA -------------    ~-----------~
          |           |    |           |
    RGB   -------------  ~~-------------~~
                         ^               ^
                         |_ _ _ _ _ _ _ _|
                          Lossy Artifacts
                               Hidden

::

    nodata blob [OPTIONS] SRC_PATH DST_PATH

    Options:
    -b, --bidx TEXT                   Bands to blob [default = all]
    -m, --max-search-distance INTEGER Maximum blobbing radius [default = 4]
    -n, --nibblemask                  Nibble blobbed nodata areas [default=False]
    --co NAME=VALUE                   Driver specific creation options.See the
                                      documentation for the selected output driver
                                      for more information.
    -d, --mask-threshold INTEGER      Alpha pixel threshold upon which to regard
                                      data as masked (ie, for lossy you'd want an
                                      aggressive threshold of 0) [default=None]
    -a, --alphafy                     If a RGB raster is found, blob + add alpha
                                      band where nodata is
    -j, --jobs                        Number of workers for multiprocessing [default=4]             
    --help                            Show this message and exit.

.. |Circle CI| image:: https://circleci.com/gh/mapbox/nodata.svg?style=svg&circle-token=c851126e89770fc401d0606d8b7aca556caeabc0
   :target: https://circleci.com/gh/mapbox/nodata
