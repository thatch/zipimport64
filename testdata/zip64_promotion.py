import struct
from dataclasses import astuple, dataclass

EOCD_FORMAT = "<IHHHHIIH"
EOCD_SIGNATURE = 0x06054B50


@dataclass
class Eocd:
    signature: int
    disknum: int
    disknum_with_cd: int
    num_entries_this_disk: int
    num_entries: int
    size: int
    position: int
    comment_size: int


EOCD64_FORMAT = "<IQHHIIQQQQ"
EOCD64_SIGNATURE = 0x06064B50


@dataclass
class Eocd64:
    signature: int
    eocd_size: int
    version_made_by: int
    version_needed: int
    disknum: int
    disknum_with_cd: int
    num_entries_this_disk: int
    num_entries: int
    size: int
    position: int


LOCATOR64_FORMAT = "<IIQI"
LOCATOR64_SIGNATURE = 0x07064B50


@dataclass
class Locator64:
    signature: int
    disknum_with_eocd: int
    eocd_position: int
    total_disks: int


def modify_to_include_zip64_eocd(
    input_filename, output_filename, extra_data_before_locator=b""
):
    with open(input_filename, "rb") as f:
        data = f.read()
    orig_data_len = len(data)

    eocd_len = struct.calcsize(EOCD_FORMAT)
    eocd64_len = struct.calcsize(EOCD64_FORMAT)
    locator64_len = struct.calcsize(LOCATOR64_FORMAT)
    current_eocd_start = orig_data_len - eocd_len

    eocd = Eocd(
        *struct.unpack(
            EOCD_FORMAT, data[current_eocd_start : current_eocd_start + eocd_len]
        )
    )
    eocd64 = Eocd64(
        signature=EOCD64_SIGNATURE,
        eocd_size=eocd64_len - 12,  # per spec
        version_made_by=0,
        version_needed=0,
        disknum=0,
        disknum_with_cd=0,
        num_entries_this_disk=eocd.num_entries_this_disk,
        num_entries=eocd.num_entries,
        size=eocd.size,
        position=eocd.position,
    )
    locator64 = Locator64(
        signature=LOCATOR64_SIGNATURE,
        disknum_with_eocd=0,
        eocd_position=current_eocd_start,
        total_disks=1,
    )

    data = (
        data[:current_eocd_start]
        + struct.pack(EOCD64_FORMAT, *astuple(eocd64))
        + struct.pack(LOCATOR64_FORMAT, *astuple(locator64))
        + extra_data_before_locator
        + data[current_eocd_start:]
    )

    with open(output_filename, "wb") as f:
        f.write(data)


def modify_to_include_all_three_zip64_extra_on_last_entry(
    input_filename, output_filename
):
    # Manually edit the last central directory entry to contain zip64 extra.  This is
    # validated by trying to extract it using the unzip utility.  The local file header
    # is not modified.

    with open(input_filename, "rb") as f:
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
                int.from_bytes(data[eocd_size_pos : eocd_size_pos + 4], "little")
                + (to_add - to_remove)
            ).to_bytes(4, "little"),
        )
    )
    for a, b, c in sorted(replacements)[::-1]:
        data = data[:a] + c + data[a + b :]
    with open(output_filename, "wb") as f:
        f.write(data)
