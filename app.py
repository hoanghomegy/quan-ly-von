import streamlit as st
import pandas as pd
from datetime import date
import io

st.set_page_config(
    page_title="Dự Đoán & Quản Lý Vốn",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Bảng thuộc tính chuẩn Roulette 37 số (0 - 36)
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

if "history" not in st.session_state:
    st.session_state.history = []

def get_session_df():
    if not st.session_state.history:
        return pd.DataFrame()
    return pd.DataFrame(st.session_state.history)

def get_prediction_info(stt, df_history):
    if stt <= 3:
        return "-", "-"
    
    base_end_stt = ((stt - 1) // 3) * 3
    if len(df_history) < base_end_stt:
        return "Chờ đủ dữ liệu", "-"
    
    step_in_block = (stt - 1) % 3
    
    if step_in_block == 0:
        bet_type = "Bàn LẺ / CHẴN"
        target_row = df_history[df_history["stt"] == base_end_stt]
        pred = target_row["player4"].values[0] if not target_row.empty else "-"
    elif step_in_block == 1:
        bet_type = "Bàn NHỎ / TO"
        target_row = df_history[df_history["stt"] == (base_end_stt - 1)]
        pred = target_row["player3"].values[0] if not target_row.empty else "-"
    else:
        bet_type = "Bàn ĐEN / ĐỎ"
        target_row = df_history[df_history["stt"] == (base_end_stt - 2)]
        pred = target_row["player2"].values[0] if not target_row.empty else "-"
        
    return bet_type, pred

def calculate_next_capital(df_history):
    stt = len(df_history) + 1
    if stt <= 3:
        return "-", 0
    if stt == 4:
        return "G1", 1
    
    last = df_history.iloc[-1]
    last_phase = last["phase"]
    last_stake = last["stake"]
    last_wl = last["win_lose"]
    last_cum = last["cumulative"]
    
    recent_loses = 0
    for wl in reversed(df_history["win_lose"].tolist()):
        if wl == "LOSE":
            recent_loses += 1
        else:
            break
            
    if last_cum >= 0:
        cur_phase = "G1"
    elif last_phase == "G3" and last_cum >= -6:
        cur_phase = "G2"
    elif last_phase == "G1" and last_wl == "LOSE" and recent_loses >= 3:
        cur_phase = "G2"
    elif last_phase == "G2" and last_wl == "LOSE" and recent_loses >= 6:
        cur_phase = "G3"
    else:
        cur_phase = last_phase
        
    if cur_phase == "G1":
        stakes = [1, 2, 3]
    elif cur_phase == "G2":
        stakes = [2, 4, 6]
    else:
        stakes = [3, 6, 9]
        
    if last_wl == "WIN" or cur_phase != last_phase:
        cur_stake = stakes[0]
    else:
        if last_stake == stakes[0]:
            cur_stake = stakes[1]
        elif last_stake == stakes[1]:
            cur_stake = stakes[2]
        else:
            cur_stake = stakes[2]
            
    return cur_phase, cur_stake

def process_round_input(kq_so, selected_date, selected_session, next_stt, cur_cum, pred_type, pred_target, next_phase, next_stake, unit_val):
    attr = ROULETTE_DATA.get(kq_so, {"p1": "0", "p2": "0", "p3": "0", "p4": "0"})
    p1, p2, p3, p4 = attr["p1"], attr["p2"], attr["p3"], attr["p4"]
    
    if next_stt <= 3:
        st.session_state.history.append({
            "session_date": str(selected_date),
            "session_name": selected_session,
            "stt": next_stt,
            "kq_so": kq_so,
            "player1": p1,
            "player2": p2,
            "player3": p3,
            "player4": p4,
            "bet_type": "-",
            "prediction": "-",
            "actual_result": "-",
            "win_lose": "MỐC",
            "phase": "-",
            "stake": 0,
            "money_stake": 0,
            "pnl": 0,
            "money_pnl": 0,
            "cumulative": 0,
            "money_cum": 0,
            "status": "Dữ liệu mốc"
        })
    else:
        actual = p4 if pred_type == "Bàn LẺ / CHẴN" else (p3 if pred_type == "Bàn NHỎ / TO" else p2)
        wl = "WIN" if actual == pred_target else "LOSE"
        pnl = next_stake if wl == "WIN" else -next_stake
        new_cum = cur_cum + pnl
        
        status = "ĐẠT TARGET (+4)" if new_cum >= 4 else ("CẮT LỖ (-36)" if new_cum <= -36 else "TIẾP TỤC")
        
        st.session_state.history.append({
            "session_date": str(selected_date),
            "session_name": selected_session,
            "stt": next_stt,
            "kq_so": kq_so,
            "player1": p1,
            "player2": p2,
            "player3": p3,
            "player4": p4,
            "bet_type": pred_type,
            "prediction": pred_target,
            "actual_result": actual,
            "win_lose": wl,
            "phase": next_phase,
            "stake": next_stake,
            "money_stake": next_stake * unit_val,
            "pnl": pnl,
            "money_pnl": pnl * unit_val,
            "cumulative": new_cum,
            "money_cum": new_cum * unit_val,
            "status": status
        })

# --- GIAO DIỆN CHÍNH ---
st.markdown("<h3 style='text-align: center; color: #1F4E78;'>🎯 DỰ ĐOÁN & QUẢN LÝ VỐN 4 PHIÊN</h3>", unsafe_allow_html=True)

# 1. BẢNG CÀI ĐẶT: NGÀY, PHIÊN & GIÁ TRỊ 1 UNIT
c_top1, c_top2, c_top3 = st.columns([1, 1, 1])
with c_top1:
    selected_date = st.date_input("Ngày:", date.today())
with c_top2:
    selected_session = st.selectbox("Phiên:", ["Phien 1 (Sang)", "Phien 2 (Trua)", "Phien 3 (Chieu)", "Phien 4 (Toi)"])
with c_top3:
    unit_val = st.number_input("Giá trị 1 Unit:", min_value=1, value=50, step=10, help="Ví dụ: Nhập 50 tương đương 1 Unit = 50k")

df_all = get_session_df()
if not df_all.empty:
    df_cur = df_all[(df_all["session_date"] == str(selected_date)) & (df_all["session_name"] == selected_session)].copy()
else:
    df_cur = pd.DataFrame()

next_stt = len(df_cur) + 1
cur_cum = int(df_cur["cumulative"].iloc[-1]) if not df_cur.empty else 0
cur_money = cur_cum * unit_val

# 2. BẢNG KPI TRẠNG THÁI VỐN & LỢI NHUẬN QUY ĐỔI
c_kpi1, c_kpi2 = st.columns(2)
target_money = 4 * unit_val
stop_money = -36 * unit_val
c_kpi1.metric("Mục tiêu / Cắt lỗ", f"+4 / -36 ĐV", f"+{target_money:,} / {stop_money:,}")

is_finished = False

if cur_cum >= 4:
    is_finished = True
    c_kpi2.metric("Lũy kế phiên", f"+{cur_cum} ĐV (+{cur_money:,})", "CHỐT LÃI (ĐẠT)")
    st.success(f"🎉 **ĐÃ HOÀN THÀNH TARGET!** Lãi: **+{cur_cum} ĐV (+{cur_money:,})** -> **KHÓA PHIÊN & DỪNG LẠI**.")
elif cur_cum <= -36:
    is_finished = True
    c_kpi2.metric("Lũy kế phiên", f"{cur_cum} ĐV ({cur_money:,})", "CẮT LỖ (DỪNG)")
    st.error(f"🛑 **CHẠM NGƯỠNG CẮT LỖ AN TOÀN!** Lỗ: **{cur_cum} ĐV ({cur_money:,})** -> **DỪNG PHIÊN NGAY LẬP TỨC**.")
else:
    c_kpi2.metric("Lũy kế phiên", f"{cur_cum} ĐV ({cur_money:,})", "ĐANG ĐÁNH")

st.markdown("---")

# 3. HỘP TÍN HIỆU VÀO LỆNH (TỰ ĐỘNG KHÓA KHI ĐẠT TARGET HOẶC CẮT LỖ)
if is_finished:
    st.markdown("""
    <div style='background-color: #E2EFDA; padding: 20px; border-radius: 12px; border: 2px solid #375623; text-align: center;'>
        <h2 style='margin:0; color: #276A3C;'>🔒 PHIÊN NÀY ĐÃ ĐƯỢC KHÓA HOÀN TOÀN</h2>
        <p style='margin: 8px 0 0 0; font-size: 16px; color: #333;'>
            Bạn đã đạt đúng kỷ luật chốt lời/cắt lỗ. Hệ thống dừng phát tín hiệu để bảo vệ vốn. Hãy nghỉ ngơi và chờ phiên tiếp theo!
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    pred_type, pred_target = get_prediction_info(next_stt, df_cur)
    next_phase, next_stake = calculate_next_capital(df_cur)
    stake_money = next_stake * unit_val

    if next_stt <= 3:
        st.info(f"⏳ **Ván mốc {next_stt}/3:** Nhập kết quả để tạo mốc tín hiệu")
    else:
        st.markdown(f"""
        <div style='background-color: #FFF2CC; padding: 15px; border-radius: 10px; border: 2px solid #D6B656; text-align: center;'>
            <h4 style='margin:0; color:#333;'>TÍN HIỆU VÁN TIẾP THEO (STT: {next_stt})</h4>
            <h1 style='margin:6px 0; color:#C00000; font-size: 34px;'>👉 ĐÁNH: <b>{pred_target}</b></h1>
            <p style='margin:0; font-size: 16px; color:#1F4E78;'>
                <b>{pred_type}</b> | Giai đoạn: <b>{next_phase}</b> | Cược: <b style='color:#C00000;'>{next_stake} ĐV ({stake_money:,})</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # FORM NHẬP KẾT QUẢ BẰNG SỐ (ĐỂ TRỐNG Ô)
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
                process_round_input(int(kq_input), selected_date, selected_session, next_stt, cur_cum, pred_type, pred_target, next_phase, next_stake, unit_val)
                st.rerun()

    # BÀN PHÍM 1 CHẠM (0 - 36)
    with st.expander("⚡ Hoặc bấm chọn nhanh số tại đây (1 Chạm)"):
        if st.button("Số 0 (Xanh)", use_container_width=True, key="num_0"):
            process_round_input(0, selected_date, selected_session, next_stt, cur_cum, pred_type, pred_target, next_phase, next_stake, unit_val)
            st.rerun()
        
        for row_start in range(1, 37, 6):
            cols = st.columns(6)
            for i in range(6):
                val = row_start + i
                if val <= 36:
                    color_type = ROULETTE_DATA[val]["p2"]
                    label = f"{val} ({color_type[0]})"
                    if cols[i].button(label, key=f"quick_num_{val}", use_container_width=True):
                        process_round_input(val, selected_date, selected_session, next_stt, cur_cum, pred_type, pred_target, next_phase, next_stake, unit_val)
                        st.rerun()

# 4. NÚT THAO TÁC PHỤ
st.write("")
btn_c1, btn_c2 = st.columns(2)
with btn_c1:
    if st.button("↩️ Xóa ván gần nhất", use_container_width=True):
        if st.session_state.history:
            st.session_state.history.pop()
            st.rerun()
with btn_c2:
    if st.button("🗑️ Reset phiên này", use_container_width=True):
        st.session_state.history = [
            x for x in st.session_state.history 
            if not (x["session_date"] == str(selected_date) and x["session_name"] == selected_session)
        ]
        st.rerun()

# 5. XUẤT FILE EXCEL
if not df_cur.empty:
    output = io.BytesIO()
    clean_sheet_name = selected_session.replace(":", "").replace(" ", "_")[:30]
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_cur.to_excel(writer, index=False, sheet_name=clean_sheet_name)
    excel_data = output.getvalue()
    st.download_button(
        label="📥 Tải lịch sử phiên về Excel",
        data=excel_data,
        file_name=f"Lich_su_{clean_sheet_name}_{selected_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# 6. BẢNG CHI TIẾT
st.markdown("#### 📋 Diễn biến chi tiết trong phiên")
if not df_cur.empty:
    show_df = df_cur[["stt", "kq_so", "prediction", "actual_result", "win_lose", "stake", "money_stake", "cumulative", "money_cum"]].copy()
    show_df.columns = ["STT", "Số", "Dự Đoán", "Ra", "W/L", "Cược (ĐV)", "Tiền Cược", "Lũy Kế (ĐV)", "Tổng Tiền"]
    st.dataframe(show_df, use_container_width=True)
else:
    st.write("Chưa có ván nào trong phiên này. Nhập 3 ván đầu tiên để bắt đầu.")
