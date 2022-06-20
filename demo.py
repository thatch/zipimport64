from zipimport64 import zipimporter
import sys

def main(filename):
    z = zipimporter(filename)
    for (filename, compress, data_size, file_size, file_offset, time, date, crc) in z._files.values():
        print(f"{filename=} {compress=} {data_size=} {file_size=} {file_offset=} {time=} {date=} {crc=}")

if __name__ == "__main__":
    main(sys.argv[1])
