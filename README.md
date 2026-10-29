# LineUnique

CLI Python untuk menghapus baris duplikat dari daftar teks UTF-8 sambil mempertahankan urutan kemunculan pertama. Cocok untuk merapikan daftar URL, nama berkas, hasil pencarian, atau daftar item yang disalin dari beberapa sumber.

Proyek tambahan **29 Oktober 2026**, dibuat sebagai uji publikasi otomatis melalui Daily App Publisher.

## Mulai cepat

Gunakan **Python 3.10+**. Ekstrak/clone proyek, masuk ke folder `lineunique-cli`, lalu jalankan:

```sh
python -m lineunique examples/daftar.txt --ignore-case --strip --drop-empty --stats
```

Tidak perlu menginstal dependensi. Keluaran stdout:

```text
apel
jeruk
pisang
```

Statistik ditulis terpisah ke stderr:

```json
{"read": 7, "written": 3, "duplicates": 3, "empty_skipped": 1}
```

## Fitur

- Menjaga urutan kemunculan pertama, tanpa mengurutkan ulang isi daftar.
- Perbandingan persis secara default, termasuk huruf besar/kecil dan spasi.
- Opsi Unicode casefold untuk perbandingan tanpa membedakan huruf besar/kecil.
- Opsi menghapus spasi di tepi dan melewati baris kosong.
- Input berkas UTF-8, termasuk UTF-8 dengan BOM, atau stdin.
- Output ke terminal atau berkas UTF-8, dengan line ending LF dan newline pada setiap baris hasil.
- Statistik JSON di stderr sehingga stdout tetap berisi data saja.
- Perlindungan berkas masukan dan penolakan menimpa hasil lama tanpa `--force`.

## Penggunaan

Simpan hasil ke berkas:

```sh
python -m lineunique daftar.txt -o hasil/unik.txt
```

Gabungkan opsi:

```sh
python -m lineunique daftar.txt --ignore-case --strip --drop-empty -o hasil/unik.txt --stats
```

Jika hasil lama ingin diganti:

```sh
python -m lineunique daftar.txt -o hasil/unik.txt --force
```

Input dan output tetap harus berbeda, termasuk ketika memakai `--force`. Penggantian dengan `--force` disiapkan pada berkas sementara dan dilakukan setelah pemrosesan berhasil. Kegagalan membaca input tidak menimpa hasil lama.

Stdin pada Bash/zsh:

```sh
printf 'apel\napel\njeruk\n' | python -m lineunique
```

Stdin pada PowerShell:

```powershell
@("apel", "apel", "jeruk") | python -m lineunique
```

Bantuan dan versi:

```sh
python -m lineunique --help
python -m lineunique --version
```

### Opsi

| Opsi | Perilaku |
| --- | --- |
| `input` | Lokasi berkas; `-` atau tidak diberikan berarti stdin. |
| `-o`, `--output` | Lokasi hasil; default stdout. Folder tujuan dibuat bila diperlukan. |
| `--ignore-case` | Bandingkan dengan Unicode casefold; teks pertama tetap dipertahankan. |
| `--strip` | Hapus whitespace tepi sebelum membandingkan dan menulis hasil. |
| `--drop-empty` | Lewati baris kosong atau hanya berisi whitespace. |
| `--stats` | Tulis statistik JSON ke stderr. |
| `--force` | Izinkan penggantian berkas output; memerlukan `--output`. |

Tanpa `--drop-empty`, satu baris kosong dipertahankan. Baris berisi spasi berbeda dari baris kosong kecuali memakai `--strip`. Dengan `--ignore-case`, kata seperti `Straße` dan `STRASSE` dianggap sama.

### Exit code

| Kode | Arti |
| ---: | --- |
| 0 | Pemrosesan berhasil, termasuk ketika ada duplikat yang dihapus. |
| 2 | Argumen, encoding, atau operasi berkas gagal. |
| 130 | Dibatalkan dengan Ctrl+C saat pemrosesan. |

Untuk stdout, keluaran yang sudah dikirim sebelum gangguan tidak dapat ditarik kembali. Berkas baru yang gagal diproses dibersihkan; penggantian hasil lama menunggu pemrosesan berhasil.

## Pengujian

```sh
python -m unittest discover -s tests -v
```

**21 tes lulus** pada Python 3.12.14/Linux. Tes mencakup Unicode, BOM/CRLF, statistik, stdin/stdout, CLI subprocess sungguhan, input invalid, hard link, dan perlindungan berkas. Pengujian Windows/macOS belum dijalankan.

Semua dependensi runtime berasal dari standard library. `pyproject.toml` juga menyediakan entry point opsional `lineunique` jika proyek diinstal dengan `python -m pip install .`; cara menjalankan dari folder proyek di atas tidak membutuhkan proses instalasi.

## Batas ruang lingkup

Program memproses baris satu per satu, dengan memori sebanding jumlah teks unik yang telah ditemukan. Ini bukan parser CSV atau pembanding objek JSON; duplikat ditentukan dari teks satu baris. Normalisasi Unicode NFC/NFKC tidak dilakukan. Input berkas memakai UTF-8; newline CRLF/CR diterima dan hasil selalu memakai LF.

## Publikasi

Source dan catatan tes dikirim sebagai paket antrean uji ke `Mavianza/daily-app-publisher`. GitHub Actions membuat repo hasil, melakukan commit, dan memeriksa SHA remote. Penanda `.daily-app-publisher.json` pada repo hasil mencatat hash paket dan commit pengirimnya.

Lisensi MIT, lihat `LICENSE`.
