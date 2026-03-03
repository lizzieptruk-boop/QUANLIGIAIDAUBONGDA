import streamlit as st
import pandas as pd
from datetime import datetime
from unidecode import unidecode 

# 1. KHỞI TẠO DỮ LIỆU
if 'df_doi' not in st.session_state:
    st.session_state.df_doi = pd.read_csv("Tin - Đội bóng.csv")
    st.session_state.df_tran = pd.read_csv("Tin - Trận đấu.csv")
    st.session_state.history = []

# 2. HÀM TÌM KIẾM (Không dấu)
def search_engine(df, query):
    if not query: return df
    # So sánh không dấu và chữ thường
    return df[df['Đội tuyển'].apply(lambda x: unidecode(query.lower()) in unidecode(str(x)).lower())]

# 3. GIAO DIỆN CHÍNH
st.title("⚽ QUẢN LÝ BÓNG ĐÁ - PHIÊN BẢN CHUẨN")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Bảng Xếp Hạng", "📅 Lịch Thi Đấu", "🛠 Cấu Hình", "📜 Nhật Ký"])

with tab1:
    search = st.text_input("🔍 Tìm kiếm đội (hỗ trợ không dấu)...")
    st.table(search_engine(st.session_state.df_doi, search))

with tab2:
    # Sửa lỗi Duplicate bằng cách gắn key theo index của dòng
    for idx, row in st.session_state.df_tran.iterrows():
        c1, s1, s2, c2 = st.columns([2, 1, 1, 2])
        c1.write(row.iloc[4])
        # KEY DUY NHẤT: kết hợp 'tran' và 'idx' (chỉ số dòng)
        n1 = s1.number_input("n1", value=int(row.iloc[5]), key=f"t1_{idx}", label_visibility="collapsed")
        n2 = s2.number_input("n2", value=int(row.iloc[6]), key=f"t2_{idx}", label_visibility="collapsed")
        c2.write(row.iloc[7])
        
        if n1 != row.iloc[5] or n2 != row.iloc[6]:
            st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[5]] = n1
            st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[6]] = n2

with tab3:
    st.subheader("➕ Thêm đội mới")
    new_team = st.text_input("Tên đội:", key="new_team_input")
    if st.button("Bắt đầu điền lịch"): 
        st.session_state.adding = new_team
        st.rerun()
    
    if 'adding' in st.session_state:
        st.write(f"Đang nhập tỉ số cho: {st.session_state.adding}")
        # KEY DUY NHẤT: kết hợp 'adding' và 'i'
        for i, team in enumerate(st.session_state.df_doi['Đội tuyển']):
            c_v, c_s1, c_s2 = st.columns(3)
            v = c_v.number_input(f"Vòng vs {team}", 1, 20, 1, key=f"v_{i}")
            b1 = c_s1.number_input(f"Bàn {st.session_state.adding}", 0, 10, 0, key=f"b1_{i}")
            b2 = c_s2.number_input(f"Bàn {team}", 0, 10, 0, key=f"b2_{i}")
            
        if st.button("Xác nhận lưu đội"):
            st.session_state.df_doi = pd.concat([st.session_state.df_doi, pd.DataFrame([{'Đội tuyển': st.session_state.adding}])], ignore_index=True)
            st.session_state.history.append(f"Đã thêm: {st.session_state.adding} lúc {datetime.now().strftime('%H:%M')}")
            del st.session_state.adding
            st.rerun()

with tab4:
    for log in st.session_state.history: 
        st.info(log)
