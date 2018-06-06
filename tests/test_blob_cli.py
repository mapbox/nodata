import os
import shutil

from click.testing import CliRunner
import rasterio as rio

import make_testing_data
import raster_tester
from nodata.scripts.cli import cli


class TestingSetup:
    def __init__(self, testdir):
        self.path = testdir
        self.cleanup()
        os.mkdir(self.path)

    def cleanup(self):
        try:
            shutil.rmtree(self.path)
        except FileNotFoundError as err:
            pass


def test_blob_filling_random():
    tmpdir = "/tmp/blob_filling"
    tester = TestingSetup(tmpdir)

    okfile = os.path.join(tmpdir, "ok-random-data.tif")
    blobfile = os.path.join(tmpdir, "ok-random-data-blobs.tif")
    filled_file = os.path.join(tmpdir, "filled-data.tif")
    make_testing_data.makehappytiff(okfile, blobfile)

    runner = CliRunner()

    result = runner.invoke(cli, ["blob", blobfile, filled_file, "-m", 4, "-n"])
    assert result.exit_code == 0

    assert make_testing_data.getnulldiff(blobfile, filled_file, 101) is None

    tester.cleanup()


def test_blob_filling_realdata():
    tmpdir = "/tmp/blob_filling"
    tester = TestingSetup(tmpdir)

    blobfile = os.path.join(os.getcwd(), "tests/fixtures/blob/seams_4band.tif")
    filled_file = os.path.join(tmpdir, "filliwack.tif")
    expectedfile = os.path.join(os.getcwd(), "tests/expected/blob/seams_4band.tif")

    runner = CliRunner()

    result = runner.invoke(
        cli, ["blob", blobfile, filled_file, "-m", 4, "-n", "--co", "compress=LZW"]
    )
    assert result.exit_code == 0

    raster_tester.compare(filled_file, expectedfile)
    tester.cleanup()


def test_blob_filling_realdata_specific_bands():
    tmpdir = "/tmp/blob_filling"
    tester = TestingSetup(tmpdir)

    blobfile = os.path.join(os.getcwd(), "tests/fixtures/blob/seams_4band.tif")
    filled_file = os.path.join(tmpdir, "filliwack-1-2-3.tif")
    expectedfile = os.path.join(
        os.getcwd(), "tests/expected/blob/bands-1-2-3-filled-only.tif"
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "blob",
            blobfile,
            filled_file,
            "-m",
            10,
            "--co",
            "compress=LZW",
            "--bidx",
            "[1, 2, 3]",
        ],
    )
    assert result.exit_code == 0

    raster_tester.compare(filled_file, expectedfile)
    tester.cleanup()


def test_blob_filling_realdata_rgb():

    tmpdir = "/tmp/blob_filling"
    tester = TestingSetup(tmpdir)

    blobfile = os.path.join(os.getcwd(), "tests/fixtures/blob/seams_4band.tif")
    rgb_file = os.path.join(tmpdir, "3band.tif")

    with rio.open(blobfile) as src:
        options = src.meta.copy()
        options.update(nodata=0.0, count=3, tiled=True, blockxsize=256, blockysize=256)
        with rio.open(rgb_file, "w", **options) as dst:
            for b in range(1, 4):
                dst.write(src.read(b), b)

    filled_file = os.path.join(tmpdir, "filliwack.tif")
    expectedfile = os.path.join(os.getcwd(), "tests/expected/blob/seams_4band.tif")

    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "blob",
            rgb_file,
            filled_file,
            "-m",
            4,
            "-n",
            "--co",
            "compress=LZW",
            "--alphafy",
        ],
    )
    assert result.exit_code == 0

    raster_tester.compare(filled_file, expectedfile)
    tester.cleanup()


def test_blob_filling_realdata_rgba_with_nodata():

    tmpdir = "/tmp/blob_filling"
    tester = TestingSetup(tmpdir)

    blobfile = os.path.join(os.getcwd(), "tests/fixtures/blob/seams_4band.tif")
    rgb_file = os.path.join(tmpdir, "3band.tif")

    with rio.open(blobfile) as src:
        options = src.meta.copy()
        options.update(nodata=0.0, tiled=True, blockxsize=256, blockysize=256)
        with rio.open(rgb_file, "w", **options) as dst:
            dst.write(src.read())

    filled_file = os.path.join(tmpdir, "filliwack.tif")
    expectedfile = os.path.join(os.getcwd(), "tests/expected/blob/seams_4band.tif")

    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "blob",
            rgb_file,
            filled_file,
            "-m",
            4,
            "-n",
            "--co",
            "compress=LZW",
            "--alphafy",
        ],
    )
    assert result.exit_code == 0

    raster_tester.compare(filled_file, expectedfile)
    tester.cleanup()


def test_blob_filling_realdata_threshold():
    tmpdir = "/tmp/blob_filling"
    tester = TestingSetup(tmpdir)

    blobfile = os.path.join(os.getcwd(), "tests/fixtures/blob/thresholder.tif")
    filled_file = os.path.join(tmpdir, "thresh_filled.tif")

    expectedfile = os.path.join(os.getcwd(), "tests/expected/blob/threshold.tif")

    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["blob", blobfile, filled_file, "-m", 4, "-n", "--co", "compress=LZW", "-d", 0],
    )
    assert result.exit_code == 0

    raster_tester.compare(filled_file, expectedfile)
    tester.cleanup()


def test_blob_filling_rgb():
    tmpdir = "/tmp/blob_filling"
    tester = TestingSetup(tmpdir)

    infile = os.path.join(os.getcwd(), "tests/fixtures/blob/rgb_toblob.tif")
    blobbed_file = os.path.join(tmpdir, "blobbedrgb.tif")
    expectedfile = os.path.join(os.getcwd(), "tests/expected/blob/rgb_toblob.tif")

    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["blob", infile, blobbed_file, "-m", 10, "--co", "compress=JPEG", "--alphafy"],
    )
    assert result.exit_code == 0

    raster_tester.compare(blobbed_file, expectedfile)
    tester.cleanup()


def test_blob_fail_no_nodata():
    """Should fail when there RGB + no nodata"""
    tmpdir = "/tmp/blob_filling"
    tester = TestingSetup(tmpdir)

    infile = os.path.join(os.getcwd(), "tests/fixtures/blob/rgb_toblob.tif")
    badfile = os.path.join(tmpdir, "badfile.tif")

    with rio.open(infile) as src:
        options = src.meta.copy()
        options.update(nodata=None)

        with rio.open(badfile, "w", **options) as dst:
            dst.write(src.read())

    blobbed_file = os.path.join(tmpdir, "blobbedrgb.tif")

    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "blob",
            badfile,
            blobbed_file,
            "-m",
            4,
            "-n",
            "--co",
            "compress=JPEG",
            "--alphafy",
        ],
    )
    assert result.exit_code == -1

    tester.cleanup()
