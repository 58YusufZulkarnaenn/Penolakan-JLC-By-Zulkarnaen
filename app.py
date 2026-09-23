import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import pytz
from barcode_scanner import barcode_scanner

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="App Penolakan Member", layout="wide")

# --- KUSTOMISASI TAMPILAN (UI/UX) ---
st.markdown("""
<style>
    /* 1. Tombol Biasa dan Tombol Submit di dalam form WAJIB BIRU */
    div.stButton > button, 
    [data-testid="stForm"] button {
        background-color: #0056b3 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        border: none !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
    }

    /* Efek pas kursor ngelewatin tombol */
    div.stButton > button:hover, 
    [data-testid="stForm"] button:hover {
        background-color: #004494 !important;
        color: white !important;
        transform: scale(1.02) !important;
    }

    /* 2. Bikin Kotak Form warnanya biru sangat muda dan garis luarnya tegas */
    [data-testid="stForm"] {
        border: 2px solid #9fbdd8 !important;
        border-radius: 10px !important;
        padding: 25px !important;
        background-color: #f2f7fc !important; 
        box-shadow: 3px 3px 15px rgba(0,0,0,0.1) !important;
    }

    /* 3. Bikin kotak input putih bersih tapi garis pinggirnya abu-abu gelap */
    input, 
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div {
        background-color: #ffffff !important;
        border: 1.5px solid #a6b5c4 !important;
        border-radius: 6px !important;
    }

    /* 4. Teks judul di sidebar */
    [data-testid="stSidebar"] h1 {
        color: #0056b3 !important;
        font-weight: 800 !important;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# KONEKSI GOOGLE SHEETS (CACHED)
# =====================================================================
@st.cache_resource
def get_google_sheet():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(credentials)
    sheet_url = "https://docs.google.com/spreadsheets/d/1rYd3AUwsUaK0TgqTboimCoiamh5ReVy9tGXofONHyJI/edit"
    return client.open_by_url(sheet_url)

@st.cache_resource
def get_worksheet(nama_sheet):
    db = get_google_sheet()
    return db.worksheet(nama_sheet)

# =====================================================================
# AMBIL DATA USER (UNTUK DROPDOWN SCO & LOGIN ADMIN)
# =====================================================================
@st.cache_data(ttl=300)  # cache 5 menit
def get_data_user():
    sheet_user = get_worksheet("DATA USER")
    return sheet_user.get_all_records()

def get_daftar_sco():
    """Ambil daftar SCO dari sheet DATA USER.
    Return: list of dict {username, nama, label}
    """
    data = get_data_user()
    daftar = []
    for user in data:
        if str(user.get('ROLE', '')).upper() == 'SCO':
            username = str(user.get('USERNAME', '')).strip()
            nama = str(user.get('NAMA SCO', '')).strip()
            # Format: "ZKARNKRW (Yusuf Zulkarnaen)"
            # Title case nama biar rapi
            nama_title = nama.title() if nama else username
            label = f"{username} ({nama_title})"
            daftar.append({
                "username": username,
                "nama": nama,
                "label": label,
            })
    return daftar

def login_admin(username, password):
    """Login admin: cek username + password + role = ADMIN."""
    data = get_data_user()
    for user in data:
        if (str(user.get('USERNAME', '')) == username
            and str(user.get('PASSWORD', '')) == password
            and str(user.get('ROLE', '')).upper() == 'ADMIN'):
            return user
    return None

# =====================================================================
# STATE MANAGEMENT
# =====================================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'show_admin_login' not in st.session_state:
    st.session_state.show_admin_login = False

# =====================================================================
# HALAMAN LOGIN (PILIH NAMA SCO, TANPA PASSWORD)
# =====================================================================
if not st.session_state.logged_in:
    st.title("📦 Data Penolakan JLC")
    st.caption("Pilih nama lu, terus klik 'Masuk' buat mulai kerja.")

    # Ambil daftar SCO dari sheet
    try:
        daftar_sco = get_daftar_sco()
    except Exception as e:
        st.error(f"Gagal narik data user: {type(e).__name__} - {e}")
        st.stop()

    if not daftar_sco:
        st.warning("Belum ada SCO di sheet DATA USER.")
        st.stop()

    # Cari index default = ZKARNKRW
    labels = [sco["label"] for sco in daftar_sco]
    default_idx = 0
    for i, sco in enumerate(daftar_sco):
        if sco["username"].upper() == "ZKARNKRW":
            default_idx = i
            break

    # Dropdown SCO
    pilihan_label = st.selectbox(
        "Pilih Nama Lu:",
        labels,
        index=default_idx,
        key="pilih_nama_sco"
    )

    # Cari data SCO yang dipilih
    sco_terpilih = next((s for s in daftar_sco if s["label"] == pilihan_label), None)

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Masuk sebagai SCO", use_container_width=True, type="primary"):
            if sco_terpilih:
                st.session_state.logged_in = True
                st.session_state.is_admin = False
                st.session_state.user_data = {
                    "USERNAME": sco_terpilih["username"],
                    "NAMA SCO": sco_terpilih["nama"],
                    "ROLE": "SCO"
                }
                st.rerun()
    with col2:
        if st.button("🔐 Admin", use_container_width=True):
            st.session_state.show_admin_login = not st.session_state.show_admin_login
            st.rerun()

    # Form login admin
    if st.session_state.show_admin_login:
        st.markdown("---")
        st.subheader("🔐 Login Admin")
        with st.form("admin_login_form"):
            admin_user = st.text_input("Username Admin")
            admin_pass = st.text_input("Password Admin", type="password")
            submit_admin = st.form_submit_button("Login Admin")

            if submit_admin:
                admin = login_admin(admin_user, admin_pass)
                if admin:
                    st.session_state.logged_in = True
                    st.session_state.user_data = admin
                    st.session_state.is_admin = True
                    st.session_state.show_admin_login = False
                    st.rerun()
                else:
                    st.error("Username atau Password admin salah!")

# =====================================================================
# HALAMAN UTAMA (SETELAH LOGIN)
# =====================================================================
else:
    user_info = st.session_state.user_data
    nama_user = user_info.get('NAMA SCO', '')
    role_user = user_info.get('ROLE', '')

    st.sidebar.title(f"Halo, {nama_user}!")
    if st.session_state.is_admin:
        st.sidebar.write("Akses: **ADMIN**")
    else:
        st.sidebar.write("Akses: **SCO**")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_data = None
        st.session_state.is_admin = False
        if "hasil_scan" in st.session_state:
            del st.session_state.hasil_scan
        st.rerun()

    # --- MENU ---
    if st.session_state.is_admin:
        menu = st.sidebar.radio("Pilih Menu", ["Dashboard Admin"])
    else:
        menu = st.sidebar.radio("Pilih Menu", ["Input Resi Baru", "Riwayat Input Gua"])

    # =================================================================
    # MENU: INPUT RESI BARU (SCO)
    # =================================================================
    if menu == "Input Resi Baru":
        st.header("Input Data Penolakan JLC")

        # === BLOK SCANNER KAMERA ===
        st.subheader("📷 Scan Barcode Resi")
        st.caption("Klik 'Mulai Scan' untuk nyalain kamera. Kamera otomatis mati setelah barcode kebaca.")

        hasil_scan = barcode_scanner(key="scanner_resi")

        if hasil_scan:
            st.session_state.hasil_scan = hasil_scan
            st.success(f"✅ Barcode terbaca: **{hasil_scan}**")

        st.markdown("---")
        # === END BLOK SCANNER ===

        with st.form("input_resi", clear_on_submit=True):
            opsi_alasan = [
                "A. Belum butuh",
                "B. Belum tertarik",
                "C. Tertarik, Tapi lagi buru buru",
                "D. Tidak tertarik karena ribet",
                "E. Belum tertarik karena jarang ngirim",
                "F. Sudah daftar, Tapi tidak ada email masuk",
                "G. Lainnya... (isi sendiri)"
            ]
            alasan = st.selectbox("Alasan Penolakan", opsi_alasan)
            detail_alasan = st.text_input("Jika pilih 'Lainnya', ketik alasannya di sini:")

            default_resi = st.session_state.get("hasil_scan", "")
            no_resi = st.text_input(
                "Nomor Resi",
                value=default_resi,
                help="Auto-isi dari hasil scan, atau ketik manual / scan pakai alat fisik"
            )

            submit_resi = st.form_submit_button("Submit Data")

            if submit_resi:
                if not no_resi:
                    st.warning("Nomor resi tidak boleh kosong!")
                elif alasan == "G. Lainnya... (isi sendiri)" and not detail_alasan:
                    st.warning("Detail alasan harus diisi!")
                else:
                    tz_jkt = pytz.timezone('Asia/Jakarta')
                    waktu_sekarang = datetime.now(tz_jkt)
                    waktu_input = waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S")
                    tanggal_transaksi = waktu_sekarang.strftime("%Y-%m-%d")

                    sheet_resi = get_worksheet("DATA RESI")
                    sheet_resi.append_row([
                        waktu_input,
                        nama_user,          # <-- simpen NAMA (YUSUF ZULKARNAEN)
                        no_resi,
                        tanggal_transaksi,
                        alasan,
                        detail_alasan
                    ])

                    # Clear cache data resi biar riwayat langsung update
                    get_all_resi.clear()

                    st.success(f"Resi {no_resi} berhasil disimpan!")

                    if "hasil_scan" in st.session_state:
                        del st.session_state.hasil_scan

    # =================================================================
    # MENU: RIWAYAT INPUT GUA (SCO)
    # =================================================================
    elif menu == "Riwayat Input Gua":
        st.header("Riwayat Input Lu")

        @st.cache_data(ttl=60)
        def get_all_resi():
            sheet_resi = get_worksheet("DATA RESI")
            return pd.DataFrame(sheet_resi.get_all_records())

        data_resi = get_all_resi()

        if not data_resi.empty:
            # Filter pakai NAMA (YUSUF ZULKARNAEN)
            data_pribadi = data_resi[data_resi['NAMA SCO'] == nama_user]
            st.dataframe(data_pribadi, use_container_width=True)
        else:
            st.info("Belum ada data yang diinput.")

    # =================================================================
    # MENU: DASHBOARD ADMIN
    # =================================================================
    elif menu == "Dashboard Admin":
        st.header("Dashboard Master Admin")

        @st.cache_data(ttl=60)
        def get_all_resi_admin():
            sheet_resi = get_worksheet("DATA RESI")
            return pd.DataFrame(sheet_resi.get_all_records())

        data_resi = get_all_resi_admin()

        if not data_resi.empty:
            tanggal_unik = data_resi['TANGGAL TRANSAKSI'].unique().tolist()
            tanggal_unik.insert(0, "Semua Tanggal")
            pilih_tanggal = st.selectbox("Filter Tanggal Transaksi", tanggal_unik)

            if pilih_tanggal != "Semua Tanggal":
                data_tampil = data_resi[data_resi['TANGGAL TRANSAKSI'] == pilih_tanggal]
            else:
                data_tampil = data_resi

            st.dataframe(data_tampil, use_container_width=True)

            csv = data_tampil.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Data (CSV)",
                data=csv,
                file_name='data_penolakan.csv',
                mime='text/csv',
            )
        else:
            st.info("Belum ada data resi yang masuk dari SCO.")
