import os, shutil

from click.testing import CliRunner
from nodata.scripts.cli import cli

import make_testing_data

class TestingSetup:
    def __init__(self, testdir):
        self.cleanup()
        self.path = testdir
        os.mkdir(self.path)

    def cleanup(self):
        try:
            shutil.rmtree(self.path)
        except:
            pass

def test_seam_filling_normal():
    tmpdir = '/tmp/seam_filling_normal'
    tester = TestingSetup(tmpdir)

    okfile = os.path.join(tmpdir, 'ok-random-data.tif')
    seamfile = os.path.join(tmpdir, 'ok-random-data-seams.tif')
    filled_file = os.path.join(tmpdir, 'filled-data.tif')
    make_testing_data.makehappytiff(okfile, seamfile)

    runner = CliRunner()

    result = runner.invoke(cli, ['seamfill', seamfile, filled_file, '-m', 4, '-n'])

    assert result.exit_code == 0

    tester.cleanup()

# echo '# testing seam filling process'
# '/fixtures/seamfill/composite_ca_chilliwack_small.tif' '/tmp/filled_ca_chilliwack_small.tif' '-m' 4 '-n'

# # $(dirname $0)/compare_geotiffs.py /tmp/filled_ca_chilliwack_small.tif $(dirname $0)/expected/seamfill/composite_ca_chilliwack_small.tif
# # tap "$?" == "0"
# tmpfiles="$tmpfiles /tmp/filled_ca_chilliwack_small.tif"

# echo '# testing seam filling process on ALPHA-type data'
# $cmd seamfill $(dirname $0)/fixtures/seamfill/composite_ca_chilliwack_alpha_small.tif /tmp/filled_ca_chilliwack_alpha_small.tif -m 4 -n
# msg="Filled matches expected"
# $(dirname $0)/compare_geotiffs.py /tmp/filled_ca_chilliwack_alpha_small.tif $(dirname $0)/expected/seamfill/composite_ca_chilliwack_alpha_small.tif
# tap "$?" == "0"
# tmpfiles="$tmpfiles /tmp/filled_ca_chilliwack_alpha_small.tif"

# echo '#testing seam filling on random data'
# python $(dirname $0)/maketestingdata.py makehappytiff /tmp/ok-random-data.tif -p /tmp/seamy-random-data.tif
# $cmd seamfill /tmp/seamy-random-data.tif /tmp/filled-random-data.tif -m 4 -n
# msg="Pixels were filled"
# python $(dirname $0)/maketestingdata.py getnulldiff /tmp/seamy-random-data.tif /tmp/filled-random-data.tif 100
# tap "$?" == "0"
# tmpfiles="$tmpfiles /tmp/ok-random-data.tif /tmp/seamy-random-data.tif /tmp/filled-random-data.tif"

# echo '#testing null filling on random data'
# python $(dirname $0)/maketestingdata.py makehappytiff /tmp/ok-random-data.tif
# $cmd nibblemask /tmp/ok-random-data.tif /tmp/nibble-random-data.tif -n 10
# msg="The mask was nibbled"
# python $(dirname $0)/maketestingdata.py getnulldiff /tmp/nibble-random-data.tif /tmp/ok-random-data.tif 100
# tap "$?" == "0"
# tmpfiles="$tmpfiles /tmp/nibble-random-data.tif"

# rm $tmpfiles