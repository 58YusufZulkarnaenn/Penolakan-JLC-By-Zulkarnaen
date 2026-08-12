import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import pytz

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="App Penolakan Member", layout="wide")

# --- KONEKSI KE GOOGLE SHEETS ---
def get_google_sheet():
    # Mengambil kredensial dari st.secrets
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(credentials)
    
    # GANTI URL DI BAWAH INI DENGAN URL GOOGLE SHEETS LU
    sheet_url = "https://docs.google.com/spreadsheets/d/1rYd3AUwsUaK0TgqTboimCoiamh5ReVy9tGXofONHyJI/edit?gid=0#gid=0" 
    return client.open_by_url(sheet_url)

# --- FUNGSI LOGIN ---
def login_user(username, password):
    db = get_google_sheet()
    sheet_user = db.worksheet("DATA USER")
    data_user = sheet_user.get_all_records()
    
    for user in data_user:
        if str(user['USERNAME']) == username and str(user['PASSWORD']) == password:
            return user
    return None

# --- STATE MANAGEMENT ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# --- HALAMAN LOGIN ---
if not st.session_state.logged_in:
    st.title("Login Sistem Penolakan Member")
    with st.form("login_form"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        submit_btn = st.form_submit_button("Login")
        
        if submit_btn:
            user = login_user(username_input, password_input)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_data = user
                st.rerun()
            else:
                st.error("Username atau Password salah!")

# --- HALAMAN UTAMA (SETELAH LOGIN) ---
else:
    user_info = st.session_state.user_data
    nama_user = user_info['NAMA SCO']
    role_user = user_info['ROLE']
    
    st.sidebar.title(f"Halo, {nama_user}!")
    st.sidebar.write(f"Akses: **{role_user}**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_data = None
        st.rerun()

    db = get_google_sheet()
    sheet_resi = db.worksheet("DATA RESI")

    # --- JIKA YANG LOGIN ADALAH SCO ---
    if role_user.upper() == "SCO":
        menu = st.sidebar.radio("Pilih Menu", ["Input Resi Baru", "Riwayat Input Gua"])
        
        if menu == "Input Resi Baru":
            st.header("Input Data Penolakan JLC")
            with st.form("input_resi", clear_on_submit=True):                
                # Opsi Alasan
                opsi_alasan = [
                    "A. Lagi buru-buru",
                    "B. Belum tertarik",
                    "C. Tertarik, Tapi lagi buru buru",
                    "D. Tidak tertarik karena ribet",
                    "E. Lainnya... (isi sendiri)"
                ]
                alasan = st.selectbox("Alasan Penolakan", opsi_alasan)
                detail_alasan = st.text_input("Jika pilih 'Lainnya', ketik alasannya di sini:")

                # Barcode scanner otomatis ngetik di sini
                no_resi = st.text_input("Nomor Resi (Bisa pakai Scanner)", help="Arahkan kursor ke sini lalu scan barcode")
                
                submit_resi = st.form_submit_button("Submit Data")
                
                if submit_resi:
                    if not no_resi:
                        st.warning("Nomor resi tidak boleh kosong!")
                    elif alasan == "E. Lainnya... (isi sendiri)" and not detail_alasan:
                        st.warning("Detail alasan harus diisi!")
                    else:
                        tz_jkt = pytz.timezone('Asia/Jakarta')
                        waktu_sekarang = datetime.now(tz_jkt)
                        waktu_input = waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S")
                        tanggal_transaksi = waktu_sekarang.strftime("%Y-%m-%d")
                        
                        # Menyimpan ke Google Sheets
                        sheet_resi.append_row([
                            waktu_input, 
                            nama_user, 
                            no_resi, 
                            tanggal_transaksi, 
                            alasan, 
                            detail_alasan
                        ])
                        st.success(f"Resi {no_resi} berhasil disimpan!")
                        
        elif menu == "Riwayat Input Gua":
            st.header("Riwayat Input Lu")
            data_resi = pd.DataFrame(sheet_resi.get_all_records())
            if not data_resi.empty:
                # Filter hanya data milik SCO yang login
                data_pribadi = data_resi[data_resi['NAMA SCO'] == nama_user]
                st.dataframe(data_pribadi, use_container_width=True)
            else:
                st.info("Belum ada data yang diinput.")

    # --- JIKA YANG LOGIN ADALAH ADMIN ---
    elif role_user.upper() == "ADMIN":
        st.header("Dashboard Master Admin")
        
        data_resi = pd.DataFrame(sheet_resi.get_all_records())
        
        if not data_resi.empty:
            # Filter Tanggal
            tanggal_unik = data_resi['TANGGAL TRANSAKSI'].unique().tolist()
            tanggal_unik.insert(0, "Semua Tanggal")
            pilih_tanggal = st.selectbox("Filter Tanggal Transaksi", tanggal_unik)
            
            if pilih_tanggal != "Semua Tanggal":
                data_tampil = data_resi[data_resi['TANGGAL TRANSAKSI'] == pilih_tanggal]
            else:
                data_tampil = data_resi
                
            st.dataframe(data_tampil, use_container_width=True)
            
            # Tombol Download ke CSV
            csv = data_tampil.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Data (CSV)",
                data=csv,
                file_name='data_penolakan.csv',
                mime='text/csv',
            )
        else:
            st.info("Belum ada data resi yang masuk dari SCO.")
