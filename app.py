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
# CSS GIAO DIỆN CẢNH BÁO: CHỮ TO RÕ NÉT THEO QUY CHUẨN
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
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        font-size: 26px;
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
    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(211, 47, 47, 0.4); }
        70% { transform: scale(1.02); box-shadow: 0 0 0 15px rgba(211, 47, 47, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(211, 47, 47, 0); }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# HÀM LOGIC TÍNH BẢNG PHỤ 1 (BIG EYE BOY) THEO CHUẨN QUỐC TẾ
# ==============================================================================
def calculate_big_eye_boy(hands):
    """
    Tính danh sách các hạt ['RED', 'BLUE'] của Bảng Phụ 1 từ chuỗi Big Road
    """
    if len(hands) < 2:
        return []
    
    cols = []
    curr = [hands[0]]
    big_eye = []
    temp_cols = []
    
    for idx in range(1, len(hands)):
        h = hands[idx]
        if h == curr[-1]:
            curr.append(h)
            is_new = False
        else:
            temp_cols.append(curr)
            curr = [h]
            is_new = True
            
        all_cols = temp_cols + [curr]
        k = len(all_cols)
        row = len(curr)
        
        # Bắt đầu xuất hiện hạt Bảng Phụ 1: (Cột 2 dòng >= 2) hoặc (Cột >= 3)
        if (k == 2 and row >= 2) or (k >= 3):
            if not is_new:
                left_col_len = len(all_cols[k-2])
                if row <= left_col_len:
                    big_eye.append('RED')
                elif row == left_col_len + 1:
                    big_eye.append('RED')
                else:
                    big_eye.append('BLUE')
            else:
                if len(all_cols[k-2]) == len(all_cols[k-3]):
                    big_eye.append('RED')
                else:
                    big_eye.append('BLUE')
    return big_eye

def predict_next_hand_for_red(hands):
    """
    Tự động thử nghiệm ván sau: Đánh B hay P thì hạt tiếp theo của Bảng Phụ 1 sẽ là HẠT ĐỎ
    """
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
        return hands[-1], f"Cả 2 đều Đỏ -> Bắt bám cầu ván trước: {hands[-1]}"
    else:
        return hands[-1], f"Ưu tiên nhịp cầu: {hands[-1]}"

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

if "table_hands" not in st.session_state:
    st.session_state["table_hands"] = []

if "order_in_session" not in st.session_state:
    st.session_state["order_in_session"] = 1

if "table_bet_step" not in st.session_state:
    st.session_state["table_bet_step"] = 1

if "current_stake" not in st.session_state:
    st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10

# Trạng thái bàn: "WAIT" (đang chờ hạt 1), "RED_READY" (đủ đk hạt đỏ), "BLUE_SKIP" (hạt 1 là xanh -> bỏ bàn)
if "table_state" not in st.session_state:
    st.session_state["table_state"] = "WAIT"

# ==============================================================================
# THANH BÊN (SIDEBAR): VỐN CƠ SỞ & LỢI NHUẬN
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
        st.success("Đã cập nhật Vốn cơ sở!")

    col_b_reset, col_b_new = st.columns(2)
    with col_b_reset:
        if st.button("🔄 Reset Vốn", use_container_width=True):
            st.session_state["base_capital"] = 5000.0
            st.session_state["current_stake"] = 500.0
            st.session_state["session_pnl"] = 0.0
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

# 1. KIỂM TRA ĐIỀU KIỆN CHỐT LÃI STOP LUÔN (+9.5% - 10%)
target_min = st.session_state["base_capital"] * 0.095

if not st.session_state["session_running"] or st.session_state["session_pnl"] >= target_min:
    st.markdown("""
        <div class="alert-stop">
            🛑 CẢNH BÁO: STOP LUÔN! ĐẠT TARGET PHIÊN NÀY (+9.5% - 10%)! KHÓA PHIÊN!
        </div>
    """, unsafe_allow_html=True)
    st.success(f"🎉 Hoàn thành Phiên {st.session_state['current_session_id']}! Lợi nhuận: **{st.session_state['session_pnl']:+,.2f}$**. Bấm **'➕ Phiên Mới'** ở thanh bên trái khi bắt đầu phiên tiếp theo.")
else:
    # 2. XÁC ĐỊNH TRẠNG THÁI BẢNG PHỤ 1
    eye_list = calculate_big_eye_boy(st.session_state["table_hands"])
    
    # Nếu đang chờ và Bảng Phụ 1 vừa xuất hiện hạt đầu tiên
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
        st.markdown(f"#### 📢 Tín Hiệu Vào Lệnh (Lệnh thứ {st.session_state['order_in_session']})")
        
        # TRƯỜNG HỢP 1: BẢNG PHỤ 1 RA HẠT XANH -> BỎ BÀN TÌM BÀN MỚI
        if st.session_state["table_state"] == "BLUE_SKIP":
            st.markdown("""
                <div class="alert-skip-table">
                    🛑 HẠT ĐẦU TIÊN BẢNG PHỤ 1 LÀ XANH -> KHÔNG ĐẠT ĐIỀU KIỆN! BỎ BÀN NÀY, TÌM BÀN MỚI NGAY!
                </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 Đã Đổi Sang Bàn Mới Tinh (Bấm Để Bắt Đầu Bàn Mới)", use_container_width=True, type="primary"):
                st.session_state["table_hands"] = []
                st.session_state["table_state"] = "WAIT"
                st.session_state["table_bet_step"] = 1
                st.rerun()

        # TRƯỜNG HỢP 2: ĐANG CHỜ BÀN MỞ RA HẠT ĐẦU TIÊN CỦA BẢNG PHỤ 1
        elif st.session_state["table_state"] == "WAIT":
            st.markdown("""
                <div class="alert-wait">
                    ⏳ CHƯA ĐỦ ĐIỀU KIỆN VÀO LỆNH: HÃY NHẬP KẾT QUẢ ĐỂ BẢNG PHỤ 1 XUẤT HIỆN HẠT ĐẦU TIÊN
                </div>
            """, unsafe_allow_html=True)
            st.caption(f"Các ván mồi đã nhập: {' - '.join(st.session_state['table_hands']) if st.session_state['table_hands'] else 'Chưa có'}")

        # TRƯỜNG HỢP 3: HẠT ĐẦU TIÊN LÀ ĐỎ -> ĐỦ ĐIỀU KIỆN VÀO LỆNH!
        elif st.session_state["table_state"] == "RED_READY":
            predicted_side, reason_text = predict_next_hand_for_red(st.session_state["table_hands"])
            
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
        st.caption(f"Trạng thái: **Ván {st.session_state['table_bet_step']} / 2 ván tối đa của bàn**")

    # ==============================================================================
    # BẢNG ĐIỀU KHIỂN DUY NHẤT: BẠN CHỈ BẤM KẾT QUẢ VÁN BÀI VỪA MỞ RA
    # ==============================================================================
    st.markdown("---")
    st.markdown("### 🎲 Nhập Kết Quả Ván Bài Vừa Mở Tại Bàn (Hệ Thống Tự So Sánh & Tính Tiền)")
    
    col_btn_b, col_btn_p, col_btn_t = st.columns(3)
    
    # ------------------ KHI BẤM BANKER (B) ------------------
    with col_btn_b:
        if st.button("🔴 BÀN VỪA MỞ RA: BANKER (B)", use_container_width=True, type="primary"):
            actual_result = "B"
            
            # Nếu đang trong trạng thái VÀO LỆNH -> Tự động so sánh dự đoán với thực tế
            if st.session_state["table_state"] == "RED_READY" and predicted_side is not None:
                is_win = (predicted_side == actual_result)
                stake = st.session_state["current_stake"]
                
                if is_win:
                    win_profit = stake * 0.95 # Banker ăn phế 5%
                    st.session_state["session_pnl"] += win_profit
                    st.session_state["daily_history"].append({
                        "Ngày": today_str,
                        "Phiên": st.session_state["current_session_id"],
                        "STT Lệnh": st.session_state["order_in_session"],
                        "Cửa Đánh": "BANKER" if predicted_side == "B" else "PLAYER",
                        "Kết Quả Thực Tế": actual_result,
                        "Đúng/Sai": "WIN (Thắng)",
                        "Tiền Cược ($)": stake,
                        "Tiền Lãi/Lỗ ($)": win_profit,
                        "Lợi Nhuận Lũy Kế ($)": st.session_state["session_pnl"]
                    })
                    
                    # Điều kiện 1: Lệnh 1 WIN -> STOP LUÔN
                    if st.session_state["order_in_session"] == 1:
                        st.session_state["session_running"] = False
                        st.rerun()
                        
                    # Điều kiện chạm target phiên
                    if st.session_state["session_pnl"] >= target_min:
                        st.session_state["session_running"] = False
                        st.rerun()
                        
                    # Thắng ván 1 -> Dừng bàn cũ, đổi bàn mới
                    st.session_state["table_hands"] = []
                    st.session_state["table_state"] = "WAIT"
                    st.session_state["table_bet_step"] = 1
                    
                    # Quản lý vốn: Vốn >= cơ sở -> Reset 10%. Vẫn âm -> Gấp đôi 20%
                    if st.session_state["session_pnl"] >= 0:
                        st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10
                    else:
                        st.session_state["current_stake"] = st.session_state["base_capital"] * 0.20
                        
                    st.session_state["order_in_session"] += 1
                    st.rerun()
                else:
                    # LOSE (THUA)
                    st.session_state["session_pnl"] -= stake
                    st.session_state["daily_history"].append({
                        "Ngày": today_str,
                        "Phiên": st.session_state["current_session_id"],
                        "STT Lệnh": st.session_state["order_in_session"],
                        "Cửa Đánh": "BANKER" if predicted_side == "B" else "PLAYER",
                        "Kết Quả Thực Tế": actual_result,
                        "Đúng/Sai": "LOSE (Thua)",
                        "Tiền Cược ($)": stake,
                        "Tiền Lãi/Lỗ ($)": -stake,
                        "Lợi Nhuận Lũy Kế ($)": st.session_state["session_pnl"]
                    })
                    
                    # Thua ván 1 -> Đánh tiếp ván 2 của bàn đó
                    if st.session_state["table_bet_step"] == 1:
                        st.session_state["table_bet_step"] = 2
                        st.session_state["table_hands"].append(actual_result)
                    else:
                        # Thua ván 2 -> Đổi bàn mới tinh
                        st.session_state["table_hands"] = []
                        st.session_state["table_state"] = "WAIT"
                        st.session_state["table_bet_step"] = 1
                        
                    # Lệnh trước thua -> Lệnh sau đánh bằng tiền cơ sở (10%)
                    st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10
                    st.session_state["order_in_session"] += 1
                    st.rerun()
            else:
                # Nếu đang ở giai đoạn ván mồi (WAIT) -> chỉ ghi nhận để tính Bảng Phụ 1
                st.session_state["table_hands"].append("B")
                st.rerun()

    # ------------------ KHI BẤM PLAYER (P) ------------------
    with col_btn_p:
        if st.button("🔵 BÀN VỪA MỞ RA: PLAYER (P)", use_container_width=True):
            actual_result = "P"
            
            if st.session_state["table_state"] == "RED_READY" and predicted_side is not None:
                is_win = (predicted_side == actual_result)
                stake = st.session_state["current_stake"]
                
                if is_win:
                    win_profit = stake * 1.0 # Player ăn đủ
                    st.session_state["session_pnl"] += win_profit
                    st.session_state["daily_history"].append({
                        "Ngày": today_str,
                        "Phiên": st.session_state["current_session_id"],
                        "STT Lệnh": st.session_state["order_in_session"],
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
                        
                    st.session_state["table_hands"] = []
                    st.session_state["table_state"] = "WAIT"
                    st.session_state["table_bet_step"] = 1
                    
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
                        "Cửa Đánh": "BANKER" if predicted_side == "B" else "PLAYER",
                        "Kết QuẢ Thực Tế": actual_result,
                        "Đúng/Sai": "LOSE (Thua)",
                        "Tiền Cược ($)": stake,
                        "Tiền Lãi/Lỗ ($)": -stake,
                        "Lợi Nhuận Lũy Kế ($)": st.session_state["session_pnl"]
                    })
                    
                    if st.session_state["table_bet_step"] == 1:
                        st.session_state["table_bet_step"] = 2
                        st.session_state["table_hands"].append(actual_result)
                    else:
                        st.session_state["table_hands"] = []
                        st.session_state["table_state"] = "WAIT"
                        st.session_state["table_bet_step"] = 1
                        
                    st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10
                    st.session_state["order_in_session"] += 1
                    st.rerun()
            else:
                st.session_state["table_hands"].append("P")
                st.rerun()

    # ------------------ KHI BẤM HÒA (TIE) ------------------
    with col_btn_t:
        if st.button("🟢 BÀN VỪA MỞ RA: HÒA (TIE)", use_container_width=True):
            st.info("Ván Hòa hoàn tiền! Giữ nguyên vị trí lệnh và mức cược.")

# ==============================================================================
# BẢNG NHẬT KÝ VÀO LỆNH TỰ ĐỘNG
# ==============================================================================
st.markdown("---")
st.markdown(f"### 📋 Nhật Ký Vào Lệnh Tự Động Hôm Nay ({today_str})")
if st.session_state["daily_history"]:
    df_history = pd.DataFrame(st.session_state["daily_history"])
    st.dataframe(df_history.iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.caption("Chưa có lệnh nào được thực hiện trong phiên hôm nay.")
