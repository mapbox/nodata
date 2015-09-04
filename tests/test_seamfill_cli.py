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

def test_seam_filling_random():
    tmpdir = '/tmp/seam_filling'
    tester = TestingSetup(tmpdir)

    okfile = os.path.join(tmpdir, 'ok-random-data.tif')
    seamfile = os.path.join(tmpdir, 'ok-random-data-seams.tif')
    filled_file = os.path.join(tmpdir, 'filled-data.tif')
    make_testing_data.makehappytiff(okfile, seamfile)

    runner = CliRunner()

    result = runner.invoke(cli, ['seamfill', seamfile, filled_file, '-m', 4, '-n'])
    assert result.exit_code == 0
    
    assert make_testing_data.getnulldiff(seamfile, filled_file, 101) == None

    tester.cleanup()

def test_seam_filling_realdata():
    tmpdir = '/tmp/seam_filling'
    tester = TestingSetup(tmpdir)

    seamfile = 'tests/fixtures/composite_ca_chilliwack_small.tif'
    filled_file = os.path.join(tmpdir, 'filliwack.tif')

    runner = CliRunner()

    result = runner.invoke(cli, ['seamfill', seamfile, filled_file, '-m', 4, '-n'])
    assert result.exit_code == 0
    
    assert make_testing_data.getnulldiff(seamfile, filled_file, 101) == None

    tester.cleanup()