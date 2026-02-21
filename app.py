import streamlit as st
import pandas as pd
from datetime import datetime
import io

# 1. Cấu hình
st.set_page_config(page_title="Football Admin Pro Max", layout="wide")

if 'session_id' not in st.session_state:
    st.session_state.session_id = 0

# 2. Đọc dữ liệu an toàn
def load_data():
    try:
        if 'df_doi' not in st.session_state:
            st.session_state.df_doi = pd.read_csv("Tin - Đội bóng.csv").dropna(subset=['Đội tuyển'])
        if 'df_tran' not in st.session_state:
            df_t = pd.read_csv("Tin - Trận đấu.csv")
            df_t['Vòng'] = df_t['Vòng'].ffill()
            df_t = df_t.dropna(subset=[df_t.columns[4], df_t.columns[7]])
            df_t.iloc[:, 5] = pd.to_numeric(df_t.iloc[:, 5], errors='coerce').fillna(0).astype(int)
            df_t.iloc[:, 6] = pd.to_numeric(df_t.iloc[:, 6], errors='coerce').fillna(0).astype(int)
            st.session_state.df_tran = df_t
    except Exception as e:
        st.error(f"Lỗi đọc file CSV: {e}. Hãy kiểm tra file của bạn.")

load_data()

if 'history' not in st.session_state:
    st.session_state.history = []

def record_history(msg):
    snapshot = {
        'msg': msg, 'time': datetime.now().strftime("%H:%M:%S"),
        'df_doi_snap': st.session_state.df_doi.copy(),
        'df_tran_snap': st.session_state.df_tran.copy()
    }
    st.session_state.history.insert(0, snapshot)
    if len(st.session_state.history) > 10: st.session_state.history.pop()

# 3. Tính BXH chuẩn
def calculate_bxh():
    teams = st.session_state.df_doi['Đội tuyển'].unique()
    bxh = pd.DataFrame(teams, columns=['Đội tuyển'])
    for col in ['Trận', 'Thắng', 'Hòa', 'Thua', 'BT', 'BB', 'HS', 'Điểm']: bxh[col] = 0
    
    for _, r in st.session_state.df_tran.iterrows():
        t1, s1, s2, t2 = r.iloc[4], r.iloc[5], r.iloc[6], r.iloc[7]
        if t1 in teams and t2 in teams:
            for t, sm, so in [(t1, s1, s2), (t2, s2, s1)]:
                idx_matches = bxh[bxh['Đội tuyển'] == t].index
                if not idx_matches.empty:
                    idx = idx_matches[0]
                    bxh.at[idx, 'Trận'] += 1
                    bxh.at[idx, 'BT'] += sm
                    bxh.at[idx, 'BB'] += so
                    if sm > so: bxh.at[idx, 'Thắng'] += 1; bxh.at[idx, 'Điểm'] += 3
                    elif sm == so: bxh.at[idx, 'Hòa'] += 1; bxh.at[idx, 'Điểm'] += 1
                    else: bxh.at[idx, 'Thua'] += 1
    
    bxh['HS'] = bxh['BT'] - bxh['BB']
    bxh = bxh.sort_values(by=['Điểm', 'HS', 'BT'], ascending=False).reset_index(drop=True)
    bxh.index = bxh.index + 1
    bxh.index.name = "STT"
    return bxh

# 4. Giao diện
st.title("🏆 QUẢN LÝ GIẢI ĐẤU BÓNG ĐÁ")
search = st.text_input("🔍 Tìm đội bóng:", key="main_search")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Bảng Xếp Hạng", "📅 Lịch Thi Đấu", "🛠 Cấu Hình Đội", "📜 Khôi Phục"])

with tab1:
    res = calculate_bxh()
    if search:
        res = res[res['Đội tuyển'].str.contains(search, case=False, na=False)]
    st.table(res) # Dùng table để STT hiện rõ ràng nhất

with tab2:
    df_m = st.session_state.df_tran
    if search:
        df_m = df_m[(df_m.iloc[:,4].str.contains(search, case=False, na=False)) | (df_m.iloc[:,7].str.contains(search, case=False, na=False))]
    
    for v in sorted(df_m['Vòng'].unique()):
        with st.expander(f"Vòng {int(v)}", expanded=True):
            v_matches = df_m[df_m['Vòng'] == v]
            for idx, r in v_matches.iterrows():
                c1, sc1, vs, sc2, c2 = st.columns([3,1,0.5,1,3])
                c1.write(f"**{r.iloc[4]}**")
                n1 = sc1.number_input("n1", 0, 100, int(r.iloc[5]), key=f"m1_{idx}_{st.session_state.session_id}", label_visibility="collapsed")
                vs.write("-")
                n2 = sc2.number_input("n2", 0, 100, int(r.iloc[6]), key=f"m2_{idx}_{st.session_state.session_id}", label_visibility="collapsed")
                c2.write(f"**{r.iloc[7]}**")
                
                if n1 != r.iloc[5] or n2 != r.iloc[6]:
                    record_history(f"Sửa điểm Vòng {v}")
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[5]] = n1
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[6]] = n2
                    st.rerun()

with tab3:
    c_add, c_del = st.columns(2)
    with c_add:
        st.subheader("Thêm Đội")
        name = st.text_input("Tên đội:", key="add_name")
        if st.button("Tiếp tục xếp lịch"):
            if name and name not in st.session_state.df_doi['Đội tuyển'].values:
                st.session_state.adding = name
                st.rerun()
        
        if 'adding' in st.session_state:
            st.write(f"Lịch cho **{st.session_state.adding}**:")
            others = st.session_state.df_doi['Đội tuyển'].unique()
            new_rows = []
            for i, op in enumerate(others):
                col_v, col_s1, col_s2 = st.columns([2, 1, 1])
                v_ = col_v.number_input(f"Vòng vs {op}", 1, 100, 1, key=f"v_add_{i}")
                s1_ = col_s1.number_input(f"Bàn {st.session_state.adding}", 0, 100, 0, key=f"s1_add_{i}")
                s2_ = col_s2.number_input(f"Bàn {op}", 0, 100, 0, key=f"s2_add_{i}")
                new_rows.append([v_, None, None, None, st.session_state.adding, s1_, s2_, op])
            
            if st.button("Hoàn tất và Lưu"):
                record_history(f"Thêm đội {st.session_state.adding}")
                st.session_state.df_doi = pd.concat([st.session_state.df_doi, pd.DataFrame([{"Đội tuyển": st.session_state.adding}])], ignore_index=True)
                st.session_state.df_tran = pd.concat([st.session_state.df_tran, pd.DataFrame(new_rows, columns=st.session_state.df_tran.columns)], ignore_index=True)
                del st.session_state.adding
                st.session_state.session_id += 1
                st.rerun()

    with c_del:
        st.subheader("Xóa Đội")
        target = st.selectbox("Chọn đội:", st.session_state.df_doi['Đội tuyển'].tolist(), key="del_sel")
        if st.button("Xác nhận xóa sạch"):
            record_history(f"Xóa đội {target}")
            st.session_state.df_doi = st.session_state.df_doi[st.session_state.df_doi['Đội tuyển'] != target]
            st.session_state.df_tran = st.session_state.df_tran[(st.session_state.df_tran.iloc[:,4] != target) & (st.session_state.df_tran.iloc[:,7] != target)]
            st.rerun()

with tab4:
    st.subheader("Nhật ký")
    for i, item in enumerate(st.session_state.history):
        c_l, c_r = st.columns([7, 3])
        c_l.info(f"{item['time']} - {item['msg']}")
        if c_r.button("Quay lại đây", key=f"rev_{i}"):
            st.session_state.df_doi = item['df_doi_snap'].copy()
            st.session_state.df_tran = item['df_tran_snap'].copy()
            st.session_state.history = st.session_state.history[i+1:]
            st.session_state.session_id += 1
            st.rerun()

