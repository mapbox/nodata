How to publish to PyPi

1. Make your changes, and make sure to bump the package version here: https://github.com/mapbox/nodata/blob/master/setup.py
2. Make a new release of this version
3. Run: `python setup.py register sdist upload` and make sure that it returns a `200 ok`
4. Bump the version in your program's `requirments.txt`