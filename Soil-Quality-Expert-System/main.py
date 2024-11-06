from flask import Flask
from flask import render_template, request
import os

main = Flask(__name__)

# Fungsi untuk menghitung Certainty Factor (CF)
def hitung_cf(cf_pengguna, cf_pakar):
    
    # Hitung CF
    return cf_pengguna * cf_pakar

def combine_cf(cf_lama, cf_baru):
    
    # Gabungkan 2 nilai CF
    return cf_lama + cf_baru - (cf_baru * cf_lama)

# Fungsi untuk mendapatkan nilai CF dari input user
def get_cf_pengguna(choice):
    return {1: 0.0, 2: 0.2, 3: 0.4, 4: 0.6, 5: 0.8, 6: 1.0}.get(choice, 0.0)

# Fungsi untuk membaca knowledge base dari file di direktori data
def load_knowledge_base_from_file():
    knowledge_base = {}
    # Tentukan path absolut untuk file knowledge base dalam direktori "data"
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "knowledge_bases.txt"))
    
    print(f"Mencoba memuat file knowledge base dari path: {file_path}")
    
    try:
        with open(file_path, 'r') as file:
            kode_kerusakan = None
            for line in file:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("K"):  # Baris yang memulai kode kerusakan
                    kode_kerusakan, nama_kerusakan = line.split(" - ")
                    knowledge_base[kode_kerusakan] = {'name': nama_kerusakan, 'symptoms': {}, 'solution': ''}
                elif line.startswith("T"):  # Baris yang memulai kode gejala
                    gejala_code, rest = line.split(": ")
                    gejala_name, weight = rest.split(" - ")
                    knowledge_base[kode_kerusakan]['symptoms'][gejala_code] = {'name': gejala_name, 'weight': float(weight)}
                elif line.startswith("Solusi:"):  # Baris solusi
                    solution = line.split("Solusi: ")[1]
                    knowledge_base[kode_kerusakan]['solution'] = solution.strip()
        print("Knowledge base berhasil dimuat.")
    except FileNotFoundError:
        print(f"File {file_path} tidak ditemukan. Pastikan file berada di direktori 'data' dan bernama 'knowledge_bases.txt'.")
    except Exception as e:
        print("Terjadi error saat membaca knowledge base:", e)
    return knowledge_base

# Fungsi untuk melakukan diagnosa
def diagnose(gejala_user, knowledge_base):
    hasil_diagnosis = []
    
    # Iterasi melalui setiap kerusakan dalam knowledge base
    for kode_kerusakan, data_kerusakan in knowledge_base.items():
        cf_combine = 0.0
        match_found = False
        
        # Iterasi melalui setiap gejala untuk kerusakan
        for gejala_code, cf_pakar in data_kerusakan['symptoms'].items():
            # Cek apakah gejala user cocok dengan gejala kerusakan
            cf_pengguna = gejala_user.get(gejala_code, 0.0)
            if cf_pengguna > 0:  # Hanya jika ada CF dari user
                match_found = True  # Menandakan ada kecocokan gejala
                cf_current = hitung_cf(cf_pengguna, cf_pakar['weight'])
                cf_combine = combine_cf(cf_combine, cf_current)

        # Hanya tambahkan hasil jika ada gejala yang cocok
        if match_found:
            hasil_diagnosis.append((data_kerusakan['name'], cf_combine, data_kerusakan['solution'] ))

    # Mengurutkan hasil berdasarkan nilai CF tertinggi
    hasil_diagnosis.sort(key=lambda x: x[1], reverse=True)
    return hasil_diagnosis

# Fungsi untuk memproses input user dari form
def process_user_input(form_data):
    gejala_user = {}
    for symptom_code in form_data:
        user_input = int(form_data[symptom_code])
        gejala_user[symptom_code] = get_cf_pengguna(user_input)
    return gejala_user

@main.route('/')
def start():
    return render_template('mulai.html')

@main.route('/diagnosa')
def index():
    # Muat knowledge base dan kumpulkan semua gejala unik
    knowledge_base = load_knowledge_base_from_file()
    if not knowledge_base:
        return "Error: File knowledge base tidak ditemukan atau kosong."
    
    symptoms = {}
    for data_kerusakan in knowledge_base.values():
        for gejala_code, gejala_data in data_kerusakan['symptoms'].items():
            if gejala_code not in symptoms:
                symptoms[gejala_code] = gejala_data['name']
    return render_template('base.html', symptoms=symptoms)

@main.route('/diagnose', methods=['POST'])
def diagnose_route():
    # Muat knowledge base
    knowledge_base = load_knowledge_base_from_file()
    if not knowledge_base:
        return "Error: Tidak dapat memuat knowledge base."

    # Ambil data dari form
    gejala_user = process_user_input(request.form)

    # Lakukan diagnosis berdasarkan gejala
    hasil_diagnosis = diagnose(gejala_user, knowledge_base)
    
    # Filter hasil diagnosis untuk nilai CF > 0
    hasil_diagnosis_filtered = [diagnosis for diagnosis in hasil_diagnosis if diagnosis[1] > 0]

    # Jika tidak ada hasil diagnosis dengan CF > 0, tampilkan pesan "tidak ada kerusakan yang terjadi"
    if not hasil_diagnosis_filtered:
       return render_template('hasil.html', diagnosis_results=[], no_damage_message="Tidak ada kerusakan yang terjadi.")
    

    # Render halaman hasil diagnosis
    return render_template('hasil.html', diagnosis_results=hasil_diagnosis_filtered)


if __name__ == '__main__':
    main.run(debug=True)
