import os
from click.testing import CliRunner
from nodata.scripts.cli import cli

datadir = os.path.join(os.path.dirname(__file__), 'fixtures', 'alpha')

def test_alpha_cli_basic():
    infile = os.path.join(datadir, 'lossy-curved-edges.tif')
    outfile = '/tmp/test_alpha_lossy-curved-edges.tif'

    runner = CliRunner()

    result = runner.invoke(cli, ['alpha', infile, outfile])
    assert result.exit_code != 0
    assert 'ndv' in result.output

    result = runner.invoke(cli, ['alpha', '--ndv', 255, infile, outfile])
    assert result.exit_code == 0

    os.remove(outfile)
