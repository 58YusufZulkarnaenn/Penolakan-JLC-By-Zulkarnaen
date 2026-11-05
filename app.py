import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from html import escape as esc
import pytz
from barcode_scanner import barcode_scanner

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Data Penolakan JLC",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# TAMPILAN GELAP PERMANEN
# Palet: Latar #0A1426 | Permukaan #111E36 | Garis #223454 | Teks #E8EEF8
#        Biru JLC #0056b3 | Emas #D4AA4F (aksen tipis)
# Font : Sora (judul) + Plus Jakarta Sans (isi)
# =====================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {
    color-scheme: dark;
    --bg: #0A1426;
    --surface: #111E36;
    --surface-2: #16263F;
    --line: #223454;
    --text: #E8EEF8;
    --muted: #8FA3C0;
    --brand: #0056b3;
    --brand-dark: #004494;
    --brand-light: #6FB1FF;
    --gold: #D4AA4F;
}

/* ---------- Sembunyikan elemen Streamlit / GitHub ---------- */
#MainMenu,
footer,
[data-testid="stToolbar"],
[data-testid="stMainMenu"],
[data-testid="stDeployButton"],
[data-testid="stAppDeployButton"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"],
.stDeployButton,
[class*="viewerBadge"],
[class*="profileContainer"],
a[href*="streamlit.io"],
a[href*="github.com"] {
    display: none !important;
    visibility: hidden !important;
}
header[data-testid="stHeader"] { background: transparent !important; }

/* ---------- Dasar ---------- */
.stApp { background: var(--bg) !important; color: var(--text); }
.block-container { padding-top: 1.6rem !important; padding-bottom: 3rem !important; max-width: 1100px; }
p, label, input, textarea, button, li, td, th, .stMarkdown, [data-baseweb="select"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
h1, h2, h3, h4 { font-family: 'Sora', sans-serif !important; color: var(--text) !important; letter-spacing: -0.01em; }
[data-testid="InputInstructions"] { display: none !important; }
label p { font-weight: 600 !important; color: var(--text) !important; font-size: .9rem !important; }
::placeholder { color: #6F83A3 !important; opacity: 1 !important; }

/* ---------- Top bar ---------- */
.topbar { display: flex; align-items: center; gap: .85rem; padding: .2rem 0 .6rem 0; }
.topbar .brand-mark { margin: 0; }
.tb-name { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 1.02rem; color: var(--text); line-height: 1.25; word-break: break-word; }
.tb-role { font-size: .8rem; color: var(--muted); }

/* ---------- Judul halaman ---------- */
.page-head { margin: .6rem 0 1.3rem 0; }
.page-head h1 { font-size: 1.7rem; font-weight: 700; margin: 0 0 .25rem 0; padding: 0; }
.page-head p { color: var(--muted); margin: 0; font-size: .95rem; }
.sec-title { font-family: 'Sora', sans-serif; font-weight: 600; font-size: 1.02rem; color: var(--text); margin: 1.6rem 0 .2rem 0; }
.sec-sub { color: var(--muted); font-size: .88rem; margin-bottom: .6rem; }

/* ---------- Logo & login ---------- */
.brand-mark {
    display: inline-flex; align-items: center; justify-content: center;
    width: 44px; height: 44px; border-radius: 12px; flex-shrink: 0;
    background: var(--brand); color: #fff;
    font-family: 'Sora', sans-serif; font-weight: 700; font-size: .85rem; letter-spacing: .02em;
}
.login-hero { text-align: center; padding: 1.2rem 0 1.4rem 0; }
.login-hero .brand-mark { width: 60px; height: 60px; border-radius: 17px; font-size: 1.1rem; margin-bottom: 1rem; }
.login-hero h1 { font-size: 1.9rem; font-weight: 700; margin: 0 0 .4rem 0; padding: 0; }
.login-hero p { color: var(--muted); margin: 0 auto; max-width: 340px; font-size: .95rem; }
.gold-rule { width: 44px; height: 3px; background: var(--gold); border-radius: 2px; margin: 1.1rem auto 0 auto; }

/* ---------- Tombol ---------- */
div.stButton > button,
[data-testid="stForm"] button,
.stDownloadButton > button {
    background-color: var(--brand) !important;
    color: #fff !important;
    border: 1px solid var(--brand) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.62rem 1.4rem !important;
    transition: background-color .2s ease, box-shadow .2s ease !important;
}
div.stButton > button:hover,
[data-testid="stForm"] button:hover,
.stDownloadButton > button:hover {
    background-color: #0A6AD6 !important;
    border-color: #0A6AD6 !important;
    color: #fff !important;
    box-shadow: 0 6px 18px rgba(0, 86, 179, .4) !important;
}
div.stButton > button:focus-visible,
[data-testid="stForm"] button:focus-visible { outline: 3px solid rgba(111, 177, 255, .5) !important; outline-offset: 2px; }
div.stButton > button[kind="secondary"],
div.stButton > button[data-testid="stBaseButton-secondary"] {
    background-color: transparent !important;
    color: var(--text) !important;
    border: 1px solid #2E4469 !important;
}
div.stButton > button[kind="secondary"]:hover,
div.stButton > button[data-testid="stBaseButton-secondary"]:hover {
    background-color: var(--surface-2) !important;
    border-color: var(--brand-light) !important;
    color: #fff !important;
    box-shadow: none !important;
}

/* ---------- Form & input ---------- */
[data-testid="stForm"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 16px !important;
    padding: 1.6rem !important;
    box-shadow: 0 12px 32px rgba(0, 0, 0, .35) !important;
}
input, textarea,
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background-color: #0D182C !important;
    color: var(--text) !important;
    border: 1.5px solid #2A3F63 !important;
    border-radius: 10px !important;
}
div[data-baseweb="select"] * { color: var(--text) !important; }
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="select"] > div:focus-within {
    border-color: var(--brand-light) !important;
    box-shadow: 0 0 0 3px rgba(111, 177, 255, .2) !important;
}

/* ---------- Kartu statistik ---------- */
.stat { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 1.05rem 1.25rem; height: 100%; }
.stat-label { color: var(--muted); font-size: .82rem; font-weight: 600; margin-bottom: .35rem; }
.stat-val { font-family: 'Sora', sans-serif; color: var(--text); font-size: 1.85rem; font-weight: 700; line-height: 1.15; }
.stat-val.small { font-size: 1rem; line-height: 1.35; padding-top: .35rem; }

/* ---------- Tabel ---------- */
[data-testid="stDataFrame"] {
    border: 1px solid var(--line);
    border-radius: 14px;
    overflow: hidden;
}

/* ---------- Tab & menu ---------- */
button[data-baseweb="tab"] { font-weight: 600 !important; }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--brand-light) !important; }
div[data-baseweb="tab-highlight"] { background-color: var(--brand-light) !important; }

/* ---------- Mobile ---------- */
@media (max-width: 640px) {
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 1.2rem !important; }
    .page-head h1 { font-size: 1.45rem; }
    .stat-val { font-size: 1.5rem; }
}
</style>
""", unsafe_allow_html=True)


# =====================================================================
# KOMPONEN TAMPILAN KECIL
# =====================================================================
def judul_halaman(teks, sub=""):
    st.markdown(
        f'<div class="page-head"><h1>{esc(teks)}</h1><p>{esc(sub)}</p></div>',
        unsafe_allow_html=True,
    )

def judul_bagian(teks, sub=""):
    html = f'<div class="sec-title">{esc(teks)}</div>'
    if sub:
        html += f'<div class="sec-sub">{esc(sub)}</div>'
    st.markdown(html, unsafe_allow_html=True)

def kartu_stat(label, nilai, kecil=False):
    kelas = "stat-val small" if kecil else "stat-val"
    return f'<div class="stat"><div class="stat-label">{esc(str(label))}</div><div class="{kelas}">{esc(str(nilai))}</div></div>'


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
# AMBIL DATA USER
# =====================================================================
@st.cache_data(ttl=300)
def get_data_user():
    sheet_user = get_worksheet("DATA USER")
    return sheet_user.get_all_records()

def get_daftar_sco():
    data = get_data_user()
    daftar = []
    for user in data:
        if str(user.get('ROLE', '')).upper() == 'SCO':
            username = str(user.get('USERNAME', '')).strip()
            nama = str(user.get('NAMA SCO', '')).strip()
            nama_title = nama.title() if nama else username
            label = f"{username} ({nama_title})"
            daftar.append({
                "username": username,
                "nama": nama,
                "label": label,
            })
    return daftar

def login_admin(username, password):
    data = get_data_user()
    for user in data:
        if (str(user.get('USERNAME', '')) == username
            and str(user.get('PASSWORD', '')) == password
            and str(user.get('ROLE', '')).upper() == 'ADMIN'):
            return user
    return None

# =====================================================================
# FUNGSI CACHE DATA RESI
# =====================================================================
@st.cache_data(ttl=10)
def get_all_resi():
    sheet_resi = get_worksheet("DATA RESI")
    raw_data = sheet_resi.get_all_values()

    if not raw_data:
        return pd.DataFrame()

    headers = [str(h).strip().upper() for h in raw_data[0]]
    data_rows = raw_data[1:]

    df = pd.DataFrame(data_rows, columns=headers)
    df = df.dropna(how='all')

    # Kolom bantu khusus buat filter (kolom asli NAMA SCO TIDAK diubah)
    if 'NAMA SCO' in df.columns:
        df['_KEY_SCO'] = df['NAMA SCO'].astype(str).str.strip().str.upper()

    return df

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

tz_jkt = pytz.timezone('Asia/Jakarta')

# =====================================================================
# HALAMAN LOGIN
# =====================================================================
if not st.session_state.logged_in:
    _, tengah, _ = st.columns([1, 1.5, 1])

    with tengah:
        st.markdown(
            '<div class="login-hero">'
            '<div class="brand-mark">JLC</div>'
            '<h1>Data Penolakan JLC</h1>'
            '<p>Catat penolakan member dengan cepat, rapi, dan langsung tersimpan.</p>'
            '<div class="gold-rule"></div>'
            '</div>',
            unsafe_allow_html=True,
        )

        try:
            daftar_sco = get_daftar_sco()
        except Exception as e:
            st.error(f"Gagal mengambil data user: {type(e).__name__} - {e}")
            st.stop()

        if not daftar_sco:
            st.warning("Belum ada SCO di sheet DATA USER.")
            st.stop()

        labels = [sco["label"] for sco in daftar_sco]
        default_idx = 0
        for i, sco in enumerate(daftar_sco):
            if sco["username"].upper() == "ZKARNKRW":
                default_idx = i
                break

        pilihan_label = st.selectbox(
            "Pilih nama Anda",
            labels,
            index=default_idx,
            key="pilih_nama_sco"
        )

        sco_terpilih = next((s for s in daftar_sco if s["label"] == pilihan_label), None)

        col1, col2 = st.columns([3, 1.4])
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
            if st.button("Admin", use_container_width=True):
                st.session_state.show_admin_login = not st.session_state.show_admin_login
                st.rerun()

        if st.session_state.show_admin_login:
            judul_bagian("Masuk sebagai Admin")
            with st.form("admin_login_form"):
                admin_user = st.text_input("Username")
                admin_pass = st.text_input("Password", type="password")
                submit_admin = st.form_submit_button("Masuk")

                if submit_admin:
                    admin = login_admin(admin_user, admin_pass)
                    if admin:
                        st.session_state.logged_in = True
                        st.session_state.user_data = admin
                        st.session_state.is_admin = True
                        st.session_state.show_admin_login = False
                        st.rerun()
                    else:
                        st.error("Username atau password salah. Periksa lagi lalu coba masuk kembali.")

# =====================================================================
# HALAMAN UTAMA
# =====================================================================
else:
    user_info = st.session_state.user_data
    # Nama user kapital & tanpa spasi; fallback ke USERNAME kalau NAMA SCO kosong
    nama_user = str(user_info.get('NAMA SCO', '')).strip().upper()
    if not nama_user:
        nama_user = str(user_info.get('USERNAME', '')).strip().upper()

    peran = "Administrator" if st.session_state.is_admin else "Sales Counter Officer"

    # --- TOP BAR (nama user + keluar) ---
    bar_kiri, bar_kanan = st.columns([5, 1.2])
    with bar_kiri:
        st.markdown(
            '<div class="topbar"><div class="brand-mark">JLC</div>'
            f'<div><div class="tb-name">{esc(nama_user)}</div><div class="tb-role">{esc(peran)}</div></div></div>',
            unsafe_allow_html=True,
        )
    with bar_kanan:
        if st.button("Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_data = None
            st.session_state.is_admin = False
            if "hasil_scan" in st.session_state:
                del st.session_state.hasil_scan
            st.rerun()

    # --- MENU (di halaman utama, bukan sidebar, biar selalu kelihatan di HP) ---
    if st.session_state.is_admin:
        menu = "Dashboard"
    else:
        opsi_menu = ["Input Resi", "Riwayat Saya"]
        try:
            menu = st.segmented_control(
                "Menu", opsi_menu, default=opsi_menu[0],
                label_visibility="collapsed", key="menu_nav",
            ) or opsi_menu[0]
        except AttributeError:
            # Streamlit versi lama tidak punya segmented_control
            menu = st.radio("Menu", opsi_menu, horizontal=True,
                            label_visibility="collapsed", key="menu_nav_radio")

    # =================================================================
    # MENU: INPUT RESI
    # =================================================================
    if menu == "Input Resi":
        judul_halaman("Input penolakan", "Scan resi lalu pilih alasan penolakan member.")

        judul_bagian("Scan barcode resi", "Tekan Mulai Scan untuk menyalakan kamera. Kamera mati otomatis setelah barcode terbaca.")

        hasil_scan = barcode_scanner(key="scanner_resi")

        if hasil_scan:
            st.session_state.hasil_scan = hasil_scan
            st.success(f"Barcode terbaca: **{hasil_scan}**")

        judul_bagian("Detail penolakan")

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
            alasan = st.selectbox("Alasan penolakan", opsi_alasan)
            detail_alasan = st.text_input("Detail alasan (wajib diisi jika memilih 'Lainnya')")

            default_resi = st.session_state.get("hasil_scan", "")
            no_resi = st.text_input(
                "Nomor resi",
                value=default_resi,
                help="Terisi otomatis dari hasil scan. Bisa juga diketik manual atau discan dengan alat fisik."
            )

            submit_resi = st.form_submit_button("Simpan data")

            if submit_resi:
                if not no_resi:
                    st.warning("Isi nomor resi terlebih dahulu.")
                elif alasan == "G. Lainnya... (isi sendiri)" and not detail_alasan:
                    st.warning("Isi detail alasan karena Anda memilih 'Lainnya'.")
                else:
                    waktu_sekarang = datetime.now(tz_jkt)
                    waktu_input = waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S")
                    tanggal_transaksi = waktu_sekarang.strftime("%Y-%m-%d")

                    sheet_resi = get_worksheet("DATA RESI")
                    sheet_resi.append_row([
                        waktu_input,
                        nama_user,
                        no_resi,
                        tanggal_transaksi,
                        alasan,
                        detail_alasan
                    ])

                    get_all_resi.clear()

                    st.success(f"Resi {no_resi} tersimpan.")

                    if "hasil_scan" in st.session_state:
                        del st.session_state.hasil_scan

    # =================================================================
    # MENU: RIWAYAT SAYA
    # =================================================================
    elif menu == "Riwayat Saya":
        judul_halaman("Riwayat saya", "Semua penolakan yang sudah Anda input, terbaru di paling atas.")

        data_resi = get_all_resi()

        if data_resi.empty or '_KEY_SCO' not in data_resi.columns:
            st.info("Belum ada data. Mulai dari menu Input Resi.")
        else:
            # Filter murni baca-saja: kolom NAMA SCO asli tidak disentuh
            data_pribadi = (
                data_resi.loc[data_resi['_KEY_SCO'] == nama_user]
                .drop(columns=['_KEY_SCO'])
            )

            if data_pribadi.empty:
                st.info("Belum ada data yang Anda input. Mulai dari menu Input Resi.")
            else:
                hari_ini_str = datetime.now(tz_jkt).strftime("%Y-%m-%d")

                total = len(data_pribadi)
                hari_ini = 0
                if 'TANGGAL TRANSAKSI' in data_pribadi.columns:
                    hari_ini = int((data_pribadi['TANGGAL TRANSAKSI'] == hari_ini_str).sum())

                alasan_top = "-"
                if 'ALASAN PENOLAKAN' in data_pribadi.columns:
                    seri = data_pribadi['ALASAN PENOLAKAN'].replace('', pd.NA).dropna()
                    if not seri.empty:
                        alasan_top = seri.mode().iloc[0]

                c1, c2, c3 = st.columns(3)
                c1.markdown(kartu_stat("Total input", total), unsafe_allow_html=True)
                c2.markdown(kartu_stat("Input hari ini", hari_ini), unsafe_allow_html=True)
                c3.markdown(kartu_stat("Alasan terbanyak", alasan_top, kecil=True), unsafe_allow_html=True)

                judul_bagian("Daftar input")
                cari = st.text_input(
                    "Cari nomor resi",
                    placeholder="Ketik sebagian nomor resi",
                    label_visibility="collapsed",
                )

                data_tampil = data_pribadi
                if cari.strip() and 'NO RESI' in data_tampil.columns:
                    data_tampil = data_tampil[
                        data_tampil['NO RESI'].astype(str).str.contains(cari.strip(), case=False, regex=False)
                    ]

                if data_tampil.empty:
                    st.info("Tidak ada resi yang cocok dengan pencarian.")
                else:
                    st.dataframe(data_tampil.iloc[::-1], use_container_width=True, hide_index=True)

    # =================================================================
    # MENU: DASHBOARD (ADMIN)
    # =================================================================
    elif menu == "Dashboard":
        judul_halaman("Dashboard admin", "Pantau seluruh data penolakan dari semua SCO.")

        data_resi = get_all_resi()

        if data_resi.empty:
            st.info("Belum ada data resi yang masuk dari SCO.")
        else:
            data_resi = data_resi.drop(columns=['_KEY_SCO'], errors='ignore')

            f1, f2 = st.columns(2)
            with f1:
                tanggal_unik = sorted(
                    [t for t in data_resi['TANGGAL TRANSAKSI'].unique().tolist() if str(t).strip()],
                    reverse=True,
                )
                pilih_tanggal = st.selectbox("Tanggal transaksi", ["Semua tanggal"] + tanggal_unik)
            with f2:
                sco_unik = sorted([s for s in data_resi['NAMA SCO'].unique().tolist() if str(s).strip()])
                pilih_sco = st.selectbox("SCO", ["Semua SCO"] + sco_unik)

            data_tampil = data_resi
            if pilih_tanggal != "Semua tanggal":
                data_tampil = data_tampil[data_tampil['TANGGAL TRANSAKSI'] == pilih_tanggal]
            if pilih_sco != "Semua SCO":
                data_tampil = data_tampil[data_tampil['NAMA SCO'] == pilih_sco]

            hari_ini_str = datetime.now(tz_jkt).strftime("%Y-%m-%d")
            jumlah_hari_ini = int((data_resi['TANGGAL TRANSAKSI'] == hari_ini_str).sum())

            c1, c2, c3 = st.columns(3)
            c1.markdown(kartu_stat("Data sesuai filter", len(data_tampil)), unsafe_allow_html=True)
            c2.markdown(kartu_stat("SCO aktif pada filter", data_tampil['NAMA SCO'].nunique()), unsafe_allow_html=True)
            c3.markdown(kartu_stat("Input hari ini (semua SCO)", jumlah_hari_ini), unsafe_allow_html=True)

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

            tab_data, tab_ringkasan = st.tabs(["Data", "Ringkasan"])

            with tab_data:
                if data_tampil.empty:
                    st.info("Tidak ada data untuk filter ini.")
                else:
                    st.dataframe(data_tampil.iloc[::-1], use_container_width=True, hide_index=True)

                    csv = data_tampil.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Unduh data (CSV)",
                        data=csv,
                        file_name='data_penolakan.csv',
                        mime='text/csv',
                    )

            with tab_ringkasan:
                if data_tampil.empty:
                    st.info("Tidak ada data untuk filter ini.")
                else:
                    judul_bagian("Jumlah input per SCO")
                    st.bar_chart(data_tampil['NAMA SCO'].value_counts())

                    judul_bagian("Sebaran alasan penolakan")
                    st.bar_chart(data_tampil['ALASAN PENOLAKAN'].replace('', pd.NA).dropna().value_counts())
