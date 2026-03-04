import streamlit as st

import pandas as pd

from datetime import datetime

import io



# 1. CẤU HÌNH

st.set_page_config(page_title="Football Admin - Master Confirm", layout="wide")



if 'session_id' not in st.session_state:

    st.session_state.session_id = 0



# 2. KHỞI TẠO DỮ LIỆU GỐC VÀ DỮ LIỆU TẠM

def load_initial_data():

    if 'df_doi' not in st.session_state:

        st.session_state.df_doi = pd.read_csv("Tin - Đội bóng.csv").dropna(subset=['Đội tuyển'])

    if 'df_tran' not in st.session_state:

        df_t = pd.read_csv("Tin - Trận đấu.csv")

        df_t['Vòng'] = df_t['Vòng'].ffill()

        df_t = df_t.dropna(subset=[df_t.columns[4], df_t.columns[7]])

        df_t.iloc[:, 5] = pd.to_numeric(df_t.iloc[:, 5], errors='coerce').fillna(0).astype(int)

        df_t.iloc[:, 6] = pd.to_numeric(df_t.iloc[:, 6], errors='coerce').fillna(0).astype(int)

        st.session_state.df_tran = df_t

    

    # Tạo bản nháp (Draft) nếu chưa có

    if 'draft_doi' not in st.session_state:

        st.session_state.draft_doi = st.session_state.df_doi.copy()

    if 'draft_tran' not in st.session_state:

        st.session_state.draft_tran = st.session_state.df_tran.copy()

    if 'has_changes' not in st.session_state:

        st.session_state.has_changes = False



load_initial_data()



if 'history' not in st.session_state:

    st.session_state.history = []



def record_history(msg):

    snapshot = {

        'msg': msg, 'time': datetime.now().strftime("%H:%M:%S"),

        'df_doi_snap': st.session_state.df_doi.copy(),

        'df_tran_snap': st.session_state.df_tran.copy()

    }

    st.session_state.history.insert(0, snapshot)



# 3. TÍNH BXH (Dựa trên dữ liệu ĐÃ XÁC NHẬN)

def calculate_bxh(df_doi_in, df_tran_in):

    teams = df_doi_in['Đội tuyển'].unique()

    bxh = pd.DataFrame(teams, columns=['Đội tuyển'])

    for col in ['Trận', 'Thắng', 'Hòa', 'Thua', 'BT', 'BB', 'HS', 'Điểm']: bxh[col] = 0

    

    for _, r in df_tran_in.iterrows():

        t1, s1, s2, t2 = r.iloc[4], r.iloc[5], r.iloc[6], r.iloc[7]

        if t1 in teams and t2 in teams:

            for t, sm, so in [(t1, s1, s2), (t2, s2, s1)]:

                idx_m = bxh[bxh['Đội tuyển'] == t].index

                if not idx_m.empty:

                    idx = idx_m[0]

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



# 4. GIAO DIỆN CHÍNH

st.title("⚽ QUẢN LÝ BÓNG ĐÁ")

# 1. Khai báo nút bấm ở tầng trên cùng (Global)
if st.button("🔤 Sắp xếp A-Z danh sách đội"):
    # Sắp xếp trực tiếp vào df_doi gốc trong session_state
    st.session_state.df_doi = st.session_state.df_doi.sort_values(by='Đội tuyển').reset_index(drop=True)
    # Rerun ngay lập tức để ép Tab 1 tính lại BXH với dữ liệu mới
    st.rerun()

# 2. Xử lý tìm kiếm (Nếu cần)
search = st.text_input("🔍 Tìm kiếm:")

# 3. THANH THÔNG BÁO VÀ NÚT XÁC NHẬN TỔNG

if st.session_state.has_changes:

    st.warning("⚠️ Bạn có thay đổi chưa lưu!")

    if st.button("💾 XÁC NHẬN TẤT CẢ THAY ĐỔI (Lưu vào hệ thống)", type="primary", use_container_width=True):

        record_history("Cập nhật tổng lực dữ liệu")

        st.session_state.df_doi = st.session_state.draft_doi.copy()

        st.session_state.df_tran = st.session_state.draft_tran.copy()

        st.session_state.has_changes = False

        st.success("Đã áp dụng toàn bộ thay đổi!")

        st.rerun()



tab1, tab2, tab3, tab4 = st.tabs(["📊 Bảng Xếp Hạng", "📅 Lịch Thi Đấu", "🛠 Cấu Hình & Chỉnh Sửa", "📜 Nhật Ký"])



with tab1:
    st.subheader("Bảng xếp hạng chính thức")
    # Luôn tính toán dựa trên dữ liệu hiện tại trong session_state
    res = calculate_bxh(st.session_state.df_doi, st.session_state.df_tran)
    
    # Logic tìm kiếm chuẩn hóa
    if search:
        # Dùng mask để lọc, đảm bảo xử lý được cả tiếng Việt và giá trị trống
        mask = res['Đội tuyển'].astype(str).str.contains(search, case=False, na=False)
        res = res[mask]
    
    if res.empty:
        st.info("Không tìm thấy đội bóng nào khớp với từ khóa.")
    else:
        st.table(res)

with tab2:

    st.subheader("Chỉnh sửa tỷ số (Bản nháp)")

    df_m = st.session_state.draft_tran
    
    if search: df_m = df_m[(df_m.iloc[:,4].str.contains(search, case=False)) | (df_m.iloc[:,7].str.contains(search, case=False))]
   
   
    for v in sorted(df_m['Vòng'].unique()):

        with st.expander(f"Vòng {int(v)}"):

            v_matches = df_m[df_m['Vòng'] == v]

            for idx, r in v_matches.iterrows():

                c1, sc1, vs, sc2, c2 = st.columns([3,1,0.5,1,3])

                c1.write(f"**{r.iloc[4]}**")

                n1 = sc1.number_input("n1", 0, 100, int(r.iloc[5]), key=f"m1_{idx}_{st.session_state.session_id}", label_visibility="collapsed")

                vs.write("-")

                n2 = sc2.number_input("n2", 0, 100, int(r.iloc[6]), key=f"m2_{idx}_{st.session_state.session_id}", label_visibility="collapsed")

                c2.write(f"**{r.iloc[7]}**")

                

                if n1 != r.iloc[5] or n2 != r.iloc[6]:

                    st.session_state.draft_tran.at[idx, st.session_state.draft_tran.columns[5]] = n1

                    st.session_state.draft_tran.at[idx, st.session_state.draft_tran.columns[6]] = n2

                    st.session_state.has_changes = True 


with tab3:
    # ABC Sắp xếp danh sách chọn đội
    all_teams_abc = sorted(st.session_state.draft_doi['Đội tuyển'].tolist())
    
    # 3.1 ĐỔI TÊN ĐỘI

    st.subheader("📝 Đổi tên đội bóng")

    all_teams = st.session_state.draft_doi['Đội tuyển'].tolist()

    c_sel, c_new = st.columns(2)

    t_old = c_sel.selectbox("Chọn đội:", all_teams, key=f"edit_s_{st.session_state.session_id}")

    t_new = c_new.text_input("Tên mới:", key=f"edit_n_{st.session_state.session_id}")

    if st.button("Lưu tạm: Đổi tên"):

        if t_new and t_new != t_old:

            st.session_state.draft_doi['Đội tuyển'] = st.session_state.draft_doi['Đội tuyển'].replace(t_old, t_new)

            st.session_state.draft_tran.iloc[:, 4] = st.session_state.draft_tran.iloc[:, 4].replace(t_old, t_new)

            st.session_state.draft_tran.iloc[:, 7] = st.session_state.draft_tran.iloc[:, 7].replace(t_old, t_new)

            st.session_state.has_changes = True

            st.rerun()



    st.divider()

    

    # 3.2 THÊM ĐỘI

    st.subheader("➕ Thêm Đội Mới")

    name = st.text_input("Tên đội mới:", key="add_name")

    if st.button("Thiết lập lịch đấu tạm"):

        if name and name not in st.session_state.draft_doi['Đội tuyển'].values:

            st.session_state.adding = name

            st.rerun()

    

    if 'adding' in st.session_state:

        st.info(f"Đang soạn lịch cho {st.session_state.adding}")

        others = st.session_state.draft_doi[st.session_state.draft_doi['Đội tuyển'] != st.session_state.adding]['Đội tuyển'].unique()

        new_rows = []

        for i, op in enumerate(others):

            col_v, col_s1, col_s2 = st.columns([2, 1, 1])

            v_ = col_v.number_input(f"Vòng vs {op}", 1, 100, 1, key=f"v_add_{i}")

            s1_ = col_s1.number_input(f"Bàn {st.session_state.adding}", 0, 100, 0, key=f"s1_add_{i}")

            s2_ = col_s2.number_input(f"Bàn {op}", 0, 100, 0, key=f"s2_add_{i}")

            new_rows.append([v_, None, None, None, st.session_state.adding, s1_, s2_, op])

        

        if st.button("Lưu tạm: Thêm đội"):

            st.session_state.draft_doi = pd.concat([st.session_state.draft_doi, pd.DataFrame([{"Đội tuyển": st.session_state.adding}])], ignore_index=True)

            st.session_state.draft_tran = pd.concat([st.session_state.draft_tran, pd.DataFrame(new_rows, columns=st.session_state.draft_tran.columns)], ignore_index=True)

            st.session_state.has_changes = True

            del st.session_state.adding

            st.rerun()



    st.divider()



    # 3.3 XÓA ĐỘI

    st.subheader("🗑️ Xóa Đội")

    target = st.selectbox("Chọn đội xóa:", st.session_state.draft_doi['Đội tuyển'].tolist(), key="del_sel")

    if st.button("Lưu tạm: Xóa đội"):

        st.session_state.draft_doi = st.session_state.draft_doi[st.session_state.draft_doi['Đội tuyển'] != target]

        st.session_state.draft_tran = st.session_state.draft_tran[(st.session_state.draft_tran.iloc[:,4] != target) & (st.session_state.draft_tran.iloc[:,7] != target)]

        st.session_state.has_changes = True

        st.rerun()



with tab4:

    st.subheader("📜 Khôi phục (Dữ liệu đã xác nhận)")

    for i, item in enumerate(st.session_state.history):

        c_l, c_r = st.columns([7, 3])

        c_l.info(f"{item['time']} - {item['msg']}")

        if c_r.button("Quay lại bản này", key=f"rev_{i}"):

            st.session_state.df_doi = item['df_doi_snap'].copy()

            st.session_state.df_tran = item['df_tran_snap'].copy()

            st.session_state.draft_doi = item['df_doi_snap'].copy()

            st.session_state.draft_tran = item['df_tran_snap'].copy()

            st.session_state.history = st.session_state.history[i+1:]

            st.session_state.has_changes = False

            st.session_state.session_id += 1

            st.rerun()









