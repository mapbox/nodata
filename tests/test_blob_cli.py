import os, shutil

from click.testing import CliRunner
from nodata.scripts.cli import cli

import raster_tester

import make_testing_data
import rasterio as rio

class TestingSetup:
    def __init__(self, testdir):
        self.path = testdir
        self.cleanup()
        os.mkdir(self.path)

    def cleanup(self):
        try:
            shutil.rmtree(self.path)
        except:
            pass

def test_blob_filling_random():
    tmpdir = '/tmp/blob_filling'
    tester = TestingSetup(tmpdir)

    okfile = os.path.join(tmpdir, 'ok-random-data.tif')
    blobfile = os.path.join(tmpdir, 'ok-random-data-blobs.tif')
    filled_file = os.path.join(tmpdir, 'filled-data.tif')
    make_testing_data.makehappytiff(okfile, blobfile)

    runner = CliRunner()

    result = runner.invoke(cli, ['blob', blobfile, filled_file, '-m', 4, '-n'])
    assert result.exit_code == 0

    assert make_testing_data.getnulldiff(blobfile, filled_file, 101) == None

    tester.cleanup()

def test_blob_filling_realdata():
    tmpdir = '/tmp/blob_filling'
    tester = TestingSetup(tmpdir)

    blobfile = os.path.join(os.getcwd(), 'tests/fixtures/seams_4band.tif')
    filled_file = os.path.join(tmpdir, 'filliwack.tif')
    expectedfile = os.path.join(os.getcwd(), 'tests/expected/seams_4band.tif')

    runner = CliRunner()

    result = runner.invoke(cli, ['blob', blobfile, filled_file, '-m', 4, '-n', '-c', 'LZW'])
    assert result.exit_code == 0
    
    raster_tester.compare(filled_file, expectedfile)
    tester.cleanup()

def test_blob_filling_rgb():
    tmpdir = '/tmp/blob_filling'
    tester = TestingSetup(tmpdir)

    infile = os.path.join(os.getcwd(), 'tests/fixtures/rgb_toblob.tif')
    blobbed_file = os.path.join(tmpdir, 'blobbedrgb.tif')
    expectedfile = os.path.join(os.getcwd(), 'tests/expected/rgb_toblob.tif')

    runner = CliRunner()

    result = runner.invoke(cli, ['blob', infile, blobbed_file, '-m', 4, '-n', '-c', 'JPEG', '--alphafy'])
    assert result.exit_code == 0

    
    raster_tester.compare(blobbed_file, expectedfile)
    tester.cleanup()

def test_blob_fail_no_nodata():
    """Should fail when there RGB + no nodata"""
    tmpdir = '/tmp/blob_filling'
    tester = TestingSetup(tmpdir)

    infile = os.path.join(os.getcwd(), 'tests/fixtures/rgb_toblob.tif')
    badfile = os.path.join(tmpdir, 'badfile.tif')

    with rio.open(infile) as src:
        options = src.meta.copy()
        options.update(nodata=None, transform=src.affine)

        with rio.open(badfile, 'w', **options) as dst:
            dst.write(src.read())

    blobbed_file = os.path.join(tmpdir, 'blobbedrgb.tif')

    runner = CliRunner()

    result = runner.invoke(cli, ['blob', badfile, blobbed_file, '-m', 4, '-n', '-c', 'JPEG', '--alphafy'])
    assert result.exit_code == -1

    tester.cleanup()