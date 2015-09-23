import os, shutil

from click.testing import CliRunner
from nodata.scripts.cli import cli

import make_testing_data

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

    blobfile = 'tests/fixtures/composite_ca_chilliwack_small.tif'
    filled_file = os.path.join(tmpdir, 'filliwack.tif')

    runner = CliRunner()

    result = runner.invoke(cli, ['blob', blobfile, filled_file, '-m', 4, '-n'])
    assert result.exit_code == 0
    
    assert make_testing_data.getnulldiff(blobfile, filled_file, 101) == None

    tester.cleanup()

def test_blob_filling_rgb():
    tmpdir = '/tmp/blob_filling'
    tester = TestingSetup(tmpdir)

    blobfile = 'tests/fixtures/13-1326-2805-test-2015-2012_30cm_592_5450.tif'
    filled_file = os.path.join(tmpdir, 'filledrgb.tif')

    runner = CliRunner()

    result = runner.invoke(cli, ['blob', blobfile, filled_file, '-m', 4, '-n'])
    assert result.exit_code == 0
    
    assert make_testing_data.getnulldiff(blobfile, filled_file, 101) == None

    tester.cleanup()