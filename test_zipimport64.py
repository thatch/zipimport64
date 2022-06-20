import os
import unittest
from dataclasses import dataclass

from zipimport64 import zipimporter, ZipImportError


@dataclass
class ZipInfo:
    filename: str
    compress: int
    data_size: int
    file_size: int
    file_offset: int
    time: int
    date: int
    crc: int


def load_entries(filename):
    files, _ = load_zipimporter(filename)
    return files


def load_zipimporter(filename):
    z = zipimporter(filename)
    files = [ZipInfo(*stuff) for stuff in z._files.values()]
    return files, z


TEST_OFFSET = 122  # amount of prepended data for par_*.zip
EXPECTED_SMALL = b"x = 1\n"
EXPECTED_ZEROES = b"\x00" * 10000


class Zipimport64Test(unittest.TestCase):

    # method=ZIP_STORED

    def test_small_directory_and_contents(self):
        e, zi = load_zipimporter("testdata/small_store.zip")
        self.assertEqual(2, len(e))
        self.assertEqual("testdata/small_store.zip/small.py", e[0].filename)
        self.assertEqual(6, e[0].file_size)
        self.assertEqual(0, e[0].file_offset)

        data = zi.get_data("testdata/small_store.zip/small.py")
        self.assertEqual(EXPECTED_SMALL, data)

    def test_small_directory_and_contents_comment(self):
        # This tests that the search-backwards-from-end can still find the EOCD even
        # with a maximum-length comment
        e, zi = load_zipimporter("testdata/small_store_comment.zip")
        self.assertEqual(2, len(e))
        self.assertEqual("testdata/small_store_comment.zip/small.py", e[0].filename)
        self.assertEqual(6, e[0].file_size)
        self.assertEqual(0, e[0].file_offset)

        data = zi.get_data("testdata/small_store_comment.zip/small.py")
        self.assertEqual(EXPECTED_SMALL, data)

    def test_small_directory_and_contents_64(self):
        e, zi = load_zipimporter("testdata/small_store_64.zip")
        self.assertEqual(65538, len(e))
        self.assertEqual("testdata/small_store_64.zip/small.py", e[0].filename)
        self.assertEqual(6, e[0].file_size)
        self.assertEqual(0, e[0].file_offset)

        data = zi.get_data("testdata/small_store_64.zip/small.py")
        self.assertEqual(EXPECTED_SMALL, data)

    def test_small_corrupt_exception(self):
        with self.assertRaisesRegex(
            ZipImportError,
            "^mismatched num_entries: 0 should be 2 in 'testdata/small_store_corrupt\.zip'$",
        ):
            load_entries("testdata/small_store_corrupt.zip")

    # method=ZIP_STORED with prefix

    def test_par_directory_and_contents(self):
        e, zi = load_zipimporter("testdata/par_store.zip")
        self.assertEqual(2, len(e))
        self.assertEqual("testdata/par_store.zip/small.py", e[0].filename)
        self.assertEqual(6, e[0].file_size)
        self.assertEqual(TEST_OFFSET, e[0].file_offset)

        data = zi.get_data("testdata/par_store.zip/small.py")
        self.assertEqual(EXPECTED_SMALL, data)

    def test_par_directory_and_contents_64(self):
        e, zi = load_zipimporter("testdata/par_store_64.zip")
        self.assertEqual(65538, len(e))
        self.assertEqual("testdata/par_store_64.zip/small.py", e[0].filename)
        self.assertEqual(6, e[0].file_size)
        self.assertEqual(TEST_OFFSET, e[0].file_offset)

        data = zi.get_data("testdata/par_store_64.zip/small.py")
        self.assertEqual(EXPECTED_SMALL, data)

    # It would appear that info-zip has a bug reading zip64 with `-A` and `-FF` that
    # cause it to miss some files; we ignore this case for now.
    # def test_par_directory_64_fixup(self):
    #     e = load_entries("testdata/par_store_64_fixup.zip")
    #     self.assertEqual(65538, len(e))
    #     self.assertEqual("testdata/par_store_64_fixup.zip/small.py", e[0].filename)
    #     self.assertEqual(6, e[0].file_size)
    #     self.assertEqual(TEST_OFFSET, e[0].file_offset)

    # method=ZIP_DEFLATED

    def test_small_deflate_extra(self):
        e = load_entries("testdata/small_deflate.zip")
        self.assertEqual(2, len(e))
        self.assertEqual("testdata/small_deflate.zip/zeroes.bin", e[1].filename)
        self.assertEqual(10000, e[1].file_size)
        self.assertEqual(27, e[1].data_size)
        self.assertEqual(46, e[1].file_offset)

        e = load_entries("testdata/small_deflate_extra.zip")
        self.assertEqual(2, len(e))
        self.assertEqual("testdata/small_deflate_extra.zip/zeroes.bin", e[1].filename)
        # These numbers are the same as above, but coverage should show the fields
        # decoded from 8 bytes.
        self.assertEqual(10000, e[1].file_size)
        self.assertEqual(27, e[1].data_size)
        self.assertEqual(46, e[1].file_offset)

    @unittest.skipIf("SLOW" not in os.environ, "Slow test")
    def test_large_directory_and_contents(self):
        e, zi = load_zipimporter("testdata/large_deflate_64.zip")
        self.assertEqual(1, len(e))
        self.assertEqual("testdata/large_deflate_64.zip/large.bin", e[0].filename)
        self.assertEqual(2_300_000_000, e[0].file_size)
        self.assertEqual(0, e[0].file_offset)

        data = zi.get_data("testdata/large_deflate_64.zip/large.bin")
        self.assertEqual(b"\x00\x00\x00\x00\x00\x00", data[:6])
        self.assertEqual(2_300_000_000, len(data))


if __name__ == "__main__":
    unittest.main()
