import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime
import sqlite3

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Quản Trị Kỷ Luật Bản Thân", layout="wide")

# --- CSS GIAO DIỆN TỐI ƯU MOBILE ---
st.markdown("""
<style>
    .signal-banker {
        background-color: #dc2626; color: #ffffff; padding: 14px 16px;
        border-radius: 8px; font-size: 19px; font-weight: 800; text-align: center;
        box-shadow: 0 4px 6px rgba(220, 38, 38, 0.4); margin: 8px 0;
    }
    .signal-player {
        background-color: #2563eb; color: #ffffff; padding: 14px 16px;
        border-radius: 8px; font-size: 19px; font-weight: 800; text-align: center;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.4); margin: 8px 0;
    }
    .signal-wait {
        background-color: #f4f4f5; color: #52525b; padding: 10px 14px;
        border-radius: 6px; font-size: 14px; font-weight: 600; text-align: center;
        border: 1px dashed #a1a1aa; margin: 8px 0;
    }
    .signal-stop {
        background-color: #991b1b; color: #ffffff; padding: 16px 20px;
        border-radius: 8px; font-size: 17px; font-weight: 800; text-align: center; margin: 8px 0;
        box-shadow: 0 4px 10px rgba(153, 27, 27, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# --- CƠ SỞ DỮ LIỆU SQLITE ---
def get_db():
    return sqlite3.connect("baccarat_data.db", check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS auth_security (
            id INTEGER PRIMARY KEY,
            pin_code TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY,
            initial_cap REAL,
            current_cap REAL,
            session_start_cap REAL,
            curr_session INTEGER,
            curr_table INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_str TEXT,
            session_idx INTEGER,
            table_idx INTEGER,
            order_name TEXT,
            bet_side TEXT,
            bet_amount REAL,
            result TEXT,
            pnl REAL,
            balance REAL
        )
    """)
    c.execute("SELECT COUNT(*) FROM config")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO config VALUES (1, 1000.0, 1000.0, 1000.0, 1, 1)")
    conn.commit()
    conn.close()

init_db()

def get_current_pin():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT pin_code FROM auth_security WHERE id = 1")
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_current_pin(new_pin):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO auth_security (id, pin_code) VALUES (1, ?)", (new_pin,))
    conn.commit()
    conn.close()

# --- XÁC THỰC MÃ PIN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

current_pin = get_current_pin()

if not st.session_state.authenticated:
    st.markdown("## 🔒 QUẢN TRỊ KỶ LUẬT BẢN THÂN")
    if current_pin is None:
        st.info("👋 Thiết lập mã PIN bảo mật ban đầu để bảo vệ dữ liệu.")
        p1 = st.text_input("Nhập mã PIN muốn tạo:", type="password")
        p2 = st.text_input("Xác nhận lại mã PIN:", type="password")
        if st.button("Lưu Mã PIN & Vào App"):
            if not p1:
                st.error("Mã PIN không được để trống!")
            elif p1 != p2:
                st.error("Xác nhận mã PIN không khớp!")
            else:
                set_current_pin(p1)
                st.session_state.authenticated = True
                st.rerun()
    else:
        pin_input = st.text_input("Nhập mã PIN bảo mật:", type="password")
        if st.button("Mở Khóa"):
            if pin_input == current_pin:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Mã PIN không đúng!")
    st.stop()

# --- TẢI DỮ LIỆU CẤU HÌNH & LỊCH SỬ ---
def load_data():
    conn = get_db()
    cfg = pd.read_sql("SELECT * FROM config WHERE id = 1", conn).iloc[0]
    his = pd.read_sql("SELECT * FROM trade_history ORDER BY id DESC", conn)
    conn.close()
    return cfg, his

cfg, df_history = load_data()

# Bộ nhớ tạm phiên
if "raw_inputs" not in st.session_state:
    st.session_state.raw_inputs = []
if "main_road" not in st.session_state:
    st.session_state.main_road = []
if "big_eye_cols" not in st.session_state:
    st.session_state.big_eye_cols = []
if "big_eye_list" not in st.session_state:
    st.session_state.big_eye_list = []

# Đếm chuỗi win liên tiếp trong phiên hiện tại
if "consecutive_wins" not in st.session_state:
    st.session_state.consecutive_wins = 0
if "last_result" not in st.session_state:
    st.session_state.last_result = None

SESSION_NAMES = {
    1: "Phiên 1 (Sáng)",
    2: "Phiên 2 (Trưa)",
    3: "Phiên 3 (Chiều)",
    4: "Phiên 4 (Tối)"
}

# --- THUẬT TOÁN ĐƯỜNG CẦU ---
def add_to_road(road, val):
    new_road = [col.copy() for col in road]
    if not new_road:
        new_road.append([val])
    else:
        if new_road[-1][-1] == val:
            new_road[-1].append(val)
        else:
            new_road.append([val])
    return new_road

def get_big_eye_color(road, col_idx, row_idx):
    if col_idx == 0 or (col_idx == 1 and row_idx == 0):
        return None
    if row_idx > 0:
        prev_len = len(road[col_idx - 1])
        return "RED" if prev_len >= (row_idx + 1) else "BLUE"
    else:
        if col_idx >= 2:
            return "RED" if len(road[col_idx - 1]) == len(road[col_idx - 2]) else "BLUE"
        return None

def find_red_choice():
    road = st.session_state.main_road
    if not road:
        return "BANKER"
    
    sim_p = add_to_road(road, "P")
    cp, rp = len(sim_p) - 1, len(sim_p[-1]) - 1
    color_p = get_big_eye_color(sim_p, cp, rp)

    sim_b = add_to_road(road, "B")
    cb, rb = len(sim_b) - 1, len(sim_b[-1]) - 1
    color_b = get_big_eye_color(sim_b, cb, rb)

    if color_p == "RED" and color_b != "RED":
        return "PLAYER"
    elif color_b == "RED" and color_p != "RED":
        return "BANKER"
    else:
        last_val = road[-1][-1]
        return "PLAYER" if last_val == "P" else "BANKER"

def reset_table(new_table_idx):
    st.session_state.raw_inputs = []
    st.session_state.main_road = []
    st.session_state.big_eye_cols = []
    st.session_state.big_eye_list = []
    conn = get_db()
    conn.execute("UPDATE config SET curr_table = ? WHERE id = 1", (new_table_idx,))
    conn.commit()
    conn.close()

# --- TIÊU ĐỀ CHÍNH ---
st.title("🎯 Quản Trị Kỷ Luật Bản Thân")

current_capital = float(cfg['current_cap'])
session_start_cap = float(cfg['session_start_cap'])
initial_capital = float(cfg['initial_cap'])
curr_session = int(cfg['curr_session'])

session_profit = current_capital - session_start_cap
session_profit_pct = (session_profit / session_start_cap) * 100 if session_start_cap > 0 else 0
total_profit = current_capital - initial_capital

# Tên phiên hiện tại
s_name = SESSION_NAMES.get(curr_session, f"Phiên {curr_session}")

# --- HIỂN THỊ ĐỒNG HÀNG: VỐN THỰC TẾ & VỐN BAN ĐẦU ---
col_m1, col_m2 = st.columns(2)
col_m1.metric("VỐN THỰC TẾ", f"${current_capital:,.2f}", delta=f"${total_profit:+,.2f}")
col_m2.metric("VỐN BAN ĐẦU (GỐC 5%)", f"${initial_capital:,.2f}")

col_m3, col_m4 = st.columns(2)
col_m3.metric(f"LÃI/LỖ {s_name}", f"${session_profit:+,.2f}", delta=f"{session_profit_pct:.2f}%")
col_m4.metric("TARGET PHIÊN (5%)", f"+${session_start_cap * 0.05:,.2f}")

st.caption(f"📌 Bàn hiện tại: **Bàn {int(cfg['curr_table'])}** | Đã cược: **{len(df_history)} lệnh**")

# MỤC ĐIỀU CHỈNH VỐN TRỰC TIẾP
with st.expander("⚡ Điều Chỉnh Vốn Ban Đầu & Vốn Thực Tế"):
    c_edit1, c_edit2 = st.columns(2)
    new_init_input = c_edit1.number_input("Sửa Vốn Ban Đầu ($):", min_value=10.0, value=initial_capital, step=50.0)
    new_curr_input = c_edit2.number_input("Sửa Vốn Thực Tế ($):", min_value=1.0, value=current_capital, step=50.0)
    
    cq1, cq2 = st.columns(2)
    if cq1.button("💾 Cập Nhật Vốn", use_container_width=True):
        conn = get_db()
        conn.execute("UPDATE config SET initial_cap = ?, current_cap = ?, session_start_cap = ? WHERE id = 1", 
                     (new_init_input, new_curr_input, new_curr_input))
        conn.commit()
        conn.close()
        st.session_state.consecutive_wins = 0
        st.session_state.last_result = None
        st.rerun()
    if cq2.button("🔄 Đổi Bàn Mới (Xóa Cầu)", use_container_width=True):
        reset_table(int(cfg['curr_table']) + 1)
        st.rerun()

st.divider()

# --- KIỂM TRA ĐIỀU KIỆN STOP PHIÊN (+5%) ---
is_session_stopped = session_profit_pct >= 5.0

if is_session_stopped:
    st.markdown(f'<div class="signal-stop">🛑 KỶ LUẬT THÉP: ĐÃ ĐẠT DƯƠNG {session_profit_pct:.2f}% (≥ 5%)!<br>BẮT BUỘC STOP PHIÊN NGAY LẬP TỨC. NGHỈ NGƠI!</div>', unsafe_allow_html=True)
    next_s_idx = curr_session + 1
    next_s_name = SESSION_NAMES.get(next_s_idx, f"Phiên {next_s_idx}")
    if next_s_idx <= 4:
        if st.button(f"✅ Xác Nhận Chốt Lời ➔ Chuyển Sang {next_s_name}", use_container_width=True):
            conn = get_db()
            conn.execute("UPDATE config SET curr_session = ?, session_start_cap = ? WHERE id = 1", (next_s_idx, current_capital))
            conn.commit()
            conn.close()
            reset_table(int(cfg['curr_table']) + 1)
            st.session_state.consecutive_wins = 0
            st.session_state.last_result = None
            st.rerun()
    else:
        st.success("🎉 Bạn đã hoàn thành xuất sắc mục tiêu cả 4 phiên trong ngày!")

# --- GIAO DIỆN BÀN CƯỢC & VÀO LỆNH ---
tab_bet, tab_chart = st.tabs(["🎮 BÀN ĐÁNH & VÀO LỆNH", "📊 DASHBOARD TĂNG TRƯỞNG"])

with tab_bet:
    def build_html_board(columns, is_big_eye=False):
        total_cols = max(55, len(columns) + 5)
        html = """<style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: sans-serif; background: transparent; }
            .wrapper { background: #ffffff; border: 1px solid #71717a; overflow-x: auto; white-space: nowrap; width: 100%; padding: 2px; }
            table { border-collapse: collapse; table-layout: fixed; background: #ffffff; }
            th { width: 24px; min-width: 24px; height: 18px; border: 1px solid #d4d4d8; border-bottom: 2px solid #27272a; font-size: 10px; font-weight: bold; color: #3f3f46; text-align: center; background: #f4f4f5; }
            td { width: 24px; min-width: 24px; height: 24px; border: 1px solid #e4e4e7; text-align: center; vertical-align: middle; padding: 0; }
            .circle-b { width: 16px; height: 16px; border-radius: 50%; border: 2.2px solid #dc2626; margin: auto; }
            .circle-p { width: 16px; height: 16px; border-radius: 50%; border: 2.2px solid #2563eb; margin: auto; }
            .eye-red { width: 14px; height: 14px; border-radius: 50%; border: 2px solid #dc2626; margin: auto; }
            .eye-blue { width: 14px; height: 14px; border-radius: 50%; border: 2px solid #2563eb; margin: auto; }
        </style><div class="wrapper"><table><thead><tr>"""
        for c in range(1, total_cols + 1):
            html += f"<th>{c}</th>"
        html += "</tr></thead><tbody>"
        for r in range(6):
            html += "<tr>"
            for c in range(total_cols):
                cnt = ""
                if c < len(columns) and r < len(columns[c]):
                    v = columns[c][r]
                    cls = ("circle-b" if v == "B" else "circle-p") if not is_big_eye else ("eye-red" if v == "RED" else "eye-blue")
                    cnt = f'<div class="{cls}"></div>'
                html += f"<td>{cnt}</td>"
            html += "</tr>"
        html += "</tbody></table></div>"
        return html

    st.markdown("##### 🔴🔵 Bảng Chính (Big Road)")
    st.components.v1.html(build_html_board(st.session_state.main_road, is_big_eye=False), height=185, scrolling=True)

    st.markdown(f"##### 🔴🔵 Bảng Phụ 1 - Big Eye Boy ({len(st.session_state.big_eye_list)} hạt)")
    st.components.v1.html(build_html_board(st.session_state.big_eye_cols, is_big_eye=True), height=185, scrolling=True)

    if st.session_state.raw_inputs:
        tags = ["<span style='color: #dc2626; font-weight: bold;'>🔴 B</span>" if x == "B" else "<span style='color: #2563eb; font-weight: bold;'>🔵 P</span>" for x in st.session_state.raw_inputs]
        st.markdown("**Các tay vừa nhập:** " + " ➔ ".join(tags[-20:]), unsafe_allow_html=True)

    st.write("---")

    # --- TÍNH TOÁN QUẢN LÝ TIỀN CƯỢC THEO VỐN BAN ĐẦU ---
    # MỐC CƠ BẢN 5% ĐƯỢC TÍNH THEO VỐN BAN ĐẦU (initial_capital)
    base_5pct = initial_capital * 0.05

    if st.session_state.consecutive_wins >= 2:
        bet_multiplier = 1.0  # Về lại 5% sau 2 lệnh win
        rate_note = "5% (Hạ về mốc an toàn sau 2 Win)"
    elif st.session_state.consecutive_wins == 1:
        bet_multiplier = 2.0  # Win 1 lệnh lẻ -> Gấp đôi lệnh kế tiếp
        rate_note = "10% (Gấp đôi thừa thắng xông lên)"
    else:
        bet_multiplier = 1.0  # Lệnh thua hoặc đầu chuỗi: 5%
        rate_note = "5% (Mức cơ sở)"

    current_bet_amount = base_5pct * bet_multiplier
    predicted_choice = find_red_choice()
    num_seeds = len(st.session_state.big_eye_list)

    # --- HIỂN THỊ KHỐI CẢNH BÁO TÍN HIỆU NGAY TRÊN NÚT BẤM ---
    can_bet = False
    if is_session_stopped:
        st.markdown('<div class="signal-stop">🛑 PHIÊN ĐÃ HOÀN THÀNH MỤC TIÊU! DỪNG VÀO LỆNH.</div>', unsafe_allow_html=True)
    elif num_seeds == 0:
        st.markdown('<div class="signal-wait">⏳ Đang chờ Bảng phụ 1 xuất hiện hạt đầu tiên để tính điểm vào...</div>', unsafe_allow_html=True)
    else:
        can_bet = True
        b_class = "signal-banker" if predicted_choice == "BANKER" else "signal-player"
        st.markdown(f'<div class="{b_class}">🚨 ĐẶT CƯỢC: {predicted_choice} | ${current_bet_amount:,.2f}<br><span style="font-size: 14px; font-weight: normal;">Chiến lược: {rate_note} (Theo Vốn Ban Đầu ${initial_capital:,.2f})</span></div>', unsafe_allow_html=True)

    # --- NÚT BẤM GHI NHẬN KẾT QUẢ ---
    col_p, col_b = st.columns(2)

    def handle_result_input(outcome):
        global initial_capital, current_capital
        st.session_state.raw_inputs.append(outcome)
        st.session_state.main_road = add_to_road(st.session_state.main_road, outcome)
        road = st.session_state.main_road
        c_idx, r_idx = len(road) - 1, len(road[-1]) - 1

        color = get_big_eye_color(road, c_idx, r_idx)
        if color is not None:
            st.session_state.big_eye_list.append(color)
            st.session_state.big_eye_cols = add_to_road(st.session_state.big_eye_cols, color)

        if can_bet and not is_session_stopped:
            now_t = datetime.datetime.now().strftime("%H:%M:%S")
            is_win = (outcome == "B" and predicted_choice == "BANKER") or (outcome == "P" and predicted_choice == "PLAYER")
            
            # Tỉ lệ trả thưởng: Player ăn 1:1, Banker ăn 1:0.95, Thua mất 100%
            if is_win:
                pnl = current_bet_amount * 0.95 if predicted_choice == "BANKER" else current_bet_amount
            else:
                pnl = -current_bet_amount

            new_cap = current_capital + pnl
            res_str = "WIN" if is_win else "LOSE"

            if is_win:
                st.session_state.consecutive_wins += 1
            else:
                st.session_state.consecutive_wins = 0

            # QUY TẮC TỰ ĐỘNG CẬP NHẬT VỐN BAN ĐẦU:
            # 1. Nếu vốn thực tế >= 2 lần vốn ban đầu -> Vốn ban đầu nâng lên bằng vốn thực tế
            # 2. Nếu vốn thực tế <= 1/2 vốn ban đầu -> Vốn ban đầu hạ xuống bằng vốn thực tế
            new_initial_cap = initial_capital
            if new_cap >= 2.0 * initial_capital:
                new_initial_cap = new_cap
            elif new_cap <= 0.5 * initial_capital:
                new_initial_cap = new_cap

            conn = get_db()
            conn.execute("UPDATE config SET current_cap = ?, initial_cap = ? WHERE id = 1", (new_cap, new_initial_cap))
            conn.execute("""
                INSERT INTO trade_history (time_str, session_idx, table_idx, order_name, bet_side, bet_amount, result, pnl, balance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now_t, curr_session, int(cfg['curr_table']), rate_note, predicted_choice, current_bet_amount, res_str, pnl, new_cap))
            conn.commit()
            conn.close()

    with col_p:
        if st.button("🔵 PLAYER (P)", use_container_width=True):
            handle_result_input("P")
            st.rerun()
    with col_b:
        if st.button("🔴 BANKER (B)", use_container_width=True):
            handle_result_input("B")
            st.rerun()

    st.write("---")
    st.subheader("📜 Nhật Ký Đặt Lệnh Chi Tiết")
    if not df_history.empty:
        disp_df = df_history[['time_str', 'session_idx', 'table_idx', 'order_name', 'bet_side', 'bet_amount', 'result', 'pnl', 'balance']].copy()
        disp_df['session_idx'] = disp_df['session_idx'].apply(lambda x: SESSION_NAMES.get(x, f"Phiên {x}"))
        disp_df['bet_amount'] = disp_df['bet_amount'].apply(lambda x: f"${x:,.2f}")
        disp_df['pnl'] = disp_df['pnl'].apply(lambda x: f"${x:+,.2f}")
        disp_df['balance'] = disp_df['balance'].apply(lambda x: f"${x:,.2f}")
        disp_df.columns = ['Giờ', 'Phiên', 'Bàn', 'Chiến Lược', 'Cửa', 'Tiền Đặt ($)', 'KQ', 'Lãi/Lỗ ($)', 'Số Dư ($)']
        st.dataframe(disp_df, use_container_width=True)

with tab_chart:
    st.subheader("📈 THEO DÕI TĂNG TRƯỞNG THEO PHIÊN")
    if df_history.empty:
        st.info("Chưa có lệnh nào được lưu.")
    else:
        chart_df = df_history.sort_values(by="id", ascending=True).copy()
        steps = [0] + list(range(1, len(chart_df) + 1))
        actual_balances = [initial_capital] + chart_df['balance'].tolist()
        
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(x=steps, y=actual_balances, mode='lines+markers', name='Vốn Thực Tế ($)', line=dict(color='#00CC96', width=3)))
        fig_equity.update_layout(title="Đường Cong Số Dư Tài Khoản", xaxis_title="Tổng Số Lệnh Đã Đánh", yaxis_title="Số Dư ($)", template="plotly_white")
        st.plotly_chart(fig_equity, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            session_sum = chart_df.groupby("session_idx")['pnl'].sum().reset_index()
            session_sum['session_idx'] = session_sum['session_idx'].apply(lambda x: SESSION_NAMES.get(x, f"Phiên {x}"))
            fig_session = px.bar(session_sum, x="session_idx", y="pnl", title="Hiệu Quả Từng Phiên Trong Ngày ($)", color="pnl", color_continuous_scale=['#EF553B', '#00CC96'])
            st.plotly_chart(fig_session, use_container_width=True)

        with c2:
            wl_count = chart_df['result'].value_counts().reset_index()
            wl_count.columns = ['Kết Quả', 'Số Lệnh']
            fig_pie = px.pie(wl_count, values='Số Lệnh', names='Kết Quả', title="Tỷ Lệ Thắng / Thua", color='Kết Quả', color_discrete_map={'WIN': '#00CC96', 'LOSE': '#EF553B'})
            st.plotly_chart(fig_pie, use_container_width=True)

# Thanh sidebar hỗ trợ đổi PIN và Đăng xuất
with st.sidebar:
    st.markdown(f"### 👤 {s_name}")
    with st.expander("🔑 Đổi Mã PIN"):
        old_p = st.text_input("Mã PIN hiện tại:", type="password", key="sb_old_pin")
        new_p1 = st.text_input("Mã PIN mới:", type="password", key="sb_new_pin1")
        new_p2 = st.text_input("Xác nhận lại PIN:", type="password", key="sb_new_pin2")
        if st.button("Cập Nhật PIN", use_container_width=True):
            if old_p != get_current_pin():
                st.error("PIN hiện tại không đúng!")
            elif not new_p1 or new_p1 != new_p2:
                st.error("Xác nhận PIN mới không khớp!")
            else:
                set_current_pin(new_p1)
                st.success("Đổi mã PIN thành công!")
                st.rerun()

    if st.button("🚪 Đăng Xuất", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()