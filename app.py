import streamlit as st
import pandas as pd
import datetime
import io

st.set_page_config(
    page_title="Baccarat Big Eye Road Strategy Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# CSS GIAO DIỆN CẢNH BÁO: CHỮ TO IN ĐẬM RÕ NÉT THEO YÊU CẦU
# ==============================================================================
st.markdown("""
<style>
    .alert-player {
        background-color: #0052cc;
        color: #ffffff;
        padding: 26px;
        border-radius: 14px;
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
        padding: 26px;
        border-radius: 14px;
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
        border: 5px solid #d32f2f;
        padding: 26px;
        border-radius: 14px;
        text-align: center;
        font-size: 36px;
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
        border-radius: 14px;
        text-align: center;
        font-size: 28px;
        font-weight: 900;
        margin: 15px 0;
    }
    .alert-wait {
        background-color: #f4f5f7;
        color: #172b4d;
        border: 2px dashed #97a0af;
        padding: 22px;
        border-radius: 14px;
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
# HÀM LOGIC SUY LUẬN BẢNG PHỤ 1 (BIG EYE ROAD)
# ==============================================================================
def calculate_big_eye_beads(history):
    """
    Tính danh sách các hạt ['RED', 'BLUE'] của Bảng Phụ 1 theo chuẩn Casino
    Hạt đầu tiên bắt đầu vẽ khi:
    - Cột 2 dòng 2 (k == 2 and r >= 2)
    - HOẶC Cột 3 dòng 1 (k >= 3)
    """
    if len(history) < 2:
        return []
    
    cols = []
    c_col = [history[0]]
    beads = []
    
    for idx in range(1, len(history)):
        item = history[idx]
        if item == c_col[-1]:
            c_col.append(item)
            is_new_col = False
        else:
            cols.append(c_col)
            c_col = [item]
            is_new_col = True
            
        all_cols = cols + [c_col]
        k = len(all_cols)
        r = len(c_col)
        
        if (k == 2 and r >= 2) or (k >= 3):
            if not is_new_col:
                left_len = len(all_cols[k-2])
                if r <= left_len:
                    beads.append('RED')
                elif r == left_len + 1:
                    beads.append('RED')
                else:
                    beads.append('BLUE')
            else:
                if len(all_cols[k-2]) == len(all_cols[k-3]):
                    beads.append('RED')
                else:
                    beads.append('BLUE')
    return beads

def predict_side_for_red(history):
    """
    Suy luận xem ván tiếp theo ra B hay P thì Bảng Phụ 1 ra HẠT ĐỎ
    """
    curr_beads_len = len(calculate_big_eye_beads(history))
    
    b_test = history + ['B']
    p_test = history + ['P']
    
    beads_b = calculate_big_eye_beads(b_test)
    beads_p = calculate_big_eye_beads(p_test)
    
    last_b = beads_b[-1] if len(beads_b) > curr_beads_len else None
    last_p = beads_p[-1] if len(beads_p) > curr_beads_len else None
    
    if last_b == 'RED' and last_p != 'RED':
        return 'B'
    elif last_p == 'RED' and last_b != 'RED':
        return 'P'
    elif last_b == 'RED' and last_p == 'RED':
        return history[-1] if history else 'B'
    else:
        return 'P' if history and history[-1] == 'B' else 'B'

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

if "is_qualified" not in st.session_state:
    st.session_state["is_qualified"] = False

if "table_status_msg" not in st.session_state:
    st.session_state["table_status_msg"] = "WAITING_FIRST_BEAD"

# ==============================================================================
# THANH BÊN (SIDEBAR): QUẢN LÝ VỐN VÀ XUẤT BÁO CÁO
# ==============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Cấu Hình Vốn & Phiên")
    
    new_base = st.number_input(
        "💵 VỐN CƠ SỞ (Có thể sửa đổi):",
        min_value=10.0,
        value=float(st.session_state["base_capital"]),
        step=100.0
    )
    if new_base != st.session_state["base_capital"]:
        st.session_state["base_capital"] = new_base
        if st.session_state["order_in_session"] == 1:
            st.session_state["current_stake"] = new_base * 0.10
        st.success("Đã cập nhật Vốn cơ sở!")

    col_btn_reset, col_btn_new_ses = st.columns(2)
    with col_btn_reset:
        if st.button("🔄 Reset Vốn", use_container_width=True):
            st.session_state["base_capital"] = 5000.0
            st.session_state["current_stake"] = 500.0
            st.session_state["session_pnl"] = 0.0
            st.session_state["order_in_session"] = 1
            st.session_state["table_bet_step"] = 1
            st.session_state["session_running"] = True
            st.session_state["table_hands"] = []
            st.session_state["is_qualified"] = False
            st.session_state["table_status_msg"] = "WAITING_FIRST_BEAD"
            st.rerun()

    with col_btn_new_ses:
        if st.button("➕ Phiên Mới", use_container_width=True):
            if st.session_state["current_session_id"] < 4:
                st.session_state["current_session_id"] += 1
                st.session_state["session_pnl"] = 0.0
                st.session_state["order_in_session"] = 1
                st.session_state["table_bet_step"] = 1
                st.session_state["session_running"] = True
                st.session_state["table_hands"] = []
                st.session_state["is_qualified"] = False
                st.session_state["table_status_msg"] = "WAITING_FIRST_BEAD"
                st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10
                st.rerun()
            else:
                st.warning("Đã hoàn thành tối đa 4 phiên trong ngày!")

    st.markdown("---")
    st.markdown("### 📊 Thống Kê Tổng Hợp")
    total_day_pnl = sum([r["Tiền Lãi/Lỗ ($)"] for r in st.session_state["daily_history"]])
    
    st.metric("Phiên hiện tại", f"Phiên {st.session_state['current_session_id']} / 4")
    st.metric(
        "Lợi Nhuận Phiên Này ($)",
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
            label="📥 Tải Báo Cáo Ra Excel",
            data=excel_data,
            file_name=f"Baccarat_Log_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# ==============================================================================
# GIAO DIỆN CHÍNH
# ==============================================================================
st.markdown("<h2 style='text-align: center; color: #1F4E78;'>🎯 BACCARAT AUTOMATIC ROAD & MONEY ENGINE</h2>", unsafe_allow_html=True)

# 1. KIỂM TRA ĐIỀU KIỆN CHỐT LÃI STOP LUÔN (+9.5% ~ 10%)
target_min = st.session_state["base_capital"] * 0.095

if not st.session_state["session_running"] or st.session_state["session_pnl"] >= target_min:
    st.markdown("""
        <div class="alert-stop">
            🛑 CẢNH BÁO: STOP LUÔN! ĐẠT TARGET PHIÊN NÀY (+9.5% - 10%)! KHÓA PHIÊN!
        </div>
    """, unsafe_allow_html=True)
    st.success(f"🎉 Hoàn thành xuất sắc Phiên {st.session_state['current_session_id']}! Lợi nhuận: **{st.session_state['session_pnl']:+,.2f}$**. Bấm **'➕ Phiên Mới'** bên trái để bắt đầu phiên tiếp.")
else:
    # 2. XÁC ĐỊNH TRẠNG THÁI BẢNG PHỤ 1
    eye_beads = calculate_big_eye_beads(st.session_state["table_hands"])
    predicted_target = None
    
    col_c1, col_c2 = st.columns([1.8, 1.2])
    
    with col_c1:
        st.markdown(f"#### 📢 Tín Hiệu Vào Lệnh (Lệnh thứ {st.session_state['order_in_session']})")
        
        # TRƯỜNG HỢP A: BẢNG PHỤ 1 RA HẠT XANH -> BỎ BÀN TÌM BÀN MỚI
        if st.session_state["table_status_msg"] == "BLUE_SKIP":
            st.markdown("""
                <div class="alert-skip-table">
                    🛑 BẢNG PHỤ 1 VỪA RA HẠT XANH -> KHÔNG ĐỦ ĐIỀU KIỆN! BỎ BÀN NÀY, TÌM BÀN MỚI NGAY!
                </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 ĐÃ ĐỔI SANG BÀN MỚI TINH KHÁC", use_container_width=True, type="primary"):
                st.session_state["table_hands"] = []
                st.session_state["is_qualified"] = False
                st.session_state["table_status_msg"] = "WAITING_FIRST_BEAD"
                st.session_state["table_bet_step"] = 1
                st.rerun()

        # TRƯỜNG HỢP B: CHỜ HẠT ĐẦU TIÊN CỦA BẢNG PHỤ 1
        elif not st.session_state["is_qualified"]:
            st.markdown("""
                <div class="alert-wait">
                    ⏳ ĐANG THEO DÕI BÀN MỚI: HÃY NHẬP KẾT QUẢ CÁC VÁN BÀI VỪA MỞ CHO ĐẾN KHI BẢNG PHỤ 1 RA HẠT ĐẦU TIÊN
                </div>
            """, unsafe_allow_html=True)
            hands_str = " - ".join(st.session_state["table_hands"]) if st.session_state["table_hands"] else "Chưa có ván nào"
            st.caption(f"Lịch sử ván mồi bàn này: **[{hands_str}]** | Hạt Bảng Phụ 1 hiện có: **{len(eye_beads)}**")

        # TRƯỜNG HỢP C: HẠT ĐẦU TIÊN LÀ ĐỎ -> ĐỦ ĐIỀU KIỆN! CẢNH BÁO LỆNH ĐÁNH!
        else:
            predicted_target = predict_side_for_red(st.session_state["table_hands"])
            if predicted_target == "P":
                st.markdown("""
                    <div class="alert-player">
                        👉 CẢNH BÁO: VÀO PLAYER (ĐỂ BẢNG PHỤ 1 RA HẠT ĐỎ)
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="alert-banker">
                        👉 CẢNH BÁO: VÀO BANKER (ĐỂ BẢNG PHỤ 1 RA HẠT ĐỎ)
                    </div>
                """, unsafe_allow_html=True)
            st.caption(f"Trạng thái: Bảng phụ 1 đã có hạt Đỏ đầu tiên. Đang đánh **Ván {st.session_state['table_bet_step']} / 2 ván** tại bàn này.")

    with col_c2:
        st.markdown("#### 💵 Mức Tiền Cược Lệnh Này")
        stake_rate = (st.session_state["current_stake"] / st.session_state["base_capital"]) * 100
        st.metric(
            label="Số tiền cược ván này",
            value=f"{st.session_state['current_stake']:,.2f} $",
            delta=f"{stake_rate:.0f}% Vốn cơ sở"
        )
        st.caption(f"Mục tiêu chốt lãi phiên: **+{target_min:,.2f}$ (+9.5% ~ 10%)**")

    # ==============================================================================
    # BẢNG ĐIỀU KHIỂN DUY NHẤT: BẤM KẾT QUẢ MỞ BÀI THỰC TẾ (BANKER / PLAYER / TIE)
    # ==============================================================================
    st.markdown("---")
    st.markdown("### 🎲 Nhập Kết Quả Thực Tế Mở Ra Tại Bàn (Hệ thống tự động so khớp & tính toán)")
    
    col_btn_b, col_btn_p, col_btn_tie, col_btn_skip = st.columns([1.5, 1.5, 1, 1.2])

    # HÀM XỬ LÝ KHI NGƯỜI DÙNG BẤM KẾT QUẢ VÁN MỚI
    def handle_actual_result(actual):
        st.session_state["table_hands"].append(actual)
        current_beads = calculate_big_eye_beads(st.session_state["table_hands"])
        
        # 1. NẾU CHƯA ĐỦ ĐIỀU KIỆN (ĐANG CHỜ HẠT ĐẦU TIÊN CỦA BẢNG PHỤ 1)
        if not st.session_state["is_qualified"]:
            if len(current_beads) > 0:
                first_bead = current_beads[0]
                if first_bead == 'RED':
                    st.session_state["is_qualified"] = True
                    st.session_state["table_status_msg"] = "RED_TRIGGERED"
                else:
                    st.session_state["is_qualified"] = False
                    st.session_state["table_status_msg"] = "BLUE_SKIP"
            return

        # 2. NẾU ĐÃ ĐỦ ĐIỀU KIỆN VÀ ĐANG VÀO LỆNH (SO SÁNH DỰ ĐOÁN VS THỰC TẾ)
        pred = predicted_target
        stake = st.session_state["current_stake"]
        
        if actual == pred:
            # === KỊCH BẢN THẮNG (WIN) ===
            win_profit = (stake * 0.95) if actual == "B" else float(stake)
            st.session_state["session_pnl"] += win_profit
            
            st.session_state["daily_history"].append({
                "Ngày": today_str,
                "Phiên": st.session_state["current_session_id"],
                "STT Lệnh": st.session_state["order_in_session"],
                "Cửa Đánh": "BANKER" if pred == "B" else "PLAYER",
                "Kết Quả Ra": "BANKER" if actual == "B" else "PLAYER",
                "Phán Đoán": "WIN ✅",
                "Tiền Cược ($)": stake,
                "Lãi/Lỗ ($)": win_profit,
                "Lợi Nhuận Lũy Kế ($)": st.session_state["session_pnl"]
            })
            
            # ĐIỀU KIỆN 1: Lệnh 1 của phiên WIN -> KHÓA PHIÊN NGAY LẬP TỨC!
            if st.session_state["order_in_session"] == 1:
                st.session_state["session_running"] = False
                return
                
            # ĐIỀU KIỆN 2: Đạt mục tiêu +9.5% ~ 10% -> STOP LUÔN
            if st.session_state["session_pnl"] >= target_min:
                st.session_state["session_running"] = False
                return
                
            # QUY TẮC ĐỔI BÀN: Thắng ván 1 -> Đổi bàn mới tinh ngay!
            st.session_state["table_hands"] = []
            st.session_state["is_qualified"] = False
            st.session_state["table_status_msg"] = "WAITING_FIRST_BEAD"
            st.session_state["table_bet_step"] = 1
            
            # QUY TẮC ĐI TIỀN:
            # Nếu vốn hồi phục >= vốn cơ sở -> BẮT BUỘC RESET 10%
            if st.session_state["session_pnl"] >= 0:
                st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10
            else:
                # Nếu vẫn đang âm: ván trước WIN -> ván sau gấp đôi 20%
                st.session_state["current_stake"] = st.session_state["base_capital"] * 0.20
                
            st.session_state["order_in_session"] += 1

        else:
            # === KỊCH BẢN THUA (LOSE) ===
            st.session_state["session_pnl"] -= float(stake)
            
            st.session_state["daily_history"].append({
                "Ngày": today_str,
                "Phiên": st.session_state["current_session_id"],
                "STT Lệnh": st.session_state["order_in_session"],
                "Cửa Đánh": "BANKER" if pred == "B" else "PLAYER",
                "Kết Quả Ra": "BANKER" if actual == "B" else "PLAYER",
                "Phán Đoán": "LOSE ❌",
                "Tiền Cược ($)": stake,
                "Lãi/Lỗ ($)": -stake,
                "Lợi Nhuận Lũy Kế ($)": st.session_state["session_pnl"]
            })
            
            # QUY TẮC BÀN: Thua ván 1 -> Vào tiếp ván 2 của bàn đó
            if st.session_state["table_bet_step"] == 1:
                st.session_state["table_bet_step"] = 2
            else:
                # Đã thua ván 2 -> Chuyển bàn mới tinh
                st.session_state["table_hands"] = []
                st.session_state["is_qualified"] = False
                st.session_state["table_status_msg"] = "WAITING_FIRST_BEAD"
                st.session_state["table_bet_step"] = 1
                
            # QUY TẮC ĐI TIỀN: Thua -> Luôn đánh bằng tiền cơ sở (10%)
            st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10
            st.session_state["order_in_session"] += 1

    with col_btn_b:
        if st.button("🔴 VÁN RA: BANKER", use_container_width=True, type="primary"):
            handle_actual_result("B")
            st.rerun()

    with col_btn_p:
        if st.button("🔵 VÁN RA: PLAYER", use_container_width=True):
            handle_actual_result("P")
            st.rerun()

    with col_btn_tie:
        if st.button("⏸ VÁN RA: HÒA (TIE)", use_container_width=True):
            st.info("Ván Hòa hoàn tiền! Giữ nguyên vị trí cược và vốn.")

    with col_btn_skip:
        if st.button("🔄 Đổi Bàn Mới Tinh", use_container_width=True):
            st.session_state["table_hands"] = []
            st.session_state["is_qualified"] = False
            st.session_state["table_status_msg"] = "WAITING_FIRST_BEAD"
            st.session_state["table_bet_step"] = 1
            st.rerun()

# ==============================================================================
# NHẬT KÝ CHI TIẾT THEO PHIÊN & NGÀY
# ==============================================================================
st.markdown("---")
st.markdown(f"### 📋 Nhật Ký Vào Lệnh Hôm Nay ({today_str})")
if st.session_state["daily_history"]:
    df_history = pd.DataFrame(st.session_state["daily_history"])
    st.dataframe(df_history.iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.caption("Chưa có lệnh nào được ghi nhận. Hãy bắt đầu nhập kết quả ván mở bài đầu tiên!")
