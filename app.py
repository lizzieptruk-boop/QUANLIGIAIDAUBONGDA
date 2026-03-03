import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime

# --- CẤU HÌNH & HỖ TRỢ ---
st.set_page_config(page_title="Football Admin Pro", layout="wide")

def remove_accents(input_str):
    s = unicodedata.normalize('NFD', str(input_str))
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()

# --- KHỞI TẠO DỮ LIỆU ---
if 'df_doi' not in st.session_state:
    st.session_state.df_doi = pd.read_csv("Tin - Đội bóng.csv")
    st.session_state.df_tran = pd.read_csv("Tin - Trận đấu.csv")
    st.session_state.history = []

# --- GIAO DIỆN CHÍNH ---
st.title("⚽ QUẢN LÝ BÓNG ĐÁ - PHIÊN BẢN CHUẨN XÁC")

# NÚT XÁC NHẬN TOÀN CỤC (Để lưu thay đổi)
if st.button("💾 XÁC NHẬN LƯU THAY ĐỔI VÀO FILE", type="primary"):
    st.session_state.df_doi.to_csv("Tin - Đội bóng.csv", index=False)
    st.session_state.df_tran.to_csv("Tin - Trận đấu.csv", index=False)
    st.session_state.history.append(f"[{datetime.now().strftime('%H:%M')}] Đã lưu dữ liệu vào file")
    st.success("Đã ghi đè dữ liệu thành công!")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Bảng Xếp Hạng", "📅 Lịch Thi Đấu", "🛠 Cấu Hình Đội", "📜 Nhật Ký"])

with tab1:
    col_s, col_abc = st.columns([3, 1])
    search = col_s.text_input("🔍 Tìm kiếm...", key="search_all")
    is_abc = col_abc.checkbox("Sắp xếp tên A-Z", key="abc_check")
    data = st.session_state.df_doi.copy()
    if search:
        data = data[data['Đội tuyển'].apply(lambda x: remove_accents(search) in remove_accents(str(x)))]
    if is_abc:
        data = data.sort_values('Đội tuyển')
    st.table(data)

with tab2:
    for v in sorted(st.session_state.df_tran['Vòng'].unique()):
        with st.expander(f"Vòng {int(v)}"):
            matches = st.session_state.df_tran[st.session_state.df_tran['Vòng'] == v]
            for idx, r in matches.iterrows():
                c1, s1, vs, s2, c2 = st.columns([3, 1, 0.5, 1, 3])
                c1.write(f"**{r.iloc[4]}**")
                # Đảm bảo key duy nhất bằng cách kết hợp vòng và chỉ số dòng
                n1 = s1.number_input("n1", value=int(r.iloc[5]), key=f"v{v}_idx{idx}_h")
                vs.write("-")
                n2 = s2.number_input("n2", value=int(r.iloc[6]), key=f"v{v}_idx{idx}_a")
                c2.write(f"**{r.iloc[7]}**")
                
                # Cập nhật tạm thời vào Session State
                if n1 != r.iloc[5] or n2 != r.iloc[6]:
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[5]] = n1
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[6]] = n2

with tab3:
    st.subheader("➕ Thêm đội mới & Lập tỉ số")
    new_team = st.text_input("Tên đội mới:")
    if st.button("Bắt đầu lập tỉ số"):
        st.session_state.temp_add = new_team
        
    if 'temp_add' in st.session_state:
        st.write(f"Đang lập tỉ số cho: **{st.session_state.temp_add}**")
        new_matches = []
        for i, team in enumerate(st.session_state.df_doi['Đội tuyển']):
            c_v, c_s1, c_s2 = st.columns(3)
            v_val = c_v.number_input(f"Vòng vs {team}", 1, 20, 1, key=f"add_v_{i}")
            b1 = c_s1.number_input(f"Bàn {st.session_state.temp_add}", 0, 10, 0, key=f"add_b1_{i}")
            b2 = c_s2.number_input(f"Bàn {team}", 0, 10, 0, key=f"add_b2_{i}")
            new_matches.append([v_val, "01/01/2026", None, None, st.session_state.temp_add, b1, b2, team])
        
        if st.button("Hoàn tất thêm đội"):
            st.session_state.df_doi = pd.concat([st.session_state.df_doi, pd.DataFrame([{'Đội tuyển': st.session_state.temp_add}])])
            st.session_state.df_tran = pd.concat([st.session_state.df_tran, pd.DataFrame(new_matches, columns=st.session_state.df_tran.columns)])
            st.session_state.history.append(f"Đã thêm đội: {st.session_state.temp_add}")
            del st.session_state.temp_add
            st.rerun()

with tab4:
    for log in reversed(st.session_state.history):
        st.info(log)
