import streamlit as st
import pandas as pd
import datetime
import io

st.set_page_config(
    page_title="Big Eye Engine",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# CSS TỐI ƯU SIÊU GỌN CHO MÀN HÌNH ĐIỆN THOẠI (MOBILE FIRST)
# ==============================================================================
st.markdown("""
<style>
    /* Giảm lề trên cùng của Streamlit để tràn viền điện thoại */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* KHỐI CẢNH BÁO ĐẬP VÀO MẮT */
    .alert-player {
        background-color: #0052cc;
        color: #ffffff;
        padding: 18px 12px;
        border-radius: 12px;
        text-align: center;
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(0, 82, 204, 0.4);
        margin: 8px 0;
    }
    .alert-banker {
        background-color: #d32f2f;
        color: #ffffff;
        padding: 18px 12px;
        border-radius: 12px;
        text-align: center;
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(211, 47, 47, 0.4);
        margin: 8px 0;
    }
    .alert-stop {
        background-color: #ffffff;
        color: #d32f2f;
        border: 4px solid #d32f2f;
        padding: 18px 12px;
        border-radius: 12px;
        text-align: center;
        font-size: 28px;
        font-weight: 900;
        animation: pulse 1.5s infinite;
        margin: 8px 0;
    }
    .alert-skip-table {
        background-color: #fff0f0;
        color: #d32f2f;
        border: 3px solid #ff4d4f;
        padding: 16px 10px;
        border-radius: 12px;
        text-align: center;
        font-size: 22px;
        font-weight: 900;
        margin: 8px 0;
    }
    .alert-wait {
        background-color: #f4f5f7;
        color: #42526e;
        border: 2px dashed #97a0af;
        padding: 18px 10px;
        border-radius: 12px;
        text-align: center;
        font-size: 24px;
        font-weight: 900;
        margin: 8px 0;
    }

    /* Ô HIỂN THỊ TIỀN CƯỢC */
    .stake-box-player {
        background-color: #0052cc;
        color: #ffffff;
        padding: 14px 8px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0, 82, 204, 0.3);
        margin-bottom: 8px;
    }
    .stake-box-banker {
        background-color: #d32f2f;
        color: #ffffff;
        padding: 14px 8px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(211, 47, 47, 0.3);
        margin-bottom: 8px;
    }
    .stake-box-neutral {
        background-color: #f4f5f7;
        color: #172b4d;
        border: 2px solid #dfe1e6;
        padding: 14px 8px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 8px;
    }
    .stake-amount {
        font-size: 28px;
        font-weight: 900;
    }

    /* Ô ÂM / DƯƠNG PHIÊN */
    .pnl-box-negative {
        background-color: #ffebe6;
        border: 2px solid #ff8f73;
        color: #de350b;
        padding: 14px 8px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 8px;
    }
    .pnl-box-positive {
        background-color: #e3fcef;
        border: 2px solid #57d9a3;
        color: #00875a;
        padding: 14px 8px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 8px;
    }
    .pnl-box-zero {
        background-color: #f4f5f7;
        border: 2px solid #dfe1e6;
        color: #42526e;
        padding: 14px 8px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 8px;
    }
    .pnl-amount {
        font-size: 28px;
        font-weight: 900;
    }

    /* HẠT TRÒN BIG ROAD */
    .bead-b {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: #d32f2f;
        color: #ffffff;
        font-weight: 900;
        font-size: 16px;
        margin: 2px;
    }
    .bead-p {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: #0052cc;
        color: #ffffff;
        font-weight: 900;
        font-size: 16px;
        margin: 2px;
    }
    /* HẠT TRÒN BẢNG PHỤ 1 */
    .eye-circle-red {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        border: 3.5px solid #d32f2f;
        background-color: #ffffff;
        margin: 2px;
    }
    .eye-circle-blue {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        border: 3.5px solid #0052cc;
        background-color: #ffffff;
        margin: 2px;
    }
    .table-badge {
        display: inline-block;
        background-color: #ebecf0;
        color: #172b4d;
        padding: 4px 10px;
        border-radius: 16px;
        font-size: 14px;
        font-weight: bold;
        margin-bottom: 6px;
    }

    /* 2 NÚT BẤM TO CHIA ĐỀU 50-50 DÀNH RIÊNG CHO ĐIỆN THOẠI */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {
        background-color: #0052cc !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        font-size: 18px !important;
        border: none !important;
        height: 60px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 10px rgba(0, 82, 204, 0.3) !important;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
        background-color: #d32f2f !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        font-size: 18px !important;
        border: none !important;
        height: 60px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 10px rgba(211, 47, 47, 0.3) !important;
    }

    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(211, 47, 47, 0.4); }
        70% { transform: scale(1.02); box-shadow: 0 0 0 15px rgba(211, 47, 47, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(211, 47, 47, 0); }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# HÀM LOGIC TÍNH BẢNG PHỤ 1 (BIG EYE BOY) CHUẨN XÁC 100% QUỐC TẾ
# ==============================================================================
def calculate_big_eye_boy(hands):
    if len(hands) < 2:
        return []
    
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
            if is_new:
                len1 = len(all_c[k - 2])
                len2 = len(all_c[k - 3])
                big_eye.append('RED' if len1 == len2 else 'BLUE')
            else:
                left_len = len(all_c[k - 2])
                if row <= left_len:
                    big_eye.append('RED')
                elif row == left_len + 1:
                    big_eye.append('BLUE')
                else:
                    big_eye.append('RED')
                    
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
        curr = hands[-1] if hands else 'B'
        return curr, f"Cả 2 đều tạo Đỏ -> Bám thế bệt: {curr}"
    else:
        curr = hands[-1] if hands else 'B'
        return curr, f"Ưu tiên nhịp cầu: {curr}"

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
    st.markdown("## ⚙️ Cấu Hình Vốn")
    new_base = st.number_input(
        "💵 VỐN CƠ SỞ:",
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
                st.warning("Đã hoàn thành tối đa 4 phiên!")

    st.markdown("---")
    st.metric("Phiên hiện tại", f"Phiên {st.session_state['current_session_id']} / 4")
    total_day_pnl = sum([r["Tiền Lãi/Lỗ ($)"] for r in st.session_state["daily_history"]])
    st.metric("Tổng Lãi/Lỗ Hôm Nay", f"{total_day_pnl:+,.2f} $")

    if st.session_state["daily_history"]:
        df_export = pd.DataFrame(st.session_state["daily_history"])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name="Nhat_Ky_Vao_Lenh")
        excel_data = output.getvalue()
        st.download_button(
            label="📥 Tải Nhật Ký Excel",
            data=excel_data,
            file_name=f"Baccarat_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ==============================================================================
# GIAO DIỆN CHÍNH (ĐÃ BỎ TIÊU ĐỀ LỚN)
# ==============================================================================
target_min = st.session_state["base_capital"] * 0.095

if not st.session_state["session_running"] or st.session_state["session_pnl"] >= target_min:
    st.markdown("""
        <div class="alert-stop">
            🛑 CẢNH BÁO: STOP LUÔN! ĐẠT TARGET (+9.5% - 10%)! KHÓA PHIÊN!
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
    
    # DÒNG THÔNG BÁO VỊ TRÍ BÀN & LỆNH
    st.markdown(f"<div class='table-badge'>🏢 BÀN {st.session_state['table_id']} | LỆNH THỨ {st.session_state['order_in_session']} (PHIÊN {st.session_state['current_session_id']})</div>", unsafe_allow_html=True)

    # KHU VỰC CẢNH BÁO
    if st.session_state["table_state"] == "BLUE_SKIP":
        st.markdown("""
            <div class="alert-skip-table">
                🛑 HẠT ĐẦU RA XANH -> BỎ BÀN NÀY, TÌM BÀN MỚI!
            </div>
        """, unsafe_allow_html=True)
    elif st.session_state["table_state"] == "WAIT":
        # ĐÃ RÚT GỌN THÀNH "⏳ CHỜ ĐỦ ĐIỀU KIỆN"
        st.markdown("""
            <div class="alert-wait">
                ⏳ CHỜ ĐỦ ĐIỀU KIỆN
            </div>
        """, unsafe_allow_html=True)
    elif st.session_state["table_state"] == "RED_READY":
        predicted_side, reason_text = predict_next_hand_for_red(st.session_state["table_hands"])
        
        step_label = "VÁN 1" if st.session_state["table_bet_step"] == 1 else "VÁN 2 (LỆNH CUỐI BÀN)"
        if predicted_side == "P":
            st.markdown(f"""
                <div class="alert-player">
                    👉 VÀO PLAYER ({step_label})
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="alert-banker">
                    👉 VÀO BANKER ({step_label})
                </div>
            """, unsafe_allow_html=True)

    # 2 Ô THÔNG SỐ: MỨC CƯỢC & ÂM/DƯƠNG
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        stake_val = st.session_state["current_stake"]
        stake_rate = (stake_val / st.session_state["base_capital"]) * 100
        
        if st.session_state["table_state"] == "RED_READY" and predicted_side == "P":
            st.markdown(f"""
                <div class="stake-box-player">
                    <div style="font-size: 12px; font-weight: bold; opacity: 0.9;">CƯỢC PLAYER ({stake_rate:.0f}%)</div>
                    <div class="stake-amount">{stake_val:,.0f} $</div>
                </div>
            """, unsafe_allow_html=True)
        elif st.session_state["table_state"] == "RED_READY" and predicted_side == "B":
            st.markdown(f"""
                <div class="stake-box-banker">
                    <div style="font-size: 12px; font-weight: bold; opacity: 0.9;">CƯỢC BANKER ({stake_rate:.0f}%)</div>
                    <div class="stake-amount">{stake_val:,.0f} $</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="stake-box-neutral">
                    <div style="font-size: 12px; font-weight: bold; color: #5e6c84;">MỨC CƯỢC ({stake_rate:.0f}%)</div>
                    <div class="stake-amount" style="color: #172b4d;">{stake_val:,.0f} $</div>
                </div>
            """, unsafe_allow_html=True)

    with col_c2:
        pnl_val = st.session_state["session_pnl"]
        cur_order = st.session_state["order_in_session"]
        
        if pnl_val < 0:
            st.markdown(f"""
                <div class="pnl-box-negative">
                    <div style="font-size: 12px; font-weight: bold;">LỆNH SỐ: {cur_order}</div>
                    <div class="pnl-amount">{pnl_val:,.0f} $</div>
                </div>
            """, unsafe_allow_html=True)
        elif pnl_val > 0:
            st.markdown(f"""
                <div class="pnl-box-positive">
                    <div style="font-size: 12px; font-weight: bold;">LỆNH SỐ: {cur_order}</div>
                    <div class="pnl-amount">+{pnl_val:,.0f} $</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="pnl-box-zero">
                    <div style="font-size: 12px; font-weight: bold;">LỆNH SỐ: {cur_order}</div>
                    <div class="pnl-amount">0 $</div>
                </div>
            """, unsafe_allow_html=True)

    # KHU VỰC HIỂN THỊ HẠT ĐÃ NHẬP & BẢNG PHỤ 1
    col_v1, col_v2 = st.columns([2.2, 0.8])
    with col_v1:
        beads_html = []
        if st.session_state["table_hands"]:
            for h in st.session_state["table_hands"]:
                beads_html.append(f"<span class='bead-{h.lower()}'>{h}</span>")
        if eye_list:
            beads_html.append("<span style='margin: 0 6px; color: #aaa;'>|</span>")
            for e in eye_list:
                cls = 'eye-circle-red' if e == 'RED' else 'eye-circle-blue'
                beads_html.append(f"<span class='{cls}'></span>")
        
        if beads_html:
            st.markdown("".join(beads_html), unsafe_allow_html=True)
        else:
            st.caption("Chưa có ván bài nào.")
    with col_v2:
        if st.button("🔄 Bỏ bàn", use_container_width=True):
            switch_to_new_table()

    # NÚT ĐỔI BÀN HOẶC 2 NÚT BẤM KẾT QUẢ DUY NHẤT (ĐÃ BỎ HÒA)
    if st.session_state["table_state"] == "BLUE_SKIP":
        if st.button("🔄 ĐỔI SANG BÀN MỚI TINH", use_container_width=True, type="primary"):
            switch_to_new_table()
    else:
        # CHỈ CÒN ĐÚNG 2 NÚT BẤM TO CHIA ĐỀU 50% - 50%
        col_btn_p, col_btn_b = st.columns(2)

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
                        "Ván": f"{current_step}/2",
                        "Cửa Đánh": "BANKER" if predicted_side == "B" else "PLAYER",
                        "Kết Quả": actual_result,
                        "Đúng/Sai": "WIN",
                        "Tiền Cược": stake,
                        "Lãi/Lỗ": win_profit,
                        "Lũy Kế": st.session_state["session_pnl"]
                    })
                    
                    if st.session_state["order_in_session"] == 1:
                        st.session_state["session_running"] = False
                        st.rerun()
                        
                    if st.session_state["session_pnl"] >= target_min:
                        st.session_state["session_running"] = False
                        st.rerun()
                        
                    # Thắng -> Đổi bàn mới
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
                        "Ván": f"{current_step}/2",
                        "Cửa Đánh": "BANKER" if predicted_side == "B" else "PLAYER",
                        "Kết Quả": actual_result,
                        "Đúng/Sai": "LOSE",
                        "Tiền Cược": stake,
                        "Lãi/Lỗ": -stake,
                        "Lũy Kế": st.session_state["session_pnl"]
                    })
                    
                    if current_step == 1:
                        st.session_state["table_bet_step"] = 2
                        st.session_state["table_hands"].append(actual_result)
                    else:
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
            if st.button("🔵 PLAYER (P)", use_container_width=True):
                process_result("P")

        with col_btn_b:
            if st.button("🔴 BANKER (B)", use_container_width=True):
                process_result("B")

# ==============================================================================
# NHẬT KÝ VÀO LỆNH GỌN GÀNG Ở DƯỚI CÙNG
# ==============================================================================
if st.session_state["daily_history"]:
    st.markdown("---")
    with st.expander("📋 Xem Nhật Ký Chi Tiết", expanded=False):
        df_history = pd.DataFrame(st.session_state["daily_history"])
        st.dataframe(df_history.iloc[::-1], use_container_width=True, hide_index=True)
