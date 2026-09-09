import streamlit as st
import pandas as pd
import datetime
from zoneinfo import ZoneInfo
import sqlite3
import os

# --- CẤU HÌNH GIAO DIỆN NHẸ MƯỢT ---
st.set_page_config(page_title="Quản Trị Kỷ Luật Bản Thân", layout="wide", initial_sidebar_state="collapsed")

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

def get_vn_time_str():
    return datetime.datetime.now(VN_TZ).strftime("%H:%M:%S - %d/%m")

# CSS tối ưu tốc độ render trên mobile
st.markdown("""
<style>
    .signal-banker {
        background-color: #dc2626; color: #ffffff; padding: 12px;
        border-radius: 8px; font-size: 18px; font-weight: 800; text-align: center; margin: 8px 0;
    }
    .signal-player {
        background-color: #2563eb; color: #ffffff; padding: 12px;
        border-radius: 8px; font-size: 18px; font-weight: 800; text-align: center; margin: 8px 0;
    }
    .signal-wait {
        background-color: #27272a; color: #a1a1aa; padding: 10px;
        border-radius: 6px; font-size: 14px; font-weight: 600; text-align: center; margin: 8px 0;
        border: 1px dashed #52525b;
    }
    .signal-stop {
        background-color: #991b1b; color: #ffffff; padding: 15px;
        border-radius: 8px; font-size: 16px; font-weight: 800; text-align: center; margin: 8px 0;
        border: 2px solid #ef4444;
    }
    .signal-table-stop {
        background-color: #b45309; color: #ffffff; padding: 14px;
        border-radius: 8px; font-size: 16px; font-weight: 800; text-align: center; margin: 8px 0;
        border: 2px solid #f59e0b;
    }
</style>
""", unsafe_allow_html=True)

# --- CƠ SỞ DỮ LIỆU SQLITE BỀN VỮNG ---
DB_PATH = "baccarat_data.db"

def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

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
            curr_table INTEGER,
            orders_in_current_table INTEGER
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
    # Kiểm tra cấu hình ban đầu
    c.execute("SELECT COUNT(*) FROM config")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO config VALUES (1, 200.0, 200.0, 200.0, 1, 1, 0)")
    else:
        # Đảm bảo cột orders_in_current_table tồn tại
        try:
            c.execute("ALTER TABLE config ADD COLUMN orders_in_current_table INTEGER DEFAULT 0")
        except:
            pass
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
                st.error("Xác nhận không khớp!")
            else:
                set_current_pin(p1)
                st.session_state.authenticated = True
                st.rerun()
    else:
        pin_input = st.text_input("Nhập mã PIN:", type="password")
        if st.button("Mở Khóa"):
            if pin_input == current_pin:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Mã PIN không đúng!")
    st.stop()

# --- TẢI DỮ LIỆU TỪ DATABASE ---
def load_data():
    conn = get_db()
    cfg = pd.read_sql("SELECT * FROM config WHERE id = 1", conn).iloc[0]
    his = pd.read_sql("SELECT * FROM trade_history ORDER BY id DESC", conn)
    conn.close()
    return cfg, his

cfg, df_history = load_data()

# Bộ nhớ tạm phiên hiện tại
if "raw_inputs" not in st.session_state:
    st.session_state.raw_inputs = []
if "main_road" not in st.session_state:
    st.session_state.main_road = []
if "big_eye_cols" not in st.session_state:
    st.session_state.big_eye_cols = []
if "big_eye_list" not in st.session_state:
    st.session_state.big_eye_list = []

SESSION_DICT = {
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
    conn.execute("UPDATE config SET curr_table = ?, orders_in_current_table = 0 WHERE id = 1", (new_table_idx,))
    conn.commit()
    conn.close()

# --- GIAO DIỆN CHÍNH ---
st.title("🎯 Quản Trị Kỷ Luật Bản Thân")

current_capital = float(cfg['current_cap'])
session_start_cap = float(cfg['session_start_cap'])
initial_capital = float(cfg['initial_cap'])
curr_session = int(cfg['curr_session'])
orders_in_table = int(cfg.get('orders_in_current_table', 0))

# --- CHỌN PHIÊN ---
col_sel_s, col_table_num = st.columns([2, 1])
with col_sel_s:
    selected_session = st.selectbox(
        "📅 Chọn Phiên Giao Dịch:",
        options=[1, 2, 3, 4],
        format_func=lambda x: SESSION_DICT[x],
        index=curr_session - 1
    )
    if selected_session != curr_session:
        conn = get_db()
        conn.execute("UPDATE config SET curr_session = ?, session_start_cap = ?, orders_in_current_table = 0 WHERE id = 1", 
                     (selected_session, current_capital))
        conn.commit()
        conn.close()
        reset_table(int(cfg['curr_table']) + 1)
        st.rerun()

with col_table_num:
    st.metric("BÀN HIỆN TẠI", f"Bàn {int(cfg['curr_table'])}", delta=f"{orders_in_table}/2 lệnh")

s_name = SESSION_DICT.get(selected_session, f"Phiên {selected_session}")

# Trích xuất toàn bộ lệnh của riêng phiên đang chọn
session_trades = df_history[df_history['session_idx'] == selected_session].sort_values(by="id", ascending=True)
num_session_trades = len(session_trades)
session_profit = current_capital - session_start_cap
session_profit_pct = (session_profit / session_start_cap) * 100 if session_start_cap > 0 else 0
total_profit = current_capital - initial_capital

# --- KIỂM TRA ĐIỀU KIỆN STOP PHIÊN ---
# 1. Lệnh 1 của phiên win -> BẮT BUỘC STOP
is_first_trade_win = False
if num_session_trades >= 1:
    if session_trades.iloc[0]['result'] == 'WIN':
        is_first_trade_win = True

# 2. Hoặc sau chuỗi gỡ mà tài khoản dương đạt target (4.7% -> 5%)
is_profit_target_reached = (session_profit >= (initial_capital * 0.047)) or (session_profit_pct >= 4.70)

is_session_stopped = is_first_trade_win or is_profit_target_reached

# --- HIỂN THỊ CHỈ SỐ VỐN ---
col_m1, col_m2 = st.columns(2)
col_m1.metric("VỐN THỰC TẾ", f"${current_capital:,.2f}", delta=f"${total_profit:+,.2f} (Tổng)")
col_m2.metric("VỐN BAN ĐẦU (GỐC 5%)", f"${initial_capital:,.2f}")

col_m3, col_m4 = st.columns(2)
col_m3.metric(f"LÃI/LỖ {s_name}", f"${session_profit:+,.2f}", delta=f"{session_profit_pct:.2f}%")
col_m4.metric("TARGET PHIÊN (5%)", f"+${initial_capital * 0.05:,.2f}")

# Menu chỉnh sửa vốn & đổi bàn
with st.expander("⚡ Điều Chỉnh Vốn & Đổi Bàn Cược"):
    c_edit1, c_edit2 = st.columns(2)
    new_init_input = c_edit1.number_input("Vốn Ban Đầu ($):", min_value=10.0, value=initial_capital, step=50.0)
    new_curr_input = c_edit2.number_input("Vốn Thực Tế ($):", min_value=1.0, value=current_capital, step=50.0)
    cq1, cq2 = st.columns(2)
    if cq1.button("💾 Lưu Vốn", use_container_width=True):
        conn = get_db()
        conn.execute("UPDATE config SET initial_cap = ?, current_cap = ?, session_start_cap = ? WHERE id = 1", 
                     (new_init_input, new_curr_input, new_curr_input))
        conn.commit()
        conn.close()
        st.rerun()
    if cq2.button("🔄 ĐỔI BÀN MỚI (XÓA CẦU)", use_container_width=True):
        reset_table(int(cfg['curr_table']) + 1)
        st.rerun()

st.divider()

# THÔNG BÁO STOP PHIÊN
if is_session_stopped:
    reason_str = "LỆNH 1 ĐẦU PHIÊN ĐÃ THẮNG (+5%)" if is_first_trade_win else f"TÀI KHOẢN ĐÃ DƯƠNG TARGET (+{session_profit_pct:.2f}%)"
    st.markdown(f'<div class="signal-stop">🛑 KỶ LUẬT THÉP: {reason_str}!<br>BẮT BUỘC STOP TOÀN BỘ PHIÊN NÀY. TẮT APP VÀ NGHỈ NGƠI!</div>', unsafe_allow_html=True)

# KIỂM TRA ĐIỀU KIỆN KHÓA BÀN (MỖI BÀN CHỈ ĐƯỢC 2 LỆNH)
is_table_locked = (orders_in_table >= 2)
if is_table_locked and not is_session_stopped:
    st.markdown(f'<div class="signal-table-stop">⚠️ BÀN NÀY ĐÃ ĐỦ 2 LỆNH (TỐI ĐA)!<br>BẮT BUỘC BẤM "🔄 ĐỔI BÀN MỚI" Ở MỤC TRÊN ĐỂ TIẾP TỤC QUẢN LÝ VỐN PHIÊN.</div>', unsafe_allow_html=True)

# --- BÀN CƯỢC & VÀO LỆNH ---
tab_bet, tab_chart = st.tabs(["🎮 BÀN ĐÁNH & VÀO LỆNH", "📊 NHẬT KÝ & BÁO CÁO"])

with tab_bet:
    # Bảng vẽ cầu rút gọn tốc độ cao (chỉ vẽ 35 cột để chống lag trên điện thoại)
    def build_fast_board(columns, is_big_eye=False):
        total_cols = max(35, len(columns) + 3)
        html = """<style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            .w { background: #18181b; overflow-x: auto; white-space: nowrap; width: 100%; padding: 2px; border: 1px solid #3f3f46; border-radius: 4px; }
            table { border-collapse: collapse; table-layout: fixed; }
            th { width: 22px; min-width: 22px; height: 16px; border: 1px solid #3f3f46; font-size: 9px; color: #a1a1aa; text-align: center; background: #27272a; }
            td { width: 22px; min-width: 22px; height: 22px; border: 1px solid #27272a; text-align: center; vertical-align: middle; }
            .cb { width: 15px; height: 15px; border-radius: 50%; border: 2.2px solid #ef4444; margin: auto; }
            .cp { width: 15px; height: 15px; border-radius: 50%; border: 2.2px solid #3b82f6; margin: auto; }
            .er { width: 13px; height: 13px; border-radius: 50%; border: 2px solid #ef4444; margin: auto; }
            .eb { width: 13px; height: 13px; border-radius: 50%; border: 2px solid #3b82f6; margin: auto; }
        </style><div class="w"><table><thead><tr>"""
        for c in range(1, total_cols + 1):
            html += f"<th>{c}</th>"
        html += "</tr></thead><tbody>"
        for r in range(6):
            html += "<tr>"
            for c in range(total_cols):
                cnt = ""
                if c < len(columns) and r < len(columns[c]):
                    v = columns[c][r]
                    cls = ("cb" if v == "B" else "cp") if not is_big_eye else ("er" if v == "RED" else "eb")
                    cnt = f'<div class="{cls}"></div>'
                html += f"<td>{cnt}</td>"
            html += "</tr>"
        html += "</tbody></table></div>"
        return html

    st.markdown("##### 🔴🔵 Bảng Chính (Big Road)")
    st.components.v1.html(build_fast_board(st.session_state.main_road, is_big_eye=False), height=170, scrolling=True)

    st.markdown(f"##### 🔴🔵 Bảng Phụ 1 - Big Eye Boy ({len(st.session_state.big_eye_list)} hạt)")
    st.components.v1.html(build_fast_board(st.session_state.big_eye_cols, is_big_eye=True), height=170, scrolling=True)

    if st.session_state.raw_inputs:
        tags = ["<span style='color: #ef4444; font-weight: bold;'>🔴 B</span>" if x == "B" else "<span style='color: #3b82f6; font-weight: bold;'>🔵 P</span>" for x in st.session_state.raw_inputs]
        st.markdown("**Đã nhập:** " + " ➔ ".join(tags[-15:]), unsafe_allow_html=True)

    st.write("---")

    # --- QUẢN LÝ TIỀN CƯỢC LOGIC CHUẨN ---
    base_5pct = initial_capital * 0.05
    num_seeds = len(st.session_state.big_eye_list)
    predicted_choice = find_red_choice()

    current_bet_side = None
    current_bet_amount = 0.0
    strategy_note = ""

    if num_session_trades == 0:
        # Lệnh đầu tiên của phiên: Luôn đánh 5%
        current_bet_amount = base_5pct
        strategy_note = "Lệnh 1 (5% Vốn - Thắng là STOP Phiên)"
    else:
        # Đếm số lệnh WIN liên tiếp tính ngược từ lệnh gần nhất
        consec_wins = 0
        for _, r in session_trades.iloc[::-1].iterrows():
            if r['result'] == 'WIN':
                consec_wins += 1
            else:
                break

        # Nếu đang âm so với đầu phiên:
        if session_profit < 0:
            if consec_wins == 1:
                current_bet_amount = base_5pct * 2.0  # Lệnh trước win -> Lệnh sau gấp đôi (10%)
                strategy_note = "10% (Gấp Đôi sau 1 Win - Săn chuỗi 2 Win)"
            else:
                current_bet_amount = base_5pct  # Lệnh trước thua hoặc đã đủ 2 win mà chưa dương -> về 5%
                strategy_note = "5% Vốn Ban Đầu (Bảo toàn vốn)"
        else:
            current_bet_amount = base_5pct
            strategy_note = "5% Vốn Ban Đầu"

    # Hiển thị tín hiệu
    if is_session_stopped:
        st.markdown('<div class="signal-stop">🛑 PHIÊN ĐÃ ĐẠT MỤC TIÊU! TOÀN BỘ LỆNH ĐÃ KHÓA CỨNG.</div>', unsafe_allow_html=True)
    elif is_table_locked:
        st.markdown('<div class="signal-table-stop">🛑 BÀN ĐÃ HẾT 2 LỆNH! HÃY BẤM "🔄 ĐỔI BÀN MỚI" Ở TRÊN.</div>', unsafe_allow_html=True)
    elif num_seeds == 0:
        st.markdown('<div class="signal-wait">⏳ Đang chờ Bảng phụ 1 xuất hiện hạt đầu tiên...</div>', unsafe_allow_html=True)
    else:
        current_bet_side = predicted_choice
        b_class = "signal-banker" if current_bet_side == "BANKER" else "signal-player"
        st.markdown(f'<div class="{b_class}">🚨 ĐẶT CƯỢC: {current_bet_side} | ${current_bet_amount:,.2f}<br><span style="font-size: 13px; font-weight: normal;">(Lệnh {orders_in_table + 1}/2 của bàn - {strategy_note})</span></div>', unsafe_allow_html=True)

    # NÚT BẤM CƯỢC: Khóa nếu phiên dừng hoặc bàn đã đủ 2 lệnh
    btn_disabled = is_session_stopped or is_table_locked

    col_p, col_b = st.columns(2)

    def handle_result_input(outcome):
        global initial_capital, current_capital, orders_in_table
        st.session_state.raw_inputs.append(outcome)
        st.session_state.main_road = add_to_road(st.session_state.main_road, outcome)
        road = st.session_state.main_road
        c_idx, r_idx = len(road) - 1, len(road[-1]) - 1

        color = get_big_eye_color(road, c_idx, r_idx)
        if color is not None:
            st.session_state.big_eye_list.append(color)
            st.session_state.big_eye_cols = add_to_road(st.session_state.big_eye_cols, color)

        if current_bet_side is not None and not is_session_stopped and not is_table_locked:
            now_t = get_vn_time_str()
            is_win = (outcome == "B" and current_bet_side == "BANKER") or (outcome == "P" and current_bet_side == "PLAYER")
            
            pnl = (current_bet_amount * 0.95 if current_bet_side == "BANKER" else current_bet_amount) if is_win else -current_bet_amount
            new_cap = current_capital + pnl
            res_str = "WIN" if is_win else "LOSE"

            # Tự động cân bằng vốn ban đầu
            new_initial_cap = initial_capital
            if new_cap >= 2.0 * initial_capital:
                new_initial_cap = new_cap
            elif new_cap <= 0.5 * initial_capital:
                new_initial_cap = new_cap

            new_orders_in_table = orders_in_table + 1

            conn = get_db()
            conn.execute("UPDATE config SET current_cap = ?, initial_cap = ?, orders_in_current_table = ? WHERE id = 1", 
                         (new_cap, new_initial_cap, new_orders_in_table))
            conn.execute("""
                INSERT INTO trade_history (time_str, session_idx, table_idx, order_name, bet_side, bet_amount, result, pnl, balance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (now_t, selected_session, int(cfg['curr_table']), strategy_note, current_bet_side, current_bet_amount, res_str, pnl, new_cap))
            conn.commit()
            conn.close()

    with col_p:
        if st.button("🔵 PLAYER (P)", use_container_width=True, disabled=btn_disabled):
            handle_result_input("P")
            st.rerun()
    with col_b:
        if st.button("🔴 BANKER (B)", use_container_width=True, disabled=btn_disabled):
            handle_result_input("B")
            st.rerun()

with tab_chart:
    st.subheader("📜 Nhật Ký Đặt Lệnh Chi Tiết")
    if not df_history.empty:
        disp_df = df_history[['time_str', 'session_idx', 'table_idx', 'order_name', 'bet_side', 'bet_amount', 'result', 'pnl', 'balance']].copy()
        disp_df['session_idx'] = disp_df['session_idx'].apply(lambda x: SESSION_DICT.get(x, f"Phiên {x}"))
        disp_df['bet_amount'] = disp_df['bet_amount'].apply(lambda x: f"${x:,.2f}")
        disp_df['pnl'] = disp_df['pnl'].apply(lambda x: f"${x:+,.2f}")
        disp_df['balance'] = disp_df['balance'].apply(lambda x: f"${x:,.2f}")
        disp_df.columns = ['Giờ (GMT+7)', 'Phiên', 'Bàn', 'Chiến Lược', 'Cửa', 'Tiền Đặt ($)', 'KQ', 'Lãi/Lỗ ($)', 'Số Dư ($)']
        st.dataframe(disp_df, use_container_width=True)
    else:
        st.info("Chưa có lệnh nào được lưu.")

# Sidebar
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
                st.error("Xác nhận PIN không khớp!")
            else:
                set_current_pin(new_p1)
                st.success("Đổi mã PIN thành công!")
                st.rerun()

    if st.button("🚪 Đăng Xuất", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
