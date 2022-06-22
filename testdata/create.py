# This allow recreating the files in this directory.  You shouldn't need to run it.

import os
import shutil
import zipfile

from zip64_promotion import (
    modify_to_include_all_three_zip64_extra_on_last_entry,
    modify_to_include_zip64_eocd,
)

SMALL = b"x = 1\n"
OUTER = b"outer = 1\n"
ZEROES = b"\x00" * 10_000


class ReproducibleZipFile(zipfile.ZipFile):
    def writestr(self, zinfo_or_arcname, data, compress_type=None, compresslevel=None):
        if isinstance(zinfo_or_arcname, str):
            zinfo_or_arcname = zipfile.ZipInfo(
                zinfo_or_arcname, date_time=(1980, 1, 1, 0, 0, 0)
            )
            zinfo_or_arcname.compress_type = self.compression
            zinfo_or_arcname._compresslevel = self.compresslevel
            # we don't need directories in these tests
            zinfo_or_arcname.external_attr = 0o600 << 16
        return super().writestr(zinfo_or_arcname, data, compress_type, compresslevel)


if __name__ == "__main__":
    os.chdir("testdata")

    for base, compression in [
        ("store", {}),
        ("deflate", {"compression": zipfile.ZIP_DEFLATED}),
    ]:
        # standard

        with ReproducibleZipFile(f"small_{base}.zip", "w", **compression) as zf:
            zf.writestr("small.py", SMALL)
            zf.writestr("zeroes.bin", ZEROES)

        shutil.copy(f"small_{base}.zip", f"small_{base}_comment.zip")
        with ReproducibleZipFile(f"small_{base}_comment.zip", "a") as zf:
            zf.comment = b" " * 65535

        with open(f"small_{base}_corrupt.zip", "wb") as f:
            # Replacing each central directory entry header with nonsense
            with open(f"small_{base}.zip", "rb") as f2:
                f.write(f2.read().replace(b"\x50\x4b\x01\x02", b"ZZZZ"))

        with open(f"par_{base}.zip", "wb") as f:
            f.write(b"# Some prepended data\n")

            # zip -A fails unless there's a lot more data
            f.write(b"\x00" * 100)

            with open(f"small_{base}.zip", "rb") as f2:
                f.write(f2.read())

        shutil.copy(f"par_{base}.zip", f"par_{base}_fixup.zip")
        os.system(f"zip -A par_{base}_fixup.zip")

        # zip64

        with ReproducibleZipFile(f"small_{base}_64.zip", "w", **compression) as zf:
            zf.writestr("small.py", SMALL)
            zf.writestr("zeroes.bin", ZEROES)

            # XXX I wish there was an easier way to force zip64
            for i in range(65536):
                zf.writestr(f"{i}.bin", str(i))

        with open(f"par_{base}_64.zip", "wb") as f:
            f.write(b"# Some prepended data\n")

            # zip -A fails unless there's a lot more data
            f.write(b"\x00" * 100)

            with open(f"small_{base}_64.zip", "rb") as f2:
                f.write(f2.read())

        if base == "deflate":
            # extra data making the locator useful
            with open(f"small_{base}_64.zip", "rb") as f:
                data = f.read()

            assert data[-42:-38] == b"PK\x06\x07"
            insert_length = 20000  # must be > 16k
            relative = int.from_bytes(data[-34:-26], "little") + insert_length
            data = (
                data[:-42]
                + b"\x05" * insert_length
                + data[-42:-34]
                + relative.to_bytes(8, "little")
                + data[-26:]
            )

            with open(f"small_{base}_64_junk.zip", "wb") as f:
                f.write(data)

            with ReproducibleZipFile(f"large_{base}_64.zip", "w", **compression) as zf:
                # this is larger than 2^31 which causes it to include zip64 extra for the
                # uncompressed file size; this is not enough to cause a zip64 EOCD however.
                zf.writestr("large.bin", "\x00" * 2_300_000_000)

            modify_to_include_all_three_zip64_extra_on_last_entry(
                f"small_{base}.zip", f"small_{base}_extra.zip"
            )

        elif base == "store":
            with ReproducibleZipFile(f"empty_{base}.zip", "w", **compression) as zf:
                pass

            modify_to_include_zip64_eocd(
                f"small_{base}.zip",
                f"small_{base}_fake64.zip",
            )

            with ReproducibleZipFile(f"turducken_{base}.zip", "w") as zf:
                # This contains a STORED zip64 at the end of a non-zip64
                zf.writestr("outer.py", OUTER)
                zf.write(f"small_{base}_fake64.zip", "inner.zip")

        # info-zip bug prevents this from working
        # shutil.copy(f"par_{base}_64.zip", f"par_{base}_64_fixup.zip")
        # os.system(f"zip -A par_{base}_64_fixup.zip")
