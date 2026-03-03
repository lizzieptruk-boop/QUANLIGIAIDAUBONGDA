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
        # Ép kiểu dữ liệu số ngay từ đầu để tránh lỗi cộng chuỗi
        df_t.iloc[:, 5] = pd.to_numeric(df_t.iloc[:, 5], errors='coerce').fillna(0).astype(int)
        df_t.iloc[:, 6] = pd.to_numeric(df_t.iloc[:, 6], errors='coerce').fillna(0).astype(int)
        st.session_state.df_tran = df_t
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'has_changes' not in st.session_state:
        st.session_state.has_changes = False

load_initial_data()

# --- HÀM HỖ TRỢ (Sửa lỗi logic) ---
def record_history(msg):
    st.session_state.history.insert(0, {
        'msg': msg, 'time': datetime.now().strftime("%H:%M:%S"),
        'df_doi_snap': st.session_state.df_doi.copy(),
        'df_tran_snap': st.session_state.df_tran.copy()
    })

def apply_changes(msg):
    st.session_state.df_doi.to_csv("Tin - Đội bóng.csv", index=False)
    st.session_state.df_tran.to_csv("Tin - Trận đấu.csv", index=False)
    record_history(msg)
    st.session_state.has_changes = False
    st.success(f"✅ Đã lưu: {msg}")

def calculate_bxh(df_doi, df_tran):
    teams = df_doi['Đội tuyển'].unique()
    bxh = pd.DataFrame(teams, columns=['Đội tuyển'])
    for col in ['Trận', 'Thắng', 'Hòa', 'Thua', 'BT', 'BB', 'HS', 'Điểm']: bxh[col] = 0
    
    for _, r in df_tran.iterrows():
        t1, s1, s2, t2 = r.iloc[4], r.iloc[5], r.iloc[6], r.iloc[7]
        # Chỉ tính nếu cả 2 đội đều có tên trong danh sách đội tuyển
        if t1 in teams and t2 in teams:
            for t, sm, so in [(t1, s1, s2), (t2, s2, s1)]:
                idx = bxh[bxh['Đội tuyển'] == t].index[0]
                bxh.at[idx, 'Trận'] += 1
                bxh.at[idx, 'BT'] += int(sm)
                bxh.at[idx, 'BB'] += int(so)
                if sm > so: bxh.at[idx, 'Thắng'] += 1; bxh.at[idx, 'Điểm'] += 3
                elif sm == so: bxh.at[idx, 'Hòa'] += 1; bxh.at[idx, 'Điểm'] += 1
                else: bxh.at[idx, 'Thua'] += 1
    
    bxh['HS'] = bxh['BT'] - bxh['BB']
    return bxh.sort_values(by=['Điểm', 'HS', 'BT'], ascending=False).reset_index(drop=True)

# 3. GIAO DIỆN
st.title("⚽ QUẢN LÝ BÓNG ĐÁ - PHIÊN BẢN ỔN ĐỊNH")

if st.session_state.has_changes:
    st.warning("⚠️ Có thay đổi chưa lưu vào file CSV!")
    if st.button("💾 XÁC NHẬN VÀ LƯU HỆ THỐNG", type="primary", use_container_width=True):
        apply_changes("Cập nhật dữ liệu từ người dùng")
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["📊 Bảng Xếp Hạng", "📅 Lịch Thi Đấu", "🛠 Cấu Hình", "📜 Nhật Ký"])

with tab1:
    c_s, c_a = st.columns([3, 1])
    search = c_s.text_input("🔍 Tìm đội...")
    abc = c_a.checkbox("Sắp xếp A-Z")
    res = calculate_bxh(st.session_state.df_doi, st.session_state.df_tran)
    if search: res = res[res['Đội tuyển'].str.contains(search, case=False)]
    if abc: res = res.sort_values('Đội tuyển')
    st.table(res)

with tab2:
    for v in sorted(st.session_state.df_tran['Vòng'].unique()):
        with st.expander(f"Vòng {int(v)}"):
            matches = st.session_state.df_tran[st.session_state.df_tran['Vòng'] == v]
            for idx, r in matches.iterrows():
                c1, sc1, vs, sc2, c2 = st.columns([3,1,0.5,1,3])
                c1.write(f"**{r.iloc[4]}**")
                n1 = sc1.number_input("n1", 0, 100, int(r.iloc[5]), key=f"s1_{idx}")
                n2 = sc2.number_input("n2", 0, 100, int(r.iloc[6]), key=f"s2_{idx}")
                c2.write(f"**{r.iloc[7]}**")
                if n1 != r.iloc[5] or n2 != r.iloc[6]:
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[5]] = n1
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[6]] = n2
                    st.session_state.has_changes = True

with tab3:
    # PHẦN THÊM ĐỘI (SỬA LỖI ĐIỀN TỈ SỐ)
    st.subheader("➕ Thêm đội & Tỉ số")
    name = st.text_input("Tên đội mới:")
    if st.button("Bước 2: Thiết lập tỉ số"):
        if name and name not in st.session_state.df_doi['Đội tuyển'].values:
            st.session_state.adding_now = name
            st.rerun()

    if 'adding_now' in st.session_state:
        st.info(f"Nhập tỉ số cho {st.session_state.adding_now}")
        new_data = []
        for i, team in enumerate(st.session_state.df_doi['Đội tuyển']):
            c_v, c_s1, c_s2 = st.columns([2, 1, 1])
            v = c_v.number_input(f"Vòng vs {team}", 1, 50, 1, key=f"v_{i}")
            s1 = c_s1.number_input(f"Bàn {st.session_state.adding_now}", 0, 20, 0, key=f"s1_{i}")
            s2 = c_s2.number_input(f"Bàn {team}", 0, 20, 0, key=f"s2_{i}")
            new_data.append([v, "01/01/2026", None, None, st.session_state.adding_now, int(s1), int(s2), team])
        
        if st.button("Hoàn tất thêm đội"):
            st.session_state.df_doi = pd.concat([st.session_state.df_doi, pd.DataFrame([{'Đội tuyển': st.session_state.adding_now}])], ignore_index=True)
            st.session_state.df_tran = pd.concat([st.session_state.df_tran, pd.DataFrame(new_data, columns=st.session_state.df_tran.columns)], ignore_index=True)
            st.session_state.has_changes = True
            del st.session_state.adding_now
            st.rerun()

    st.divider()
    # Đổi tên & Xóa (Giữ nguyên logic cũ)
    t_old = st.selectbox("Chọn đội:", st.session_state.df_doi['Đội tuyển'])
    col_r, col_d = st.columns(2)
    new_t_name = col_r.text_input("Tên thay thế:")
    if col_r.button("Đổi tên"):
        st.session_state.df_doi.replace(t_old, new_t_name, inplace=True)
        st.session_state.df_tran.replace(t_old, new_t_name, inplace=True)
        st.session_state.has_changes = True
        st.rerun()
    if col_d.button("Xóa đội", type="secondary"):
        st.session_state.df_doi = st.session_state.df_doi[st.session_state.df_doi['Đội tuyển'] != t_old]
        st.session_state.df_tran = st.session_state.df_tran[(st.session_state.df_tran.iloc[:,4] != t_old) & (st.session_state.df_tran.iloc[:,7] != t_old)]
        st.session_state.has_changes = True
        st.rerun()

with tab4:
    st.subheader("📜 Nhật ký")
    for i, item in enumerate(st.session_state.history):
        c_m, c_b = st.columns([7, 3])
        c_m.write(f"[{item['time']}] {item['msg']}")
        if c_b.button("Khôi phục", key=f"h_{i}"):
            st.session_state.df_doi = item['df_doi_snap'].copy()
            st.session_state.df_tran = item['df_tran_snap'].copy()
            apply_changes("Khôi phục lịch sử")
            st.rerun()
