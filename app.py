import streamlit as st
import pandas as pd
from datetime import date
import json
import os
import io

st.set_page_config(
    page_title="Dự Đoán & Quản Lý Vốn 5%",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DB_FILE = "history_data.json"
CONFIG_FILE = "config_capital.json"

# --- 1. LƯU TRỮ VÀ ĐỌC DỮ LIỆU BỀN VỮNG ---
def load_all_history():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_all_history(data_list):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)

def load_capital_config():
    default_config = {
        "base_capital": 1000000,
        "session_start_cap": 1000000
    }
    if not os.path.exists(CONFIG_FILE):
        return default_config
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_config

def save_capital_config(config_dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=2)

# Bảng tra cứu thuộc tính chuẩn Roulette 37 số (0 - 36)
ROULETTE_DATA = {
    0: {"p1": "0", "p2": "0", "p3": "0", "p4": "0"},
    1: {"p1": "I", "p2": "ĐỎ", "p3": "NHỎ", "p4": "LẺ"},
    2: {"p1": "I", "p2": "ĐEN", "p3": "NHỎ", "p4": "CHẴN"},
    3: {"p1": "I", "p2": "ĐỎ", "p3": "NHỎ", "p4": "LẺ"},
    4: {"p1": "I", "p2": "ĐEN", "p3": "NHỎ", "p4": "CHẴN"},
    5: {"p1": "I", "p2": "ĐỎ", "p3": "NHỎ", "p4": "LẺ"},
    6: {"p1": "I", "p2": "ĐEN", "p3": "NHỎ", "p4": "CHẴN"},
    7: {"p1": "I", "p2": "ĐỎ", "p3": "NHỎ", "p4": "LẺ"},
    8: {"p1": "I", "p2": "ĐEN", "p3": "NHỎ", "p4": "CHẴN"},
    9: {"p1": "I", "p2": "ĐỎ", "p3": "NHỎ", "p4": "LẺ"},
    10: {"p1": "I", "p2": "ĐEN", "p3": "NHỎ", "p4": "CHẴN"},
    11: {"p1": "I", "p2": "ĐEN", "p3": "NHỎ", "p4": "LẺ"},
    12: {"p1": "I", "p2": "ĐỎ", "p3": "NHỎ", "p4": "CHẴN"},
    13: {"p1": "II", "p2": "ĐEN", "p3": "NHỎ", "p4": "LẺ"},
    14: {"p1": "II", "p2": "ĐỎ", "p3": "NHỎ", "p4": "CHẴN"},
    15: {"p1": "II", "p2": "ĐEN", "p3": "NHỎ", "p4": "LẺ"},
    16: {"p1": "II", "p2": "ĐỎ", "p3": "NHỎ", "p4": "CHẴN"},
    17: {"p1": "II", "p2": "ĐEN", "p3": "NHỎ", "p4": "LẺ"},
    18: {"p1": "II", "p2": "ĐỎ", "p3": "NHỎ", "p4": "CHẴN"},
    19: {"p1": "II", "p2": "ĐỎ", "p3": "TO", "p4": "LẺ"},
    20: {"p1": "II", "p2": "ĐEN", "p3": "TO", "p4": "CHẴN"},
    21: {"p1": "II", "p2": "ĐỎ", "p3": "TO", "p4": "LẺ"},
    22: {"p1": "II", "p2": "ĐEN", "p3": "TO", "p4": "CHẴN"},
    23: {"p1": "II", "p2": "ĐỎ", "p3": "TO", "p4": "LẺ"},
    24: {"p1": "II", "p2": "ĐEN", "p3": "TO", "p4": "CHẴN"},
    25: {"p1": "III", "p2": "ĐỎ", "p3": "TO", "p4": "LẺ"},
    26: {"p1": "III", "p2": "ĐEN", "p3": "TO", "p4": "CHẴN"},
    27: {"p1": "III", "p2": "ĐỎ", "p3": "TO", "p4": "LẺ"},
    28: {"p1": "III", "p2": "ĐEN", "p3": "TO", "p4": "CHẴN"},
    29: {"p1": "III", "p2": "ĐEN", "p3": "TO", "p4": "LẺ"},
    30: {"p1": "III", "p2": "ĐỎ", "p3": "TO", "p4": "CHẴN"},
    31: {"p1": "III", "p2": "ĐEN", "p3": "TO", "p4": "LẺ"},
    32: {"p1": "III", "p2": "ĐỎ", "p3": "TO", "p4": "CHẴN"},
    33: {"p1": "III", "p2": "ĐEN", "p3": "TO", "p4": "LẺ"},
    34: {"p1": "III", "p2": "ĐỎ", "p3": "TO", "p4": "CHẴN"},
    35: {"p1": "III", "p2": "ĐEN", "p3": "TO", "p4": "LẺ"},
    36: {"p1": "III", "p2": "ĐỎ", "p3": "TO", "p4": "CHẴN"},
}

# --- 2. LOGIC VÀO LỆNH MỚI THEO YÊU CẦU ---
# Ván mốc: V1 = Nhỏ/To, V2 = Lẻ/Chẵn, V3 = Đen/Đỏ
# Dự đoán đánh ngược: V4 = Đen/Đỏ (lấy V3), V5 = Lẻ/Chẵn (lấy V2), V6 = Nhỏ/To (lấy V1)
def get_prediction_info(stt, df_history):
    if stt <= 3:
        return "-", "-"
    
    base_end_stt = ((stt - 1) // 3) * 3
    if len(df_history) < base_end_stt:
        return "Chờ đủ dữ liệu", "-"
    
    step_in_block = (stt - 1) % 3
    
    if step_in_block == 0:
        # Ván 4 (lệnh 1 chu kỳ): Bàn ĐEN / ĐỎ -> lấy Player 2 của ván 3 (base_end_stt)
        bet_type = "Bàn ĐEN / ĐỎ"
        target_row = df_history[df_history["stt"] == base_end_stt]
        pred = target_row["player2"].values[0] if not target_row.empty else "-"
    elif step_in_block == 1:
        # Ván 5 (lệnh 2 chu kỳ): Bàn LẺ / CHẴN -> lấy Player 4 của ván 2 (base_end_stt - 1)
        bet_type = "Bàn LẺ / CHẴN"
        target_row = df_history[df_history["stt"] == (base_end_stt - 1)]
        pred = target_row["player4"].values[0] if not target_row.empty else "-"
    else:
        # Ván 6 (lệnh 3 chu kỳ): Bàn NHỎ / TO -> lấy Player 3 của ván 1 (base_end_stt - 2)
        bet_type = "Bàn NHỎ / TO"
        target_row = df_history[df_history["stt"] == (base_end_stt - 2)]
        pred = target_row["player3"].values[0] if not target_row.empty else "-"
        
    return bet_type, pred

# --- 3. GIAO DIỆN CHÍNH ---
st.markdown("<h3 style='text-align: center; color: #1F4E78;'>🎯 DỰ ĐOÁN & QUẢN LÝ VỐN 5% CƠ SỞ</h3>", unsafe_allow_html=True)

# Đọc cấu hình vốn đã lưu
cap_cfg = load_capital_config()

# KHU VỰC CÀI ĐẶT THỜI GIAN & PHIÊN
c_date, c_sess = st.columns(2)
with c_date:
    selected_date = st.date_input("Ngày:", date.today())
with c_sess:
    selected_session = st.selectbox("Phiên:", ["Phien 1 (Sang)", "Phien 2 (Trua)", "Phien 3 (Chieu)", "Phien 4 (Toi)"])

# KHU VỰC 3 Ô VỐN QUẢN LÝ
st.markdown("##### 💼 BẢNG QUẢN LÝ VỐN PHIÊN")
c_v1, c_v2, c_v3 = st.columns(3)

with c_v1:
    base_capital = st.number_input(
        "1. Vốn Cơ Sở (Ban đầu):",
        min_value=1000,
        value=int(cap_cfg.get("base_capital", 1000000)),
        step=50000,
        help="Vốn gốc dùng để tính chuẩn mức đi lệnh 5% và target"
    )

with c_v2:
    start_session_cap = st.number_input(
        "2. Vốn Trước Khi Vào Phiên:",
        min_value=0,
        value=int(cap_cfg.get("session_start_cap", base_capital)),
        step=50000,
        help="Số dư vốn thực tế bạn đang có trước khi bắt đầu phiên này"
    )

# Lưu lại nếu người dùng thay đổi vốn cơ sở hoặc vốn trước phiên
if base_capital != cap_cfg.get("base_capital") or start_session_cap != cap_cfg.get("session_start_cap"):
    save_capital_config({"base_capital": base_capital, "session_start_cap": start_session_cap})

# Tải lịch sử phiên hiện tại
all_records = load_all_history()
if all_records:
    df_all = pd.DataFrame(all_records)
    df_cur = df_all[(df_all["session_date"] == str(selected_date)) & (df_all["session_name"] == selected_session)].copy()
else:
    df_all = pd.DataFrame()
    df_cur = pd.DataFrame()

next_stt = len(df_cur) + 1

# Lãi / Lỗ lũy kế của phiên hiện tại
cur_session_pnl = int(df_cur["money_pnl"].sum()) if not df_cur.empty else 0
current_real_cap = start_session_cap + cur_session_pnl

with c_v3:
    st.metric(
        "3. Vốn Thực Tế Hiện Tại:",
        f"{current_real_cap:,}",
        delta=f"{'+' if cur_session_pnl >= 0 else ''}{cur_session_pnl:,} ({cur_session_pnl/base_capital*100:.2f}%)"
    )

# Mức cược mỗi lệnh: ĐI ĐỀU 5% VỐN CƠ SỞ
stake_amount = int(base_capital * 0.05)
target_threshold = base_capital * 0.0475  # Target >= 4.75% hoặc 5%

# Kiểm tra điều kiện khóa phiên
is_target_hit = cur_session_pnl >= target_threshold

# Kiểm tra Lệnh 1 (Ván 4) nếu WIN thì khóa ngay
is_round1_won = False
if len(df_cur) >= 4:
    v4 = df_cur[df_cur["stt"] == 4]
    if not v4.empty and v4["win_lose"].values[0] == "WIN":
        is_round1_won = True

is_finished = is_target_hit or is_round1_won

# BẢNG THÔNG BÁO TRẠNG THÁI TIẾN ĐỘ TARGET
st.markdown("---")
c_kpi1, c_kpi2 = st.columns(2)
c_kpi1.metric("Mức cược chuẩn (5% vốn CS)", f"{stake_amount:,}")
c_kpi2.metric("Mục tiêu phiên (>= 4.75% ~ 5%)", f"+{int(target_threshold):,} đến +{stake_amount:,}")

if is_finished:
    st.success(f"🎉 **ĐÃ HOÀN THÀNH MỤC TIÊU PHIÊN!** Lợi nhuận: **+{cur_session_pnl:,}** ({cur_session_pnl/base_capital*100:.2f}%) ➔ **KHÓA PHIÊN & NGHỈ NGƠI**.")
    st.markdown("""
    <div style='background-color: #E2EFDA; padding: 18px; border-radius: 10px; border: 2px solid #375623; text-align: center;'>
        <h2 style='margin:0; color: #276A3C;'>🔒 PHIÊN NÀY ĐÃ ĐƯỢC KHÓA HOÀN TOÀN</h2>
        <p style='margin: 8px 0 0 0; font-size: 16px; color: #333;'>
            Lệnh 1 Win hoặc Lợi nhuận đã đạt chỉ tiêu <b>>= 4.75% - 5%</b>. Dừng ngay theo đúng kỷ luật, không phát thêm tín hiệu!
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    # HIỂN THỊ TÍN HIỆU VÁN TIẾP THEO
    pred_type, pred_target = get_prediction_info(next_stt, df_cur)

    if next_stt <= 3:
        moc_names = {1: "NHỎ / TO", 2: "LẺ / CHẴN", 3: "ĐEN / ĐỎ"}
        st.info(f"⏳ **Ván mốc {next_stt}/3 (Mốc {moc_names[next_stt]}):** Nhập kết quả để tạo mốc tín hiệu")
    else:
        st.markdown(f"""
        <div style='background-color: #FFF2CC; padding: 15px; border-radius: 10px; border: 2px solid #D6B656; text-align: center;'>
            <h4 style='margin:0; color:#333;'>TÍN HIỆU VÁN TIẾP THEO (STT: {next_stt})</h4>
            <h1 style='margin:6px 0; color:#C00000; font-size: 34px;'>👉 ĐÁNH: <b>{pred_target}</b></h1>
            <p style='margin:0; font-size: 16px; color:#1F4E78;'>
                <b>{pred_type}</b> | Đi lệnh đều 5%: <b style='color:#C00000;'>{stake_amount:,}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # HÀM XỬ LÝ NHẬP VÁN
    def handle_round_submit(val_so):
        attr = ROULETTE_DATA.get(val_so, {"p1": "0", "p2": "0", "p3": "0", "p4": "0"})
        p1, p2, p3, p4 = attr["p1"], attr["p2"], attr["p3"], attr["p4"]
        
        all_recs = load_all_history()
        
        if next_stt <= 3:
            new_row = {
                "session_date": str(selected_date),
                "session_name": selected_session,
                "stt": next_stt,
                "kq_so": val_so,
                "player1": p1,
                "player2": p2,
                "player3": p3,
                "player4": p4,
                "bet_type": "-",
                "prediction": "-",
                "actual_result": "-",
                "win_lose": "MỐC",
                "stake_amount": 0,
                "money_pnl": 0,
                "cur_balance": start_session_cap,
                "status": "Dữ liệu mốc"
            }
        else:
            # So khớp theo đúng loại bàn cược
            if pred_type == "Bàn ĐEN / ĐỎ":
                actual = p2
            elif pred_type == "Bàn LẺ / CHẴN":
                actual = p4
            else:  # Bàn NHỎ / TO
                actual = p3

            wl = "WIN" if actual == pred_target else "LOSE"
            pnl = stake_amount if wl == "WIN" else -stake_amount
            new_balance = current_real_cap + pnl
            
            # Kiểm tra trạng thái
            new_pnl_session = cur_session_pnl + pnl
            if (next_stt == 4 and wl == "WIN") or (new_pnl_session >= target_threshold):
                stat = "HOÀN THÀNH TARGET (KHÓA PHIÊN)"
            else:
                stat = "TIẾP TỤC"
                
            new_row = {
                "session_date": str(selected_date),
                "session_name": selected_session,
                "stt": next_stt,
                "kq_so": val_so,
                "player1": p1,
                "player2": p2,
                "player3": p3,
                "player4": p4,
                "bet_type": pred_type,
                "prediction": pred_target,
                "actual_result": actual,
                "win_lose": wl,
                "stake_amount": stake_amount,
                "money_pnl": pnl,
                "cur_balance": new_balance,
                "status": stat
            }
            
        all_recs.append(new_row)
        save_all_history(all_recs)

    # 1. FORM NHẬP KẾT QUẢ GÕ SỐ
    with st.form("input_form", clear_on_submit=True):
        kq_input = st.number_input(
            "Nhập số mở thưởng (0 - 36):",
            min_value=0,
            max_value=36,
            value=None,
            step=1,
            placeholder="Chạm vào để gõ số..."
        )
        submitted = st.form_submit_button("XÁC NHẬN KẾT QUẢ", use_container_width=True)
        if submitted:
            if kq_input is None:
                st.warning("⚠️ Vui lòng gõ số kết quả trước khi bấm xác nhận!")
            else:
                handle_round_submit(int(kq_input))
                st.rerun()

    # 2. BÀN PHÍM CHỌN NHANH 1 CHẠM
    with st.expander("⚡ Hoặc bấm chọn nhanh số tại đây (1 Chạm)"):
        if st.button("Số 0 (Xanh)", use_container_width=True, key="btn_0"):
            handle_round_submit(0)
            st.rerun()
            
        for row_start in range(1, 37, 6):
            cols = st.columns(6)
            for i in range(6):
                val = row_start + i
                if val <= 36:
                    color_type = ROULETTE_DATA[val]["p2"]
                    label = f"{val} ({color_type[0]})"
                    if cols[i].button(label, key=f"quick_{val}", use_container_width=True):
                        handle_round_submit(val)
                        st.rerun()

# NÚT ĐIỀU KHIỂN & QUẢN TRỊ DỮ LIỆU
st.write("")
btn_c1, btn_c2 = st.columns(2)
with btn_c1:
    if st.button("↩️ Xóa ván gần nhất", use_container_width=True):
        all_recs = load_all_history()
        for idx in range(len(all_recs) - 1, -1, -1):
            if all_recs[idx]["session_date"] == str(selected_date) and all_recs[idx]["session_name"] == selected_session:
                all_recs.pop(idx)
                save_all_history(all_recs)
                st.rerun()
                break

with btn_c2:
    if st.button("🗑️ Xóa trắng phiên này", use_container_width=True):
        all_recs = load_all_history()
        all_recs = [
            x for x in all_recs 
            if not (x["session_date"] == str(selected_date) and x["session_name"] == selected_session)
        ]
        save_all_history(all_recs)
        st.rerun()

# KHU VỰC XUẤT DỮ LIỆU RA EXCEL LÂU DÀI
st.markdown("---")
st.markdown("##### 📊 XUẤT BÁO CÁO & THỐNG KÊ EXCEL")
col_ex1, col_ex2 = st.columns(2)

with col_ex1:
    if not df_cur.empty:
        output_cur = io.BytesIO()
        clean_name = selected_session.replace(":", "").replace(" ", "_")[:30]
        with pd.ExcelWriter(output_cur, engine='openpyxl') as writer:
            df_cur.to_excel(writer, index=False, sheet_name=clean_name)
        excel_cur = output_cur.getvalue()
        st.download_button(
            label="📥 Tải Excel Phiên Hiện Tại",
            data=excel_cur,
            file_name=f"Phien_{clean_name}_{selected_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

with col_ex2:
    all_stored = load_all_history()
    if all_stored:
        df_all_full = pd.DataFrame(all_stored)
        output_all = io.BytesIO()
        with pd.ExcelWriter(output_all, engine='openpyxl') as writer:
            df_all_full.to_excel(writer, index=False, sheet_name="Lich_Su_Toan_Bo")
        excel_all = output_all.getvalue()
        st.download_button(
            label="📦 Tải Toàn Bộ Lịch Sử (Tất Cả Ngày)",
            data=excel_all,
            file_name=f"Lich_Su_Tong_Hop_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# BẢNG CHI TIẾT DIỄN BIẾN PHIÊN
st.markdown("#### 📋 Diễn biến chi tiết trong phiên")
if not df_cur.empty:
    show_df = df_cur[["stt", "kq_so", "prediction", "actual_result", "win_lose", "stake_amount", "money_pnl", "cur_balance", "status"]].copy()
    show_df.columns = ["STT", "Số", "Dự Đoán", "Ra", "W/L", "Tiền Cược", "Lãi/Lỗ", "Vốn Hiện Tại", "Trạng Thái"]
    st.dataframe(show_df, use_container_width=True)
else:
    st.write("Chưa có ván nào trong phiên này. Nhập 3 ván đầu tiên để bắt đầu.")

# NÚT RESET TOÀN BỘ HỆ THỐNG / NÂNG VỐN THÁNG MỚI (CÓ BẢO MẬT XÁC NHẬN)
with st.expander("⚙️ Quản trị: Reset toàn bộ hệ thống để nâng vốn mới"):
    st.warning("⚠️ Thao tác này sẽ xóa toàn bộ lịch sử lưu trữ để bạn bắt đầu chu kỳ vốn mới.")
    confirm_reset = st.checkbox("Tôi xác nhận muốn xóa sạch toàn bộ lịch sử để nâng vốn cơ sở mới")
    if confirm_reset:
        if st.button("🔴 TIẾN HÀNH RESET TOÀN BỘ HỆ THỐNG", use_container_width=True):
            save_all_history([])
            st.success("Đã xóa sạch dữ liệu lưu trữ! Bạn có thể nhập vốn cơ sở mới.")
            st.rerun()
