import streamlit as st
import pandas as pd
from datetime import datetime
import io

# 1. CẤU HÌNH & KHỞI TẠO
st.set_page_config(page_title="Football Admin Optimized", layout="wide")

if 'session_id' not in st.session_state:
    st.session_state.session_id = 0

def load_data():
    if 'df_doi' not in st.session_state:
        st.session_state.df_doi = pd.read_csv("Tin - Đội bóng.csv").dropna(subset=['Đội tuyển'])
    if 'df_tran' not in st.session_state:
        df_t = pd.read_csv("Tin - Trận đấu.csv")
        df_t['Vòng'] = df_t['Vòng'].ffill()
        df_t = df_t.dropna(subset=[df_t.columns[4], df_t.columns[7]])
        for i in [5, 6]: df_t.iloc[:, i] = pd.to_numeric(df_t.iloc[:, i], errors='coerce').fillna(0).astype(int)
        st.session_state.df_tran = df_t
    
    # Khởi tạo bản Nháp (Draft)
    if 'draft_doi' not in st.session_state: st.session_state.draft_doi = st.session_state.df_doi.copy()
    if 'draft_tran' not in st.session_state: st.session_state.draft_tran = st.session_state.df_tran.copy()
    if 'change_flag' not in st.session_state: st.session_state.change_flag = False

load_data()

# 2. HÀM TÍNH BXH
def calculate_bxh(df_d, df_t):
    teams = sorted(df_d['Đội tuyển'].unique()) # Sắp xếp ABC cho danh sách đội
    bxh = pd.DataFrame(teams, columns=['Đội tuyển'])
    for col in ['Trận', 'Thắng', 'Hòa', 'Thua', 'BT', 'BB', 'HS', 'Điểm']: bxh[col] = 0
    
    for _, r in df_t.iterrows():
        t1, s1, s2, t2 = r.iloc[4], r.iloc[5], r.iloc[6], r.iloc[7]
        if t1 in teams and t2 in teams:
            for t, sm, so in [(t1, s1, s2), (t2, s2, s1)]:
                idx = bxh[bxh['Đội tuyển'] == t].index[0]
                bxh.at[idx, 'Trận'] += 1
                bxh.at[idx, 'BT'] += sm; bxh.at[idx, 'BB'] += so
                if sm > so: bxh.at[idx, 'Thắng'] += 1; bxh.at[idx, 'Điểm'] += 3
                elif sm == so: bxh.at[idx, 'Hòa'] += 1; bxh.at[idx, 'Điểm'] += 1
                else: bxh.at[idx, 'Thua'] += 1
    bxh['HS'] = bxh['BT'] - bxh['BB']
    bxh = bxh.sort_values(by=['Điểm', 'HS', 'BT'], ascending=False).reset_index(drop=True)
    bxh.index = bxh.index + 1
    return bxh

# 3. GIAO DIỆN CHÍNH
st.title("⚽ QUẢN LÝ GIẢI ĐẤU - TỐI ƯU")

# THANH XÁC NHẬN TỔNG (CHỈ XUẤT HIỆN KHI CÓ THAY ĐỔI)
if st.session_state.change_flag:
    c1, c2 = st.columns([4, 1])
    c1.warning("🔔 Bạn đang có thay đổi trong bản nháp chưa lưu vào hệ thống!")
    if c1.button("💾 XÁC NHẬN LƯU TẤT CẢ", type="primary", use_container_width=True):
        st.session_state.df_doi = st.session_state.draft_doi.copy()
        st.session_state.df_tran = st.session_state.draft_tran.copy()
        st.session_state.change_flag = False
        st.rerun()
    if c2.button("🗑️ HỦY NHÁP", use_container_width=True):
        st.session_state.draft_doi = st.session_state.df_doi.copy()
        st.session_state.draft_tran = st.session_state.df_tran.copy()
        st.session_state.change_flag = False
        st.rerun()

search = st.text_input("🔍 Tìm kiếm đội bóng (áp dụng cho cả BXH và Lịch đấu):")

tab1, tab2, tab3 = st.tabs(["📊 BXH CHÍNH THỨC", "📅 SỬA LỊCH ĐẤU", "🛠 CẤU HÌNH ĐỘI"])

with tab1:
    res = calculate_bxh(st.session_state.df_doi, st.session_state.df_tran)
    if search: res = res[res['Đội tuyển'].str.contains(search, case=False)]
    st.table(res)

with tab2:
    st.subheader("Chỉnh sửa tỷ số trực tiếp")
    df_m = st.session_state.draft_tran
    if search: df_m = df_m[(df_m.iloc[:,4].str.contains(search, case=False)) | (df_m.iloc[:,7].str.contains(search, case=False))]
    
    for v in sorted(df_m['Vòng'].unique()):
        with st.expander(f"Vòng {int(v)}"):
            for idx, r in df_m[df_m['Vòng'] == v].iterrows():
                col1, sc1, vs, sc2, col2 = st.columns([3,1,0.5,1,3])
                col1.write(f"**{r.iloc[4]}**")
                n1 = sc1.number_input("n1", 0, 100, int(r.iloc[5]), key=f"n1_{idx}_{st.session_state.session_id}", label_visibility="collapsed")
                vs.write("-")
                n2 = sc2.number_input("n2", 0, 100, int(r.iloc[6]), key=f"n2_{idx}_{st.session_state.session_id}", label_visibility="collapsed")
                col2.write(f"**{r.iloc[7]}**")
                if n1 != r.iloc[5] or n2 != r.iloc[6]:
                    st.session_state.draft_tran.at[idx, st.session_state.draft_tran.columns[5]] = n1
                    st.session_state.draft_tran.at[idx, st.session_state.draft_tran.columns[6]] = n2
                    st.session_state.change_flag = True

with tab3:
    # ABC Sắp xếp danh sách chọn đội
    all_teams_abc = sorted(st.session_state.draft_doi['Đội tuyển'].tolist())
    
    st.subheader("📝 Đổi tên / 🗑️ Xóa đội")
    c_sel, c_edit, c_btn = st.columns([3,3,2])
    t_old = c_sel.selectbox("Chọn đội:", all_teams_abc, key="sel_abc")
    t_new = c_edit.text_input("Tên mới (để trống nếu muốn Xóa):")
    
    if c_btn.button("Thực hiện thay đổi nháp"):
        st.session_state.change_flag = True
        if not t_new: # XÓA ĐỘI
            st.session_state.draft_doi = st.session_state.draft_doi[st.session_state.draft_doi['Đội tuyển'] != t_old]
            st.session_state.draft_tran = st.session_state.draft_tran[(st.session_state.draft_tran.iloc[:,4] != t_old) & (st.session_state.draft_tran.iloc[:,7] != t_old)]
        else: # ĐỔI TÊN
            st.session_state.draft_doi['Đội tuyển'] = st.session_state.draft_doi['Đội tuyển'].replace(t_old, t_new)
            for i in [4, 7]: st.session_state.draft_tran.iloc[:, i] = st.session_state.draft_tran.iloc[:, i].replace(t_old, t_new)
        st.rerun()

    st.divider()
    st.subheader("➕ Thêm đội mới")
    new_team = st.text_input("Tên đội mới:")
    if st.button("Tạo lịch đấu nháp cho đội này"):
        if new_team and new_team not in all_teams_abc:
            st.session_state.adding_now = new_team
            st.rerun()
    
    if 'adding_now' in st.session_state:
        st.info(f"Soạn lịch cho {st.session_state.adding_now}")
        new_matches = []
        for i, op in enumerate(all_teams_abc):
            cv, cs1, cs2 = st.columns([2, 1, 1])
            v_ = cv.number_input(f"Vòng vs {op}", 1, 100, 1, key=f"v_{i}")
            s1_ = cs1.number_input(f"Bàn {st.session_state.adding_now}", 0, 100, 0, key=f"s1_{i}")
            s2_ = cs2.number_input(f"Bàn {op}", 0, 100, 0, key=f"s2_{i}")
            new_matches.append([v_, None, None, None, st.session_state.adding_now, s1_, s2_, op])
        
        if st.button("Lưu vào bản nháp"):
            st.session_state.draft_doi = pd.concat([st.session_state.draft_doi, pd.DataFrame([{"Đội tuyển": st.session_state.adding_now}])], ignore_index=True)
            st.session_state.draft_tran = pd.concat([st.session_state.draft_tran, pd.DataFrame(new_matches, columns=st.session_state.draft_tran.columns)], ignore_index=True)
            st.session_state.change_flag = True
            del st.session_state.adding_now
            st.rerun()
