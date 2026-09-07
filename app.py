import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime
import sqlite3

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Quản Lý Kỷ Luật & Soi Cầu Baccarat (USD)", layout="wide")

# --- CSS GIAO DIỆN KHỐI TÍN HIỆU TƯƠNG PHẢN CAO ---
st.markdown("""
<style>
    .signal-banker {
        background-color: #dc2626; color: #ffffff; padding: 16px 20px;
        border-radius: 8px; font-size: 21px; font-weight: 800; text-align: center;
        box-shadow: 0 4px 6px rgba(220, 38, 38, 0.4); margin: 10px 0;
    }
    .signal-player {
        background-color: #2563eb; color: #ffffff; padding: 16px 20px;
        border-radius: 8px; font-size: 21px; font-weight: 800; text-align: center;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.4); margin: 10px 0;
    }
    .signal-wait {
        background-color: #f4f4f5; color: #52525b; padding: 14px 20px;
        border-radius: 8px; font-size: 16px; font-weight: 600; text-align: center;
        border: 1px dashed #a1a1aa; margin: 10px 0;
    }
    .signal-stop {
        background-color: #991b1b; color: #ffffff; padding: 16px 20px;
        border-radius: 8px; font-size: 18px; font-weight: 800; text-align: center; margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- CƠ SỞ DỮ LIỆU SQLITE (LƯU BẢO MẬT & VĨNH VIỄN) ---
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
        # Khởi tạo mặc định $1,000
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

# --- LỚP XÁC THỰC MÃ PIN BẢO MẬT ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

current_pin = get_current_pin()

if not st.session_state.authenticated:
    st.markdown("## 🔒 HỆ THỐNG QUẢN LÝ KỶ LUẬT RIÊNG TƯ")
    if current_pin is None:
        st.info("👋 Vui lòng thiết lập mã PIN bảo mật ban đầu để bảo vệ dữ liệu.")
        p1 = st.text_input("Nhập mã PIN muốn tạo (ví dụ: 4-6 số):", type="password")
        p2 = st.text_input("Xác nhận lại mã PIN vừa nhập:", type="password")
        if st.button("Lưu Mã PIN & Vào App"):
            if not p1:
                st.error("Mã PIN không được để trống!")
            elif p1 != p2:
                st.error("Hai lần nhập mã PIN không khớp nhau!")
            else:
                set_current_pin(p1)
                st.session_state.authenticated = True
                st.success("Thiết lập mã PIN thành công!")
                st.rerun()
    else:
        pin_input = st.text_input("Nhập mã PIN bảo mật để mở khóa:", type="password")
        if st.button("Mở Khóa"):
            if pin_input == current_pin:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Mã PIN không đúng! Vui lòng nhập lại.")
    st.stop()

# --- TẢI DỮ LIỆU ---
def load_data():
    conn = get_db()
    cfg = pd.read_sql("SELECT * FROM config WHERE id = 1", conn).iloc[0]
    his = pd.read_sql("SELECT * FROM trade_history ORDER BY id DESC", conn)
    conn.close()
    return cfg, his

cfg, df_history = load_data()

# Khởi tạo bộ nhớ tạm
if "raw_inputs" not in st.session_state:
    st.session_state.raw_inputs = []
if "main_road" not in st.session_state:
    st.session_state.main_road = []
if "big_eye_cols" not in st.session_state:
    st.session_state.big_eye_cols = []
if "big_eye_list" not in st.session_state:
    st.session_state.big_eye_list = []

if "trade_status" not in st.session_state:
    st.session_state.trade_status = 0
if "last_bet_amount" not in st.session_state:
    st.session_state.last_bet_amount = 0.0

# --- THUẬT TOÁN ĐƯỜNG CẦU BACCARAT ---
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
    sim_b = add_to_road(road, "B")
    color_b = get_big_eye_color(sim_b, len(sim_b) - 1, len(sim_b[-1]) - 1)
    if color_b == "RED":
        return "BANKER"

    sim_p = add_to_road(road, "P")
    color_p = get_big_eye_color(sim_p, len(sim_p) - 1, len(sim_p[-1]) - 1)
    if color_p == "RED":
        return "PLAYER"
    return "BANKER"

def reset_table(new_table_idx):
    st.session_state.raw_inputs = []
    st.session_state.main_road = []
    st.session_state.big_eye_cols = []
    st.session_state.big_eye_list = []
    st.session_state.trade_status = 0
    st.session_state.last_bet_amount = 0.0
    conn = get_db()
    conn.execute("UPDATE config SET curr_table = ? WHERE id = 1", (new_table_idx,))
    conn.commit()
    conn.close()

# --- THANH BÊN (SIDEBAR): QUẢN LÝ VỐN USD & ĐỔI PIN ---
with st.sidebar:
    st.header("⚙️ Quản Lý Vốn (USD)")
    new_init_cap = st.number_input("Số vốn ban đầu ($):", min_value=10.0, value=float(cfg['initial_cap']), step=50.0)
    if st.button("💾 Cập Nhật Lại Vốn", use_container_width=True):
        conn = get_db()
        conn.execute("UPDATE config SET initial_cap=?, current_cap=?, session_start_cap=?, curr_session=1, curr_table=1 WHERE id=1", 
                     (new_init_cap, new_init_cap, new_init_cap))
        conn.execute("DELETE FROM trade_history")
        conn.commit()
        conn.close()
        reset_table(1)
        st.rerun()

    st.write("---")
    st.markdown(f"**Phiên hiện tại:** `Phiên {int(cfg['curr_session'])} / 4`")
    st.markdown(f"**Bàn hiện tại:** `Bàn {int(cfg['curr_table'])}`")
    if st.button("🔄 Đổi Bàn Mới (Xóa cầu)", use_container_width=True):
        reset_table(int(cfg['curr_table']) + 1)
        st.rerun()

    st.write("---")
    with st.expander("🔑 Đổi Mã PIN Bảo Mật"):
        old_p = st.text_input("Mã PIN hiện tại:", type="password", key="old_pin_field")
        new_p1 = st.text_input("Mã PIN mới:", type="password", key="new_pin_1")
        new_p2 = st.text_input("Xác nhận PIN mới:", type="password", key="new_pin_2")
        if st.button("Lưu Mã PIN Mới", use_container_width=True):
            if old_p != get_current_pin():
                st.error("Mã PIN hiện tại không chính xác!")
            elif not new_p1:
                st.error("Mã PIN mới không được để trống!")
            elif new_p1 != new_p2:
                st.error("Xác nhận mã PIN mới không khớp!")
            else:
                set_current_pin(new_p1)
                st.success("Đổi mã PIN thành công!")
                st.rerun()

    if st.button("🚪 Đăng Xuất", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# --- HEADER DASHBOARD THỐNG KÊ (USD) ---
current_capital = float(cfg['current_cap'])
session_start_cap = float(cfg['session_start_cap'])
initial_capital = float(cfg['initial_cap'])

session_profit = current_capital - session_start_cap
session_profit_pct = (session_profit / session_start_cap) * 100
total_profit = current_capital - initial_capital

st.title("🎯 Quản Trị Kỷ Luật & Soi Cầu Baccarat")

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("VỐN THỰC TẾ", f"${current_capital:,.2f}", delta=f"${total_profit:+,.2f} (Tổng)")
col_m2.metric("LÃI/LỖ PHIÊN NÀY", f"${session_profit:+,.2f}", delta=f"{session_profit_pct:.2f}%")
col_m3.metric("TARGET PHIÊN (5%)", f"${session_start_cap * 0.05:,.2f}")
col_m4.metric("SỐ LỆNH ĐÃ ĐẶT", f"{len(df_history)} lệnh")

st.divider()

# Cảnh báo Target phiên 5%
if session_profit_pct >= 5.0:
    st.error(f"🛑 CẢNH BÁO STOP! Đã đạt target phiên: +{session_profit_pct:.2f}% (≥ 5%). DỪNG PHIÊN NGAY LẬP TỨC!")
    if st.button("Xác Nhận Chốt Lời ➔ Sang Phiên Mới"):
        conn = get_db()
        next_s = int(cfg['curr_session']) + 1
        if next_s <= 4:
            conn.execute("UPDATE config SET curr_session=?, session_start_cap=? WHERE id=1", (next_s, current_capital))
            conn.commit()
            conn.close()
            reset_table(int(cfg['curr_table']) + 1)
            st.rerun()
        else:
            st.warning("Đã hoàn thành toàn bộ 4 phiên trong ngày!")
            conn.close()

# --- TAB GIAO DIỆN ---
tab_bet, tab_chart = st.tabs(["🎮 BÀN ĐÁNH & VÀO LỆNH", "📊 DASHBOARD BIỂU ĐỒ LÃI KÉP"])

with tab_bet:
    st.markdown("### 🔔 VÀO LỆNH NGAY :")
    base_5pct = current_capital * 0.05
    predicted_choice = find_red_choice()
    num_seeds = len(st.session_state.big_eye_list)

    current_bet_side = None
    current_bet_amount = 0.0

    if st.session_state.trade_status == 3:
        st.markdown('<div class="signal-stop">🛑 ĐÃ HOÀN THÀNH BÀN NÀY (HẾT 2 HẠT ĐỎ HOẶC ĐÃ WIN LỆNH 1)! BẤM "ĐỔI BÀN MỚI" ĐỂ TIẾP TỤC.</div>', unsafe_allow_html=True)
    elif num_seeds == 0:
        st.markdown('<div class="signal-wait">⏳ Đang chờ Bảng phụ 1 xuất hiện hạt đầu tiên... (Nhập kết quả các ván bài bên dưới)</div>', unsafe_allow_html=True)
    elif st.session_state.trade_status == 1:
        current_bet_side = predicted_choice
        current_bet_amount = base_5pct
        st.session_state.last_bet_amount = base_5pct
        b_class = "signal-banker" if current_bet_side == "BANKER" else "signal-player"
        st.markdown(f'<div class="{b_class}">🚨 ĐẶT LỆNH 1: ĐÁNH {current_bet_side} | SỐ TIỀN: ${current_bet_amount:,.2f} (5% Vốn)</div>', unsafe_allow_html=True)
    elif st.session_state.trade_status == 2:
        current_bet_side = predicted_choice
        current_bet_amount = st.session_state.last_bet_amount
        b_class = "signal-banker" if current_bet_side == "BANKER" else "signal-player"
        st.markdown(f'<div class="{b_class}">🚨 ĐẶT LỆNH 2: ĐÁNH {current_bet_side} | SỐ TIỀN: ${current_bet_amount:,.2f} (Bằng số tiền Lệnh 1)</div>', unsafe_allow_html=True)

    st.divider()

    # Bảng cầu
    def build_html_board(columns, is_big_eye=False):
        total_cols = max(55, len(columns) + 5)
        html = """<style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: sans-serif; background: transparent; }
            .wrapper { background: #ffffff; border: 1px solid #71717a; overflow-x: auto; white-space: nowrap; width: 100%; padding: 2px; }
            table { border-collapse: collapse; table-layout: fixed; background: #ffffff; }
            th { width: 26px; min-width: 26px; height: 20px; border: 1px solid #d4d4d8; border-bottom: 2px solid #27272a; font-size: 11px; font-weight: bold; color: #3f3f46; text-align: center; background: #f4f4f5; }
            td { width: 26px; min-width: 26px; height: 26px; border: 1px solid #e4e4e7; text-align: center; vertical-align: middle; padding: 0; }
            .circle-b { width: 18px; height: 18px; border-radius: 50%; border: 2.5px solid #dc2626; margin: auto; }
            .circle-p { width: 18px; height: 18px; border-radius: 50%; border: 2.5px solid #2563eb; margin: auto; }
            .eye-red { width: 15px; height: 15px; border-radius: 50%; border: 2px solid #dc2626; margin: auto; }
            .eye-blue { width: 15px; height: 15px; border-radius: 50%; border: 2px solid #2563eb; margin: auto; }
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
    st.components.v1.html(build_html_board(st.session_state.main_road, is_big_eye=False), height=205, scrolling=True)

    st.markdown(f"##### 🔴🔵 Bảng Phụ 1 - Big Eye Boy ({len(st.session_state.big_eye_list)} hạt)")
    st.components.v1.html(build_html_board(st.session_state.big_eye_cols, is_big_eye=True), height=205, scrolling=True)

    if st.session_state.raw_inputs:
        tags = ["<span style='color: #dc2626; font-weight: bold;'>🔴 B</span>" if x == "B" else "<span style='color: #2563eb; font-weight: bold;'>🔵 P</span>" for x in st.session_state.raw_inputs]
        st.markdown("**Các tay vừa nhập:** " + " ➔ ".join(tags[-25:]), unsafe_allow_html=True)

    st.divider()

    col_p, col_b = st.columns(2)

    def handle_input(outcome):
        st.session_state.raw_inputs.append(outcome)
        st.session_state.main_road = add_to_road(st.session_state.main_road, outcome)
        road = st.session_state.main_road
        c_idx, r_idx = len(road) - 1, len(road[-1]) - 1

        color = get_big_eye_color(road, c_idx, r_idx)
        if color is not None:
            st.session_state.big_eye_list.append(color)
            st.session_state.big_eye_cols = add_to_road(st.session_state.big_eye_cols, color)
            if len(st.session_state.big_eye_list) == 1 and st.session_state.trade_status == 0:
                st.session_state.trade_status = 1

        if current_bet_side is not None:
            now_t = datetime.datetime.now().strftime("%H:%M:%S - %d/%m")
            is_win = (outcome == "B" and current_bet_side == "BANKER") or (outcome == "P" and current_bet_side == "PLAYER")
            pnl = (current_bet_amount * 0.95 if current_bet_side == "BANKER" else current_bet_amount) if is_win else -current_bet_amount
            new_cap = current_capital + pnl
            res_str = "WIN" if is_win else "LOSE"

            o_name = "Lệnh 1" if st.session_state.trade_status == 1 else "Lệnh 2"

            if is_win:
                st.session_state.trade_status = 3
            else:
                st.session_state.trade_status = 2 if st.session_state.trade_status == 1 else 3

            conn = get_db()
            conn.execute("UPDATE config SET current_cap = ? WHERE id = 1", (new_cap,))
            conn.execute("""
                INSERT INTO trade_history (time_str, session_idx, table_idx, order_name, bet_side, bet_amount, result, pnl, balance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now_t, int(cfg['curr_session']), int(cfg['curr_table']), o_name, current_bet_side, current_bet_amount, res_str, pnl, new_cap))
            conn.commit()
            conn.close()

    with col_p:
        if st.button("🔵 PLAYER (P)", use_container_width=True):
            handle_input("P")
            st.rerun()
    with col_b:
        if st.button("🔴 BANKER (B)", use_container_width=True):
            handle_input("B")
            st.rerun()

    st.divider()
    st.subheader("📜 Lịch Sử Cược Chi Tiết")
    if not df_history.empty:
        display_df = df_history[['time_str', 'session_idx', 'table_idx', 'order_name', 'bet_side', 'bet_amount', 'result', 'pnl', 'balance']].copy()
        display_df['bet_amount'] = display_df['bet_amount'].apply(lambda x: f"${x:,.2f}")
        display_df['pnl'] = display_df['pnl'].apply(lambda x: f"${x:+,.2f}")
        display_df['balance'] = display_df['balance'].apply(lambda x: f"${x:,.2f}")
        display_df.columns = ['Thời Gian', 'Phiên', 'Bàn', 'Lệnh', 'Cửa Đặt', 'Tiền Đặt ($)', 'Kết Quả', '+/- Lãi Lỗ ($)', 'Số Dư ($)']
        st.dataframe(display_df, use_container_width=True)

with tab_chart:
    st.subheader("📈 BÁO CÁO DASHBOARD TĂNG TRƯỞNG LÃI KÉP (USD)")
    if df_history.empty:
        st.info("Chưa có dữ liệu lệnh. Hãy đặt một vài lệnh để hiển thị biểu đồ phân tích.")
    else:
        chart_df = df_history.sort_values(by="id", ascending=True).copy()
        
        steps = [0] + list(range(1, len(chart_df) + 1))
        actual_balances = [initial_capital] + chart_df['balance'].tolist()
        
        target_compound = [initial_capital]
        for i in range(1, len(chart_df) + 1):
            target_compound.append(target_compound[-1] * 1.05)
            
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(x=steps, y=actual_balances, mode='lines+markers', name='Vốn Thực Tế ($)', line=dict(color='#00CC96', width=3)))
        fig_equity.add_trace(go.Scatter(x=steps, y=target_compound, mode='lines', name='Mục Tiêu Lãi Kép (+5%/lệnh)', line=dict(color='#FFA15A', dash='dash')))
        fig_equity.update_layout(title="Đường Cong Tăng Trưởng Vốn Thực Tế vs Mục Tiêu Lãi Kép", xaxis_title="Chuỗi Lệnh Đã Đánh", yaxis_title="Số Dư ($)", template="plotly_white")
        st.plotly_chart(fig_equity, use_container_width=True)

        c_left, c_right = st.columns(2)
        with c_left:
            session_sum = chart_df.groupby("session_idx")['pnl'].sum().reset_index()
            session_sum['session_idx'] = session_sum['session_idx'].apply(lambda x: f"Phiên {x}")
            fig_session = px.bar(session_sum, x="session_idx", y="pnl", title="Tổng Lợi Nhuận Từng Phiên ($)", color="pnl", color_continuous_scale=['#EF553B', '#00CC96'])
            st.plotly_chart(fig_session, use_container_width=True)

        with c_right:
            win_loss_count = chart_df['result'].value_counts().reset_index()
            win_loss_count.columns = ['Kết Quả', 'Số Lệnh']
            fig_pie = px.pie(win_loss_count, values='Số Lệnh', names='Kết Quả', title="Tỷ Lệ Thắng / Thua", color='Kết Quả', color_discrete_map={'WIN': '#00CC96', 'LOSE': '#EF553B'})
            st.plotly_chart(fig_pie, use_container_width=True)