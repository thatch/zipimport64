# zipimport64

The goal is a fairly upstreamable modification to zipimport.py to enable support
for zip64 and other modern compression types.

Zip64 files *should* be easily detected because the "version needed to extract" field is
updated from 1.0 to be 4.5, but this cannot be trusted (both info-zip and Python's
zipfile fail to write it consistently).

There are two changes with Zip64:

## zip64 EOCD

From https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT section 4.3.6

      [central directory header 1]
      .
      .
      .
      [central directory header n]
      [zip64 end of central directory record]
      [zip64 end of central directory locator] 
      [end of central directory record]

The final "end of central directory record" contains an absolute file offset where the
"central directory header 1" starts.  However, to support par files (and self-extracting
.exe) with unfixed offsets, we don't trust it.  Instead, both zipfile and zipimport use
another field which is the total size of all the central directory header records, and
treat that as a relative offset.

Because there are new records in between the central directory and the EOCD, this offset
is incorrect.  The same trick can be used on the zip64 EOCD (by virtue of being directly
after the central directory) size value, which is the simplest way of supporting most
such files.

Because this is probably feature, having existed for a long time, it would be a breaking
change to require that zips actually include correct offsets (trivially done with `zip
-A` although there's a bug in info-zip with fixing Zip64).  Other choices include

* Try both absolute and calculated relative positions for the central directory
* Start searching at the given absolute position (the real position will be later by the
  size of the prepended stub)

Any strategies involving searching (including ones we already do) are prone to issues on
files that are multiple concatenated zips, or zips containing stored binary data
(including in the comment field, or accidentally in integer fields).  The spec does not
call these out specifically, and I'm reluctant to make much of the size-checking more
strict to try multiple found possibilities because of the difficulty in tfound
possibilities because of the difficulty in testing such scenarios.  This implementation
is a bit of "hope for the best" combined with a set of files (produced by zipfile) that
are considered "compliant."

## zip64 EOCD Locator

In the name of simplicity, the new implementation also ignores the locator block, which
is mainly (in single-disk archives) for allowing arbitrary data between the Zip64 EOCD
and the start of the classic EOCD.  I am not aware of any examples of such data, and
this still kind of supports them (as long as the comment + extensible data is not
>16KB).

If you have example files for this, please point me at them (and the tool that created
them) and I'll add support.

## zip64 extensions in file headers

Each file in a zip has its own header (which occurs twice :/ ) and the fields in
old-style headers only allow 4GB (per the spec, but only 2GB per the zipfile
implementation) maximum size.  There are actually several fields treated specially
with an all 0xff value that means you read from the zip64 extension.

This is the sketchiest part of the implementation change, because of the
difficulty in checking in the example files, or even creating them on the fly.  A file
created with standard info-zip would need to be ~8GB in size, containing first a 4GB
file and then a >4GB file of good random data compressed using deflate (so the
starting offset, compressed size, and uncompressed size are all different and >4GB).

Instead what I have is a synthetic file created from a standard zip, and modifying bytes
per a careful reading of the spec, and checking that unzip still reads it correctly.
This gets us line coverage on the entire reader, but introduces another sketchy part of
the code in byte-editing the synthetic file that is prone to human error).
