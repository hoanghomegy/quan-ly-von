import streamlit as st
import pandas as pd
import datetime
from zoneinfo import ZoneInfo
import sqlite3
import os

# --- CẤU HÌNH HỆ THỐNG & GIAO DIỆN ---
st.set_page_config(
    page_title="Quản Trị Kỷ Luật Bản Thân",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Múi giờ Việt Nam GMT+7
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

def get_vn_now():
    return datetime.datetime.now(VN_TZ)

# --- MÃ PIN CỐ ĐỊNH AN TOÀN (Tùy chỉnh số bạn thích) ---
MASTER_PIN = "6868"

# --- CSS SIÊU TỐI ƯU GIAO DIỆN VÀ TỐC ĐỘ BẤM NÚT TRÊN MOBILE ---
st.markdown("""
<style>
    /* Ẩn các icon thừa của streamlit để tăng tốc render */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .metric-container {
        background-color: #1e1e24; border-radius: 8px; padding: 10px; border: 1px solid #333;
    }
    .box-signal-banker {
        background-color: #d32f2f !important;
        color: #ffffff !important;
        padding: 16px;
        border-radius: 10px;
        font-size: 20px;
        font-weight: 900;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(211, 47, 47, 0.6);
        letter-spacing: 1px;
    }
    .box-signal-player {
        background-color: #1976d2 !important;
        color: #ffffff !important;
        padding: 16px;
        border-radius: 10px;
        font-size: 20px;
        font-weight: 900;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(25, 118, 210, 0.6);
        letter-spacing: 1px;
    }
    .box-signal-wait {
        background-color: #27272a;
        color: #a1a1aa;
        padding: 12px;
        border-radius: 8px;
        font-size: 15px;
        font-weight: 600;
        text-align: center;
        margin: 10px 0;
        border: 1px dashed #52525b;
    }
    .box-signal-stop {
        background-color: #7f1d1d;
        color: #fecaca;
        padding: 18px;
        border-radius: 10px;
        font-size: 18px;
        font-weight: 900;
        text-align: center;
        margin: 10px 0;
        border: 2px solid #ef4444;
        box-shadow: 0 4px 14px rgba(239, 68, 68, 0.5);
    }
    .box-signal-table-lock {
        background-color: #78350f;
        color: #fde68a;
        padding: 14px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 800;
        text-align: center;
        margin: 10px 0;
        border: 2px solid #f59e0b;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE QUẢN LÝ DỮ LIỆU BỀN VỮNG (SQLITE CÓ FILE DỰ PHÒNG) ---
DB_FILE = "baccarat_system.db"
BACKUP_CSV = "trade_history_backup.csv"

def get_db_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_system_database():
    conn = get_db_connection()
    c = conn.cursor()
    # Bảng lưu trữ cấu hình vốn & trạng thái
    c.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY,
            initial_cap REAL,
            current_cap REAL,
            session_start_cap REAL,
            curr_session_idx INTEGER,
            curr_table_num INTEGER,
            table_orders_count INTEGER,
            last_date TEXT
        )
    """)
    # Bảng lịch sử đặt lệnh chi tiết
    c.execute("""
        CREATE TABLE IF NOT EXISTS trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date TEXT,
            time_str TEXT,
            session_name TEXT,
            session_idx INTEGER,
            table_num INTEGER,
            order_in_session INTEGER,
            order_in_table INTEGER,
            strategy_desc TEXT,
            bet_side TEXT,
            bet_amount REAL,
            result TEXT,
            pnl REAL,
            ending_balance REAL
        )
    """)
    
    c.execute("SELECT COUNT(*) FROM system_config")
    if c.fetchone()[0] == 0:
        today_str = get_vn_now().strftime("%Y-%m-%d")
        c.execute("""
            INSERT INTO system_config VALUES (1, 200.0, 200.0, 200.0, 1, 1, 0, ?)
        """, (today_str,))
    conn.commit()
    conn.close()

init_system_database()

# --- XÁC THỰC BẢO MẬT BẰNG PIN ---
if "is_auth" not in st.session_state:
    st.session_state.is_auth = False

if not st.session_state.is_auth:
    st.markdown("<h2 style='text-align:center;'>🔒 QUẢN TRỊ KỶ LUẬT BẢN THÂN</h2>", unsafe_allow_html=True)
    st.write("Vui lòng nhập mã PIN bảo mật để vào phiên làm việc:")
    pin = st.text_input("Nhập mã PIN:", type="password", key="pin_login")
    if st.button("MỞ KHÓA BÀN ĐÁNH", use_container_width=True):
        if pin == MASTER_PIN:
            st.session_state.is_auth = True
            st.rerun()
        else:
            st.error("❌ Mã PIN không chính xác!")
    st.stop()

# --- TẢI DỮ LIỆU & ĐỒNG BỘ MỐC VỐN ---
def load_app_state():
    conn = get_db_connection()
    cfg = pd.read_sql("SELECT * FROM system_config WHERE id = 1", conn).iloc[0]
    his = pd.read_sql("SELECT * FROM trade_history ORDER BY id DESC", conn)
    conn.close()
    return cfg, his

cfg, df_history = load_app_state()

initial_capital = float(cfg['initial_cap'])
current_capital = float(cfg['current_cap'])
session_start_cap = float(cfg['session_start_cap'])
curr_session = int(cfg['curr_session_idx'])
curr_table = int(cfg['curr_table_num'])
orders_in_table = int(cfg['table_orders_count'])

SESSION_MAP = {
    1: "Phiên 1 (Sáng)",
    2: "Phiên 2 (Trưa)",
    3: "Phiên 3 (Chiều)",
    4: "Phiên 4 (Tối)"
}

# --- BỘ ĐỆM ĐƯỜNG CẦU TRONG BÀN ---
if "inputs_raw" not in st.session_state:
    st.session_state.inputs_raw = []
if "road_main" not in st.session_state:
    st.session_state.road_main = []
if "road_bigeye" not in st.session_state:
    st.session_state.road_bigeye = []
if "list_bigeye" not in st.session_state:
    st.session_state.list_bigeye = []

# --- THUẬT TOÁN ĐƯỜNG CẦU QUỐC TẾ CHUẨN XÁC ---
def append_road(road, val):
    new_r = [c.copy() for c in road]
    if not new_r:
        new_r.append([val])
    else:
        if new_r[-1][-1] == val:
            new_r[-1].append(val)
        else:
            new_r.append([val])
    return new_r

def calc_big_eye_color(road, col_i, row_i):
    if col_i == 0 or (col_i == 1 and row_i == 0):
        return None
    if row_i > 0:
        prev_len = len(road[col_i - 1])
        return "RED" if prev_len >= (row_i + 1) else "BLUE"
    else:
        if col_i >= 2:
            return "RED" if len(road[col_i - 1]) == len(road[col_i - 2]) else "BLUE"
        return None

def predict_side_for_red():
    """Tìm cửa đặt (PLAYER hay BANKER) để bảng phụ 1 tạo ra HẠT ĐỎ"""
    road = st.session_state.road_main
    if not road:
        return "BANKER"
    
    # Thử giả lập PLAYER
    sim_p = append_road(road, "P")
    cp, rp = len(sim_p) - 1, len(sim_p[-1]) - 1
    color_p = calc_big_eye_color(sim_p, cp, rp)

    # Thử giả lập BANKER
    sim_b = append_road(road, "B")
    cb, rb = len(sim_b) - 1, len(sim_b[-1]) - 1
    color_b = calc_big_eye_color(sim_b, cb, rb)

    if color_p == "RED" and color_b != "RED":
        return "PLAYER"
    elif color_b == "RED" and color_p != "RED":
        return "BANKER"
    else:
        # Trường hợp cả 2 cùng màu: Đánh theo nhịp bệt hiện tại
        return "PLAYER" if road[-1][-1] == "P" else "BANKER"

def execute_reset_table(next_table_num):
    st.session_state.inputs_raw = []
    st.session_state.road_main = []
    st.session_state.road_bigeye = []
    st.session_state.list_bigeye = []
    conn = get_db_connection()
    conn.execute("UPDATE system_config SET curr_table_num = ?, table_orders_count = 0 WHERE id = 1", (next_table_num,))
    conn.commit()
    conn.close()

# --- HEADER & BỘ ĐIỀU HƯỚNG PHIÊN ---
st.markdown("<h3 style='margin-bottom:0px;'>🎯 Quản Trị Kỷ Luật Bản Thân</h3>", unsafe_allow_html=True)

# Lọc các lệnh của phiên hiện tại trong ngày hôm nay
today_str = get_vn_now().strftime("%d/%m/%Y")
session_trades = df_history[
    (df_history['session_idx'] == curr_session) & 
    (df_history['trade_date'] == today_str)
].sort_values(by="id", ascending=True)

order_in_session_count = len(session_trades)
session_profit = current_capital - session_start_cap
session_profit_pct = (session_profit / session_start_cap) * 100 if session_start_cap > 0 else 0

# --- KIỂM TRA ĐIỀU KIỆN STOP / KHÓA PHIÊN ---
# 1. Target WIN: Nếu lệnh 1 của phiên WIN -> Khóa ngay! Hoặc tổng lãi phiên >= +4.70% (chạm 5%)
is_first_trade_win = (order_in_session_count >= 1 and session_trades.iloc[0]['result'] == 'WIN')
is_session_profit_reached = (session_profit_pct >= 4.70) or (session_profit >= initial_capital * 0.047)
is_session_target_win = is_first_trade_win or is_session_profit_reached

# 2. Target LOSE: Phiên lỗ chạm -50% vốn -> Dừng phiên cắt lỗ tuyệt đối!
is_session_target_lose = (session_profit <= -(session_start_cap * 0.50)) or (session_profit_pct <= -50.0)

is_session_locked = is_session_target_win or is_session_target_lose
is_table_locked = (orders_in_table >= 2)

# Hàng điều khiển Phiên & Bàn
col_h1, col_h2 = st.columns([2, 1])
with col_h1:
    selected_sess = st.selectbox(
        "📅 Chọn Phiên Giao Dịch Trong Ngày:",
        options=[1, 2, 3, 4],
        format_func=lambda x: SESSION_MAP[x],
        index=curr_session - 1
    )
    if selected_sess != curr_session:
        conn = get_db_connection()
        conn.execute("""
            UPDATE system_config 
            SET curr_session_idx = ?, session_start_cap = ?, table_orders_count = 0 
            WHERE id = 1
        """, (selected_sess, current_capital))
        conn.commit()
        conn.close()
        execute_reset_table(curr_table + 1)
        st.rerun()

with col_h2:
    st.metric("BÀN HIỆN TẠI", f"Bàn {curr_table}", delta=f"{orders_in_table}/2 lệnh cược")

# --- HÀNG CHỈ SỐ VỐN THỰC TẾ & VỐN BAN ĐẦU ---
c_m1, c_m2 = st.columns(2)
c_m1.metric("VỐN THỰC TẾ (SỐ DƯ)", f"${current_capital:,.2f}", delta=f"${current_capital - initial_capital:+,.2f} (Tổng)")
c_m2.metric("VỐN BAN ĐẦU (MỐC 5%)", f"${initial_capital:,.2f}")

c_m3, c_m4 = st.columns(2)
c_m3.metric(f"LÃI/LỖ {SESSION_MAP[curr_session]}", f"${session_profit:+,.2f}", delta=f"{session_profit_pct:.2f}%")
c_m4.metric("TARGET CHỐT PHIÊN (+5%)", f"+${initial_capital * 0.05:,.2f}", delta="Cắt lỗ: -50%")

# Nút đổi bàn & chỉnh sửa vốn
with st.expander("⚡ Cài Đặt Vốn & Quản Lý Bàn"):
    ce1, ce2 = st.columns(2)
    custom_init = ce1.number_input("Sửa Vốn Gốc Cơ Sở ($):", value=initial_capital, step=50.0)
    custom_curr = ce2.number_input("Sửa Vốn Thực Tế Hiện Có ($):", value=current_capital, step=50.0)
    cb1, cb2 = st.columns(2)
    if cb1.button("💾 Lưu Cập Nhật Vốn", use_container_width=True):
        conn = get_db_connection()
        conn.execute("UPDATE system_config SET initial_cap = ?, current_cap = ?, session_start_cap = ? WHERE id = 1", 
                     (custom_init, custom_curr, custom_curr))
        conn.commit()
        conn.close()
        st.rerun()
    if cb2.button("🔄 ĐỔI BÀN MỚI (XÓA CẦU)", use_container_width=True):
        execute_reset_table(curr_table + 1)
        st.rerun()

# --- KHỐI CẢNH BÁO STOP PHIÊN HOẶC KHÓA BÀN ---
if is_session_target_win:
    st.markdown("""
        <div class="box-signal-stop">
            🛑 KỶ LUẬT THÉP: ĐÃ ĐẠT TARGET DƯƠNG 5% CỦA PHIÊN!<br>
            BẮT BUỘC DỪNG PHIÊN NGAY LẬP TỨC. HÃY TẮT ỨNG DỤNG VÀ NGHỈ NGƠI!
        </div>
    """, unsafe_allow_html=True)
elif is_session_target_lose:
    st.markdown("""
        <div class="box-signal-stop">
            🛑 BẢO VỆ TÀI KHOẢN: ĐÃ CHẠM MỐC DỪNG LỖ (-50%)!<br>
            BẮT BUỘC KHÓA PHIÊN NGAY LẬP TỨC. KHÔNG ĐƯỢC GỠ!
        </div>
    """, unsafe_allow_html=True)
elif is_table_locked:
    st.markdown("""
        <div class="box-signal-table-lock">
            ⚠️ BÀN NÀY ĐÃ ĐỦ 2 LỆNH CƯỢC!<br>
            BẮT BUỘC BẤM NÚT "🔄 ĐỔI BÀN MỚI" Ở MỤC TRÊN ĐỂ TIẾP TỤC THEO QUẢN LÝ VỐN.
        </div>
    """, unsafe_allow_html=True)

# --- TAB GIAO DIỆN ---
tab_game, tab_history, tab_report = st.tabs(["🎮 BÀN ĐÁNH & VÀO LỆNH", "📜 LỊCH SỬ CƯỢC", "📊 BÁO CÁO NGÀY/TUẦN/THÁNG"])

with tab_game:
    # Hàm vẽ cầu siêu nhẹ, không lag
    def render_light_board(columns, is_big_eye=False):
        total_cols = max(35, len(columns) + 3)
        html = """<style>
            .b-wrap { background: #121214; overflow-x: auto; white-space: nowrap; width: 100%; border: 1px solid #333; border-radius: 6px; padding: 2px; }
            table { border-collapse: collapse; table-layout: fixed; }
            th { width: 22px; min-width: 22px; height: 16px; border: 1px solid #2d2d30; font-size: 9px; color: #888; text-align: center; background: #1e1e24; }
            td { width: 22px; min-width: 22px; height: 22px; border: 1px solid #222; text-align: center; vertical-align: middle; padding: 0; }
            .c-b { width: 15px; height: 15px; border-radius: 50%; border: 2.5px solid #d32f2f; margin: auto; }
            .c-p { width: 15px; height: 15px; border-radius: 50%; border: 2.5px solid #1976d2; margin: auto; }
            .e-r { width: 13px; height: 13px; border-radius: 50%; border: 2px solid #d32f2f; margin: auto; }
            .e-b { width: 13px; height: 13px; border-radius: 50%; border: 2px solid #1976d2; margin: auto; }
        </style><div class="b-wrap"><table><thead><tr>"""
        for c in range(1, total_cols + 1):
            html += f"<th>{c}</th>"
        html += "</tr></thead><tbody>"
        for r in range(6):
            html += "<tr>"
            for c in range(total_cols):
                cell_div = ""
                if c < len(columns) and r < len(columns[c]):
                    val = columns[c][r]
                    if not is_big_eye:
                        cell_div = f'<div class="{"c-b" if val=="B" else "c-p"}"></div>'
                    else:
                        cell_div = f'<div class="{"e-r" if val=="RED" else "e-b"}"></div>'
                html += f"<td>{cell_div}</td>"
            html += "</tr>"
        html += "</tbody></table></div>"
        return html

    st.markdown("##### 🔴🔵 Bảng Chính (Big Road)")
    st.components.v1.html(render_light_board(st.session_state.road_main, False), height=170, scrolling=True)

    st.markdown(f"##### 🔴🔵 Bảng Phụ 1 - Big Eye Boy ({len(st.session_state.list_bigeye)} hạt)")
    st.components.v1.html(render_light_board(st.session_state.road_bigeye, True), height=170, scrolling=True)

    if st.session_state.inputs_raw:
        tag_list = [f"<span style='color:{'#d32f2f' if x=='B' else '#1976d2'}; font-weight:bold;'>{'🔴 B' if x=='B' else '🔵 P'}</span>" for x in st.session_state.inputs_raw]
        st.markdown("**Các tay vừa nhập:** " + " ➔ ".join(tag_list[-15:]), unsafe_allow_html=True)

    st.write("---")

    # --- TÍNH TOÁN QUY MÔ TIỀN CƯỢC THEO QUẢN LÝ VỐN 2 LỆNH WIN LIÊN TIẾP ---
    base_bet = initial_capital * 0.05
    num_seeds = len(st.session_state.list_bigeye)
    predicted_choice = predict_side_for_red()

    current_bet_side = None
    current_bet_amount = 0.0
    strategy_label = ""

    # Kiểm tra chuỗi Win gần nhất trong phiên
    consec_wins = 0
    for _, r in session_trades.iloc[::-1].iterrows():
        if r['result'] == 'WIN':
            consec_wins += 1
        else:
            break

    # Phân bổ mức cược:
    if order_in_session_count == 0:
        current_bet_amount = base_bet
        strategy_label = "Lệnh 1 (5% Vốn Ban Đầu - Thắng là STOP)"
    else:
        # Nếu đang âm: Win 1 lệnh lẻ -> Gấp đôi 10% để bắt nhịp 2 Win
        if session_profit < 0:
            if consec_wins == 1:
                current_bet_amount = base_bet * 2.0
                strategy_label = "10% (Gấp Đôi sau 1 Win - Tìm nhịp 2 WIN)"
            else:
                current_bet_amount = base_bet
                strategy_label = "5% Vốn (Sau Thua hoặc sau 2 Win)"
        else:
            current_bet_amount = base_bet
            strategy_label = "5% Vốn Ban Đầu"

    # HIỂN THỊ CẢNH BÁO VÀO LỆNH (NỀN ĐỎ CHỮ TRẮNG CHO BANKER, NỀN XANH CHỮ TRẮNG CHO PLAYER)
    if is_session_locked:
        st.markdown('<div class="box-signal-stop">🛑 PHIÊN ĐÃ HOÀN THÀNH HOẶC KHÓA DỪNG LỖ. KHÔNG THỂ ĐẶT THÊM.</div>', unsafe_allow_html=True)
    elif is_table_locked:
        st.markdown('<div class="box-signal-table-lock">🛑 BÀN NÀY ĐÃ ĐỦ 2 LỆNH! VUI LÒNG BẤM "🔄 ĐỔI BÀN MỚI".</div>', unsafe_allow_html=True)
    elif num_seeds == 0:
        st.markdown('<div class="box-signal-wait">⏳ Đang chờ Bảng phụ 1 xuất hiện hạt đầu tiên (Xanh hoặc Đỏ) để tính lệnh vào...</div>', unsafe_allow_html=True)
    else:
        current_bet_side = predicted_choice
        if current_bet_side == "BANKER":
            st.markdown(f"""
                <div class="box-signal-banker">
                    🚨 DỰ ĐOÁN: BANKER | ${current_bet_amount:,.2f}<br>
                    <span style="font-size:14px; font-weight:normal;">Lệnh {orders_in_table + 1}/2 bàn • {strategy_label}</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="box-signal-player">
                    🚨 DỰ ĐOÁN: PLAYER | ${current_bet_amount:,.2f}<br>
                    <span style="font-size:14px; font-weight:normal;">Lệnh {orders_in_table + 1}/2 bàn • {strategy_label}</span>
                </div>
            """, unsafe_allow_html=True)

    # NÚT BẤM CƯỢC: Khóa nếu phiên STOP hoặc bàn đã đủ 2 lệnh
    can_press = not is_session_locked and not is_table_locked

    col_btn_p, col_btn_b = st.columns(2)

    def handle_click_outcome(outcome):
        global initial_capital, current_capital, orders_in_table
        # 1. Cập nhật bảng cầu
        st.session_state.inputs_raw.append(outcome)
        st.session_state.road_main = append_road(st.session_state.road_main, outcome)
        road = st.session_state.road_main
        ci, ri = len(road) - 1, len(road[-1]) - 1

        color = calc_big_eye_color(road, ci, ri)
        if color is not None:
            st.session_state.list_bigeye.append(color)
            st.session_state.road_bigeye = append_road(st.session_state.road_bigeye, color)

        # 2. Xử lý lệnh cược nếu có tín hiệu
        if current_bet_side is not None and not is_session_locked and not is_table_locked:
            vn_now = get_vn_now()
            t_date = vn_now.strftime("%d/%m/%Y")
            t_time = vn_now.strftime("%H:%M:%S")

            is_win = (outcome == "B" and current_bet_side == "BANKER") or (outcome == "P" and current_bet_side == "PLAYER")
            
            # Tỷ lệ: Player 1:1, Banker 1:0.95, Thua -100%
            if is_win:
                pnl = current_bet_amount * 0.95 if current_bet_side == "BANKER" else current_bet_amount
            else:
                pnl = -current_bet_amount

            new_current_cap = current_capital + pnl
            res_str = "WIN" if is_win else "LOSE"

            # QUY ƯỚC TỰ ĐỘNG CẬP NHẬT VỐN GỐC (DƯƠNG 100% HOẶC ÂM 50%):
            new_initial_cap = initial_capital
            if new_current_cap >= 2.0 * initial_capital:
                new_initial_cap = new_current_cap  # Tăng gấp đôi mốc vốn gốc
            elif new_current_cap <= 0.5 * initial_capital:
                new_initial_cap = new_current_cap  # Giảm 50% mốc vốn gốc

            new_table_orders = orders_in_table + 1
            new_session_orders = order_in_session_count + 1

            # Lưu trực tiếp vào Database
            conn = get_db_connection()
            conn.execute("""
                UPDATE system_config 
                SET current_cap = ?, initial_cap = ?, table_orders_count = ? 
                WHERE id = 1
            """, (new_current_cap, new_initial_cap, new_table_orders))

            conn.execute("""
                INSERT INTO trade_history (
                    trade_date, time_str, session_name, session_idx, table_num, 
                    order_in_session, order_in_table, strategy_desc, bet_side, 
                    bet_amount, result, pnl, ending_balance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t_date, t_time, SESSION_MAP[curr_session], curr_session, curr_table,
                new_session_orders, new_table_orders, strategy_label, current_bet_side,
                current_bet_amount, res_str, pnl, new_current_cap
            ))
            conn.commit()
            conn.close()

    with col_btn_p:
        if st.button("🔵 PLAYER (P)", use_container_width=True, disabled=not can_press):
            handle_click_outcome("P")
            st.rerun()
    with col_btn_b:
        if st.button("🔴 BANKER (B)", use_container_width=True, disabled=not can_press):
            handle_click_outcome("B")
            st.rerun()

with tab_history:
    st.subheader("📜 Nhật Ký Giao Dịch Chi Tiết")
    if not df_history.empty:
        # Chuẩn hóa bảng hiển thị đầy đủ theo đúng yêu cầu
        h_df = df_history[[
            'trade_date', 'time_str', 'session_name', 'order_in_session', 'table_num', 
            'order_in_table', 'strategy_desc', 'bet_side', 'bet_amount', 'result', 'pnl', 'ending_balance'
        ]].copy()
        h_df['bet_amount'] = h_df['bet_amount'].apply(lambda x: f"${x:,.2f}")
        h_df['pnl'] = h_df['pnl'].apply(lambda x: f"${x:+,.2f}")
        h_df['ending_balance'] = h_df['ending_balance'].apply(lambda x: f"${x:,.2f}")
        h_df.columns = [
            'Ngày', 'Giờ', 'Phiên', 'STT Phiên', 'Bàn', 
            'STT Bàn', 'Chiến Lược', 'Cửa Đặt', 'Tiền Đặt ($)', 'Kết Quả', 'Lãi/Lỗ ($)', 'Vốn Biến Động ($)'
        ]
        st.dataframe(h_df, use_container_width=True)
        
        # Nút xuất dữ liệu CSV về điện thoại để an tâm lưu giữ
        csv_data = df_history.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Tải Nhật Ký Cược Toàn Bộ (.CSV) Về Máy",
            data=csv_data,
            file_name=f"baccarat_history_{get_vn_now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("Chưa có dữ liệu đặt cược nào.")

with tab_report:
    st.subheader("📊 Báo Cáo Hiệu Quả Quản Trị Vốn")
    if not df_history.empty:
        # Chuyển đổi định dạng ngày tháng để gom nhóm
        rep_df = df_history.copy()
        rep_df['dt'] = pd.to_datetime(rep_df['trade_date'], format='%d/%m/%Y', errors='coerce')
        rep_df = rep_df.sort_values(by="id")

        # 1. Báo cáo theo Ngày
        st.markdown("#### 📅 1. Báo Cáo Theo Ngày")
        day_summary = rep_df.groupby('trade_date').agg(
            Tổng_Lệnh=('id', 'count'),
            Số_Win=('result', lambda x: (x == 'WIN').sum()),
            Số_Lose=('result', lambda x: (x == 'LOSE').sum()),
            Tổng_PnL=('pnl', 'sum'),
            Vốn_Cuối=('ending_balance', 'last')
        ).reset_index()
        day_summary['Tỷ Lệ Win'] = (day_summary['Số_Win'] / day_summary['Tổng_Lệnh'] * 100).round(1).astype(str) + "%"
        day_summary['Tổng_PnL'] = day_summary['Tổng_PnL'].apply(lambda x: f"${x:+,.2f}")
        day_summary['Vốn_Cuối'] = day_summary['Vốn_Cuối'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(day_summary, use_container_width=True)

        # 2. Báo cáo theo Phiên (Sáng, Trưa, Chiều, Tối)
        st.markdown("#### 🕒 2. Báo Cáo Theo Phiên Trong Ngày")
        sess_summary = rep_df.groupby('session_name').agg(
            Số_Lệnh=('id', 'count'),
            Tổng_Lãi_Lỗ=('pnl', 'sum')
        ).reset_index()
        sess_summary['Tổng_Lãi_Lỗ'] = sess_summary['Tổng_Lãi_Lỗ'].apply(lambda x: f"${x:+,.2f}")
        st.dataframe(sess_summary, use_container_width=True)

        # 3. Báo cáo theo Tuần & Tháng
        st.markdown("#### 📈 3. Tổng Hợp Tuần & Tháng")
        rep_df['year_week'] = rep_df['dt'].dt.strftime('%Y - Tuần %U')
        rep_df['year_month'] = rep_df['dt'].dt.strftime('%m/%Y')
        
        col_w, col_m = st.columns(2)
        with col_w:
            st.caption("Theo Tuần:")
            week_sum = rep_df.groupby('year_week')['pnl'].sum().reset_index()
            week_sum.columns = ['Tuần', 'PnL ($)']
            week_sum['PnL ($)'] = week_sum['PnL ($)'].apply(lambda x: f"${x:+,.2f}")
            st.dataframe(week_sum, use_container_width=True)
            
        with col_m:
            st.caption("Theo Tháng:")
            month_sum = rep_df.groupby('year_month')['pnl'].sum().reset_index()
            month_sum.columns = ['Tháng', 'PnL ($)']
            month_sum['PnL ($)'] = month_sum['PnL ($)'].apply(lambda x: f"${x:+,.2f}")
            st.dataframe(month_sum, use_container_width=True)
    else:
        st.info("Báo cáo sẽ tự động tổng hợp khi bạn bắt đầu có các lệnh cược.")
