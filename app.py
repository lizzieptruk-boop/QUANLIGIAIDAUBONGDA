import streamlit as st
import pandas as pd
import io

# CẤU HÌNH TRANG
st.set_page_config(page_title="Football Admin Pro", layout="wide")

# 1. TẢI DỮ LIỆU
def load_data():
    if 'df_doi' not in st.session_state:
        st.session_state.df_doi = pd.read_csv("Tin - Đội bóng.csv").dropna(subset=['Đội tuyển'])
    if 'df_tran' not in st.session_state:
        df_t = pd.read_csv("Tin - Trận đấu.csv")
        df_t['Vòng'] = df_t['Vòng'].ffill()
        for i in [5, 6]: df_t.iloc[:, i] = pd.to_numeric(df_t.iloc[:, i], errors='coerce').fillna(0).astype(int)
        st.session_state.df_tran = df_t

load_data()

# 2. HÀM TÍNH BXH & XUẤT EXCEL
def get_bxh():
    teams = st.session_state.df_doi['Đội tuyển'].unique()
    bxh = pd.DataFrame(teams, columns=['Đội tuyển'])
    for col in ['Trận', 'Thắng', 'Hòa', 'Thua', 'BT', 'BB', 'HS', 'Điểm']: bxh[col] = 0
    for _, r in st.session_state.df_tran.iterrows():
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
    return bxh.sort_values(by=['Điểm', 'HS', 'BT'], ascending=False).reset_index(drop=True)

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='BXH')
    return output.getvalue()

# 3. GIAO DIỆN
st.title("⚽ QUẢN LÝ BÓNG ĐÁ - PHIÊN BẢN HOÀN THIỆN")

# Thanh điều khiển
c1, c2, c3 = st.columns([3, 1, 1])
search = c1.text_input("🔍 Tìm kiếm đội bóng:")
if c2.button("🔤 Sắp xếp ABC"):
    st.session_state.df_doi = st.session_state.df_doi.sort_values('Đội tuyển').reset_index(drop=True)
    st.rerun()
# Nút xuất Excel
st.download_button("📥 Tải Bảng Xếp Hạng (Excel)", data=to_excel(get_bxh()), file_name="BXH_BongDa.xlsx", mime="application/vnd.ms-excel")

tab1, tab2, tab3 = st.tabs(["📊 Bảng Xếp Hạng", "📅 Lịch Thi Đấu", "🛠 Quản lý Đội"])

with tab1:
    res = get_bxh()
    if search: res = res[res['Đội tuyển'].str.contains(search, case=False, na=False)]
    st.table(res)

with tab2:
    for v in sorted(st.session_state.df_tran['Vòng'].unique()):
        with st.expander(f"Vòng {int(v)}"):
            for idx, r in st.session_state.df_tran[st.session_state.df_tran['Vòng'] == v].iterrows():
                if search and search.lower() not in [str(r.iloc[4]).lower(), str(r.iloc[7]).lower()]: continue
                col1, sc1, vs, sc2, col2 = st.columns([3,1,0.5,1,3])
                col1.write(f"**{r.iloc[4]}**")
                n1 = sc1.number_input("n1", 0, 100, int(r.iloc[5]), key=f"n1_{idx}", label_visibility="collapsed")
                n2 = sc2.number_input("n2", 0, 100, int(r.iloc[6]), key=f"n2_{idx}", label_visibility="collapsed")
                col2.write(f"**{r.iloc[7]}**")
                if n1 != r.iloc[5] or n2 != r.iloc[6]:
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[5]] = n1
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[6]] = n2
                    st.rerun()

with tab3:
    all_teams = st.session_state.df_doi['Đội tuyển'].tolist()
    t_old = st.selectbox("Chọn đội:", all_teams)
    t_new = st.text_input("Tên mới (để trống để xóa đội):")
    if st.button("Áp dụng thay đổi"):
        if not t_new: 
            st.session_state.df_doi = st.session_state.df_doi[st.session_state.df_doi['Đội tuyển'] != t_old]
            st.session_state.df_tran = st.session_state.df_tran[(st.session_state.df_tran.iloc[:,4] != t_old) & (st.session_state.df_tran.iloc[:,7] != t_old)]
        else:
            st.session_state.df_doi['Đội tuyển'] = st.session_state.df_doi['Đội tuyển'].replace(t_old, t_new)
            for i in [4, 7]: st.session_state.df_tran.iloc[:, i] = st.session_state.df_tran.iloc[:, i].replace(t_old, t_new)
        st.rerun()
