import os
import json
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Memuat berkas .env jika ada
load_dotenv()

# Mengimpor modul pencarian BFS dari kaumita_bfs.py
try:
    from kaumita_bfs import LayananGraph, KaumitaBFS, DAFTAR_TAG_VALID, KOTA_VALID
except ImportError:
    # Fallback jika terjadi error impor relatif
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from kaumita_bfs import LayananGraph, KaumitaBFS, DAFTAR_TAG_VALID, KOTA_VALID

app = Flask(__name__)

# Resolusi path CSV
base_dir = os.path.dirname(os.path.abspath(__file__))
path_csv = os.path.join(base_dir, "layanan.csv")

# Memuat data graf & BFS
print("Loading KAUMITA Graph...")
graf = LayananGraph.dari_csv(path_csv)
bfs = KaumitaBFS(graf)
print(f"Loaded successfully: {graf.info()}")

@app.route("/")
def index():
    """Halaman Utama"""
    return render_template("index.html")

@app.route("/api/lembaga", methods=["GET"])
def get_lembaga():
    """Mengembalikan semua daftar lembaga dalam format JSON"""
    lembaga_list = []
    for lid, v in graf.vertices.items():
        lembaga_list.append({
            "id": v.id,
            "nama": v.nama,
            "kategori": v.kategori,
            "tags": list(v.tags),
            "kontak": v.kontak,
            "wa": v.wa,
            "email": v.email,
            "sosmed": v.sosmed,
            "kota": v.kota,
            "disabilitas_friendly": v.disabilitas_friendly
        })
    # Urutkan berdasarkan ID
    lembaga_list.sort(key=lambda x: x["id"])
    return jsonify(lembaga_list)

@app.route("/api/chat", methods=["POST"])
def chat():
    """Endpoint untuk interaksi Chatbot AI Gemini + Pencarian BFS"""
    data = request.json or {}
    message = data.get("message", "").strip()
    gender = data.get("gender", "").strip().lower()
    disabilitas = data.get("disabilitas", False)
    anak = data.get("anak", False)
    kategori_pilihan = data.get("kategori", []) # Kebutuhan Pokok, Bantuan Hukum, Konseling

    if not message:
        return jsonify({"error": "Pesan cerita tidak boleh kosong"}), 400

    # Inisialisasi API Gemini
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({
            "sapaan": "Kunci API Gemini tidak disetel di server web. Mohon konfigurasikan GEMINI_API_KEY.",
            "kebutuhan": [],
            "kota": None,
            "hasil": [],
            "bfs_tree": {}
        })

    import google.generativeai as genai
    genai.configure(api_key=api_key)

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        return jsonify({"error": f"Gagal inisialisasi model: {str(e)}"}), 500

    # Persiapan prompt analisis Gemini
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
            f"{prompt}\n\nCerita Pengguna: {message}",
            generation_config={"response_mime_type": "application/json"}
        )
        res_data = json.loads(response.text)
    except Exception as e:
        return jsonify({
            "sapaan": f"Maaf, saya sedang mengalami kesulitan memproses cerita Anda (API Error: {str(e)}). Namun saya akan mencoba mencarikan rujukan berdasarkan filter formulir Anda.",
            "kebutuhan": [],
            "kota": None,
            "hasil": [],
            "bfs_tree": {}
        })

    sapaan = res_data.get("sapaan", "")
    kebutuhan_raw = res_data.get("kebutuhan", [])
    kota_raw = res_data.get("kota", None)

    # 1. Gabungkan tag hasil ekstraksi Gemini
    kebutuhan = set(k.strip().lower() for k in kebutuhan_raw) & DAFTAR_TAG_VALID

    # 2. Gabungkan tag hasil isian formulir UI
    if disabilitas:
        kebutuhan.add("disabilitas")
    if anak:
        kebutuhan.add("anak")
        kebutuhan.add("perlindungan_anak")
    if gender in ["perempuan", "nonbiner"]:
        kebutuhan.add("perempuan")
        kebutuhan.add("perlindungan_perempuan")
    
    # Gabungkan filter kategori bantuan dari card UI
    for kat in kategori_pilihan:
        if kat == "Kebutuhan Pokok":
            kebutuhan.add("bantuan_umum")
        elif kat == "Bantuan Hukum":
            kebutuhan.add("hukum")
            kebutuhan.add("konsultasi_hukum")
        elif kat == "Konseling Psikologis":
            kebutuhan.add("konseling")
            kebutuhan.add("psikologi")
            kebutuhan.add("trauma")

    # Normalisasi kota
    kota = None
    if kota_raw and str(kota_raw).strip().lower() in KOTA_VALID:
        kota = str(kota_raw).strip().title()
        if kota.lower() == "nasional":
            kota = None

    # Jalankan BFS
    hasil_bfs = bfs.cari(kebutuhan, kota=kota)

    # Susun hasil lembaga dalam format serializable
    hasil_list = []
    for lbg in hasil_bfs:
        hasil_list.append({
            "id": lbg.id,
            "nama": lbg.nama,
            "kategori": lbg.kategori,
            "tags": list(lbg.tags),
            "kontak": lbg.kontak,
            "wa": lbg.wa,
            "email": lbg.email,
            "sosmed": lbg.sosmed,
            "kota": lbg.kota,
            "disabilitas_friendly": lbg.disabilitas_friendly
        })

    # Dapatkan BFS Tree
    parent, level = bfs.bfs_tree(kebutuhan, kota=kota)
    
    # Susun visualisasi BFS Tree agar mudah dirender di web
    # Kita pangkas agar hanya menampilkan node hasil pencarian dan parent-nya ke atas (lebih bersih dan relevan)
    bfs_tree_data = {}
    hasil_ids = {lbg.id for lbg in hasil_bfs}
    relevan_ids = set()
    for hid in hasil_ids:
        curr = hid
        while curr is not None:
            relevan_ids.add(curr)
            curr = parent.get(curr)
            
    # Jika tidak ada hasil, tampilkan saja root-root utama
    if not relevan_ids:
        relevan_ids = {nid for nid, p in parent.items() if p is None}
        
    for node_id in relevan_ids:
        lvl = level.get(node_id, 0)
        p = parent.get(node_id)
        parent_name = graf.vertices[p].nama if p is not None else None
        bfs_tree_data[node_id] = {
            "nama": graf.vertices[node_id].nama,
            "level": lvl,
            "parent_id": p,
            "parent_nama": parent_name
        }

    return jsonify({
        "sapaan": sapaan,
        "kebutuhan": list(kebutuhan),
        "kota": kota or "Nasional & Semua Wilayah",
        "hasil": hasil_list,
        "bfs_tree": bfs_tree_data
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
