# Hasil pemeriksaan lokal

Proyek tambahan 29 Oktober 2026. Lingkungan aktual: Python 3.12.14, Linux.

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` menghasilkan **21 tes lulus, 0 gagal, 0 dilewati**. Tes CLI menjalankan proses Python sesungguhnya, termasuk pembacaan berkas, penulisan, dan stdin/stdout.

Contoh `examples/daftar.txt` dengan opsi `--ignore-case --strip --drop-empty --stats` menghasilkan tiga baris `apel`, `jeruk`, dan `pisang`; statistik: 7 dibaca, 3 ditulis, 3 duplikat, 1 baris kosong dilewati.

Catatan ini melaporkan pemeriksaan lokal sebelum pengiriman paket. Identitas publikasi aktual disimpan oleh publisher dalam `.daily-app-publisher.json` pada repo hasil. Tidak ada pengujian Windows/macOS atau instalasi pip yang diklaim.
