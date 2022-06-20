# This allow recreating the files in this directory.  You shouldn't need to run it.

import os
import shutil
import zipfile

SMALL = b"x = 1\n"
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
            with ReproducibleZipFile(f"large_{base}_64.zip", "w", **compression) as zf:
                # this is larger than 2^31 which causes it to include zip64 extra for the
                # uncompressed file size; this is not enough to cause a zip64 EOCD however.
                zf.writestr("large.bin", "\x00" * 2_300_000_000)

            # Manually edit one of the files to contain zip64 extra.  This is validated
            # by trying to extract it using the unzip utility.

            with open(f"small_{base}.zip", "rb") as f:
                data = f.read()
            orig_data_len = len(data)
            # only update the last file in the central directory
            file_header_pos = data.rfind(b"PK\x01\x02")
            assert file_header_pos >= 0
            # tag and future length for all 3
            extra = [b"\x01\x00\x18\x00"]
            replacements = []
            # file_size, data_size, file_offset
            for p in (24, 20, 42):
                extra.append(
                    int.from_bytes(
                        data[file_header_pos + p : file_header_pos + p + 4], "little"
                    ).to_bytes(8, "little")
                )
                replacements.append((file_header_pos + p, 4, b"\xff\xff\xff\xff"))
            extra_bytes = b"".join(extra)
            # extra length
            replacements.append(
                (file_header_pos + 30, 2, len(extra_bytes).to_bytes(2, "little"))
            )
            # extra itself, right after name
            replacements.append(
                (
                    file_header_pos
                    + 46
                    + int.from_bytes(
                        data[file_header_pos + 28 : file_header_pos + 30], "little"
                    ),
                    0,
                    extra_bytes,
                )
            )
            eocd_size_pos = len(data) - 22 + 12

            to_remove = sum(i[1] for i in replacements)
            to_add = sum(len(i[2]) for i in replacements)
            assert to_remove != to_add
            replacements.append(
                (
                    eocd_size_pos,
                    4,
                    (
                        int.from_bytes(
                            data[eocd_size_pos : eocd_size_pos + 4], "little"
                        )
                        + (to_add - to_remove)
                    ).to_bytes(4, "little"),
                )
            )
            for a, b, c in sorted(replacements)[::-1]:
                data = data[:a] + c + data[a + b :]
            with open(f"small_{base}_extra.zip", "wb") as f:
                f.write(data)

        # info-zip bug prevents this from working
        # shutil.copy(f"par_{base}_64.zip", f"par_{base}_64_fixup.zip")
        # os.system(f"zip -A par_{base}_64_fixup.zip")
