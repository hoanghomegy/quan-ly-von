import streamlit as st
import pandas as pd
import datetime
import io

st.set_page_config(
    page_title="Baccarat Big Eye Auto Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# CSS GIAO DIỆN CẢNH BÁO, HẠT TRÒN & NÚT ĐỔI BÀN
# ==============================================================================
st.markdown("""
<style>
    .alert-player {
        background-color: #0052cc;
        color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        font-size: 34px;
        font-weight: 900;
        letter-spacing: 2px;
        box-shadow: 0 4px 15px rgba(0, 82, 204, 0.4);
        margin: 15px 0;
    }
    .alert-banker {
        background-color: #d32f2f;
        color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        font-size: 34px;
        font-weight: 900;
        letter-spacing: 2px;
        box-shadow: 0 4px 15px rgba(211, 47, 47, 0.4);
        margin: 15px 0;
    }
    .alert-stop {
        background-color: #ffffff;
        color: #d32f2f;
        border: 4px solid #d32f2f;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        font-size: 34px;
        font-weight: 900;
        letter-spacing: 2px;
        animation: pulse 1.5s infinite;
        margin: 15px 0;
    }
    .alert-skip-table {
        background-color: #fff0f0;
        color: #d32f2f;
        border: 3px solid #ff4d4f;
        padding: 22px;
        border-radius: 12px;
        text-align: center;
        font-size: 28px;
        font-weight: 900;
        margin: 15px 0;
    }
    .alert-wait {
        background-color: #f4f5f7;
        color: #42526e;
        border: 2px dashed #97a0af;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        font-size: 24px;
        font-weight: 700;
        margin: 15px 0;
    }
    /* HẠT TRÒN BIG ROAD */
    .bead-b {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background-color: #d32f2f;
        color: #ffffff;
        font-weight: 900;
        font-size: 18px;
        margin: 3px;
        box-shadow: 0 2px 5px rgba(211, 47, 47, 0.4);
    }
    .bead-p {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background-color: #0052cc;
        color: #ffffff;
        font-weight: 900;
        font-size: 18px;
        margin: 3px;
        box-shadow: 0 2px 5px rgba(0, 82, 204, 0.4);
    }
    /* HẠT TRÒN BẢNG PHỤ 1 */
    .eye-circle-red {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        border: 4px solid #d32f2f;
        background-color: #ffffff;
        margin: 3px;
        box-shadow: 0 2px 4px rgba(211, 47, 47, 0.2);
    }
    .eye-circle-blue {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        border: 4px solid #0052cc;
        background-color: #ffffff;
        margin: 3px;
        box-shadow: 0 2px 4px rgba(0, 82, 204, 0.2);
    }
    .table-badge {
        display: inline-block;
        background-color: #ebecf0;
        color: #172b4d;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 8px;
    }

    /* MÀU NỀN 3 NÚT NHẬP KẾT QUẢ */
    div.row-widget.stButton > button, div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {
        background-color: #0052cc !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        font-size: 17px !important;
        border: none !important;
        height: 54px !important;
        border-radius: 8px !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
        background-color: #d32f2f !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        font-size: 17px !important;
        border: none !important;
        height: 54px !important;
        border-radius: 8px !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button {
        background-color: #2e7d32 !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        font-size: 17px !important;
        border: none !important;
        height: 54px !important;
        border-radius: 8px !important;
    }

    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(211, 47, 47, 0.4); }
        70% { transform: scale(1.02); box-shadow: 0 0 0 15px rgba(211, 47, 47, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(211, 47, 47, 0); }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# HÀM LOGIC TÍNH BẢNG PHỤ 1 (BIG EYE BOY) CHUẨN XÁC QUỐC TẾ
# ==============================================================================
def calculate_big_eye_boy(hands):
    if len(hands) < 2:
        return []
    
    cols = []
    curr = [hands[0]]
    for h in hands[1:]:
        if h == curr[-1]:
            curr.append(h)
        else:
            cols.append(curr)
            curr = [h]
    cols.append(curr)
    
    big_eye = []
    temp_cols = []
    curr_c = [hands[0]]
    
    for idx in range(1, len(hands)):
        h = hands[idx]
        if h == curr_c[-1]:
            curr_c.append(h)
            is_new = False
        else:
            temp_cols.append(curr_c)
            curr_c = [h]
            is_new = True
            
        all_c = temp_cols + [curr_c]
        k = len(all_c)
        row = len(curr_c)
        
        if (k == 2 and row >= 2) or (k >= 3):
            if not is_new:
                left_len = len(all_c[k - 2])
                if row <= left_len:
                    big_eye.append('RED')
                else:
                    big_eye.append('BLUE')
            else:
                len_prev1 = len(all_c[k - 2])
                len_prev2 = len(all_c[k - 3])
                if len_prev1 == len_prev2:
                    big_eye.append('RED')
                else:
                    big_eye.append('BLUE')
                    
    return big_eye

def predict_next_hand_for_red(hands):
    eye_now = calculate_big_eye_boy(hands)
    eye_b = calculate_big_eye_boy(hands + ['B'])
    eye_p = calculate_big_eye_boy(hands + ['P'])
    
    b_gives_red = (len(eye_b) > len(eye_now)) and (eye_b[-1] == 'RED')
    p_gives_red = (len(eye_p) > len(eye_now)) and (eye_p[-1] == 'RED')
    
    if b_gives_red and not p_gives_red:
        return 'B', "Đánh BANKER để Bảng Phụ 1 ra Hạt Đỏ"
    elif p_gives_red and not b_gives_red:
        return 'P', "Đánh PLAYER để Bảng Phụ 1 ra Hạt Đỏ"
    elif b_gives_red and p_gives_red:
        opp = 'P' if hands[-1] == 'B' else 'B'
        return opp, f"Cả 2 đều Đỏ -> Bắt nhịp cầu nhảy: {opp}"
    else:
        opp = 'P' if hands[-1] == 'B' else 'B'
        return opp, f"Dự phòng nhịp đổi: {opp}"

# ==============================================================================
# KHỞI TẠO BỘ NHỚ TRÌNH DUYỆT (SESSION STATE)
# ==============================================================================
today_str = datetime.date.today().strftime("%Y-%m-%d")

if "daily_history" not in st.session_state:
    st.session_state["daily_history"] = []

if "current_session_id" not in st.session_state:
    st.session_state["current_session_id"] = 1

if "base_capital" not in st.session_state:
    st.session_state["base_capital"] = 5000.0

if "session_running" not in st.session_state:
    st.session_state["session_running"] = True

if "session_pnl" not in st.session_state:
    st.session_state["session_pnl"] = 0.0

if "table_id" not in st.session_state:
    st.session_state["table_id"] = 1

if "table_hands" not in st.session_state:
    st.session_state["table_hands"] = []

if "order_in_session" not in st.session_state:
    st.session_state["order_in_session"] = 1

if "table_bet_step" not in st.session_state:
    st.session_state["table_bet_step"] = 1

if "current_stake" not in st.session_state:
    st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10

if "table_state" not in st.session_state:
    st.session_state["table_state"] = "WAIT"

# ==============================================================================
# HÀM TIỆN ÍCH: ĐỔI SANG BÀN MỚI TINH
# ==============================================================================
def switch_to_new_table():
    st.session_state["table_hands"] = []
    st.session_state["table_state"] = "WAIT"
    st.session_state["table_bet_step"] = 1
    st.session_state["table_id"] += 1
    st.rerun()

# ==============================================================================
# THANH BÊN (SIDEBAR)
# ==============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Cấu Hình Vốn & Phiên")
    
    new_base = st.number_input(
        "💵 VỐN CƠ SỞ (Sửa đổi & Tự động lưu):",
        min_value=10.0,
        value=float(st.session_state["base_capital"]),
        step=100.0
    )
    if new_base != st.session_state["base_capital"]:
        st.session_state["base_capital"] = new_base
        if st.session_state["order_in_session"] == 1:
            st.session_state["current_stake"] = new_base * 0.10
        st.success("Đã cập nhật Vốn cơ sở mới!")

    col_b_reset, col_b_new = st.columns(2)
    with col_b_reset:
        if st.button("🔄 Reset Vốn", use_container_width=True):
            st.session_state["base_capital"] = 5000.0
            st.session_state["current_stake"] = 500.0
            st.session_state["session_pnl"] = 0.0
            st.session_state["table_id"] = 1
            st.session_state["order_in_session"] = 1
            st.session_state["table_bet_step"] = 1
            st.session_state["session_running"] = True
            st.session_state["table_hands"] = []
            st.session_state["table_state"] = "WAIT"
            st.rerun()

    with col_b_new:
        if st.button("➕ Phiên Mới", use_container_width=True):
            if st.session_state["current_session_id"] < 4:
                st.session_state["current_session_id"] += 1
                st.session_state["session_pnl"] = 0.0
                st.session_state["table_id"] = 1
                st.session_state["order_in_session"] = 1
                st.session_state["table_bet_step"] = 1
                st.session_state["session_running"] = True
                st.session_state["table_hands"] = []
                st.session_state["table_state"] = "WAIT"
                st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10
                st.rerun()
            else:
                st.warning("Đã hoàn thành tối đa 4 phiên trong ngày!")

    st.markdown("---")
    st.markdown("### 📊 Thống Kê Lợi Nhuận")
    total_day_pnl = sum([r["Tiền Lãi/Lỗ ($)"] for r in st.session_state["daily_history"]])
    
    st.metric("Phiên hiện tại", f"Phiên {st.session_state['current_session_id']} / 4")
    st.metric(
        "Lợi Nhuận Phiên ($)",
        f"{st.session_state['session_pnl']:+,.2f} $",
        delta=f"{(st.session_state['session_pnl'] / st.session_state['base_capital'])*100:+.1f}%"
    )
    st.metric(
        "Tổng Lợi Nhuận Hôm Nay ($)",
        f"{total_day_pnl:+,.2f} $",
        delta=f"{(total_day_pnl / st.session_state['base_capital'])*100:+.1f}%"
    )

    st.markdown("---")
    if st.session_state["daily_history"]:
        df_export = pd.DataFrame(st.session_state["daily_history"])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name="Nhat_Ky_Vao_Lenh")
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Tải Nhật Ký Ra Excel",
            data=excel_data,
            file_name=f"Baccarat_Log_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ==============================================================================
# GIAO DIỆN CHÍNH
# ==============================================================================
st.markdown("<h2 style='text-align: center; color: #1F4E78;'>🎯 BACCARAT BIG EYE ROAD & MONEY MANAGEMENT ENGINE</h2>", unsafe_allow_html=True)

target_min = st.session_state["base_capital"] * 0.095

if not st.session_state["session_running"] or st.session_state["session_pnl"] >= target_min:
    st.markdown("""
        <div class="alert-stop">
            🛑 CẢNH BÁO: STOP LUÔN! ĐẠT TARGET PHIÊN NÀY (+9.5% - 10%)! KHÓA PHIÊN!
        </div>
    """, unsafe_allow_html=True)
    st.success(f"🎉 Hoàn thành Phiên {st.session_state['current_session_id']}! Lợi nhuận: **{st.session_state['session_pnl']:+,.2f}$**.")
else:
    # 1. Tính toán Bảng Phụ 1 hiện tại
    eye_list = calculate_big_eye_boy(st.session_state["table_hands"])
    
    if st.session_state["table_state"] == "WAIT":
        if len(eye_list) > 0:
            if eye_list[0] == 'RED':
                st.session_state["table_state"] = "RED_READY"
            else:
                st.session_state["table_state"] = "BLUE_SKIP"

    predicted_side = None
    reason_text = ""
    
    col_c1, col_c2 = st.columns([1.8, 1.2])
    with col_c1:
        st.markdown(f"<div class='table-badge'>🏢 ĐANG Ở BÀN SỐ {st.session_state['table_id']} | LỆNH THỨ {st.session_state['order_in_session']} CỦA PHIÊN</div>", unsafe_allow_html=True)
        
        # TRƯỜNG HỢP 1: BẢNG PHỤ 1 RA XANH -> BỎ BÀN
        if st.session_state["table_state"] == "BLUE_SKIP":
            st.markdown("""
                <div class="alert-skip-table">
                    🛑 HẠT ĐẦU TIÊN LÀ XANH -> BỎ BÀN NÀY, TÌM BÀN MỚI NGAY!
                </div>
            """, unsafe_allow_html=True)

        # TRƯỜNG HỢP 2: ĐANG CHỜ HẠT ĐẦU TIÊN
        elif st.session_state["table_state"] == "WAIT":
            st.markdown("""
                <div class="alert-wait">
                    ⏳ CHỜ BÀN MỚI RA HẠT ĐẦU TIÊN Ở BẢNG PHỤ 1 (ĐỎ = ĐỦ ĐIỀU KIỆN, XANH = BỎ BÀN)
                </div>
            """, unsafe_allow_html=True)

        # TRƯỜNG HỢP 3: ĐỦ ĐIỀU KIỆN VÀO LỆNH
        elif st.session_state["table_state"] == "RED_READY":
            predicted_side, reason_text = predict_next_hand_for_red(st.session_state["table_hands"])
            
            step_label = "VÁN 1 (LỆNH MỞ BÀN)" if st.session_state["table_bet_step"] == 1 else "VÁN 2 (LỆNH CUỐI CỦA BÀN NÀY)"
            st.markdown(f"**Trạng thái bàn hiện tại:** `{step_label}`")
            
            if predicted_side == "P":
                st.markdown("""
                    <div class="alert-player">
                        👉 CẢNH BÁO: ĐÁNH PLAYER (ĐỂ BẢNG PHỤ 1 RA HẠT ĐỎ)
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="alert-banker">
                        👉 CẢNH BÁO: ĐÁNH BANKER (ĐỂ BẢNG PHỤ 1 RA HẠT ĐỎ)
                    </div>
                """, unsafe_allow_html=True)
            st.caption(f"🔍 Logic: {reason_text}")

    with col_c2:
        st.markdown("#### 💵 Mức Tiền Cược Lệnh Này")
        stake_rate = (st.session_state["current_stake"] / st.session_state["base_capital"]) * 100
        st.metric(
            label="Số tiền cược ván này",
            value=f"{st.session_state['current_stake']:,.2f} $",
            delta=f"{stake_rate:.0f}% Vốn cơ sở"
        )
        st.caption(f"Trạng thái: **Đang đánh Ván {st.session_state['table_bet_step']} / Tối đa 2 ván**")

    # ==============================================================================
    # KHU VỰC HIỂN THỊ HẠT TRÒN B/P & NÚT ĐỔI BÀN THỦ CÔNG
    # ==============================================================================
    st.markdown("---")
    
    col_v1, col_v2, col_v3 = st.columns([1.5, 1.2, 0.8])
    with col_v1:
        st.write("**Chuỗi ván bài (Big Road) đã nhập:**")
        if st.session_state["table_hands"]:
            beads_html = []
            for h in st.session_state["table_hands"]:
                if h == 'B':
                    beads_html.append("<span class='bead-b'>B</span>")
                else:
                    beads_html.append("<span class='bead-p'>P</span>")
            st.markdown(" ".join(beads_html), unsafe_allow_html=True)
        else:
            st.caption("Chưa có ván bài nào.")
            
    with col_v2:
        st.write("**Bảng Phụ 1 tương ứng:**")
        if eye_list:
            eye_html = []
            for e in eye_list:
                if e == 'RED':
                    eye_html.append("<span class='eye-circle-red'></span>")
                else:
                    eye_html.append("<span class='eye-circle-blue'></span>")
            st.markdown(" ".join(eye_html), unsafe_allow_html=True)
        else:
            st.caption("Chưa đủ ván để xuất hiện hạt đầu tiên.")

    with col_v3:
        st.write("**Thao tác bàn:**")
        if st.button("🔄 Đổi Bàn Này Đi", use_container_width=True):
            switch_to_new_table()

    # ==============================================================================
    # KHU VỰC ĐIỀU KHIỂN & NÚT ĐỔI BÀN MỚI TINH RÕ RÀNG
    # ==============================================================================
    st.markdown("---")
    
    # NẾU GẶP BÀN HẠT XANH -> HIỂN THỊ NÚT TO ĐỂ ĐỔI BÀN, KHÓA NHẬP KẾT QUẢ CŨ
    if st.session_state["table_state"] == "BLUE_SKIP":
        st.markdown("<h3 style='color: #d32f2f; text-align: center;'>⚠️ BÀN NÀY ĐÃ BỊ HỦY DO HẠT ĐẦU TIÊN RA XANH</h3>", unsafe_allow_html=True)
        if st.button("🔄 BẤM VÀO ĐÂY ĐỂ ĐỔI SANG BÀN MỚI TINH (RESET BÀN)", use_container_width=True, type="primary"):
            switch_to_new_table()
    else:
        # ĐANG CHỜ HOẶC ĐANG VÀO LỆNH: HIỂN THỊ 3 NÚT NHẬP KẾT QUẢ
        st.markdown("### 🎲 Nhập Kết Quả Ván Bài Vừa Mở Tại Bàn")
        
        col_btn_p, col_btn_b, col_btn_t = st.columns(3)

        def process_result(actual_result):
            if st.session_state["table_state"] == "RED_READY" and predicted_side is not None:
                is_win = (predicted_side == actual_result)
                stake = st.session_state["current_stake"]
                current_table = st.session_state["table_id"]
                current_step = st.session_state["table_bet_step"]
                
                if is_win:
                    win_profit = (stake * 0.95) if predicted_side == "B" else (stake * 1.0)
                    st.session_state["session_pnl"] += win_profit
                    
                    st.session_state["daily_history"].append({
                        "Ngày": today_str,
                        "Phiên": st.session_state["current_session_id"],
                        "STT Lệnh": st.session_state["order_in_session"],
                        "Bàn": current_table,
                        "Ván Tại Bàn": f"Ván {current_step}/2",
                        "Cửa Đánh": "BANKER" if predicted_side == "B" else "PLAYER",
                        "Kết Quả Thực Tế": actual_result,
                        "Đúng/Sai": "WIN (Thắng)",
                        "Tiền Cược ($)": stake,
                        "Tiền Lãi/Lỗ ($)": win_profit,
                        "Lợi Nhuận Lũy Kế ($)": st.session_state["session_pnl"]
                    })
                    
                    if st.session_state["order_in_session"] == 1:
                        st.session_state["session_running"] = False
                        st.rerun()
                        
                    if st.session_state["session_pnl"] >= target_min:
                        st.session_state["session_running"] = False
                        st.rerun()
                        
                    # Thắng ván 1 hoặc ván 2 -> Chuyển bàn mới
                    st.session_state["table_hands"] = []
                    st.session_state["table_state"] = "WAIT"
                    st.session_state["table_bet_step"] = 1
                    st.session_state["table_id"] += 1
                    
                    if st.session_state["session_pnl"] >= 0:
                        st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10
                    else:
                        st.session_state["current_stake"] = st.session_state["base_capital"] * 0.20
                        
                    st.session_state["order_in_session"] += 1
                    st.rerun()
                    
                else:
                    st.session_state["session_pnl"] -= stake
                    st.session_state["daily_history"].append({
                        "Ngày": today_str,
                        "Phiên": st.session_state["current_session_id"],
                        "STT Lệnh": st.session_state["order_in_session"],
                        "Bàn": current_table,
                        "Ván Tại Bàn": f"Ván {current_step}/2",
                        "Cửa Đánh": "BANKER" if predicted_side == "B" else "PLAYER",
                        "Kết Quả Thực Tế": actual_result,
                        "Đúng/Sai": "LOSE (Thua)",
                        "Tiền Cược ($)": stake,
                        "Tiền Lãi/Lỗ ($)": -stake,
                        "Lợi Nhuận Lũy Kế ($)": st.session_state["session_pnl"]
                    })
                    
                    # Ván 1 Thua -> Tiếp tục Ván 2
                    if current_step == 1:
                        st.session_state["table_bet_step"] = 2
                        st.session_state["table_hands"].append(actual_result)
                    else:
                        # Đã xong Ván 2 mà Thua -> Đổi sang bàn mới
                        st.session_state["table_hands"] = []
                        st.session_state["table_state"] = "WAIT"
                        st.session_state["table_bet_step"] = 1
                        st.session_state["table_id"] += 1
                        
                    st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10
                    st.session_state["order_in_session"] += 1
                    st.rerun()
            else:
                st.session_state["table_hands"].append(actual_result)
                st.rerun()

        with col_btn_p:
            if st.button("🔵 BÀN RA: PLAYER (P)", use_container_width=True):
                process_result("P")

        with col_btn_b:
            if st.button("🔴 BÀN RA: BANKER (B)", use_container_width=True):
                process_result("B")

        with col_btn_t:
            if st.button("🟢 BÀN RA: HÒA (TIE)", use_container_width=True):
                st.info("Ván Hòa hoàn tiền! Giữ nguyên trạng thái lệnh.")

# ==============================================================================
# NHẬT KÝ CHI TIẾT
# ==============================================================================
st.markdown("---")
st.markdown(f"### 📋 Nhật Ký Vào Lệnh Hôm Nay ({today_str})")
if st.session_state["daily_history"]:
    df_history = pd.DataFrame(st.session_state["daily_history"])
    st.dataframe(df_history.iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.caption("Chưa có lệnh nào được thực hiện trong phiên hôm nay.")
