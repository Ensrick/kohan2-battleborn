"""Reader/writer for Kohan II .rwd resource archives (TimeGate "TGCK" format).

Layout (little-endian, reverse-engineered from Data.rwd / Music.rwd / Warchest.rwd):

    0x00  char[4]  "TGCK"
    0x04  u32      format version (2)
    0x08  u32      section count (3)
    0x0c  Header section (0x12 bytes):
              u32  2
              u16  game-id length (2), wchar[] "K2"
              u32  0
              u32  stamp   <- the value the multiplayer handshake prints per depot
    0x1e  Files section: every file's bytes back to back, in load-index order, no padding
          Footer section (the directory):
              u32  file count
              per file: u16 name length (wchars), wchar[] name ('/' separated, relative
                        to the depot root), u64 offset (from the Files section start),
                        u64 size, u32 0, u32 load index
          Section table, 96 bytes per section, at the very end of the file:
              wchar[32] name ("Header" / "Files" / "Footer"), u64 offset, u64 size,
              u32 x2 (uninitialised stack data in TimeGate's packer - ignored), u64 size

    py -3 tools/rwd.py list  <archive>
    py -3 tools/rwd.py extract <archive> <out_dir> [name ...]
    py -3 tools/rwd.py pack <src_dir> <archive> [--stamp HEX]
    py -3 tools/rwd.py roundtrip <archive>    (re-encodes in memory, must be byte-identical)
"""

import hashlib
import os
import struct
import sys
import zlib

MAGIC = b"TGCK"
SECTION_REC = 96
CHUNK = 1 << 20


class Entry:
    __slots__ = ("name", "offset", "size", "unknown", "index")

    def __init__(self, name, offset, size, unknown=0, index=0):
        self.name, self.offset, self.size, self.unknown, self.index = name, offset, size, unknown, index


class Archive:
    """Parsed view of an .rwd file. Content is read lazily from the file."""

    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            head = f.read(0x1e)
            magic, self.version, nsec = struct.unpack_from("<4sII", head, 0)
            if magic != MAGIC:
                raise ValueError(f"{path}: not a TGCK archive")
            f.seek(0, 2)
            n = f.tell()
            f.seek(n - SECTION_REC * nsec)
            table = f.read(SECTION_REC * nsec)
            self.sections = []
            for i in range(nsec):
                rec = table[i * SECTION_REC:(i + 1) * SECTION_REC]
                name = rec[:64].decode("utf-16-le").split("\0", 1)[0]
                off, size, j1, j2, size2 = struct.unpack_from("<QQIIQ", rec, 64)
                self.sections.append([name, off, size, j1, j2, size2])
            sec = {s[0]: s for s in self.sections}
            f.seek(sec["Header"][1])
            self.header = f.read(sec["Header"][2])
            self.files_base = sec["Files"][1]
            f.seek(sec["Footer"][1])
            foot = f.read(sec["Footer"][2])
        count = struct.unpack_from("<I", foot, 0)[0]
        p = 4
        self.entries = []
        for _ in range(count):
            ln = struct.unpack_from("<H", foot, p)[0]
            p += 2
            name = foot[p:p + 2 * ln].decode("utf-16-le")
            p += 2 * ln
            off, size, unk, idx = struct.unpack_from("<QQII", foot, p)
            p += 24
            self.entries.append(Entry(name, off, size, unk, idx))
        self.size = n

    @property
    def stamp(self):
        return struct.unpack_from("<I", self.header, len(self.header) - 4)[0]

    def read(self, entry):
        with open(self.path, "rb") as f:
            f.seek(self.files_base + entry.offset)
            return f.read(entry.size)

    def iter_chunks(self, entry):
        with open(self.path, "rb") as f:
            f.seek(self.files_base + entry.offset)
            left = entry.size
            while left:
                block = f.read(min(CHUNK, left))
                if not block:
                    raise IOError(f"truncated content for {entry.name}")
                left -= len(block)
                yield block

    def find(self, name):
        key = name.replace("\\", "/").lower()
        for e in self.entries:
            if e.name.lower() == key:
                return e
        return None


def header_payload(stamp, game_id="K2"):
    gid = game_id.encode("utf-16-le")
    return struct.pack("<IH", 2, len(game_id)) + gid + struct.pack("<II", 0, stamp)


def write(out, files, stamp, dir_order=None, header=None, section_junk=(0, 0)):
    """Write an archive to the binary stream `out`.

    files: list of (name, size, chunk_iterable_factory) in load-index order.
    dir_order: optional list of load indices giving the directory order (default: load order).
    header: raw Header section bytes (default: built from stamp).
    """
    header = header if header is not None else header_payload(stamp)
    pos = 0
    out.write(struct.pack("<4sII", MAGIC, 2, 3))
    pos += 12
    hdr_off = pos
    out.write(header)
    pos += len(header)
    files_off = pos
    offsets = []
    rel = 0
    for name, size, chunks in files:
        offsets.append(rel)
        written = 0
        for block in chunks():
            out.write(block)
            written += len(block)
        if written != size:
            raise IOError(f"{name}: wrote {written} bytes, expected {size}")
        rel += size
    pos += rel
    files_size = rel
    order = dir_order if dir_order is not None else range(len(files))
    foot = bytearray(struct.pack("<I", len(files)))
    for i in order:
        name, size, _ = files[i]
        enc = name.encode("utf-16-le")
        foot += struct.pack("<H", len(name)) + enc + struct.pack("<QQII", offsets[i], size, 0, i)
    foot_off = pos
    out.write(foot)
    pos += len(foot)
    for name, off, size in (("Header", hdr_off, len(header)), ("Files", files_off, files_size),
                            ("Footer", foot_off, len(foot))):
        rec = name.encode("utf-16-le").ljust(64, b"\0")
        out.write(rec + struct.pack("<QQIIQ", off, size, section_junk[0], section_junk[1], size))


def default_stamp(files_digest):
    """Stamp for archives we build: CRC32 of the content digest, so every distinct build differs."""
    return zlib.crc32(files_digest) & 0xFFFFFFFF


def pack_dir(src, archive, stamp=None):
    names = []
    for dp, _, fs in os.walk(src):
        for fn in fs:
            full = os.path.join(dp, fn)
            names.append(os.path.relpath(full, src).replace(os.sep, "/"))
    names.sort(key=str.lower)
    files = []
    digest = hashlib.sha256()
    for nm in names:
        full = os.path.join(src, nm)
        data = open(full, "rb").read()
        digest.update(nm.lower().encode() + b"\0" + data)
        files.append((nm, len(data), (lambda d=data: [d])))
    if stamp is None:
        stamp = default_stamp(digest.digest())
    tmp = archive + ".tmp"
    with open(tmp, "wb") as out:
        write(out, files, stamp)
    os.replace(tmp, archive)
    return stamp, len(files)


class _HashSink:
    def __init__(self):
        self.h = hashlib.sha256()
        self.n = 0

    def write(self, b):
        self.h.update(b)
        self.n += len(b)


def roundtrip(path):
    """Re-encode an archive from its own parsed contents and compare SHA256 with the original."""
    a = Archive(path)
    by_index = sorted(a.entries, key=lambda e: e.index)
    if [e.index for e in by_index] != list(range(len(by_index))):
        raise ValueError("load indices are not a permutation")
    files = [(e.name, e.size, (lambda e=e: a.iter_chunks(e))) for e in by_index]
    dir_order = [e.index for e in a.entries]
    junk = (a.sections[0][3], a.sections[0][4])
    sink = _HashSink()
    write(sink, files, a.stamp, dir_order=dir_order, header=a.header, section_junk=junk)
    orig = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            orig.update(block)
    return sink.h.hexdigest() == orig.hexdigest(), sink.n, a.size, len(a.entries)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "list":
        a = Archive(argv[1])
        print(f"stamp {a.stamp:08x}  files {len(a.entries)}")
        for e in sorted(a.entries, key=lambda e: e.index):
            print(f"{e.size:>10}  {e.name}")
    elif cmd == "extract":
        a = Archive(argv[1])
        want = {n.replace("\\", "/").lower() for n in argv[3:]}
        for e in a.entries:
            if want and e.name.lower() not in want:
                continue
            dst = os.path.join(argv[2], *e.name.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                for block in a.iter_chunks(e):
                    f.write(block)
    elif cmd == "pack":
        stamp = None
        if "--stamp" in argv:
            stamp = int(argv[argv.index("--stamp") + 1], 16)
        s, n = pack_dir(argv[1], argv[2], stamp)
        print(f"packed {n} files into {argv[2]}, stamp {s:08x}")
    elif cmd == "roundtrip":
        ok, wrote, size, n = roundtrip(argv[1])
        print(f"{'IDENTICAL' if ok else 'DIFFERENT'}: {n} files, rebuilt {wrote} bytes vs original {size}")
        return 0 if ok else 1
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
