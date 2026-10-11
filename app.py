import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import json
import os
import io

st.set_page_config(
    page_title="Hệ Thống Dự Đoán 4 Phiên - 5 Bàn (GMT+7)",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DB_FILE = "history_data.json"
CONFIG_FILE = "config_capital.json"

# Lấy ngày hiện tại chuẩn múi giờ Việt Nam GMT+7
VN_TZ = timezone(timedelta(hours=7))
def get_current_vn_date():
    return datetime.now(VN_TZ).date()

# --- 1. LƯU TRỮ VÀ ĐỌC DỮ LIỆU ---
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
        "base_capital": 4000,
        "session_start_cap": 4000
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

# --- 2. LOGIC DỰ ĐOÁN (CHU KỲ NGƯỢC 3 VÁN) ---
def get_prediction_info(stt, df_history):
    if stt <= 3:
        return "-", "-"
    
    base_end_stt = ((stt - 1) // 3) * 3
    if len(df_history) < base_end_stt:
        return "Chờ đủ dữ liệu", "-"
    
    step_in_block = (stt - 1) % 3
    
    if step_in_block == 0:
        # Ván 4: Bàn ĐEN / ĐỎ -> lấy Ván 3
        bet_type = "Bàn ĐEN / ĐỎ"
        target_row = df_history[df_history["stt"] == base_end_stt]
        pred = target_row["player2"].values[0] if not target_row.empty else "-"
    elif step_in_block == 1:
        # Ván 5: Bàn LẺ / CHẴN -> lấy Ván 2
        bet_type = "Bàn LẺ / CHẴN"
        target_row = df_history[df_history["stt"] == (base_end_stt - 1)]
        pred = target_row["player4"].values[0] if not target_row.empty else "-"
    else:
        # Ván 6: Bàn NHỎ / TO -> lấy Ván 1
        bet_type = "Bàn NHỎ / TO"
        target_row = df_history[df_history["stt"] == (base_end_stt - 2)]
        pred = target_row["player3"].values[0] if not target_row.empty else "-"
        
    return bet_type, pred

# --- 3. LOGIC TÍNH TIỀN CƯỢC THEO TỪNG BÀN ---
def get_next_stake(df_table, base_capital):
    unit_5pct = int(base_capital * 0.05)
    unit_10pct = unit_5pct * 2
    
    if len(df_table) < 3:
        return 0, "Mốc"
    if len(df_table) == 3:
        return unit_5pct, "Lệnh 1 (5%)"
    
    # Tính PnL lũy kế riêng của bàn này
    table_pnl = df_table["money_pnl"].sum()
    last_row = df_table.iloc[-1]
    last_wl = last_row["win_lose"]
    last_stake = last_row["stake_amount"]
    
    # Nếu bàn đang hòa hoặc có lãi: Luôn đánh 5%
    if table_pnl >= 0:
        return unit_5pct, "Đủ vốn (5%)"
    
    # Nếu bàn đang bị âm:
    if last_wl == "WIN":
        if last_stake == unit_5pct:
            return unit_10pct, "Săn 2 WIN (Gấp đôi 10%)"
        else:
            return unit_5pct, "Chốt chuỗi (Về 5%)"
    else:
        return unit_5pct, "Giữ nhịp (5%)"

# --- 4. GIAO DIỆN CHÍNH ---
st.markdown("<h3 style='text-align: center; color: #1F4E78;'>🎯 QUẢN LÝ VỐN 4 PHIÊN - 5 BÀN (GMT+7)</h3>", unsafe_allow_html=True)

cap_cfg = load_capital_config()
today_vn = get_current_vn_date()

# KHU VỰC CHỌN NGÀY, PHIÊN, BÀN
c_date, c_sess, c_tbl = st.columns([1.1, 1.2, 1.1])
with c_date:
    selected_date = st.date_input("Ngày (GMT+7):", today_vn)
with c_sess:
    selected_session = st.selectbox("Phiên:", ["Phien 1 (Sang)", "Phien 2 (Trua)", "Phien 3 (Chieu)", "Phien 4 (Toi)"])

# Đọc toàn bộ dữ liệu
all_records = load_all_history()
if all_records:
    df_all = pd.DataFrame(all_records)
    # Lọc theo Ngày + Phiên
    df_sess = df_all[(df_all["session_date"] == str(selected_date)) & (df_all["session_name"] == selected_session)].copy()
else:
    df_all = pd.DataFrame()
    df_sess = pd.DataFrame()

# Kiểm tra trạng thái 5 bàn trong phiên đã chọn
table_names = [f"Bàn {i}" for i in range(1, 6)]
table_options = []

base_cap_default = int(cap_cfg.get("base_capital", 4000))
target_threshold_table = base_cap_default * 0.0475

for t_name in table_names:
    if not df_sess.empty and "table_name" in df_sess.columns:
        df_t = df_sess[df_sess["table_name"] == t_name]
    else:
        df_t = pd.DataFrame()
    
    t_pnl = df_t["money_pnl"].sum() if not df_t.empty else 0
    t_round1_won = False
    if len(df_t) >= 4:
        v4 = df_t[df_t["stt"] == 4]
        if not v4.empty and v4["win_lose"].values[0] == "WIN":
            t_round1_won = True
    
    if t_pnl >= target_threshold_table or t_round1_won:
        table_options.append(f"{t_name} 🔒 (Xong 5%)")
    else:
        table_options.append(t_name)

with c_tbl:
    selected_table_display = st.selectbox("Chọn Bàn Chơi:", table_options)
    selected_table = selected_table_display.split(" ")[0] + " " + selected_table_display.split(" ")[1]

# Lọc dữ liệu riêng của bàn hiện tại
if not df_sess.empty and "table_name" in df_sess.columns:
    df_cur = df_sess[df_sess["table_name"] == selected_table].copy()
else:
    df_cur = pd.DataFrame()

next_stt = len(df_cur) + 1

# BẢNG 3 Ô VỐN QUẢN LÝ
st.markdown("##### 💼 BẢNG QUẢN LÝ VỐN")
c_v1, c_v2, c_v3 = st.columns(3)

with c_v1:
    base_capital = st.number_input(
        "1. Vốn Cơ Sở (Ban đầu):",
        min_value=100,
        value=base_cap_default,
        step=500,
        help="Vốn chuẩn tính 5% cược và target"
    )

with c_v2:
    start_session_cap = st.number_input(
        "2. Vốn Trước Khi Vào Phiên:",
        min_value=0,
        value=int(cap_cfg.get("session_start_cap", base_capital)),
        step=500,
        help="Số dư vốn thực tế của bạn trước phiên"
    )

if base_capital != cap_cfg.get("base_capital") or start_session_cap != cap_cfg.get("session_start_cap"):
    save_capital_config({"base_capital": base_capital, "session_start_cap": start_session_cap})

# Tính lũy kế toàn phiên và của riêng bàn
session_total_pnl = int(df_sess["money_pnl"].sum()) if not df_sess.empty else 0
table_pnl = int(df_cur["money_pnl"].sum()) if not df_cur.empty else 0
current_real_cap = start_session_cap + session_total_pnl

with c_v3:
    st.metric(
        "3. Vốn Thực Tế Hiện Tại:",
        f"{current_real_cap:,}",
        delta=f"{'+' if session_total_pnl >= 0 else ''}{session_total_pnl:,} (Cả phiên)"
    )

# KIỂM TRA ĐIỀU KIỆN KHÓA BÀN HIỆN TẠI (5% VỐN CƠ SỞ)
unit_base_5pct = int(base_capital * 0.05)
target_threshold = base_capital * 0.0475

is_table_target_hit = table_pnl >= target_threshold
is_round1_won = False
if len(df_cur) >= 4:
    v4 = df_cur[df_cur["stt"] == 4]
    if not v4.empty and v4["win_lose"].values[0] == "WIN":
        is_round1_won = True

is_table_locked = is_table_target_hit or is_round1_won

# TIẾN ĐỘ 5 BÀN CỦA PHIÊN
st.markdown("---")
st.markdown(f"**Tiến độ 5 Bàn của {selected_session}:**")
p_cols = st.columns(5)
for idx, t_opt in enumerate(table_options):
    if "🔒" in t_opt:
        p_cols[idx].success(f"{table_names[idx]}: ✅ XONG")
    else:
        p_cols[idx].info(f"{table_names[idx]}: ⏳ CHƯA XONG")

c_kpi1, c_kpi2 = st.columns(2)
c_kpi1.metric("Mức cược chuẩn (5% vốn CS)", f"{unit_base_5pct:,}")
c_kpi2.metric("Lợi nhuận riêng bàn này", f"{'+' if table_pnl >= 0 else ''}{table_pnl:,}", f"Target: +{unit_base_5pct:,}")

# NẾU BÀN ĐÃ HOÀN THÀNH -> KHÓA BÀN VÀ KHÔNG CHO MỞ RA NỮA
if is_table_locked:
    st.success(f"🎉 **{selected_table.upper()} ĐÃ HOÀN THÀNH TARGET 5% (+{table_pnl:,})!**")
    st.markdown(f"""
    <div style='background-color: #E2EFDA; padding: 20px; border-radius: 12px; border: 2px solid #375623; text-align: center;'>
        <h2 style='margin:0; color: #276A3C;'>🔒 {selected_table.upper()} ĐÃ ĐƯỢC TỰ ĐỘNG KHÓA</h2>
        <p style='margin: 8px 0 0 0; font-size: 16px; color: #333;'>
            Mục tiêu 5% của bàn này đã đạt. Hệ thống khóa hoàn toàn để bảo toàn lợi nhuận.<br>
            👉 <b>Hãy chọn Bàn tiếp theo</b> chưa hoàn thành trong phiên này. Sang ngày hôm sau (00:00 GMT+7) hệ thống sẽ mở lại từ đầu.
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    # HIỂN THỊ TÍN HIỆU VÀ NÚT ĐÁNH
    pred_type, pred_target = get_prediction_info(next_stt, df_cur)
    stake_amount, stake_note = get_next_stake(df_cur, base_capital)

    if next_stt <= 3:
        moc_names = {1: "NHỎ / TO", 2: "LẺ / CHẴN", 3: "ĐEN / ĐỎ"}
        st.info(f"⏳ **{selected_table} - Ván mốc {next_stt}/3 (Mốc {moc_names[next_stt]}):** Nhập kết quả lấy mốc tín hiệu")
    else:
        st.markdown(f"""
        <div style='background-color: #FFF2CC; padding: 16px; border-radius: 12px; border: 2px solid #D6B656; text-align: center;'>
            <h4 style='margin:0; color:#555;'>{selected_table.upper()} - VÁN TIẾP THEO (STT: {next_stt})</h4>
            <h1 style='margin:8px 0; color:#C00000; font-size: 38px; letter-spacing: 1px;'>
                👉 ĐÁNH: <b>{pred_target} - {stake_amount:,}</b>
            </h1>
            <p style='margin:0; font-size: 15px; color:#1F4E78;'>
                <b>{pred_type}</b> | Chế độ vốn: <i>{stake_note}</i>
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    def handle_round_submit(val_so):
        attr = ROULETTE_DATA.get(val_so, {"p1": "0", "p2": "0", "p3": "0", "p4": "0"})
        p1, p2, p3, p4 = attr["p1"], attr["p2"], attr["p3"], attr["p4"]
        
        all_recs = load_all_history()
        
        if next_stt <= 3:
            new_row = {
                "session_date": str(selected_date),
                "session_name": selected_session,
                "table_name": selected_table,
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
                "cur_balance": current_real_cap,
                "status": "Dữ liệu mốc"
            }
        else:
            if pred_type == "Bàn ĐEN / ĐỎ":
                actual = p2
            elif pred_type == "Bàn LẺ / CHẴN":
                actual = p4
            else:
                actual = p3

            wl = "WIN" if actual == pred_target else "LOSE"
            pnl = stake_amount if wl == "WIN" else -stake_amount
            new_balance = current_real_cap + pnl
            
            new_t_pnl = table_pnl + pnl
            if (next_stt == 4 and wl == "WIN") or (new_t_pnl >= target_threshold):
                stat = "HOÀN THÀNH TARGET (KHÓA BÀN)"
            else:
                stat = "TIẾP TỤC"
                
            new_row = {
                "session_date": str(selected_date),
                "session_name": selected_session,
                "table_name": selected_table,
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
    if st.button(f"↩️ Xóa ván gần nhất ({selected_table})", use_container_width=True):
        all_recs = load_all_history()
        for idx in range(len(all_recs) - 1, -1, -1):
            if (all_recs[idx]["session_date"] == str(selected_date) and 
                all_recs[idx]["session_name"] == selected_session and 
                all_recs[idx].get("table_name", "Bàn 1") == selected_table):
                all_recs.pop(idx)
                save_all_history(all_recs)
                st.rerun()
                break

with btn_c2:
    if st.button(f"🗑️ Xóa trắng riêng {selected_table}", use_container_width=True):
        all_recs = load_all_history()
        all_recs = [
            x for x in all_recs 
            if not (x["session_date"] == str(selected_date) and 
                    x["session_name"] == selected_session and 
                    x.get("table_name", "Bàn 1") == selected_table)
        ]
        save_all_history(all_recs)
        st.rerun()

# KHU VỰC XUẤT DỮ LIỆU RA EXCEL
st.markdown("---")
st.markdown("##### 📊 XUẤT BÁO CÁO & THỐNG KÊ EXCEL")
col_ex1, col_ex2 = st.columns(2)

with col_ex1:
    if not df_sess.empty:
        output_cur = io.BytesIO()
        clean_name = selected_session.replace(":", "").replace(" ", "_")[:30]
        with pd.ExcelWriter(output_cur, engine='openpyxl') as writer:
            df_sess.to_excel(writer, index=False, sheet_name=clean_name)
        excel_cur = output_cur.getvalue()
        st.download_button(
            label="📥 Tải Excel Phiên Này (Cả 5 Bàn)",
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
            file_name=f"Lich_Su_Tong_Hop_{today_vn}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# BẢNG CHI TIẾT DIỄN BIẾN BÀN
st.markdown(f"#### 📋 Diễn biến chi tiết ({selected_table})")
if not df_cur.empty:
    show_df = df_cur[["stt", "kq_so", "prediction", "actual_result", "win_lose", "stake_amount", "money_pnl", "cur_balance", "status"]].copy()
    show_df.columns = ["STT", "Số", "Dự Đoán", "Ra", "W/L", "Tiền Cược", "Lãi/Lỗ", "Vốn Hiện Tại", "Trạng Thái"]
    st.dataframe(show_df, use_container_width=True)
else:
    st.write(f"Chưa có ván nào trong {selected_table}. Hãy nhập 3 ván đầu tiên để bắt đầu.")

# NÚT RESET TOÀN BỘ HỆ THỐNG / NÂNG VỐN THÁNG MỚI
with st.expander("⚙️ Quản trị: Reset toàn bộ hệ thống để nâng vốn mới"):
    st.warning("⚠️ Thao tác này sẽ xóa toàn bộ lịch sử lưu trữ của tất cả các ngày.")
    confirm_reset = st.checkbox("Tôi xác nhận muốn xóa sạch toàn bộ lịch sử để nâng vốn cơ sở mới")
    if confirm_reset:
        if st.button("🔴 TIẾN HÀNH RESET TOÀN BỘ HỆ THỐNG", use_container_width=True):
            save_all_history([])
            st.success("Đã xóa sạch dữ liệu lưu trữ! Bạn có thể nhập vốn cơ sở mới.")
            st.rerun()
