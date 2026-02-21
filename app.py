import streamlit as st
import pandas as pd
from datetime import datetime
import io

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Football Admin Final Pro", layout="wide")

if 'session_id' not in st.session_state:
    st.session_state.session_id = 0

# 2. KHỞI TẠO DỮ LIỆU
if 'df_doi' not in st.session_state:
    st.session_state.df_doi = pd.read_csv("Tin - Đội bóng.csv").dropna(subset=['Đội tuyển'])
if 'df_tran' not in st.session_state:
    df_t = pd.read_csv("Tin - Trận đấu.csv")
    df_t['Vòng'] = df_t['Vòng'].ffill()
    df_t = df_t.dropna(subset=[df_t.columns[4], df_t.columns[7]])
    df_t.iloc[:, 5] = pd.to_numeric(df_t.iloc[:, 5], errors='coerce').fillna(0).astype(int)
    df_t.iloc[:, 6] = pd.to_numeric(df_t.iloc[:, 6], errors='coerce').fillna(0).astype(int)
    st.session_state.df_tran = df_t
if 'history' not in st.session_state:
    st.session_state.history = []

# --- HÀM LƯU LỊCH SỬ ---
def record_history(msg):
    snapshot = {
        'msg': msg,
        'time': datetime.now().strftime("%H:%M:%S"),
        'df_doi_snap': st.session_state.df_doi.copy(),
        'df_tran_snap': st.session_state.df_tran.copy()
    }
    st.session_state.history.insert(0, snapshot)
    if len(st.session_state.history) > 20: st.session_state.history.pop()

# 3. BỘ NÃO TÍNH TOÁN BXH (STT từ 1, HS = BT-BB)
def calculate_bxh():
    teams = st.session_state.df_doi['Đội tuyển'].unique()
    bxh = pd.DataFrame(teams, columns=['Đội tuyển'])
    for col in ['Trận', 'Thắng', 'Hòa', 'Thua', 'BT', 'BB', 'HS', 'Điểm']: bxh[col] = 0
    
    for _, r in st.session_state.df_tran.iterrows():
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
    bxh.index = bxh.index + 1  # Bắt đầu STT từ 1
    bxh.index.name = "STT"
    return bxh

# 4. GIAO DIỆN
st.title("⚽ HỆ THỐNG QUẢN LÝ GIẢI ĐẤU TOÀN DIỆN")
search = st.text_input("🔍 Tra cứu đội bóng:", placeholder="Nhập tên đội...")

tab1, tab2, tab3, tab4 = st.tabs(["📊 BXH", "📅 TRẬN ĐẤU", "🛠 QUẢN LÝ", "📜 LỊCH SỬ"])

with tab1:
    df_res = calculate_bxh()
    if search:
        df_res = df_res[df_res['Đội tuyển'].str.contains(search, case=False, na=False)]
    st.dataframe(df_res, use_container_width=True)
    
    # Nút Download Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_res.to_excel(writer, sheet_name='BXH')
    st.download_button("📥 Tải BXH Excel", buffer.getvalue(), "BXH_Pro.xlsx")

with tab2:
    df_matches = st.session_state.df_tran
    if search:
        df_matches = df_matches[(df_matches.iloc[:,4].str.contains(search, case=False, na=False)) | (df_matches.iloc[:,7].str.contains(search, case=False, na=False))]
    
    for v in sorted(df_matches['Vòng'].unique()):
        with st.expander(f"Vòng {int(v)}", expanded=True):
            for idx, r in df_matches[df_matches['Vòng'] == v].iterrows():
                c1, sc1, vs, sc2, c2 = st.columns([3,1,0.5,1,3])
                with c1: st.write(f"**{r.iloc[4]}**")
                with sc1: ns1 = st.number_input("", value=int(r.iloc[5]), key=f"s1_{idx}_{st.session_state.session_id}", step=1, label_visibility="collapsed")
                with vs: st.write("-")
                with sc2: ns2 = st.number_input("", value=int(r.iloc[6]), key=f"s2_{idx}_{st.session_state.session_id}", step=1, label_visibility="collapsed")
                with c2: st.write(f"**{r.iloc[7]}**")
                
                if ns1 != r.iloc[5] or ns2 != r.iloc[6]:
                    record_history(f"Sửa Vòng {int(v)}: {r.iloc[4]} vs {r.iloc[7]}")
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[5]] = ns1
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[6]] = ns2
                    st.rerun()

with tab3:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("➕ Thêm Đội & Xếp Vòng")
        new_name = st.text_input("Tên đội mới:", key=f"add_in_{st.session_state.session_id}")
        if st.button("Bước 1: Tạo đội"):
            if new_name and new_name not in st.session_state.df_doi['Đội tuyển'].values:
                st.session_state.temp_team = new_name
                st.rerun()

        if 'temp_team' in st.session_state:
            st.info(f"Đang xếp lịch cho: **{st.session_state.temp_team}**")
            others = st.session_state.df_doi['Đội tuyển'].unique()
            new_data = []
            for i, opp in enumerate(others):
                st.write(f"Trận với **{opp}**")
                cv, cs1, cvs, cs2 = st.columns([2.5, 1, 0.5, 1])
                v_val = cv.number_input(f"Chọn Vòng thứ mấy cho {opp}", 1, 100, value=1, key=f"v_set_{i}")
                s1_v = cs1.number_input(f"Bàn {st.session_state.temp_team}", 0, key=f"s1_set_{i}")
                s2_v = cs2.number_input(f"Bàn {opp}", 0, key=f"s2_set_{i}")
                new_data.append([v_val, None, None, None, st.session_state.temp_team, s1_v, s2_v, opp])
                st.divider()
            
            if st.button("BƯỚC 2: LƯU LỊCH THI ĐẤU"):
                record_history(f"Thêm đội {st.session_state.temp_team}")
                st.session_state.df_doi = pd.concat([st.session_state.df_doi, pd.DataFrame([{"Đội tuyển": st.session_state.temp_team}])], ignore_index=True)
                st.session_state.df_tran = pd.concat([st.session_state.df_tran, pd.DataFrame(new_data, columns=st.session_state.df_tran.columns)], ignore_index=True)
                del st.session_state.temp_team
                st.session_state.session_id += 1
                st.rerun()

    with col_b:
        st.subheader("🗑️ Xóa Đội")
        target = st.selectbox("Chọn đội:", st.session_state.df_doi['Đội tuyển'].tolist(), key=f"del_s_{st.session_state.session_id}")
        if st.button("Xác nhận Xóa"):
            record_history(f"Xóa đội: {target}")
            st.session_state.df_doi = st.session_state.df_doi[st.session_state.df_doi['Đội tuyển'] != target]
            st.session_state.df_tran = st.session_state.df_tran[(st.session_state.df_tran.iloc[:,4] != target) & (st.session_state.df_tran.iloc[:,7] != target)]
            st.rerun()

with tab4:
    st.subheader("📜 Nhật ký Recover")
    if not st.session_state.history: st.write("Trống.")
    for i, item in enumerate(st.session_state.history):
        c_t, c_b = st.columns([7, 3])
        c_t.warning(f"🕒 {item['time']} - {item['msg']}")
        if c_b.button("♻️ PHỤC HỒI", key=f"rec_{i}"):
            st.session_state.df_doi = item['df_doi_snap'].copy()
            st.session_state.df_tran = item['df_tran_snap'].copy()
            st.session_state.history = st.session_state.history[i+1:]
            st.session_state.session_id += 1
            st.rerun()
