import streamlit as st
import pandas as pd

st.set_page_config(page_title="Office Supplies Manager", page_icon="📦", layout="wide")

# --- Inisialisasi data di session_state ---
if "stok" not in st.session_state:
    st.session_state.stok = pd.DataFrame({
        "Nama Barang": ["Pulpen", "Buku Tulis", "Stapler", "Kertas A4", "Spidol"],
        "Stok": [50, 30, 10, 100, 20]
    })

if "requests" not in st.session_state:
    st.session_state.requests = []  # list of pending requests

if "history" not in st.session_state:
    st.session_state.history = []  # list of confirmed transactions

st.markdown(
    "<h1 style='color:#2C3E50; text-align:center;'>📦 Office Supplies Manager</h1>", 
    unsafe_allow_html=True
)

tabs = st.tabs(["📝 Form Request", "🛠️ Admin Panel", "📊 Stok Barang", "📚 History Transaksi"])

# --- TAB FORM REQUEST ---
with tabs[0]:
    st.subheader("Form Request Karyawan")
    with st.form("form_request"):
        nama = st.text_input("Nama", "")
        departemen = st.text_input("Departemen", "")

        st.write("Daftar Barang yang diminta:")
        barang_list = []
        for i in range(3):  # contoh: max 3 item per request
            col1, col2 = st.columns([2,1])
            with col1:
                item = st.selectbox(f"Pilih Barang {i+1}", ["-"] + st.session_state.stok["Nama Barang"].tolist(), key=f"item_{i}")
            with col2:
                jumlah = st.number_input(f"Jumlah {i+1}", min_value=0, step=1, key=f"jumlah_{i}")
            
            if item != "-" and jumlah > 0:
                barang_list.append((item, jumlah))

        submitted = st.form_submit_button("Kirim Request")

        if submitted:
            if nama and departemen and barang_list:
                st.session_state.requests.append({
                    "Nama": nama,
                    "Departemen": departemen,
                    "Barang": barang_list,
                    "Status": "Menunggu Konfirmasi"
                })
                st.success("Request berhasil dikirim!")
            else:
                st.error("Mohon isi semua data dan pilih minimal 1 barang.")

# --- TAB ADMIN PANEL ---
with tabs[1]:
    st.subheader("Admin Panel - Konfirmasi Request")
    
    if not st.session_state.requests:
        st.info("Belum ada request masuk.")
    else:
        for idx, req in enumerate(st.session_state.requests):
            with st.expander(f"{req['Nama']} - {req['Departemen']} | Status: {req['Status']}"):
                st.write("**Detail Barang Diminta:**")
                for item, qty in req["Barang"]:
                    st.write(f"- {item} : {qty}")
                
                if req["Status"] == "Menunggu Konfirmasi":
                    confirm = st.button(f"Konfirmasi Request #{idx+1}", key=f"confirm_{idx}")
                    if confirm:
                        # cek stok
                        stok_cukup = True
                        for item, qty in req["Barang"]:
                            stok_tersedia = st.session_state.stok.loc[
                                st.session_state.stok["Nama Barang"] == item, "Stok"
                            ].values[0]
                            if qty > stok_tersedia:
                                stok_cukup = False
                                st.error(f"Stok {item} tidak cukup.")
                                break
                        
                        if stok_cukup:
                            # kurangi stok
                            for item, qty in req["Barang"]:
                                idx_stok = st.session_state.stok[
                                    st.session_state.stok["Nama Barang"] == item
                                ].index[0]
                                st.session_state.stok.at[idx_stok, "Stok"] -= qty
                            
                            # ubah status dan simpan ke history
                            req["Status"] = "Dikonfirmasi"
                            st.session_state.history.append(req)
                            st.success("Request berhasil dikonfirmasi & stok terupdate!")

# --- TAB STOK BARANG ---
with tabs[2]:
    st.subheader("Stok Barang Tersedia")
    st.dataframe(st.session_state.stok, use_container_width=True)

# --- TAB HISTORY TRANSAKSI ---
with tabs[3]:
    st.subheader("History Transaksi")
    if not st.session_state.history:
        st.info("Belum ada transaksi tercatat.")
    else:
        history_data = []
        for h in st.session_state.history:
            for item, qty in h["Barang"]:
                history_data.append({
                    "Nama": h["Nama"],
                    "Departemen": h["Departemen"],
                    "Barang": item,
                    "Jumlah": qty,
                    "Status": h["Status"]
                })
        df_history = pd.DataFrame(history_data)
        st.dataframe(df_history, use_container_width=True)
