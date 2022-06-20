import unittest

from test_zipimport64 import (
    EXPECTED_SMALL,
    EXPECTED_ZEROES,
    load_entries,
    load_zipimporter,
)


class DecompressionTest(unittest.TestCase):
    def test_store(self):
        e, zf = load_zipimporter("testdata/small_store.zip")
        self.assertEqual("testdata/small_store.zip/small.py", e[0].filename)
        self.assertEqual(0, e[0].compress)
        self.assertEqual(6, e[0].file_size)
        self.assertEqual(6, e[0].data_size)
        self.assertEqual(
            EXPECTED_SMALL, zf.get_data("testdata/small_store.zip/small.py")
        )

        self.assertEqual("testdata/small_store.zip/zeroes.bin", e[1].filename)
        self.assertEqual(0, e[1].compress)
        self.assertEqual(10000, e[1].file_size)
        self.assertEqual(10000, e[1].data_size)
        self.assertEqual(
            EXPECTED_ZEROES, zf.get_data("testdata/small_store.zip/zeroes.bin")
        )

    def test_deflate(self):
        e, zf = load_zipimporter("testdata/small_deflate.zip")
        self.assertEqual("testdata/small_deflate.zip/small.py", e[0].filename)
        self.assertEqual(8, e[0].compress)
        self.assertEqual(6, e[0].file_size)
        self.assertEqual(8, e[0].data_size)
        self.assertEqual(
            EXPECTED_SMALL, zf.get_data("testdata/small_deflate.zip/small.py")
        )

        self.assertEqual("testdata/small_deflate.zip/zeroes.bin", e[1].filename)
        self.assertEqual(8, e[1].compress)
        self.assertEqual(10000, e[1].file_size)
        self.assertEqual(27, e[1].data_size)
        self.assertEqual(
            EXPECTED_ZEROES, zf.get_data("testdata/small_deflate.zip/zeroes.bin")
        )

    def test_bzip2(self):
        e, zf = load_zipimporter("testdata/small_bzip2.zip")
        self.assertEqual("testdata/small_bzip2.zip/small.py", e[0].filename)
        self.assertEqual(12, e[0].compress)
        self.assertEqual(6, e[0].file_size)
        self.assertEqual(46, e[0].data_size)
        self.assertEqual(
            EXPECTED_SMALL, zf.get_data("testdata/small_bzip2.zip/small.py")
        )

        self.assertEqual("testdata/small_bzip2.zip/zeroes.bin", e[1].filename)
        self.assertEqual(12, e[1].compress)
        self.assertEqual(10000, e[1].file_size)
        self.assertEqual(46, e[1].data_size)
        self.assertEqual(
            EXPECTED_ZEROES, zf.get_data("testdata/small_bzip2.zip/zeroes.bin")
        )

    def test_lzma(self):
        e, zf = load_zipimporter("testdata/small_lzma.zip")
        self.assertEqual("testdata/small_lzma.zip/small.py", e[0].filename)
        self.assertEqual(14, e[0].compress)
        self.assertEqual(6, e[0].file_size)
        self.assertEqual(25, e[0].data_size)
        self.assertEqual(
            EXPECTED_SMALL, zf.get_data("testdata/small_lzma.zip/small.py")
        )

        self.assertEqual("testdata/small_lzma.zip/zeroes.bin", e[1].filename)
        self.assertEqual(14, e[1].compress)
        self.assertEqual(10000, e[1].file_size)
        self.assertEqual(59, e[1].data_size)
        self.assertEqual(
            EXPECTED_ZEROES, zf.get_data("testdata/small_lzma.zip/zeroes.bin")
        )

    def test_zstd(self):
        e, zf = load_zipimporter("testdata/small_zstd.zip")
        self.assertEqual("testdata/small_zstd.zip/small.py", e[0].filename)
        self.assertEqual(93, e[0].compress)
        self.assertEqual(6, e[0].file_size)
        self.assertEqual(15, e[0].data_size)
        self.assertEqual(
            EXPECTED_SMALL, zf.get_data("testdata/small_zstd.zip/small.py")
        )

        self.assertEqual("testdata/small_zstd.zip/zeroes.bin", e[1].filename)
        self.assertEqual(93, e[1].compress)
        self.assertEqual(10000, e[1].file_size)
        self.assertEqual(17, e[1].data_size)
        self.assertEqual(
            EXPECTED_ZEROES, zf.get_data("testdata/small_zstd.zip/zeroes.bin")
        )


if __name__ == "__main__":
    unittest.main()
