import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CẤU HÌNH
st.set_page_config(page_title="Football Admin Pro", layout="wide")

# 2. KHỞI TẠO DỮ LIỆU
def load_initial_data():
    if 'df_doi' not in st.session_state:
        st.session_state.df_doi = pd.read_csv("Tin - Đội bóng.csv").dropna(subset=['Đội tuyển'])
    if 'df_tran' not in st.session_state:
        df_t = pd.read_csv("Tin - Trận đấu.csv")
        df_t['Vòng'] = df_t['Vòng'].ffill()
        df_t = df_t.dropna(subset=[df_t.columns[4], df_t.columns[7]])
        # Chuyển đổi tỷ số sang kiểu số
        df_t.iloc[:, 5] = pd.to_numeric(df_t.iloc[:, 5], errors='coerce').fillna(0).astype(int)
        df_t.iloc[:, 6] = pd.to_numeric(df_t.iloc[:, 6], errors='coerce').fillna(0).astype(int)
        st.session_state.df_tran = df_t
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'has_changes' not in st.session_state:
        st.session_state.has_changes = False

load_initial_data()

# --- CÁC HÀM HỖ TRỢ ---
def record_history(msg):
    snapshot = {
        'msg': msg, 'time': datetime.now().strftime("%H:%M:%S"),
        'df_doi_snap': st.session_state.df_doi.copy(),
        'df_tran_snap': st.session_state.df_tran.copy()
    }
    st.session_state.history.insert(0, snapshot)

def apply_changes(msg="Cập nhật dữ liệu"):
    # Ghi đè trực tiếp vào file CSV
    st.session_state.df_doi.to_csv("Tin - Đội bóng.csv", index=False)
    st.session_state.df_tran.to_csv("Tin - Trận đấu.csv", index=False)
    record_history(msg)
    st.session_state.has_changes = False
    st.success(f"✅ Đã lưu thành công: {msg}")

def calculate_bxh(df_doi, df_tran):
    teams = df_doi['Đội tuyển'].unique()
    bxh = pd.DataFrame(teams, columns=['Đội tuyển'])
    for col in ['Trận', 'Thắng', 'Hòa', 'Thua', 'BT', 'BB', 'HS', 'Điểm']: bxh[col] = 0
    
    for _, r in df_tran.iterrows():
        t1, s1, s2, t2 = r.iloc[4], r.iloc[5], r.iloc[6], r.iloc[7]
        if t1 in teams and t2 in teams:
            for t, sm, so in [(t1, s1, s2), (t2, s2, s1)]:
                idx = bxh[bxh['Đội tuyển'] == t].index[0]
                bxh.at[idx, 'Trận'] += 1
                bxh.at[idx, 'BT'] += sm
                bxh.at[idx, 'BB'] += so
                if sm > so: bxh.at[idx, 'Thắng'] += 1; bxh.at[idx, 'Điểm'] += 3
                elif sm == so: bxh.at[idx, 'Hòa'] += 1; bxh.at[idx, 'Điểm'] += 1
                else: bxh.at[idx, 'Thua'] += 1
    
    bxh['HS'] = bxh['BT'] - bxh['BB']
    bxh = bxh.sort_values(by=['Điểm', 'HS', 'BT'], ascending=False).reset_index(drop=True)
    bxh.index = bxh.index + 1
    return bxh

# 3. GIAO DIỆN CHÍNH
st.title("⚽ QUẢN LÝ BÓNG ĐÁ - PHIÊN BẢN TỔNG HỢP")

# Nút xác nhận tổng (Chỉ hiện khi có thay đổi)
if st.session_state.has_changes:
    st.warning("⚠️ Bạn có thay đổi chưa được lưu vào file CSV!")
    if st.button("💾 XÁC NHẬN VÀ GHI ĐÈ FILE HỆ THỐNG", type="primary", use_container_width=True):
        apply_changes("Người dùng xác nhận lưu thay đổi")
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["📊 Bảng Xếp Hạng", "📅 Lịch Thi Đấu", "🛠 Cấu Hình Đội", "📜 Nhật Ký"])

with tab1:
    col_s, col_abc = st.columns([3, 1])
    search = col_s.text_input("🔍 Tìm kiếm tên đội bóng...")
    abc = col_abc.checkbox("Sắp xếp tên A-Z")
    
    res = calculate_bxh(st.session_state.df_doi, st.session_state.df_tran)
    if search:
        res = res[res['Đội tuyển'].str.contains(search, case=False)]
    if abc:
        res = res.sort_values(by='Đội tuyển')
    st.table(res)

with tab2:
    st.subheader("Chỉnh sửa tỷ số trực tiếp (Nhấn 'Xác nhận' phía trên để lưu vĩnh viễn)")
    for v in sorted(st.session_state.df_tran['Vòng'].unique()):
        with st.expander(f"Vòng {int(v)}"):
            matches = st.session_state.df_tran[st.session_state.df_tran['Vòng'] == v]
            for idx, r in matches.iterrows():
                c1, sc1, vs, sc2, c2 = st.columns([3,1,0.5,1,3])
                c1.write(f"**{r.iloc[4]}**")
                n1 = sc1.number_input("n1", 0, 100, int(r.iloc[5]), key=f"s1_{idx}", label_visibility="collapsed")
                vs.write("-")
                n2 = sc2.number_input("n2", 0, 100, int(r.iloc[6]), key=f"s2_{idx}", label_visibility="collapsed")
                c2.write(f"**{r.iloc[7]}**")
                
                if n1 != r.iloc[5] or n2 != r.iloc[6]:
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[5]] = n1
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[6]] = n2
                    st.session_state.has_changes = True

with tab3:
    # Đổi tên đội
    st.subheader("
