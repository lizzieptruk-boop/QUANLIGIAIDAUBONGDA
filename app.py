import streamlit as st

import pandas as pd

from datetime import datetime

import io



# 1. CẤU HÌNH

st.set_page_config(page_title="Football Admin - Master Confirm", layout="wide")
if 'sort_abc' not in st.session_state:
    st.session_state.sort_abc = False


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

def calculate_bxh(df_doi_in, df_tran_in, sort_by_abc=False):
    teams = df_doi_in['Đội tuyển'].unique()
    # Nếu đang ở chế độ ABC, sắp xếp danh sách đội tuyển trước khi tạo bảng
    if sort_by_abc:
        teams = sorted(teams)
        
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
    
    # NẾU KHÔNG PHẢI CHẾ ĐỘ ABC -> Sắp xếp theo điểm (BXH bóng đá chuẩn)
    if not sort_by_abc:
        bxh = bxh.sort_values(by=['Điểm', 'HS', 'BT'], ascending=False).reset_index(drop=True)
    
    bxh.index = bxh.index + 1
    bxh.index.name = "STT"
    return bxh



# 4. GIAO DIỆN CHÍNH

st.title("⚽ QUẢN LÝ BÓNG ĐÁ")

# 1. Đặt nút bấm và ô tìm kiếm cạnh nhau cho đẹp
c1, c2 = st.columns([3, 1])
search = c1.text_input("🔍 Tìm kiếm:")

# 2. Nút bấm này đóng vai trò "Công tắc" (Toggle)
label = "🔄 Xem theo Điểm" if st.session_state.sort_abc else "🔤 Xem theo A-Z"
if c2.button(label):
    st.session_state.sort_abc = not st.session_state.sort_abc
    st.rerun()

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
    t.subheader("Bảng xếp hạng " + ("(A-Z)" if st.session_state.sort_abc else "(Theo Điểm)"))
    
    # Truyền biến sort_abc vào hàm tính toán
    res = calculate_bxh(st.session_state.df_doi, st.session_state.df_tran, sort_by_abc=st.session_state.sort_abc
    
    # Logic tìm kiếm chuẩn hóa
    if search:
        # 1. Làm sạch cột Đội tuyển: xóa khoảng trắng thừa, chuẩn hóa Unicode
        import unicodedata
        
        # Chuẩn hóa cột tên đội trong DataFrame
        res['Search_Col'] = res['Đội tuyển'].astype(str).str.strip().apply(lambda x: unicodedata.normalize('NFC', x))
        
        # Chuẩn hóa từ khóa tìm kiếm
        clean_search = unicodedata.normalize('NFC', search.strip())
        
        # 2. Tìm kiếm trên cột đã làm sạch
        res = res[res['Search_Col'].str.contains(clean_search, case=False, na=False)]
        
        # 3. Bỏ cột phụ Search_Col trước khi hiển thị
        res = res.drop(columns=['Search_Col'])
        
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
    # Sắp xếp danh sách đội để khi chọn tên trong Selectbox sẽ dễ tìm hơn
    all_teams = sorted(st.session_state.draft_doi['Đội tuyển'].tolist()) 
    
    st.subheader("📝 Đổi tên đội bóng")
    # Thay all_teams vào Selectbox
    t_old = c_sel.selectbox("Chọn đội:", all_teams, key=f"edit_s_{st.session_state.session_id}")
    
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













