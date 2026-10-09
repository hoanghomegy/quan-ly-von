import streamlit as st
import pandas as pd
from datetime import date
import io

st.set_page_config(
    page_title="Dự Đoán & Quản Lý Vốn 4 Phiên",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Khởi tạo bộ nhớ phiên (Session State)
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

# --- GIAO DIỆN ĐIỀU KHIỂN ---
st.sidebar.title("🎮 ĐIỀU KHIỂN HỆ THỐNG")
selected_date = st.sidebar.date_input("Ngày giao dịch:", date.today())
session_names = ["Phiên 1: Sáng", "Phiên 2: Trưa", "Phiên 3: Chiều", "Phiên 4: Tối"]
selected_session = st.sidebar.selectbox("Chọn phiên làm việc:", session_names)

df_all = get_session_df()
if not df_all.empty:
    df_cur = df_all[(df_all["session_date"] == str(selected_date)) & (df_all["session_name"] == selected_session)].copy()
else:
    df_cur = pd.DataFrame()

next_stt = len(df_cur) + 1
cur_cum = df_cur["cumulative"].iloc[-1] if not df_cur.empty else 0

# Thẻ chỉ số trạng thái
c1, c2, c3, c4 = st.columns(4)
c1.metric("Phiên làm việc", selected_session)
c2.metric("Mục tiêu (Target)", "+4 Đơn vị")
c3.metric("Cắt lỗ (Stop Loss)", "-36 Đơn vị")

if cur_cum >= 4:
    c4.metric("Lũy kế", f"+{cur_cum}", "CHỐT LÃI (+4)")
    st.success("🎉 ĐÃ ĐẠT TARGET +4 ĐƠN VỊ! ĐÓNG PHIÊN VÀ DỪNG LẠI.")
elif cur_cum <= -36:
    c4.metric("Lũy kế", f"{cur_cum}", "CẮT LỖ (-36)")
    st.error("⚠️ ĐÃ CHẠM MỨC CẮT LỖ -36! DỪNG PHIÊN.")
else:
    c4.metric("Lũy kế", f"{cur_cum} ĐV", "ĐANG CHẠY")

st.markdown("---")

# Hộp báo tín hiệu ván tiếp theo
pred_type, pred_target = get_prediction_info(next_stt, df_cur)
next_phase, next_stake = calculate_next_capital(df_cur)

st.subheader(f"📌 TÍN HIỆU VÁN TIẾP THEO (STT: {next_stt})")
b1, b2, b3, b4 = st.columns(4)
if next_stt <= 3:
    b1.info(f"Ván mốc {next_stt}/3: Nhập kết quả")
    b2.write("-")
    b3.write("-")
    b4.write("-")
else:
    b1.warning(f"🎯 **BÀN CƯỢC:** {pred_type}")
    b2.error(f"👉 **CỬA VÀO LỆNH:** **{pred_target}**")
    b3.info(f"📊 **GIAI ĐOẠN:** **{next_phase}**")
    b4.success(f"💰 **MỨC CƯỢC:** **{next_stake} ĐƠN VỊ**")

# Form nhập kết quả ván đấu
st.markdown("#### 📝 Nhập kết quả mở thưởng")
with st.form("input_form", clear_on_submit=True):
    col_in1, col_in2, col_in3, col_in4, col_in5 = st.columns(5)
    kq_so = col_in1.number_input("Số ra", min_value=0, max_value=36, value=0, step=1)
    player1 = col_in2.selectbox("Player 1 (3 Cửa)", ["I", "II", "III", "0"])
    player2 = col_in3.selectbox("Player 2 (Đen/Đỏ)", ["ĐỎ", "ĐEN", "0"])
    player3 = col_in4.selectbox("Player 3 (Nhỏ/To)", ["NHỎ", "TO", "0"])
    player4 = col_in5.selectbox("Player 4 (Lẻ/Chẵn)", ["LẺ", "CHẴN", "0"])
    
    submitted = st.form_submit_button("Xác nhận kết quả ván này", use_container_width=True)
    
    if submitted:
        if next_stt <= 3:
            st.session_state.history.append({
                "session_date": str(selected_date),
                "session_name": selected_session,
                "stt": next_stt,
                "kq_so": kq_so,
                "player1": player1,
                "player2": player2,
                "player3": player3,
                "player4": player4,
                "bet_type": "-",
                "prediction": "-",
                "actual_result": "-",
                "win_lose": "MỐC",
                "phase": "-",
                "stake": 0,
                "pnl": 0,
                "cumulative": 0,
                "status": "Dữ liệu mốc"
            })
            st.rerun()
        else:
            if pred_type == "Bàn LẺ / CHẴN":
                actual = player4
            elif pred_type == "Bàn NHỎ / TO":
                actual = player3
            else:
                actual = player2
                
            wl = "WIN" if actual == pred_target else "LOSE"
            pnl = next_stake if wl == "WIN" else -next_stake
            new_cum = cur_cum + pnl
            status = "ĐẠT TARGET (+4)" if new_cum >= 4 else ("CẮT LỖ (-36)" if new_cum <= -36 else "TIẾP TỤC")
            
            st.session_state.history.append({
                "session_date": str(selected_date),
                "session_name": selected_session,
                "stt": next_stt,
                "kq_so": kq_so,
                "player1": player1,
                "player2": player2,
                "player3": player3,
                "player4": player4,
                "bet_type": pred_type,
                "prediction": pred_target,
                "actual_result": actual,
                "win_lose": wl,
                "phase": next_phase,
                "stake": next_stake,
                "pnl": pnl,
                "cumulative": new_cum,
                "status": status
            })
            st.rerun()

# Nút hoàn tác, xóa phiên và xuất file
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
if col_btn1.button("↩️ Xóa ván gần nhất"):
    if st.session_state.history:
        st.session_state.history.pop()
        st.rerun()

if col_btn2.button("🗑️ Reset phiên này"):
    st.session_state.history = [
        item for item in st.session_state.history 
        if not (item["session_date"] == str(selected_date) and item["session_name"] == selected_session)
    ]
    st.rerun()

if not df_cur.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_cur.to_excel(writer, index=False, sheet_name=selected_session[:10])
    excel_data = output.getvalue()
    col_btn3.download_button(
        label="📥 Tải lịch sử phiên về Excel",
        data=excel_data,
        file_name=f"Lich_Su_{selected_session}_{selected_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("### 📋 Diễn biến chi tiết trong phiên")
if not df_cur.empty:
    st.dataframe(df_cur[[
        "stt", "kq_so", "player1", "player2", "player3", "player4",
        "bet_type", "prediction", "actual_result", "win_lose",
        "phase", "stake", "pnl", "cumulative", "status"
    ]], use_container_width=True)
else:
    st.info("Chưa có ván nào trong phiên này. Nhập 3 ván đầu tiên để làm mốc tín hiệu.")
