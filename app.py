import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import random
import io

st.set_page_config(
    page_title="Baccarat 8-Bot Backtest Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 1. MA TRẬN 8 BOT CHU KỲ 6 BƯỚC HOÁN VỊ (MISTER RAFAEL)
# ==============================================================================
BASE_MATRIX_6 = [
    ['B', 'B', 'P', 'P', 'B', 'P', 'P', 'B'],  # Bước 1
    ['P', 'B', 'B', 'P', 'P', 'P', 'B', 'B'],  # Bước 2
    ['B', 'P', 'B', 'P', 'P', 'B', 'P', 'B'],  # Bước 3
    ['B', 'P', 'B', 'P', 'B', 'P', 'B', 'P'],  # Bước 4
    ['B', 'P', 'P', 'B', 'P', 'B', 'B', 'P'],  # Bước 5
    ['P', 'P', 'B', 'B', 'B', 'P', 'P', 'B'],  # Bước 6
]

# ==============================================================================
# 2. HÀM MÔ PHỎNG BACKTEST TOÀN BỘ CÁC KHAY BÀI (SHOES)
# ==============================================================================
def run_backtest_simulation(
    num_shoes, hands_per_shoe, unit_val, target_units, stop_loss_units, 
    commission_enabled, initial_balance
):
    results = []
    equity_curve = [initial_balance]
    current_total_balance = initial_balance
    
    # Xác suất Baccarat chuẩn quốc tế (đã loại bỏ Tie)
    # Banker: 50.68%, Player: 49.32%
    weights = [0.5068, 0.4932]

    for s in range(num_shoes):
        actual_hands = random.choices(['B', 'P'], weights=weights, k=hands_per_shoe)
        shoe_pnl = 0.0
        user_cycle_pnl = 0
        user_stake = 1  # Tính bằng units
        last_bet_won = False
        bot_streak = [0] * 8  # >0: chuỗi Win, <0: chuỗi Lose
        
        total_bets = 0
        wins = 0
        losses = 0
        
        for t, actual in enumerate(actual_hands):
            # Lấy dự đoán của 8 bot theo chu kỳ 6 bước
            step = t % 6
            preds = BASE_MATRIX_6[step]
            
            # --- BƯỚC 1: CHỌN CỬA (B/P) DỰA TRÊN MOMENTUM CỦA 8 BOT ---
            b_bots = [i for i, p in enumerate(preds) if p == 'B']
            p_bots = [i for i, p in enumerate(preds) if p == 'P']
            
            b_score = sum(bot_streak[i] for i in b_bots)
            p_score = sum(bot_streak[i] for i in p_bots)
            
            if b_score > p_score:
                bet_side = 'B'
            elif p_score > b_score:
                bet_side = 'P'
            else:
                bet_side = preds[0]  # Mặc định theo Bot 1
                
            # --- BƯỚC 2: BỘ LỌC SKIP (NGHỈ) SAU KHI CHỐT CHU KỲ +1U ---
            if last_bet_won and user_cycle_pnl == 0:
                is_bet = False
                last_bet_won = False
            else:
                is_bet = True
                
            # --- BƯỚC 3: QUẢN LÝ TIỀN THEO OSCAR'S GRIND ---
            if is_bet:
                total_bets += 1
                stake = user_stake if user_cycle_pnl < 0 else 1
                if user_cycle_pnl < 0:
                    needed = 1 - user_cycle_pnl
                    stake = min(user_stake, needed)
                    
                # Giới hạn không cược vượt quá mục tiêu phiên
                rem = target_units - shoe_pnl
                if rem > 0 and stake > rem:
                    stake = max(1, int(rem))
                    
                # Tính tiền thắng / thua
                if bet_side == actual:
                    # Nếu đánh Banker thắng: trừ 5% hoa hồng nếu bật commission
                    win_profit = (stake * 0.95) if (bet_side == 'B' and commission_enabled) else float(stake)
                    shoe_pnl += win_profit
                    user_cycle_pnl += stake
                    wins += 1
                    last_bet_won = True
                    
                    if user_cycle_pnl >= 1:
                        user_cycle_pnl = 0
                        user_stake = 1
                    else:
                        user_stake = min(user_stake + 1, 1 - user_cycle_pnl)
                else:
                    shoe_pnl -= float(stake)
                    user_cycle_pnl -= stake
                    losses += 1
                    last_bet_won = False
                    # Thua: giữ nguyên mức cược
                    
            # --- BƯỚC 4: CẬP NHẬT PHONG ĐỘ CHO 8 BOT ---
            for i, p in enumerate(preds):
                if p == actual:
                    bot_streak[i] = bot_streak[i] + 1 if bot_streak[i] > 0 else 1
                else:
                    bot_streak[i] = bot_streak[i] - 1 if bot_streak[i] < 0 else -1
                    
            # --- BƯỚC 5: ĐIỀU KIỆN DỪNG PHIÊN (TARGET HOẶC STOP LOSS) ---
            if shoe_pnl >= target_units or shoe_pnl <= stop_loss_units:
                break
                
        shoe_money_pnl = shoe_pnl * unit_val
        current_total_balance += shoe_money_pnl
        equity_curve.append(current_total_balance)
        
        status = "✅ Đạt Target" if shoe_pnl >= target_units else ("❌ Chạm Stoploss" if shoe_pnl <= stop_loss_units else "⏹ Hết Khay")
        
        results.append({
            "Khay (Shoe)": s + 1,
            "Số ván cược": total_bets,
            "Thắng (W)": wins,
            "Thua (L)": losses,
            "Tỷ lệ Thắng (%)": round((wins / total_bets * 100), 1) if total_bets > 0 else 0,
            "Lãi/Lỗ (Units)": round(shoe_pnl, 2),
            "Lãi/Lỗ ($)": round(shoe_money_pnl, 2),
            "Số dư lũy kế ($)": round(current_total_balance, 2),
            "Kết Quả Phiên": status
        })
        
    return pd.DataFrame(results), equity_curve

# ==============================================================================
# 3. GIAO DIỆN NGƯỜI DÙNG STREAMLIT
# ==============================================================================
st.markdown("<h2 style='text-align: center; color: #1F4E78;'>🚀 BACCARAT 8-BOT BACKTEST ENGINE</h2>", unsafe_allow_html=True)
st.caption("<div style='text-align: center;'>Hệ thống kiểm thử xác suất độc lập thuật toán 8 Bot Ma Trận Hoán Vị & Oscar's Grind</div>", unsafe_allow_html=True)

# SIDEBAR: CẤU HÌNH THAM SỐ BACKTEST
with st.sidebar:
    st.markdown("### ⚙️ Cấu Hình Tham Số")
    
    num_shoes = st.slider("Số lượng Khay bài (Shoes):", min_value=10, max_value=1000, value=100, step=10)
    hands_per_shoe = st.slider("Số ván trung bình / Khay:", min_value=40, max_value=85, value=70, step=5)
    
    st.markdown("---")
    st.markdown("### 💰 Quản Lý Vốn")
    initial_balance = st.number_input("Vốn khởi điểm ($):", min_value=100, value=1780, step=100)
    unit_val = st.number_input("Giá trị 1 Unit ($):", min_value=1, value=5, step=1)
    target_units = st.number_input("Mục tiêu Chốt Lời / Phiên (Units):", min_value=1, value=8, step=1)
    stop_loss_units = st.number_input("Mức Cắt Lỗ / Phiên (Units âm):", max_value=-5, value=-40, step=5)
    
    st.markdown("---")
    st.markdown("### 🎲 Cơ Chế Bàn Chơi")
    commission_enabled = st.checkbox("Tính phí hoa hồng Banker (5%)", value=True)
    
    target_money = target_units * unit_val
    stop_loss_money = stop_loss_units * unit_val
    st.caption(f"🎯 Target phiên: `+{target_money}$` | 🛑 Cắt lỗ phiên: `{stop_loss_money}$`")

# GIAO DIỆN CHÍNH
btn_run = st.button("🔥 BẮT ĐẦU CHẠY BACKTEST", use_container_width=True, type="primary")

if btn_run:
    with st.spinner(f"Đang mô phỏng {num_shoes:,} khay bài (~{num_shoes * hands_per_shoe:,} ván)..."):
        df_results, equity = run_backtest_simulation(
            num_shoes, hands_per_shoe, unit_val, target_units, stop_loss_units,
            commission_enabled, initial_balance
        )
        st.session_state["df_results"] = df_results
        st.session_state["equity"] = equity

if "df_results" in st.session_state:
    df_res = st.session_state["df_results"]
    equity = st.session_state["equity"]
    
    # 1. CÁC CHỈ SỐ KPI CHÍNH
    total_shoes = len(df_res)
    target_hit_count = (df_res["Kết Quả Phiên"] == "✅ Đạt Target").sum()
    sl_hit_count = (df_res["Kết Quả Phiên"] == "❌ Chạm Stoploss").sum()
    win_shoe_rate = (target_hit_count / total_shoes) * 100
    
    final_balance = equity[-1]
    net_profit = final_balance - initial_balance
    total_bets_all = df_res["Số ván cược"].sum()
    avg_bets_per_shoe = df_res["Số ván cược"].mean()
    
    # Max Drawdown
    peak = equity[0]
    max_dd = 0
    for val in equity:
        if val > peak:
            peak = val
        dd = peak - val
        if dd > max_dd:
            max_dd = dd

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Lợi nhuận ròng ($)", f"{net_profit:+,.2f}$", delta=f"{((net_profit/initial_balance)*100):+.1f}%")
    k2.metric("Tỷ lệ Thắng Phiên", f"{win_shoe_rate:.1f}%", f"{target_hit_count}/{total_shoes} Phiên")
    k3.metric("Số dư cuối cùng", f"{final_balance:,.2f}$", f"Vốn đầu: {initial_balance:,.0f}$")
    k4.metric("Sụt giảm vốn lớn nhất", f"-{max_dd:,.2f}$", f"SL dính: {sl_hit_count} phiên")

    st.markdown("---")

    # 2. ĐỒ THỊ TĂNG TRƯỞNG VỐN (EQUITY CURVE)
    st.markdown("#### 📈 Biểu Đồ Đường Cong Tăng Trưởng Vốn (Equity Curve)")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=equity,
        mode='lines',
        name='Số Dư Tài Khoản ($)',
        line=dict(color='#0D6EFD', width=2.5),
        fill='tozeroy',
        fillcolor='rgba(13, 110, 253, 0.08)'
    ))
    fig.add_hline(y=initial_balance, line_dash="dash", line_color="orange", annotation_text="Vốn Khởi Điểm")
    
    fig.update_layout(
        xaxis_title="Số lượng Khay bài đã chơi (Shoes)",
        yaxis_title="Số dư tài khoản ($)",
        template="plotly_white",
        height=450,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    # 3. THỐNG KÊ CHI TIẾT & TẢI XUỐNG EXCEL
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.markdown(f"#### 📋 Nhật Ký Chi Tiết {total_shoes} Khay Bài")
    with col_t2:
        # Xuất kết quả ra file Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_res.to_excel(writer, index=False, sheet_name="Backtest_Results")
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Tải Báo Cáo Kết Quả Ra Excel",
            data=excel_data,
            file_name=f"Baccarat_Backtest_{total_shoes}_Shoes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.dataframe(df_res, use_container_width=True, hide_index=True)
else:
    st.info("👈 Hãy chọn các tham số ở thanh bên trái và bấm **BẮT ĐẦU CHẠY BACKTEST** để xem biểu đồ và kết quả mô phỏng!")
