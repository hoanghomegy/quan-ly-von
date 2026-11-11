import streamlit as st
import pandas as pd
import datetime
import io

# Cấu hình giao diện Streamlit
st.set_page_config(
    page_title="Baccarat Big Eye Road Strategy Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# CSS TÙY CHỈNH THEO ĐÚNG YÊU CẦU MÀU SẮC & CHỮ TO RÕ NÉT
# ==============================================================================
st.markdown("""
<style>
    .alert-player {
        background-color: #0052cc;
        color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        font-size: 32px;
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
        font-size: 32px;
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
# HÀM LOGIC SUY LUẬN NGƯỢC BẢNG PHỤ 1 (BIG EYE BOY ROAD)
# ==============================================================================
def get_big_road_matrix(history):
    """Chuyển chuỗi ván bài Big Road thành danh sách độ dài các cột"""
    if not history:
        return []
    columns = []
    current_col = [history[0]]
    for item in history[1:]:
        if item == current_col[-1]:
            current_col.append(item)
        else:
            columns.append(current_col)
            current_col = [item]
    columns.append(current_col)
    return columns

def predict_red_big_eye(history):
    """
    Suy luận xem ván tiếp theo nếu ra Banker hay Player thì Bảng Phụ 1 ra HẠT ĐỎ:
    Quy tắc chuẩn quốc tế:
    - Nếu đi tiếp trong cột hiện tại (xuống dưới): So sánh độ dài cột trước (k - 1) với cột trước nữa (k - 2).
    - Nếu bẻ sang cột mới: So sánh độ dài 2 cột liền kề trước đó. Bằng nhau -> ĐỎ, Khác nhau -> XANH.
    """
    if len(history) < 2:
        return "WAIT", "Chưa đủ ván mồi để tính Bảng Phụ 1 (Cần tối thiểu 2 ván ở bàn mới)"
        
    cols = get_big_road_matrix(history)
    k = len(cols)
    curr_len = len(cols[-1])
    curr_side = cols[-1][0]
    opp_side = 'P' if curr_side == 'B' else 'B'
    
    # 1. Kịch bản nếu ra cùng cửa (tiếp tục cột)
    same_gives_red = False
    if k >= 2:
        prev_len = len(cols[k-2])
        if curr_len < prev_len:
            same_gives_red = True
        elif curr_len == prev_len:
            same_gives_red = False
        else:
            same_gives_red = (curr_len - prev_len == 1)
            
    # 2. Kịch bản nếu bẻ cửa (mở cột mới)
    diff_gives_red = False
    if k >= 2:
        prev_col_len = len(cols[-1])
        ref_col_len = len(cols[-2])
        if prev_col_len == ref_col_len:
            diff_gives_red = True
            
    if same_gives_red and not diff_gives_red:
        return curr_side, f"Đánh {curr_side} để Bảng Phụ 1 ra Hạt Đỏ"
    elif diff_gives_red and not same_gives_red:
        return opp_side, f"Đánh {opp_side} để Bảng Phụ 1 ra Hạt Đỏ"
    elif same_gives_red and diff_gives_red:
        return curr_side, f"Cả 2 đều Đỏ (Ưu tiên thế cầu: {curr_side})"
    else:
        # Nếu cả 2 đều không tạo đỏ, ưu tiên bắt theo ván trước
        return opp_side, f"Dự phòng nhịp đổi: {opp_side}"

# ==============================================================================
# KHỞI TẠO SESSION STATE (BỘ NHỚ TRÌNH DUYỆT)
# ==============================================================================
today_str = datetime.date.today().strftime("%Y-%m-%d")

if "daily_history" not in st.session_state:
    st.session_state["daily_history"] = []

if "current_session_id" not in st.session_state:
    st.session_state["current_session_id"] = 1

if "base_capital" not in st.session_state:
    st.session_state["base_capital"] = 1000.0

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

if "last_bet_result" not in st.session_state:
    st.session_state["last_bet_result"] = None

if "current_stake" not in st.session_state:
    st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10

# ==============================================================================
# THANH BÊN (SIDEBAR): VỐN CƠ SỞ & THỐNG KÊ TOÀN DIỆN
# ==============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Cấu Hình Vốn & Phiên")
    
    # Ô NHẬP VỐN CƠ SỞ: Cho phép sửa, thay đổi và có nút Reset
    new_base = st.number_input(
        "💵 VỐN CƠ SỞ (Có thể sửa đổi):",
        min_value=10.0,
        value=float(st.session_state["base_capital"]),
        step=50.0
    )
    if new_base != st.session_state["base_capital"]:
        st.session_state["base_capital"] = new_base
        if st.session_state["order_in_session"] == 1:
            st.session_state["current_stake"] = new_base * 0.10
        st.success("Đã cập nhật Vốn cơ sở mới!")

    col_btn_reset, col_btn_new_ses = st.columns(2)
    with col_btn_reset:
        if st.button("🔄 Reset Vốn", use_container_width=True):
            st.session_state["base_capital"] = 1000.0
            st.session_state["current_stake"] = 100.0
            st.session_state["session_pnl"] = 0.0
            st.session_state["order_in_session"] = 1
            st.session_state["table_bet_step"] = 1
            st.session_state["session_running"] = True
            st.session_state["table_hands"] = []
            st.session_state["last_bet_result"] = None
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
                st.session_state["last_bet_result"] = None
                st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10
                st.rerun()
            else:
                st.warning("Đã hoàn thành tối đa 4 phiên của ngày hôm nay!")

    st.markdown("---")
    st.markdown("### 📊 Thống Kê Tổng Hợp")
    
    # Tính lợi nhuận ngày
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

    # Nút xuất file Excel
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
# GIAO DIỆN CHÍNH: KHU VỰC CẢNH BÁO TÍN HIỆU RÕ RÀNG
# ==============================================================================
st.markdown("<h2 style='text-align: center; color: #1F4E78;'>🎯 BACCARAT BIG EYE ROAD & MONEY MANAGEMENT ENGINE</h2>", unsafe_allow_html=True)
st.caption("<div style='text-align: center;'>Hệ Thống Phân Tích Bảng Phụ 1 Sang Hạt Đỏ & Cơ Chế Khóa Phiên Mục Tiêu 9.5% - 10%</div>", unsafe_allow_html=True)

# 1. KIỂM TRA ĐIỀU KIỆN STOP LUÔN (CHỐT LÃI PHIÊN)
target_min = st.session_state["base_capital"] * 0.095
target_max = st.session_state["base_capital"] * 0.100

if not st.session_state["session_running"] or st.session_state["session_pnl"] >= target_min:
    st.markdown("""
        <div class="alert-stop">
            🛑 CẢNH BÁO: STOP LUÔN! ĐẠT TARGET PHIÊN NÀY (+9.5% - 10%)! KHÓA PHIÊN!
        </div>
    """, unsafe_allow_html=True)
    st.info(f"🎉 Bạn đã hoàn thành mục tiêu Phiên {st.session_state['current_session_id']} với lợi nhuận: **{st.session_state['session_pnl']:+,.2f}$**. Hãy bấm **'➕ Phiên Mới'** ở thanh bên trái khi bắt đầu phiên tiếp theo.")
else:
    # 2. TÍNH TOÁN VÀ CẢNH BÁO TÍN HIỆU TỪ BẢNG PHỤ 1
    predicted_side, reason_text = predict_red_big_eye(st.session_state["table_hands"])
    
    col_c1, col_c2 = st.columns([1.8, 1.2])
    with col_c1:
        st.markdown(f"#### 📢 Tín Hiệu Vào Lệnh (Lệnh thứ {st.session_state['order_in_session']})")
        
        if len(st.session_state["table_hands"]) < 2:
            st.markdown("""
                <div class="alert-wait">
                    ⏳ VUI LÒNG NHẬP 2 VÁN MỒI CỦA BÀN MỚI ĐỂ BẢNG PHỤ 1 XUẤT HIỆN
                </div>
            """, unsafe_allow_html=True)
        elif predicted_side == "P":
            st.markdown("""
                <div class="alert-player">
                    👉 CẢNH BÁO: ĐÁNH PLAYER (TẠO HẠT ĐỎ BẢNG PHỤ 1)
                </div>
            """, unsafe_allow_html=True)
        elif predicted_side == "B":
            st.markdown("""
                <div class="alert-banker">
                    👉 CẢNH BÁO: ĐÁNH BANKER (TẠO HẠT ĐỎ BẢNG PHỤ 1)
                </div>
            """, unsafe_allow_html=True)
            
        st.caption(f"🔍 Logic suy luận: {reason_text}")

    with col_c2:
        st.markdown("#### 💵 Mức Tiền Cược Lệnh Này")
        stake_rate = (st.session_state["current_stake"] / st.session_state["base_capital"]) * 100
        st.metric(
            label="Số tiền cược ván này",
            value=f"{st.session_state['current_stake']:,.2f} $",
            delta=f"{stake_rate:.0f}% Vốn cơ sở"
        )
        st.caption(f"Trạng thái bàn hiện tại: **Ván {st.session_state['table_bet_step']} / 2 ván tối đa của bàn**")

    # ==============================================================================
    # KHU VỰC NHẬP KẾT QUẢ VÁN BÀI VÀ CẬP NHẬT TRẠNG THÁI
    # ==============================================================================
    st.markdown("---")
    st.markdown("### 🎲 Bảng Điều Khiển Nhập Kết Quả Thực Tế")
    
    # 2 Nút nhập ván mồi cho bàn mới
    if len(st.session_state["table_hands"]) < 2:
        st.write("Nhập kết quả các ván bài vừa mở tại bàn:")
        btn_m1, btn_m2, btn_m3 = st.columns(3)
        with btn_m1:
            if st.button("➕ Nhập ván mở ra: BANKER (B)", use_container_width=True):
                st.session_state["table_hands"].append("B")
                st.rerun()
        with btn_m2:
            if st.button("➕ Nhập ván mở ra: PLAYER (P)", use_container_width=True):
                st.session_state["table_hands"].append("P")
                st.rerun()
        with btn_m3:
            if st.button("🔄 Xóa ván mồi bàn này", use_container_width=True):
                st.session_state["table_hands"] = []
                st.rerun()
    else:
        st.write("Sau khi vào lệnh xong, hãy bấm kết quả ván bài vừa rồi của bạn:")
        col_act1, col_act2, col_act3 = st.columns(3)
        
        # Xử lý khi WIN
        with col_act1:
            if st.button("✅ LỆNH VỪA RỒI THẮNG (WIN)", use_container_width=True, type="primary"):
                stake = st.session_state["current_stake"]
                # Banker ăn 95%, Player ăn 100%
                win_profit = (stake * 0.95) if predicted_side == "B" else stake
                
                st.session_state["session_pnl"] += win_profit
                
                # Lưu lịch sử
                st.session_state["daily_history"].append({
                    "Ngày": today_str,
                    "Phiên": st.session_state["current_session_id"],
                    "STT Lệnh": st.session_state["order_in_session"],
                    "Cửa Đánh": "BANKER" if predicted_side == "B" else "PLAYER",
                    "Tiền Cược ($)": stake,
                    "Kết Quả": "WIN",
                    "Tiền Lãi/Lỗ ($)": win_profit,
                    "Lợi Nhuận Lũy Kế ($)": st.session_state["session_pnl"]
                })
                
                # KIỂM TRA ĐIỀU KIỆN 1: Nếu là Lệnh 1 của phiên mà WIN -> STOP LUÔN
                if st.session_state["order_in_session"] == 1:
                    st.session_state["session_running"] = False
                    st.rerun()
                    
                # KIỂM TRA ĐIỀU KIỆN CHỐT TARGET PHIÊN (+9.5% - 10%)
                if st.session_state["session_pnl"] >= target_min:
                    st.session_state["session_running"] = False
                    st.rerun()
                    
                # QUY TẮC BÀN: Nếu ván 1 WIN -> Dừng bàn cũ, đổi bàn mới tinh
                if st.session_state["table_bet_step"] == 1:
                    st.session_state["table_hands"] = []
                    st.session_state["table_bet_step"] = 1
                else:
                    # Đã đánh xong ván 2 -> Chuyển bàn
                    st.session_state["table_hands"] = []
                    st.session_state["table_bet_step"] = 1
                    
                # QUY TẮC ĐI TIỀN:
                # Nếu vốn hiện tại giật về bằng hoặc lớn hơn vốn cơ sở ban đầu -> BẮT BUỘC RESET VỀ 10%
                if st.session_state["session_pnl"] >= 0:
                    st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10
                else:
                    # Nếu vẫn đang âm: lệnh trước WIN -> lệnh này gấp đôi (20%)
                    st.session_state["current_stake"] = st.session_state["base_capital"] * 0.20
                    
                st.session_state["order_in_session"] += 1
                st.session_state["last_bet_result"] = "WIN"
                st.rerun()

        # Xử lý khi LOSE
        with col_act2:
            if st.button("❌ LỆNH VỪA RỒI THUA (LOSE)", use_container_width=True):
                stake = st.session_state["current_stake"]
                st.session_state["session_pnl"] -= stake
                
                st.session_state["daily_history"].append({
                    "Ngày": today_str,
                    "Phiên": st.session_state["current_session_id"],
                    "STT Lệnh": st.session_state["order_in_session"],
                    "Cửa Đánh": "BANKER" if predicted_side == "B" else "PLAYER",
                    "Tiền Cược ($)": stake,
                    "Kết Quả": "LOSE",
                    "Tiền Lãi/Lỗ ($)": -stake,
                    "Lợi Nhuận Lũy Kế ($)": st.session_state["session_pnl"]
                })
                
                # QUY TẮC BÀN: Nếu ván 1 LOSE -> Ở lại bàn đó đánh tiếp ván 2
                if st.session_state["table_bet_step"] == 1:
                    st.session_state["table_bet_step"] = 2
                    # Ghi nhận kết quả ván bài để cập nhật Big Road
                    st.session_state["table_hands"].append("P" if predicted_side == "B" else "B")
                else:
                    # Đã hết ván 2 -> Đổi bàn mới tinh
                    st.session_state["table_hands"] = []
                    st.session_state["table_bet_step"] = 1
                    
                # QUY TẮC ĐI TIỀN: Lệnh trước LOSE -> Luôn đánh bằng tiền cơ sở (10%)
                st.session_state["current_stake"] = st.session_state["base_capital"] * 0.10
                st.session_state["order_in_session"] += 1
                st.session_state["last_bet_result"] = "LOSE"
                st.rerun()

        # Xử lý khi TIE (HÒA)
        with col_act3:
            if st.button("⏸ VÁN RA HÒA (TIE - HOÀN TIỀN)", use_container_width=True):
                st.info("Ván Hòa hoàn tiền! Giữ nguyên vị trí lệnh và số tiền cược.")

# ==============================================================================
# BẢNG NHẬT KÝ CHI TIẾT THEO PHIÊN & NGÀY
# ==============================================================================
st.markdown("---")
st.markdown(f"### 📋 Nhật Ký Vào Lệnh Hôm Nay ({today_str})")
if st.session_state["daily_history"]:
    df_history = pd.DataFrame(st.session_state["daily_history"])
    st.dataframe(df_history.iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.caption("Chưa có lệnh nào được ghi nhận trong ngày hôm nay. Hãy bắt đầu vào lệnh ván đầu tiên!")
