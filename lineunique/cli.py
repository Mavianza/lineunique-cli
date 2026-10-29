"""CLI tanpa dependensi eksternal untuk merapikan daftar teks UTF-8."""

import argparse
from contextlib import contextmanager, nullcontext, suppress
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Iterable, Iterator

from . import __version__


@dataclass
class Stats:
    read: int = 0
    written: int = 0
    duplicates: int = 0
    empty_skipped: int = 0


def unique_lines(
    lines: Iterable[str], *, ignore_case: bool = False, strip: bool = False,
    drop_empty: bool = False, stats: Stats | None = None,
) -> Iterator[str]:
    """Hasil berupa baris dengan LF; teks pertama untuk setiap kunci dipertahankan."""
    stats = stats if stats is not None else Stats()
    seen: set[str] = set()
    for raw in lines:
        stats.read += 1
        text = raw.removesuffix("\n").removesuffix("\r")
        if strip:
            text = text.strip()
        if drop_empty and not text.strip():
            stats.empty_skipped += 1
            continue
        key = text.casefold() if ignore_case else text
        if key in seen:
            stats.duplicates += 1
            continue
        seen.add(key)
        stats.written += 1
        yield text + "\n"


@contextmanager
def output_file(path: Path, force: bool):
    path.parent.mkdir(parents=True, exist_ok=True)
    if force:
        fd, temporary = tempfile.mkstemp(prefix=".lineunique-", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                yield stream
            os.replace(temporary, path)
        finally:
            with suppress(FileNotFoundError):
                os.unlink(temporary)
        return
    created = False
    completed = False
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            created = True
            yield stream
        completed = True
    finally:
        if created and not completed:
            with suppress(OSError):
                path.unlink()


def main(argv=None, *, stdin=None, stdout=None, stderr=None) -> int:
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr
    parser = argparse.ArgumentParser(description="Hapus baris duplikat; pertahankan urutan kemunculan pertama.")
    parser.add_argument("input", nargs="?", default="-", help="Berkas UTF-8 atau - untuk stdin (default)")
    parser.add_argument("-o", "--output", default="-", help="Berkas hasil UTF-8 atau - untuk stdout")
    parser.add_argument("--ignore-case", action="store_true", help="Bandingkan huruf menggunakan Unicode casefold")
    parser.add_argument("--strip", action="store_true", help="Hapus spasi tepi sebelum perbandingan dan penulisan")
    parser.add_argument("--drop-empty", action="store_true", help="Lewati baris kosong atau hanya berisi spasi")
    parser.add_argument("--stats", action="store_true", help="Cetak statistik JSON ke stderr")
    parser.add_argument("--force", action="store_true", help="Izinkan penggantian berkas hasil yang sudah ada")
    parser.add_argument("--version", action="version", version=f"LineUnique {__version__}")
    args = parser.parse_args(argv)
    if args.force and args.output == "-":
        parser.error("--force memerlukan --output berupa berkas.")
    try:
        source = None if args.input == "-" else Path(args.input)
        destination = None if args.output == "-" else Path(args.output)
        if source is not None and destination is not None:
            same_path = source.resolve() == destination.resolve()
            same_file = source.exists() and destination.exists() and os.path.samefile(source, destination)
            if same_path or same_file:
                raise ValueError("Berkas hasil harus berbeda dari berkas masukan, termasuk saat memakai --force.")
        stats = Stats()
        reader = nullcontext(stdin) if source is None else source.open("r", encoding="utf-8-sig", newline=None)
        with reader as incoming:
            writer = nullcontext(stdout) if destination is None else output_file(destination, args.force)
            with writer as outgoing:
                for line in unique_lines(incoming, ignore_case=args.ignore_case, strip=args.strip,
                                         drop_empty=args.drop_empty, stats=stats):
                    outgoing.write(line)
                outgoing.flush()
        if args.stats:
            stderr.write(json.dumps(asdict(stats), ensure_ascii=False) + "\n")
        return 0
    except FileExistsError:
        stderr.write("Gagal: berkas hasil sudah ada. Pilih lokasi lain atau gunakan --force.\n")
    except UnicodeError:
        stderr.write("Gagal: masukan harus berupa teks UTF-8 dan keluaran harus mendukung karakter yang ditulis.\n")
    except (OSError, ValueError) as error:
        stderr.write(f"Gagal: {error}\n")
    except KeyboardInterrupt:
        stderr.write("Proses dibatalkan.\n")
        return 130
    return 2
