"""
KAUMITA - Pencarian Layanan Advokasi, Bantuan, dan Perlindungan Inklusif
Implementasi Breadth-First Search (BFS)

Kelompok 10 Kelas C IF 24
- Azzaral Aswad Asshiddiqy   (L0124090)
- Daffa Dewanda Putra         (L0124094)
- Muhammad Raditya Boy W.     (L0124109)

Arsitektur:
    data/layanan.csv  -->  LayananGraph (graf adjacency)  -->  BFS  -->  Hasil Rekomendasi
"""

import csv
import json
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# 1. DATA CLASS  –  merepresentasikan satu node
# ─────────────────────────────────────────────

@dataclass
class Layanan:
    """
    Satu node dalam graf KAUMITA.
    V = (id, nama, kategori, tags, kontak, kota, flags)
    """
    id: int
    nama: str
    kategori: str          # "pengaduan" | "kesehatan" | "konseling"
    tags: set              # himpunan fitur/layanan yang disediakan
    kontak: str
    wa: str
    email: str
    sosmed: str
    kota: str
    disabilitas_friendly: bool

    def __repr__(self) -> str:
        return f"Layanan(id={self.id}, nama='{self.nama}', kota='{self.kota}')"

    def memenuhi(self, kebutuhan: set) -> bool:
        """
        Cek apakah SEMUA kebutuhan pengguna ada di tags lembaga ini.
        U(req) ⊆ A(v)  →  True
        """
        return kebutuhan.issubset(self.tags)

    def memenuhi_hybrid(self, kebutuhan: set) -> bool:
        """
        Kombinasi Filter Wajib (Disabilitas) & Filter Opsional (Irisan Tag).
        """
        # 1. Filter Wajib Disabilitas
        if "disabilitas" in kebutuhan and not self.disabilitas_friendly:
            return False

        # 2. Filter Opsional (Soft Match / Irisan)
        tags_opsional = kebutuhan - {"disabilitas"}
        if tags_opsional:
            return bool(tags_opsional & self.tags)
        return True


# ─────────────────────────────────────────────
# 2. GRAF  –  struktur data adjacency list
# ─────────────────────────────────────────────

class LayananGraph:
    """
    G = (V, E)
      V  : dict[id → Layanan]
      E  : dict[id → list[id]]   (directed, berdasarkan rujukan antarlembaga)

    Aturan pembentukan edge otomatis:
      Dua lembaga dihubungkan jika memiliki setidaknya satu tag yang sama
      (rujukan antarlembaga yang tematik).
    """

    def __init__(self):
        self.vertices: dict[int, Layanan] = {}   # V
        self.edges: dict[int, list[int]] = {}    # E (adjacency list)

    # ── Memuat data ──────────────────────────

    @classmethod
    def dari_csv(cls, path_csv: str) -> "LayananGraph":
        """
        Pseudocode:
            BACA file CSV
            UNTUK setiap baris:
                buat objek Layanan  →  tambahkan ke V
            UNTUK setiap pasang (u, v) di V:
                JIKA tags[u] ∩ tags[v] ≠ ∅ → tambahkan edge u→v dan v→u
            KEMBALIKAN graf
        """
        g = cls()

        # Langkah 1 – baca node
        with open(path_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                tags_raw = row["tags"].strip()
                tags = set(t.strip() for t in tags_raw.split(",") if t.strip())

                layanan = Layanan(
                    id=int(row["id"]),
                    nama=row["nama"].strip(),
                    kategori=row["kategori"].strip(),
                    tags=tags,
                    kontak=row["kontak"].strip(),
                    wa=row["wa"].strip(),
                    email=row["email"].strip(),
                    sosmed=row["sosmed"].strip(),
                    kota=row["kota"].strip(),
                    disabilitas_friendly=row["disabilitas_friendly"].strip().lower() == "true",
                )
                g.vertices[layanan.id] = layanan
                g.edges[layanan.id] = []

        # Langkah 2 – bangun edge berdasarkan irisan tag
        ids = list(g.vertices.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                u, v = ids[i], ids[j]
                irisan = g.vertices[u].tags & g.vertices[v].tags
                if irisan:                         # ada kesamaan layanan
                    g.edges[u].append(v)
                    g.edges[v].append(u)

        return g

    # ── Statistik graf ───────────────────────

    def info(self) -> str:
        total_edge = sum(len(nbr) for nbr in self.edges.values()) // 2
        return (f"Graf KAUMITA  |  |V| = {len(self.vertices)} node  "
                f"|  |E| = {total_edge} edge")


# ─────────────────────────────────────────────
# 3. ALGORITMA BFS  –  pencarian utama
# ─────────────────────────────────────────────

class KaumitaBFS:
    """
    Implementasi Breadth-First Search untuk mencari lembaga yang
    memenuhi SEMUA kebutuhan pengguna U(req).

    Kompleksitas  :  O(V + E)
    Struktur data :  queue FIFO (collections.deque)
    """

    def __init__(self, graf: LayananGraph):
        self.graf = graf

    def cari(
        self,
        kebutuhan: set,
        kota: Optional[str] = None,
        node_awal_id: Optional[int] = None,
        hybrid: bool = True,
    ) -> list[Layanan]:
        """
        Pseudocode BFS KAUMITA
        ──────────────────────
        FUNGSI cari(kebutuhan U_req, kota, node_awal):

            hasil        ← []
            dikunjungi   ← {}
            antrian      ← FIFO queue

            // Tentukan node awal
            JIKA node_awal diberikan:
                antrian.enqueue(node_awal)
            LAIN:
                antrian.enqueue(semua node di V)   // BFS dari semua sumber

            SELAMA antrian tidak kosong:
                v ← antrian.dequeue()

                JIKA v sudah dikunjungi: LANJUT

                tandai v sebagai dikunjungi

                // Filter kota (opsional)
                JIKA kota diberikan DAN layanan[v].kota ≠ kota DAN
                     layanan[v].kota ≠ "Nasional":
                    LANJUT ke tetangga

                // Cek pemenuhan kebutuhan  U_req ⊆ A(v)
                JIKA layanan[v].memenuhi(U_req):
                    tambahkan layanan[v] ke hasil

                // Ekspansi ke tetangga (level berikutnya)
                UNTUK setiap tetangga w dari v:
                    JIKA w belum dikunjungi:
                        antrian.enqueue(w)

            KEMBALIKAN hasil

        Catatan: Algoritma tidak berhenti saat menemukan satu hasil
                 agar semua lembaga yang memenuhi syarat ditemukan.
        """

        hasil: list[Layanan] = []
        dikunjungi: set[int] = set()
        antrian: deque[int] = deque()

        # ── Inisialisasi antrian ─────────────
        if node_awal_id is not None and node_awal_id in self.graf.vertices:
            antrian.append(node_awal_id)
        else:
            # Tanpa node awal → masukkan semua node ke antrian (multi-source BFS)
            for nid in self.graf.vertices:
                antrian.append(nid)

        # ── Traversal BFS ────────────────────
        while antrian:
            v = antrian.popleft()          # dequeue

            if v in dikunjungi:
                continue

            dikunjungi.add(v)              # tandai dikunjungi
            layanan_v = self.graf.vertices[v]

            # Filter kota (opsional)
            kota_cocok = (
                kota is None
                or layanan_v.kota.strip().lower() == kota.strip().lower()
                or layanan_v.kota.strip().lower() == "nasional"
            )

            if hybrid:
                kebutuhan_cocok = layanan_v.memenuhi_hybrid(kebutuhan)
            else:
                kebutuhan_cocok = layanan_v.memenuhi(kebutuhan)

            if kota_cocok and kebutuhan_cocok:
                hasil.append(layanan_v)

            # Ekspansi ke tetangga
            for w in self.graf.edges[v]:
                if w not in dikunjungi:
                    antrian.append(w)      # enqueue

        if hybrid and kebutuhan:
            # Urutkan hasil berdasarkan:
            # 1. Jumlah kecocokan tag opsional terbanyak (relevansi)
            # 2. Lokasi terdekat (Kota cocok persis > "Nasional")
            tags_opsional = kebutuhan - {"disabilitas"}
            
            def sort_key(x):
                tag_score = len(tags_opsional & x.tags) if tags_opsional else 0
                kota_score = 1 if (kota and x.kota.strip().lower() == kota.strip().lower()) else 0
                return (tag_score, kota_score)
                
            hasil.sort(key=sort_key, reverse=True)

        # Batasi hasil maksimal 3 lembaga
        return hasil[:3]

    def bfs_tree(
        self,
        kebutuhan: set,
        kota: Optional[str] = None,
        node_awal_id: Optional[int] = None,
    ):
        """
        Menghasilkan BFS tree:
            parent[v] = node asal
            level[v]  = kedalaman BFS
        """

        dikunjungi: set[int] = set()
        parent: dict[int, Optional[int]] = {}
        level: dict[int, int] = {}

        antrian = deque()

        # Inisialisasi root
        if node_awal_id is not None and node_awal_id in self.graf.vertices:
            roots = [node_awal_id]
        else:
            roots = list(self.graf.vertices.keys())

        for root in roots:
            if root not in dikunjungi:
                antrian.append(root)
                parent[root] = None
                level[root] = 0

                while antrian:
                    v = antrian.popleft()

                    if v in dikunjungi:
                        continue

                    dikunjungi.add(v)

                    for w in self.graf.edges[v]:
                        if w not in dikunjungi and w not in parent:
                            parent[w] = v
                            level[w] = level[v] + 1
                            antrian.append(w)

        return parent, level
    
    @staticmethod
    def tampilkan_bfs_tree(
        parent: dict[int, Optional[int]],
        level: dict[int, int],
        graf: LayananGraph,
    ):
        """
        Visualisasi sederhana BFS tree di terminal.
        """

        print("\n" + "═" * 60)
        print("  VISUALISASI BFS TREE")
        print("═" * 60)

        # Kelompokkan node berdasarkan level
        level_map = {}

        for node_id, lvl in level.items():
            level_map.setdefault(lvl, []).append(node_id)

        for lvl in sorted(level_map.keys()):
            print(f"\nLevel {lvl}")

            for node_id in level_map[lvl]:
                layanan = graf.vertices[node_id]

                p = parent[node_id]

                if p is None:
                    print(f"  ROOT → [{node_id}] {layanan.nama}")
                else:
                    parent_nama = graf.vertices[p].nama
                    print(
                        f"  [{p}] {parent_nama}"
                        f"\n      └── [{node_id}] {layanan.nama}"
                    )
    # ── Format output ────────────────────────

    @staticmethod
    def format_hasil(
        hasil: list[Layanan],
        kebutuhan: set,
        kota: Optional[str] = None,
    ) -> str:
        """Menampilkan hasil BFS ke layar secara rapi."""
        garis = "─" * 60
        baris = []

        baris.append("\n" + "═" * 60)
        baris.append("  KAUMITA – Hasil Pencarian Layanan")
        baris.append("═" * 60)
        baris.append(f"  Kebutuhan  : {', '.join(sorted(kebutuhan))}")
        if kota:
            baris.append(f"  Kota/Wilayah: {kota}")
        baris.append(f"  Ditemukan  : {len(hasil)} lembaga")
        baris.append(garis)

        if not hasil:
            baris.append("  Tidak ditemukan lembaga yang sepenuhnya")
            baris.append("  memenuhi semua kebutuhan Anda.")
            baris.append("  → Coba kurangi kriteria atau pilih 'Nasional'.")
        else:
            for idx, lbg in enumerate(hasil, 1):
                baris.append(f"\n  [{idx}] {lbg.nama}")
                baris.append(f"      Kategori  : {lbg.kategori.capitalize()}")
                baris.append(f"      Kota      : {lbg.kota}")
                baris.append(f"      Layanan   : {', '.join(sorted(lbg.tags))}")

                kontak_list = []
                if lbg.kontak:
                    kontak_list.append(f"Telp: {lbg.kontak}")
                if lbg.wa:
                    kontak_list.append(f"WA: {lbg.wa}")
                if lbg.email:
                    kontak_list.append(f"Email: {lbg.email}")
                if lbg.sosmed:
                    kontak_list.append(f"IG: {lbg.sosmed}")
                if kontak_list:
                    baris.append(f"      Kontak    : {' | '.join(kontak_list)}")

                flags = []
                if lbg.disabilitas_friendly:
                    flags.append("♿ Disabilitas Friendly")
                if flags:
                    baris.append(f"      Fitur     : {' | '.join(flags)}")

                baris.append("      " + garis[6:])

        baris.append("═" * 60 + "\n")
        return "\n".join(baris)


# ─────────────────────────────────────────────
# 4. ANTARMUKA CLI  –  interaksi pengguna
# ─────────────────────────────────────────────

DAFTAR_TAG_VALID = {
    "kekerasan_seksual", "konseling", "pendampingan", "konsultasi_hukum",
    "hukum", "pengaduan", "perempuan", "anak", "disabilitas",
    "mahasiswa", "bantuan_umum", "medis", "kesehatan", "trauma", "pemulihan",
    "psikologi", "perlindungan_anak", "perlindungan_perempuan",
    "perlindungan_korban", "perlindungan_saksi", "pemberdayaan_perempuan",
    "hak_asasi_manusia", "eksploitasi_seksual", "rumah_sakit",
}

KOTA_VALID = {
    "nasional", "jakarta", "yogyakarta", "surakarta", "semarang",
    "jawa tengah", "bali",
}


def tampilkan_menu():
    print("\n" + "═" * 60)
    print("  ██╗  ██╗ █████╗ ██╗   ██╗███╗   ███╗██╗████████╗ █████╗ ")
    print("  ██║ ██╔╝██╔══██╗██║   ██║████╗ ████║██║╚══██╔══╝██╔══██╗")
    print("  █████╔╝ ███████║██║   ██║██╔████╔██║██║   ██║   ███████║")
    print("  ██╔═██╗ ██╔══██║██║   ██║██║╚██╔╝██║██║   ██║   ██╔══██║")
    print("  ██║  ██╗██║  ██║╚██████╔╝██║ ╚═╝ ██║██║   ██║   ██║  ██║")
    print("  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝   ╚═╝   ╚═╝  ╚═╝")
    print("═" * 60)
    print("  Pencarian Layanan Advokasi, Bantuan & Perlindungan Inklusif")
    print("  Berbasis Algoritma Breadth-First Search")
    print("═" * 60)


def tampilkan_tag_tersedia():
    print("\n  Tag layanan yang tersedia:")
    tags_sorted = sorted(DAFTAR_TAG_VALID)
    for i in range(0, len(tags_sorted), 3):
        baris = tags_sorted[i:i+3]
        print("    " + "   ".join(f"{t:<28}" for t in baris))


def input_kebutuhan() -> set:
    tampilkan_tag_tersedia()
    print("\n  Masukkan kebutuhan Anda (pisahkan dengan koma).")
    print("  Contoh: kekerasan_seksual, konseling")
    raw = input("  > ").strip()
    kebutuhan = set(k.strip().lower() for k in raw.split(",") if k.strip())

    tidak_valid = kebutuhan - DAFTAR_TAG_VALID
    if tidak_valid:
        print(f"\n  ⚠  Tag tidak dikenali: {', '.join(tidak_valid)}")
        print("     Tag tersebut akan diabaikan.")
        kebutuhan -= tidak_valid

    return kebutuhan


def input_kota() -> Optional[str]:
    print(f"\n  Kota/wilayah yang tersedia: {', '.join(sorted(KOTA_VALID))}")
    print("  (kosongkan untuk semua wilayah + Nasional)")
    raw = input("  Kota > ").strip().lower()
    if not raw:
        return None
    if raw not in KOTA_VALID:
        print(f"  ⚠  Kota '{raw}' tidak dikenali, diabaikan (cari semua wilayah).")
        return None
    return raw.title()


def jalankan_demo(bfs: KaumitaBFS):
    """Menjalankan dua contoh pencarian otomatis sebagai demonstrasi."""
    print("\n" + "─" * 60)
    print("  DEMO 1 – Korban kekerasan seksual, butuh konseling & pendampingan")
    print("─" * 60)
    req1 = {"kekerasan_seksual", "konseling", "pendampingan"}
    hasil1 = bfs.cari(req1)
    print(KaumitaBFS.format_hasil(hasil1, req1))

    print("─" * 60)
    print("  DEMO 2 – Perempuan di Surakarta butuh pendampingan & konseling")
    print("─" * 60)
    req2 = {"pendampingan", "konseling"}
    hasil2 = bfs.cari(req2, kota="Surakarta")
    print(KaumitaBFS.format_hasil(hasil2, req2, kota="Surakarta"))


def jalankan_chatbot(bfs: KaumitaBFS):
    """Menjalankan sesi tanya-jawab interaktif berbasis AI Gemini."""
    print("\n" + "═" * 60)
    print("  CHATBOT KAUMITA - AI KONSULTASI & RUJUKAN")
    print("═" * 60)
    
    try:
        import google.generativeai as genai
    except ImportError:
        print("\n  ⚠  Paket 'google-generativeai' belum terinstal.")
        print("     Silakan jalankan perintah berikut terlebih dahulu di terminal:")
        print("     pip install google-generativeai")
        return

    import os
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n  Kunci API Gemini tidak ditemukan di variabel lingkungan.")
        print("  Silakan masukkan API Key Gemini Anda secara manual:")
        api_key = input("  API Key > ").strip()
        if not api_key:
            print("  ⚠  API Key tidak boleh kosong. Membatalkan chatbot.")
            return

    genai.configure(api_key=api_key)
    
    try:
        # Menggunakan model gemini-2.5-flash untuk respon cepat dan andal
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        print(f"  ✗  Gagal menginisialisasi model Gemini: {e}")
        return

    print("\n  Halo! Saya adalah KAUMITA AI, konselor bantuan sosial inklusif Anda.")
    print("  Silakan ceritakan situasi atau masalah yang Anda alami secara bebas.")
    print("  Saya akan menganalisis cerita Anda dan memberikan rekomendasi rujukan terdekat.")
    print("  (Ketik 'keluar' untuk kembali ke menu utama)")
    
    while True:
        cerita = input("\n  Cerita Anda > ").strip()
        if cerita.lower() == 'keluar':
            break
        if not cerita:
            continue
            
        print("  [AI] Menganalisis keluhan Anda...")
        
        prompt = f"""
        Kamu adalah konselor AI empati bernama KAUMITA. Pengguna akan menceritakan keluhan, situasi, atau masalah mereka.
        Tugasmu adalah:
        1. Memberikan respon empati singkat (maksimal 2 kalimat) untuk menguatkan mereka.
        2. Menganalisis cerita pengguna untuk mencari kebutuhan yang cocok dengan daftar tag layanan kami.
        3. Mencari kota/wilayah jika disebutkan oleh pengguna.

        Daftar tag layanan valid: {sorted(list(DAFTAR_TAG_VALID))}
        Daftar kota/wilayah valid: {sorted(list(KOTA_VALID))}

        Kamu harus merespon HANYA dengan format JSON berikut tanpa blok kode markdown:
        {{
          "sapaan": "pesan empati singkat Anda untuk korban",
          "kebutuhan": ["tag1", "tag2"],
          "kota": "nama kota" (atau null jika tidak disebutkan)
        }}
        """
        
        try:
            response = model.generate_content(
                f"{prompt}\n\nCerita Pengguna: {cerita}",
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Parsing response JSON
            res_data = json.loads(response.text)
            
            sapaan = res_data.get("sapaan", "")
            kebutuhan_raw = res_data.get("kebutuhan", [])
            kota_raw = res_data.get("kota", None)
            
            # Saring agar hanya mencakup tag dan kota yang valid
            kebutuhan = set(k.strip().lower() for k in kebutuhan_raw) & DAFTAR_TAG_VALID
            
            kota = None
            if kota_raw and str(kota_raw).strip().lower() in KOTA_VALID:
                kota = str(kota_raw).strip().title()
                if kota.lower() == "nasional":
                    kota = None # Biarkan None agar mencari Nasional + Daerah
            
            print(f"\n  [AI]: \"{sapaan}\"")
            
            if kebutuhan:
                print(f"  [AI]: Kebutuhan terdeteksi: {', '.join(sorted(kebutuhan))}")
                if kota:
                    print(f"  [AI]: Wilayah/Kota terdeteksi: {kota}")
                else:
                    print(f"  [AI]: Wilayah: Nasional & Semua Wilayah")
                
                # Jalankan pencarian BFS
                hasil = bfs.cari(kebutuhan, kota=kota)
                print(KaumitaBFS.format_hasil(hasil, kebutuhan, kota=kota))
                
                # Tampilkan visualisasi BFS tree
                parent, level = bfs.bfs_tree(kebutuhan, kota=kota)
                bfs.tampilkan_bfs_tree(parent, level, bfs.graf)
            else:
                print("\n  [AI]: Saya tidak dapat mendeteksi kategori kebutuhan bantuan sosial spesifik dari cerita Anda.")
                print("        Cobalah sebutkan bantuan yang dibutuhkan secara lebih spesifik (misal: butuh konseling, hukum, pendampingan).")
                
        except Exception as e:
            print(f"  ✗  Gagal menghubungi API Gemini atau format tidak sesuai: {e}")


# ─────────────────────────────────────────────
# 5. ENTRY POINT
# ─────────────────────────────────────────────

def main():
    import os
    import sys
    # Mengatur encoding output agar mendukung karakter Unicode/Emoji di terminal Windows
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    # Resolusi path CSV relatif terhadap script ini
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path_csv = os.path.join(base_dir, "layanan.csv")

    # ── Bangun graf ──────────────────────────
    print("  Memuat data layanan...")
    try:
        graf = LayananGraph.dari_csv(path_csv)
    except FileNotFoundError:
        print(f"  ✗  File tidak ditemukan: {path_csv}")
        return

    print(f"  ✓  {graf.info()}")
    bfs = KaumitaBFS(graf)

    # ── Loop utama ───────────────────────────
    while True:
        tampilkan_menu()
        print("\n  [1] Cari layanan secara manual")
        print("  [2] Jalankan Demo")
        print("  [3] Lihat semua lembaga")
        print("  [4] Chatbot KAUMITA (Gemini AI)")
        print("  [0] Keluar")
        pilihan = input("\n  Pilihan > ").strip()

        if pilihan == "1":
            kebutuhan = input_kebutuhan()
            if not kebutuhan:
                print("  ⚠  Tidak ada kebutuhan valid yang dimasukkan.")
                continue
            kota = input_kota()
            hasil = bfs.cari(kebutuhan, kota=kota)

            print(KaumitaBFS.format_hasil(hasil, kebutuhan, kota=kota))

            # Visualisasi BFS tree
            parent, level = bfs.bfs_tree(kebutuhan, kota=kota)
            bfs.tampilkan_bfs_tree(parent, level, graf)

        elif pilihan == "2":
            jalankan_demo(bfs)

        elif pilihan == "3":
            print("\n  Daftar seluruh lembaga dalam sistem:")
            print("  " + "─" * 56)
            for v in graf.vertices.values():
                flags = ""
                if v.disabilitas_friendly:
                    flags += " ♿"
                print(f"  [{v.id:>2}] {v.nama:<42} ({v.kota}){flags}")

        elif pilihan == "4":
            jalankan_chatbot(bfs)

        elif pilihan == "0":
            print("\n  Terima kasih telah menggunakan KAUMITA.\n")
            break

        else:
            print("  Pilihan tidak valid.")


if __name__ == "__main__":
    main()