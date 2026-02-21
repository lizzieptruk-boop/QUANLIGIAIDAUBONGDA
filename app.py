import streamlit as st
import pandas as pd
from datetime import datetime
import io

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Football Admin Pro", layout="wide")

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

def record_history(msg):
    snapshot = {
        'msg': msg,
        'time': datetime.now().strftime("%H:%M:%S"),
        'df_doi_snap': st.session_state.df_doi.copy(),
        'df_tran_snap': st.session_state.df_tran.copy()
    }
    st.session_state.history.insert(0, snapshot)

# 3. BỘ NÃO TÍNH TOÁN (FIX HS & STT)
def calculate_bxh():
    teams = st.session_state.df_doi['Đội tuyển'].unique()
    bxh = pd.DataFrame(teams, columns=['Đội tuyển'])
    for col in ['Trận', 'Thắng', 'Hòa', 'Thua', 'BT', 'BB', 'HS', 'Điểm']:
        bxh[col] = 0
    
    for _, r in st.session_state.df_tran.iterrows():
        t1, s1, s2, t2 = r.iloc[4], r.iloc[5], r.iloc[6], r.iloc[7]
        if t1 in teams and t2 in teams:
            idx1 = bxh[bxh['Đội tuyển'] == t1].index[0]
            idx2 = bxh[bxh['Đội tuyển'] == t2].index[0]
            
            bxh.at[idx1, 'Trận'] += 1
            bxh.at[idx1, 'BT'] += s1
            bxh.at[idx1, 'BB'] += s2
            
            bxh.at[idx2, 'Trận'] += 1
            bxh.at[idx2, 'BT'] += s2
            bxh.at[idx2, 'BB'] += s1
            
            if s1 > s2:
                bxh.at[idx1, 'Thắng'] += 1; bxh.at[idx1, 'Điểm'] += 3
                bxh.at[idx2, 'Thua'] += 1
            elif s1 == s2:
                bxh.at[idx1, 'Hòa'] += 1; bxh.at[idx1, 'Điểm'] += 1
                bxh.at[idx2, 'Hòa'] += 1; bxh.at[idx2, 'Điểm'] += 1
            else:
                bxh.at[idx2, 'Thắng'] += 1; bxh.at[idx2, 'Điểm'] += 3
                bxh.at[idx1, 'Thua'] += 1

    # TÍNH HỆ SỐ CHUẨN: HS = BT - BB
    bxh['HS'] = bxh['BT'] - bxh['BB']
    
    # Sắp xếp
    bxh = bxh.sort_values(by=['Điểm', 'HS', 'BT'], ascending=False).reset_index(drop=True)
    
    # ĐỔI SỐ THỨ TỰ BẮT ĐẦU TỪ 1
    bxh.index = bxh.index + 1
    return bxh

# 4. GIAO DIỆN
st.title("🏆 QUẢN LÝ GIẢI ĐẤU - HOÀN THIỆN HS & STT")

tab1, tab2, tab3, tab4 = st.tabs(["📊 BXH", "📅 TRẬN ĐẤU", "🛠 QUẢN LÝ", "📜 LỊCH SỬ"])

with tab1:
    res_bxh = calculate_bxh()
    # Hiển thị index (STT) rõ ràng
    st.dataframe(res_bxh, use_container_width=True)
    
    # Nút Export Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        res_bxh.to_excel(writer, sheet_name='BXH')
    st.download_button(label="📥 Tải BXH Excel", data=buffer.getvalue(), file_name="BXH_Final.xlsx")

# --- TAB 2, 3, 4 giữ nguyên logic đã tối ưu ở các phiên bản trước ---
with tab2:
    df_matches = st.session_state.df_tran
    for v in sorted(df_matches['Vòng'].unique()):
        with st.expander(f"Vòng {int(v)}", expanded=True):
            for idx, r in df_matches[df_matches['Vòng'] == v].iterrows():
                c1, sc1, vs, sc2, c2 = st.columns([3,1,0.5,1,3])
                with c1: st.write(f"**{r.iloc[4]}**")
                with sc1: n1 = st.number_input("", value=int(r.iloc[5]), key=f"s1_{idx}_{st.session_state.session_id}", step=1, label_visibility="collapsed")
                with vs: st.write("-")
                with sc2: n2 = st.number_input("", value=int(r.iloc[6]), key=f"s2_{idx}_{st.session_state.session_id}", step=1, label_visibility="collapsed")
                with c2: st.write(f"**{r.iloc[7]}**")
                if n1 != r.iloc[5] or n2 != r.iloc[6]:
                    record_history(f"Sửa Vòng {int(v)}: {r.iloc[4]} vs {r.iloc[7]}")
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[5]] = n1
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[6]] = n2
                    st.rerun()

with tab3:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("➕ Thêm Đội")
        new_name = st.text_input("Tên đội:", key=f"add_t_{st.session_state.session_id}")
        if st.button("Tạo đội"):
            if new_name and new_name not in st.session_state.df_doi['Đội tuyển'].values:
                st.session_state.temp_team = new_name
                st.rerun()
        if 'temp_team' in st.session_state:
            st.warning(f"Thiết lập vòng đấu cho {st.session_state.temp_team}")
            others = st.session_state.df_doi['Đội tuyển'].unique()
            new_data = []
            for i, opp in enumerate(others):
                cv, cs1, cvs, cs2 = st.columns([2,1,0.5,1])
                v_val = cv.number_input(f"Vòng cho {opp}", 1, value=1, key=f"v_{i}")
                s1 = cs1.number_input(f"Bàn {st.session_state.temp_team}", 0, key=f"s1_{i}")
                s2 = cs2.number_input(f"Bàn {opp}", 0, key=f"s2_{i}")
                new_data.append([v_val, None, None, None, st.session_state.temp_team, s1, s2, opp])
            if st.button("LƯU TẤT CẢ"):
                record_history(f"Thêm đội {st.session_state.temp_team}")
                st.session_state.df_doi = pd.concat([st.session_state.df_doi, pd.DataFrame([{"Đội tuyển": st.session_state.temp_team}])], ignore_index=True)
                st.session_state.df_tran = pd.concat([st.session_state.df_tran, pd.DataFrame(new_data, columns=st.session_state.df_tran.columns)], ignore_index=True)
                del st.session_state.temp_team
                st.session_state.session_id += 1
                st.rerun()

    with col_b:
        st.subheader("🗑️ Xóa Đội")
        target = st.selectbox("Chọn đội:", st.session_state.df_doi['Đội tuyển'].tolist(), key=f"del_{st.session_state.session_id}")
        if st.button("Xác nhận Xóa"):
            record_history(f"Xóa đội: {target}")
            st.session_state.df_doi = st.session_state.df_doi[st.session_state.df_doi['Đội tuyển'] != target]
            st.session_state.df_tran = st.session_state.df_tran[(st.session_state.df_tran.iloc[:,4] != target) & (st.session_state.df_tran.iloc[:,7] != target)]
            st.rerun()

with tab4:
    st.subheader("📜 Lịch sử")
    for i, item in enumerate(st.session_state.history):
        c_t, c_b = st.columns([8, 2])
        c_t.write(f"🕒 {item['time']} - {item['msg']}")
        if c_b.button("Recover", key=f"rec_{i}"):
            st.session_state.df_doi = item['df_doi_snap'].copy()
            st.session_state.df_tran = item['df_tran_snap'].copy()
            st.session_state.history = st.session_state.history[i+1:]
            st.session_id += 1
            st.rerun()