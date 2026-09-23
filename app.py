import streamlit as st
import pandas as pd
import datetime
from zoneinfo import ZoneInfo
import json
import base64
import requests
import os
import threading

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(
    page_title="Quản Trị Kỷ Luật Bản Thân",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Chuẩn múi giờ Việt Nam GMT+7
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

def get_vn_now():
    return datetime.datetime.now(VN_TZ)

MASTER_PIN = "6868"
DATA_FILE_PATH = "baccarat_data.json"

# CSS Mobile siêu mượt, loại bỏ độ trễ, tối ưu hiển thị
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .box-signal-banker {
        background-color: #dc2626 !important;
        color: #ffffff !important;
        padding: 16px;
        border-radius: 8px;
        font-size: 20px;
        font-weight: 900;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 10px rgba(220, 38, 38, 0.5);
    }
    .box-signal-player {
        background-color: #2563eb !important;
        color: #ffffff !important;
        padding: 16px;
        border-radius: 8px;
        font-size: 20px;
        font-weight: 900;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.5);
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
        background-color: #991b1b;
        color: #fee2e2;
        padding: 16px;
        border-radius: 8px;
        font-size: 17px;
        font-weight: 900;
        text-align: center;
        margin: 10px 0;
        border: 2px solid #f87171;
    }
    .box-signal-table-lock {
        background-color: #9a3412;
        color: #ffedd5;
        padding: 14px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 800;
        text-align: center;
        margin: 10px 0;
        border: 2px solid #fb923c;
    }
    /* Style bảng cầu nhẹ không cần iframe */
    .board-container {
        background: #121214;
        overflow-x: auto;
        white-space: nowrap;
        width: 100%;
        border: 1px solid #333;
        border-radius: 6px;
        padding: 4px;
        margin-bottom: 8px;
    }
    .board-table {
        border-collapse: collapse;
        table-layout: fixed;
    }
    .board-th {
        width: 20px; min-width: 20px; height: 16px;
        border: 1px solid #2d2d30;
        font-size: 9px; color: #71717a; text-align: center; background: #18181b;
    }
    .board-td {
        width: 20px; min-width: 20px; height: 20px;
        border: 1px solid #27272a; text-align: center; vertical-align: middle; padding: 0;
    }
    .dot-b { width: 14px; height: 14px; border-radius: 50%; border: 2.5px solid #dc2626; margin: auto; }
    .dot-p { width: 14px; height: 14px; border-radius: 50%; border: 2.5px solid #2563eb; margin: auto; }
    .dot-er { width: 12px; height: 12px; border-radius: 50%; border: 2px solid #dc2626; margin: auto; }
    .dot-eb { width: 12px; height: 12px; border-radius: 50%; border: 2px solid #2563eb; margin: auto; }
</style>
""", unsafe_allow_html=True)

# --- CƠ CHẾ LƯU DỮ LIỆU ĐỒNG BỘ CHẠY NGẦM KHÔNG GIẬT LAG ---
def get_default_data():
    today_vn = get_vn_now().strftime("%d/%m/%Y")
    return {
        "config": {
            "initial_cap": 200.0,
            "current_cap": 200.0,
            "curr_session_idx": 1,
            "curr_table_num": 1,
            "table_orders_count": 0,
            "table_completed": 0,
            "last_active_date": today_vn,
            "completed_sessions": [],
            "session_start_caps": {}
        },
        "history": []
    }

def sync_read_data():
    if os.path.exists(DATA_FILE_PATH):
        try:
            with open(DATA_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    token = st.secrets.get("GITHUB_TOKEN", "")
    repo = st.secrets.get("REPO_NAME", "hoanghomegy/quan-ly-von")
    
    if token and repo:
        url = f"https://api.github.com/repos/{repo}/contents/{DATA_FILE_PATH}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        try:
            r = requests.get(url, headers=headers, timeout=4)
            if r.status_code == 200:
                content_b64 = r.json().get("content", "")
                decoded = base64.b64decode(content_b64).decode("utf-8")
                data = json.loads(decoded)
                with open(DATA_FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return data
        except Exception:
            pass
            
    return get_default_data()

def _push_github_background(token, repo, data_obj):
    url = f"https://api.github.com/repos/{repo}/contents/{DATA_FILE_PATH}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    try:
        sha = None
        r_get = requests.get(url, headers=headers, timeout=5)
        if r_get.status_code == 200:
            sha = r_get.json().get("sha")

        json_str = json.dumps(data_obj, ensure_ascii=False, indent=2)
        content_b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

        payload = {
            "message": f"Auto-sync trade: {get_vn_now().strftime('%H:%M:%S %d/%m')}",
            "content": content_b64
        }
        if sha:
            payload["sha"] = sha

        requests.put(url, headers=headers, json=payload, timeout=5)
    except Exception:
        pass

def sync_write_data(data_obj):
    with open(DATA_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data_obj, f, ensure_ascii=False, indent=2)

    token = st.secrets.get("GITHUB_TOKEN", "")
    repo = st.secrets.get("REPO_NAME", "hoanghomegy/quan-ly-von")
    if token and repo:
        t = threading.Thread(target=_push_github_background, args=(token, repo, data_obj))
        t.start()

# --- BẢO MẬT MÃ PIN ---
if "is_auth" not in st.session_state:
    st.session_state.is_auth = False

if not st.session_state.is_auth:
    st.markdown("<h2 style='text-align:center;'>🔒 QUẢN TRỊ KỶ LUẬT BẢN THÂN</h2>", unsafe_allow_html=True)
    pin = st.text_input("Nhập mã PIN truy cập:", type="password", key="login_pin")
    if st.button("MỞ KHÓA BÀN ĐÁNH", use_container_width=True):
        if pin == MASTER_PIN:
            st.session_state.is_auth = True
            st.rerun()
        else:
            st.error("❌ Mã PIN không chính xác!")
    st.stop()

# --- TẢI DỮ LIỆU & TỰ ĐỘNG CHUYỂN SANG NGÀY MỚI (GMT+7) ---
full_data = sync_read_data()
cfg = full_data["config"]

today_vn_str = get_vn_now().strftime("%d/%m/%Y")
last_date_recorded = cfg.get("last_active_date", today_vn_str)

if today_vn_str != last_date_recorded:
    cfg["last_active_date"] = today_vn_str
    cfg["curr_session_idx"] = 1
    cfg["curr_table_num"] = 1
    cfg["table_orders_count"] = 0
    cfg["table_completed"] = 0
    cfg["completed_sessions"] = []
    cfg["session_start_caps"] = { "1": cfg["current_cap"] }
    full_data["config"] = cfg
    sync_write_data(full_data)

if "completed_sessions" not in cfg:
    cfg["completed_sessions"] = []
if "session_start_caps" not in cfg:
    cfg["session_start_caps"] = {}

df_history = pd.DataFrame(full_data.get("history", []))

initial_capital = float(cfg['initial_cap'])
current_capital = float(cfg['current_cap'])
curr_session = int(cfg['curr_session_idx'])
curr_table = int(cfg['curr_table_num'])
orders_in_table = int(cfg['table_orders_count'])
table_completed = int(cfg.get('table_completed', 0))

SESSION_MAP = {
    1: "Phiên 1 (Sáng)",
    2: "Phiên 2 (Trưa)",
    3: "Phiên 3 (Chiều)",
    4: "Phiên 4 (Tối)"
}

# Bộ đệm đường cầu
if "inputs_raw" not in st.session_state:
    st.session_state.inputs_raw = []
if "road_main" not in st.session_state:
    st.session_state.road_main = []
if "road_bigeye" not in st.session_state:
    st.session_state.road_bigeye = []
if "list_bigeye" not in st.session_state:
    st.session_state.list_bigeye = []

# --- THUẬT TOÁN ĐƯỜNG CẦU QUỐC TẾ ---
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
    road = st.session_state.road_main
    if not road:
        return "BANKER"
    sim_p = append_road(road, "P")
    color_p = calc_big_eye_color(sim_p, len(sim_p)-1, len(sim_p[-1])-1)

    sim_b = append_road(road, "B")
    color_b = calc_big_eye_color(sim_b, len(sim_b)-1, len(sim_b[-1])-1)

    if color_p == "RED" and color_b != "RED":
        return "PLAYER"
    elif color_b == "RED" and color_p != "RED":
        return "BANKER"
    else:
        return "PLAYER" if road[-1][-1] == "P" else "BANKER"

def execute_reset_table(next_table_num):
    st.session_state.inputs_raw = []
    st.session_state.road_main = []
    st.session_state.road_bigeye = []
    st.session_state.list_bigeye = []
    full_data["config"]["curr_table_num"] = next_table_num
    full_data["config"]["table_orders_count"] = 0
    full_data["config"]["table_completed"] = 0
    sync_write_data(full_data)

# --- THỐNG KÊ PHIÊN ĐANG CHỌN TRONG NGÀY ---
if not df_history.empty:
    session_trades = df_history[
        (df_history['session_idx'] == curr_session) & 
        (df_history['trade_date'] == today_vn_str)
    ]
else:
    session_trades = pd.DataFrame()

order_in_session_count = len(session_trades)

s_key = str(curr_session)
if s_key not in cfg["session_start_caps"]:
    cfg["session_start_caps"][s_key] = current_capital
    full_data["config"] = cfg
    sync_write_data(full_data)

session_start_cap = float(cfg["session_start_caps"][s_key])
session_pnl_calc = session_trades['pnl'].sum() if not session_trades.empty else 0.0
session_profit_pct = (session_pnl_calc / session_start_cap) * 100 if session_start_cap > 0 else 0

# --- KIỂM TRA ĐIỀU KIỆN STOP & KHÓA PHIÊN ---
is_already_completed = curr_session in cfg.get("completed_sessions", [])
is_session_target_win = (session_profit_pct >= 4.75) or (session_pnl_calc >= initial_capital * 0.0475)
is_session_target_lose = (session_pnl_calc <= -(session_start_cap * 0.50))

if (is_session_target_win or is_session_target_lose) and not is_already_completed:
    cfg["completed_sessions"].append(curr_session)
    full_data["config"] = cfg
    sync_write_data(full_data)
    is_already_completed = True

is_session_locked = is_already_completed

# --- ĐIỀU KIỆN VÀO LỆNH TẠI BÀN (HẠT ĐỎ MỚI ĐÁNH) ---
first_seed_is_blue = (len(st.session_state.list_bigeye) > 0 and st.session_state.list_bigeye[0] == "BLUE")
is_table_locked = (table_completed == 1) or (orders_in_table >= 2) or first_seed_is_blue

# --- GIAO DIỆN HEADER ---
st.markdown(f"<h3 style='margin-bottom:0px;'>🎯 Quản Trị Kỷ Luật Bản Thân <span style='font-size:14px; color:#a1a1aa;'>({today_vn_str})</span></h3>", unsafe_allow_html=True)

def format_session_label(s_idx):
    status = " [🔒 ĐÃ XONG]" if s_idx in cfg.get("completed_sessions", []) else ""
    return f"{SESSION_MAP[s_idx]}{status}"

col_h1, col_h2 = st.columns([2, 1])
with col_h1:
    selected_sess = st.selectbox(
        "📅 Chọn Phiên Giao Dịch Trong Ngày:",
        options=[1, 2, 3, 4],
        format_func=format_session_label,
        index=curr_session - 1
    )
    if selected_sess != curr_session:
        full_data["config"]["curr_session_idx"] = selected_sess
        if str(selected_sess) not in full_data["config"]["session_start_caps"]:
            full_data["config"]["session_start_caps"][str(selected_sess)] = current_capital
        full_data["config"]["table_orders_count"] = 0
        full_data["config"]["table_completed"] = 0
        sync_write_data(full_data)
        execute_reset_table(curr_table + 1)
        st.rerun()

with col_h2:
    st.metric("BÀN HIỆN TẠI", f"Bàn {curr_table}", delta=f"{orders_in_table}/2 lệnh")

# 4 Ô THÔNG SỐ VỐN
c_m1, c_m2 = st.columns(2)
c_m1.metric("VỐN THỰC TẾ", f"${current_capital:,.2f}", delta=f"${current_capital - initial_capital:+,.2f} (Tổng)")
c_m2.metric("VỐN BAN ĐẦU (GỐC 5%)", f"${initial_capital:,.2f}")

c_m3, c_m4 = st.columns(2)
c_m3.metric(f"LÃI/LỖ {SESSION_MAP[curr_session]}", f"${session_pnl_calc:+,.2f}", delta=f"{session_profit_pct:.2f}%")
c_m4.metric("TARGET CHỐT (+4.75% ➔ 5%)", f"+${initial_capital * 0.05:,.2f}", delta="Cắt lỗ: -50%")

# KHU VỰC CÀI ĐẶT & RESET
with st.expander("⚡ Cài Đặt Vốn & Quản Lý Bàn"):
    ce1, ce2 = st.columns(2)
    custom_init = ce1.number_input("Sửa Vốn Gốc Cơ Sở ($):", value=initial_capital, step=50.0)
    custom_curr = ce2.number_input("Sửa Vốn Thực Tế Hiện Có ($):", value=current_capital, step=50.0)
    
    cb1, cb2 = st.columns(2)
    if cb1.button("💾 Lưu Cập Nhật Vốn", use_container_width=True):
        full_data["config"]["initial_cap"] = custom_init
        full_data["config"]["current_cap"] = custom_curr
        sync_write_data(full_data)
        st.rerun()
    if cb2.button("🔄 ĐỔI BÀN MỚI (XÓA CẦU)", use_container_width=True):
        execute_reset_table(curr_table + 1)
        st.rerun()

    st.markdown("---")
    st.caption("🗑️ **Khôi phục cài đặt gốc:** Xóa sạch lịch sử và đưa vốn về ban đầu:")
    reset_val = st.number_input("Số vốn khởi tạo lại ($):", value=200.0, step=50.0)
    if st.button("⚠️ XÁC NHẬN RESET TOÀN BỘ VỀ TRẠNG THÁI ĐẦU", type="primary", use_container_width=True):
        full_data = get_default_data()
        full_data["config"]["initial_cap"] = reset_val
        full_data["config"]["current_cap"] = reset_val
        full_data["config"]["session_start_caps"] = { "1": reset_val }
        sync_write_data(full_data)
        st.session_state.inputs_raw = []
        st.session_state.road_main = []
        st.session_state.road_bigeye = []
        st.session_state.list_bigeye = []
        st.success("Đã reset app về trạng thái ban đầu!")
        st.rerun()

# THÔNG BÁO CẢNH BÁO STOP / KHÓA BÀN
if is_session_locked:
    st.markdown("""
        <div class="box-signal-stop">
            🛑 KỶ LUẬT THÉP: PHIÊN NÀY ĐÃ HOÀN THÀNH VÀ CHỐT KHÓA TRONG NGÀY!<br>
            BẮT BUỘC ĐỢI QUA 00:00 (GMT+7) NGÀY HÔM SAU ĐỂ MỞ LẠI. HÃY NGHỈ NGƠI HOẶC CHỌN PHIÊN KHÁC CHƯA CHƠI!
        </div>
    """, unsafe_allow_html=True)
elif first_seed_is_blue:
    st.markdown("""
        <div class="box-signal-table-lock">
            ⚠️ HẠT ĐẦU TIÊN BẢNG PHỤ 1 LÀ MÀU XANH ➔ KHÔNG ĐỦ ĐIỀU KIỆN VÀO LỆNH!<br>
            BẮT BUỘC BẤM "🔄 ĐỔI BÀN MỚI" Ở TRÊN ĐỂ TÌM BÀN KHÁC.
        </div>
    """, unsafe_allow_html=True)
elif is_table_locked:
    st.markdown("""
        <div class="box-signal-table-lock">
            ⚠️ BÀN ĐÃ HOÀN THÀNH (WIN LỆNH 1 HOẶC ĐỦ 2 LỆNH)!<br>
            BẮT BUỘC BẤM "🔄 ĐỔI BÀN MỚI" Ở MỤC TRÊN ĐỂ TIẾP TỤC THEO QUẢN LÝ VỐN.
        </div>
    """, unsafe_allow_html=True)

# --- TAB GIAO DIỆN ---
tab_game, tab_history, tab_report = st.tabs(["🎮 BÀN ĐÁNH & VÀO LỆNH", "📜 LỊCH SỬ CƯỢC", "📊 BÁO CÁO NGÀY/TUẦN/THÁNG"])

with tab_game:
    def render_fast_board(columns, is_big_eye=False):
        total_cols = max(30, len(columns) + 3)
        html = '<div class="board-container"><table class="board-table"><thead><tr>'
        for c in range(1, total_cols + 1):
            html += f'<th class="board-th">{c}</th>'
        html += '</tr></thead><tbody>'
        for r in range(6):
            html += '<tr>'
            for c in range(total_cols):
                cell_div = ""
                if c < len(columns) and r < len(columns[c]):
                    val = columns[c][r]
                    if not is_big_eye:
                        cell_div = f'<div class="{"dot-b" if val=="B" else "dot-p"}"></div>'
                    else:
                        cell_div = f'<div class="{"dot-er" if val=="RED" else "dot-eb"}"></div>'
                html += f'<td class="board-td">{cell_div}</td>'
            html += '</tr>'
        html += '</tbody></table></div>'
        return html

    st.markdown("##### 🔴🔵 Bảng Chính (Big Road)")
    st.markdown(render_fast_board(st.session_state.road_main, False), unsafe_allow_html=True)

    st.markdown(f"##### 🔴🔵 Bảng Phụ 1 - Big Eye Boy ({len(st.session_state.list_bigeye)} hạt)")
    st.markdown(render_fast_board(st.session_state.road_bigeye, True), unsafe_allow_html=True)

    if st.session_state.inputs_raw:
        tag_list = [f"<span style='color:{'#dc2626' if x=='B' else '#2563eb'}; font-weight:bold;'>{'🔴 B' if x=='B' else '🔵 P'}</span>" for x in st.session_state.inputs_raw]
        st.markdown("**Đã nhập:** " + " ➔ ".join(tag_list[-15:]), unsafe_allow_html=True)

    st.write("---")

    # =========================================================================
    # --- LOGIC QUẢN LÝ VỐN NÂNG CẤP: CHỈ GẤP ĐÔI KHI ÂM TỪ 10% VỐN ---
    # =========================================================================
    base_bet = initial_capital * 0.05
    num_seeds = len(st.session_state.list_bigeye)
    predicted_choice = predict_side_for_red()

    current_bet_side = None
    current_bet_amount = 0.0
    strategy_label = ""

    consec_wins = 0
    if not session_trades.empty:
        for _, r in session_trades.iloc[::-1].iterrows():
            if r['result'] == 'WIN':
                consec_wins += 1
            else:
                break

    # Điều kiện âm từ 10% vốn cơ sở trở lên (ví dụ: vốn 200$, PnL <= -20$)
    is_down_10pct = (session_pnl_calc <= -(initial_capital * 0.10))

    if order_in_session_count == 0:
        current_bet_amount = base_bet
        strategy_label = "5% Vốn Ban Đầu (Cơ Sở)"
    else:
        last_trade_res = session_trades.iloc[-1]['result']
        if last_trade_res == 'LOSE':
            current_bet_amount = base_bet
            strategy_label = "5% Vốn (Sau Thua - Đánh bằng tiền)"
        else:
            # Lệnh trước là WIN
            # CHỈ gấp đôi nếu phiên đang bị ÂM từ 10% trở lên và đang có đúng 1 WIN
            if is_down_10pct and consec_wins == 1:
                current_bet_amount = base_bet * 2.0
                strategy_label = "10% (Gấp Đôi vì Âm ≥ 10% - Săn chuỗi 2 WIN)"
            else:
                current_bet_amount = base_bet
                if not is_down_10pct:
                    strategy_label = "5% Vốn (Chưa âm đủ 10% / Đã hồi vốn)"
                else:
                    strategy_label = "5% Vốn (Quay về cơ sở sau 2 Win)"

    # ĐIỀU KIỆN VÀO LỆNH TẠI BÀN
    if is_session_locked:
        st.markdown('<div class="box-signal-stop">🛑 PHIÊN ĐÃ HOÀN THÀNH. KHÓA CỨNG TOÀN BỘ NÚT ĐẶT LỆNH.</div>', unsafe_allow_html=True)
    elif first_seed_is_blue:
        st.markdown('<div class="box-signal-table-lock">🛑 HẠT ĐẦU TIÊN LÀ XANH ➔ BỎ BÀN. BẤM "🔄 ĐỔI BÀN MỚI".</div>', unsafe_allow_html=True)
    elif is_table_locked:
        st.markdown('<div class="box-signal-table-lock">🛑 BÀN ĐÃ HẾT LƯỢT ĐÁNH (WIN LỆNH 1 HOẶC ĐỦ 2 LỆNH)!<br>HÃY BẤM "🔄 ĐỔI BÀN MỚI" Ở TRÊN ĐỂ TIẾP TỤC.</div>', unsafe_allow_html=True)
    elif num_seeds == 0:
        st.markdown('<div class="box-signal-wait">⏳ Đang chờ Bảng phụ 1 xuất hiện hạt đầu tiên (phải là hạt ĐỎ mới đánh)...</div>', unsafe_allow_html=True)
    else:
        current_bet_side = predicted_choice
        if current_bet_side == "BANKER":
            st.markdown(f"""
                <div class="box-signal-banker">
                    🚨 DỰ ĐOÁN: BANKER | ${current_bet_amount:,.2f}<br>
                    <span style="font-size:14px; font-weight:normal;">(Lệnh {orders_in_table + 1}/2 của bàn • {strategy_label})</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="box-signal-player">
                    🚨 DỰ ĐOÁN: PLAYER | ${current_bet_amount:,.2f}<br>
                    <span style="font-size:14px; font-weight:normal;">(Lệnh {orders_in_table + 1}/2 của bàn • {strategy_label})</span>
                </div>
            """, unsafe_allow_html=True)

    can_press = not is_session_locked and not is_table_locked

    col_btn_p, col_btn_b = st.columns(2)

    def handle_click_outcome(outcome):
        global initial_capital, current_capital, orders_in_table
        st.session_state.inputs_raw.append(outcome)
        st.session_state.road_main = append_road(st.session_state.road_main, outcome)
        road = st.session_state.road_main
        ci, ri = len(road) - 1, len(road[-1]) - 1

        color = calc_big_eye_color(road, ci, ri)
        if color is not None:
            st.session_state.list_bigeye.append(color)
            st.session_state.road_bigeye = append_road(st.session_state.road_bigeye, color)

        if current_bet_side is not None and not is_session_locked and not is_table_locked:
            vn_now = get_vn_now()
            t_date = vn_now.strftime("%d/%m/%Y")
            t_time = vn_now.strftime("%H:%M:%S")

            is_win = (outcome == "B" and current_bet_side == "BANKER") or (outcome == "P" and current_bet_side == "PLAYER")
            pnl = (current_bet_amount * 0.95 if current_bet_side == "BANKER" else current_bet_amount) if is_win else -current_bet_amount
            new_current_cap = current_capital + pnl
            res_str = "WIN" if is_win else "LOSE"

            new_initial_cap = initial_capital
            if new_current_cap >= 2.0 * initial_capital:
                new_initial_cap = new_current_cap
            elif new_current_cap <= 0.5 * initial_capital:
                new_initial_cap = new_current_cap

            new_table_orders = orders_in_table + 1
            new_session_orders = order_in_session_count + 1

            table_done = 0
            if is_win and orders_in_table == 0:
                table_done = 1
            elif new_table_orders >= 2:
                table_done = 1

            cur_pnl_after = session_pnl_calc + pnl
            cur_pct_after = (cur_pnl_after / session_start_cap) * 100 if session_start_cap > 0 else 0
            is_win_stop = (cur_pct_after >= 4.75) or (cur_pnl_after >= initial_capital * 0.0475)
            is_lose_stop = (cur_pnl_after <= -(session_start_cap * 0.50))
            
            if is_win_stop or is_lose_stop:
                if curr_session not in full_data["config"]["completed_sessions"]:
                    full_data["config"]["completed_sessions"].append(curr_session)

            full_data["config"]["current_cap"] = new_current_cap
            full_data["config"]["initial_cap"] = new_initial_cap
            full_data["config"]["table_orders_count"] = new_table_orders
            full_data["config"]["table_completed"] = table_done

            new_record = {
                "trade_date": t_date,
                "time_str": t_time,
                "session_name": SESSION_MAP[curr_session],
                "session_idx": curr_session,
                "table_num": curr_table,
                "order_in_session": new_session_orders,
                "order_in_table": new_table_orders,
                "strategy_desc": strategy_label,
                "bet_side": current_bet_side,
                "bet_amount": current_bet_amount,
                "result": res_str,
                "pnl": pnl,
                "ending_balance": new_current_cap
            }
            if "history" not in full_data:
                full_data["history"] = []
            full_data["history"].append(new_record)

            sync_write_data(full_data)

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
        h_df = df_history[[
            'trade_date', 'time_str', 'session_name', 'order_in_session', 'table_num', 
            'order_in_table', 'strategy_desc', 'bet_side', 'bet_amount', 'result', 'pnl', 'ending_balance'
        ]].iloc[::-1].copy()
        h_df['bet_amount'] = h_df['bet_amount'].apply(lambda x: f"${x:,.2f}")
        h_df['pnl'] = h_df['pnl'].apply(lambda x: f"${x:+,.2f}")
        h_df['ending_balance'] = h_df['ending_balance'].apply(lambda x: f"${x:,.2f}")
        h_df.columns = [
            'Ngày', 'Giờ', 'Phiên', 'STT Phiên', 'Bàn', 
            'STT Bàn', 'Chiến Lược', 'Cửa Đặt', 'Tiền Đặt ($)', 'Kết Quả', 'Lãi/Lỗ ($)', 'Vốn Biến Động ($)'
        ]
        st.dataframe(h_df, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu đặt cược nào.")

with tab_report:
    st.subheader("📊 Báo Cáo Quản Trị Vốn Theo Ngày / Tuần / Tháng")
    if not df_history.empty:
        rep_df = df_history.copy()
        rep_df['dt'] = pd.to_datetime(rep_df['trade_date'], format='%d/%m/%Y', errors='coerce')

        st.markdown("#### 📅 1. Báo Cáo Theo Ngày")
        day_summary = rep_df.groupby('trade_date').agg(
            Tổng_Lệnh=('result', 'count'),
            Số_Win=('result', lambda x: (x == 'WIN').sum()),
            Số_Lose=('result', lambda x: (x == 'LOSE').sum()),
            Tổng_PnL=('pnl', 'sum'),
            Vốn_Cuối=('ending_balance', 'last')
        ).reset_index()
        day_summary['Tỷ Lệ Win'] = (day_summary['Số_Win'] / day_summary['Tổng_Lệnh'] * 100).round(1).astype(str) + "%"
        day_summary['Tổng_PnL'] = day_summary['Tổng_PnL'].apply(lambda x: f"${x:+,.2f}")
        day_summary['Vốn_Cuối'] = day_summary['Vốn_Cuối'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(day_summary, use_container_width=True)

        st.markdown("#### 🕒 2. Báo Cáo Theo Phiên")
        sess_summary = rep_df.groupby('session_name').agg(
            Số_Lệnh=('result', 'count'),
            Tổng_PnL=('pnl', 'sum')
        ).reset_index()
        sess_summary['Tổng_PnL'] = sess_summary['Tổng_PnL'].apply(lambda x: f"${x:+,.2f}")
        st.dataframe(sess_summary, use_container_width=True)

        st.markdown("#### 📈 3. Tổng Hợp Tuần & Tháng")
        rep_df['year_week'] = rep_df['dt'].dt.strftime('%Y - Tuần %U')
        rep_df['year_month'] = rep_df['dt'].dt.strftime('%m/%Y')
        col_w, col_m = st.columns(2)
        with col_w:
            w_sum = rep_df.groupby('year_week')['pnl'].sum().reset_index()
            w_sum.columns = ['Tuần', 'PnL ($)']
            w_sum['PnL ($)'] = w_sum['PnL ($)'].apply(lambda x: f"${x:+,.2f}")
            st.dataframe(w_sum, use_container_width=True)
        with col_m:
            m_sum = rep_df.groupby('year_month')['pnl'].sum().reset_index()
            m_sum.columns = ['Tháng', 'PnL ($)']
            m_sum['PnL ($)'] = m_sum['PnL ($)'].apply(lambda x: f"${x:+,.2f}")
            st.dataframe(m_sum, use_container_width=True)
    else:
        st.info("Báo cáo sẽ tự động tổng hợp khi bạn có lệnh cược.")
