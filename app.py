import csv
import os
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session, flash

# --- Konfigurasi File ---
NAMA_FILE_RESI = 'data_resi.csv'
HEADER_RESI = ['Toko E-commerce', 'Nomor Pesanan', 'Tanggal Pembelian', 'Deskripsi/Tautan Resi']

NAMA_FILE_PENGGUNA = 'pengguna.csv'
HEADER_PENGGUNA = ['Username', 'Password_Hash']

# Inisialisasi aplikasi Flask
app = Flask(__name__)
# Set secret key untuk sesi (PENTING untuk keamanan)
# GANTI DENGAN KUNCI ASLI YANG LEBIH KUAT UNTUK PRODUKSI!
app.secret_key = 'kunci_rahasia_sangat_aman_dan_sulit_ditebak_anda' 

# --- Fungsi Utilitas File ---
def inisialisasi_file(nama_file, header):
    """Memastikan file ada dan memiliki header yang benar."""
    if not os.path.exists(nama_file):
        with open(nama_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(header)
        print(f"File '{nama_file}' telah dibuat.")

# Inisialisasi kedua file saat aplikasi dimulai
inisialisasi_file(NAMA_FILE_RESI, HEADER_RESI)
inisialisasi_file(NAMA_FILE_PENGGUNA, HEADER_PENGGUNA)

# --- Fungsi Autentikasi Pengguna ---
def hash_password(password):
    """Menghasilkan hash SHA256 dari password."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- Route Aplikasi Web ---

@app.before_request
def check_authentication():
    """Middleware untuk memastikan pengguna login sebelum mengakses halaman tertentu."""
    # Izinkan akses ke halaman login, register, dan file statis tanpa autentikasi
    if 'username' not in session and request.endpoint not in ['login', 'register', 'static']:
        return redirect(url_for('login'))

@app.route('/')
def index():
    """Halaman utama, redirect ke dashboard jika sudah login, atau ke login."""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Menangani login pengguna."""
    if 'username' in session: # Jika sudah login, langsung ke dashboard
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash_input = hash_password(password)

        try:
            with open(NAMA_FILE_PENGGUNA, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader) # Lewati header
                for row in reader:
                    if row[0] == username and row[1] == password_hash_input:
                        session['username'] = username # Simpan username di sesi
                        flash('Login berhasil!', 'success')
                        return redirect(url_for('dashboard'))
            flash('Username atau password salah.', 'danger')
        except FileNotFoundError:
            flash('Belum ada akun terdaftar. Silakan daftar terlebih dahulu.', 'info')
        except Exception as e:
            flash(f'Terjadi kesalahan saat login: {e}', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Menangani pendaftaran pengguna baru."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Username dan password tidak boleh kosong.', 'danger')
            return render_template('register.html')

        try:
            # Periksa apakah username sudah ada
            with open(NAMA_FILE_PENGGUNA, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader) # Lewati header
                for row in reader:
                    if row[0] == username:
                        flash('Username ini sudah ada. Silakan pilih username lain.', 'warning')
                        return render_template('register.html')
            
            # Tambahkan pengguna baru
            password_hash = hash_password(password)
            with open(NAMA_FILE_PENGGUNA, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([username, password_hash])
            flash('Pendaftaran berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f'Terjadi kesalahan saat mendaftar: {e}', 'danger')
            
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    """Halaman dashboard setelah login."""
    if 'username' not in session: # Redundansi, tapi lebih aman
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/add_receipt', methods=['GET', 'POST'])
def add_receipt():
    """Menambahkan resi baru."""
    if 'username' not in session: # Redundansi, tapi lebih aman
        return redirect(url_for('login'))

    if request.method == 'POST':
        toko = request.form['toko']
        nomor_pesanan = request.form['nomor_pesanan']
        tanggal = request.form['tanggal']
        deskripsi_tautan = request.form['deskripsi_tautan']

        data_baru = [toko, nomor_pesanan, tanggal, deskripsi_tautan]

        try:
            with open(NAMA_FILE_RESI, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(data_baru)
            flash('Resi berhasil ditambahkan!', 'success')
            return redirect(url_for('view_receipts'))
        except Exception as e:
            flash(f'Terjadi kesalahan saat menyimpan resi: {e}', 'danger')
            
    return render_template('add_receipt.html')

@app.route('/view_receipts')
def view_receipts():
    """Menampilkan semua resi yang tersimpan."""
    if 'username' not in session: # Redundansi, tapi lebih aman
        return redirect(url_for('login'))

    receipts = []
    try:
        with open(NAMA_FILE_RESI, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader) # Lewati header
            for row in reader:
                # Mengubah list row menjadi dictionary untuk kemudahan akses di template
                receipts.append({
                    'toko': row[0],
                    'nomor_pesanan': row[1],
                    'tanggal': row[2],
                    'deskripsi_tautan': row[3]
                })
    except FileNotFoundError:
        flash('Belum ada resi yang tersimpan.', 'info')
    except Exception as e:
        flash(f'Terjadi kesalahan saat membaca resi: {e}', 'danger')

    return render_template('receipts.html', receipts=receipts)

@app.route('/logout')
def logout():
    """Menangani logout pengguna."""
    session.pop('username', None) # Hapus username dari sesi
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Jalankan aplikasi di mode debug (akan otomatis reload saat ada perubahan kode)
    # JANGAN GUNAKAN debug=True DI LINGKUNGAN PRODUKSI
    app.run(debug=True)