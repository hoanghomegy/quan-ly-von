import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import json
import os
import io

st.set_page_config(
    page_title="Baccarat 8-Bot Oscar's Grind Algorithm (Chuẩn Video Rafael)",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "baccarat_history.json"
CONFIG_FILE = "baccarat_config.json"

VN_TZ = timezone(timedelta(hours=7))
def get_current_vn_date():
    return datetime.now(VN_TZ).date()

# --- 1. LƯU TRỮ VÀ ĐỌC DỮ LIỆU ---
def load_all_history():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_all_history(data_list):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)

def load_config():
    default_cfg = {
        "account_balance": 1780,
        "risk_bankroll": 700,
        "target_percent": 5.0,
        "unit_size": 1
    }
    if not os.path.exists(CONFIG_FILE):
        return default_cfg
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_cfg

def save_config(cfg_dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg_dict, f, ensure_ascii=False, indent=2)

# --- 2. LOGIC TÍNH TOÁN 8 BOT ẢO (4 CẶP ĐỘ TRỄ) ---
BOT_SPECS = [
    {"name": "Tom", "lag": 1, "opp": False},
    {"name": "Pablo", "lag": 1, "opp": True},
    {"name": "Mel", "lag": 2, "opp": False},
    {"name": "Hamza", "lag": 2, "opp": True},
    {"name": "Kevin", "lag": 3, "opp": False},
    {"name": "Gukesh", "lag": 3, "opp": True},
    {"name": "Olivia", "lag": 4, "opp": False},
    {"name": "Zion", "lag": 4, "opp": True},
]

def simulate_bots(history_hands):
    bot_stats = {
        b["name"]: {
            "loss_streak": 0,
            "win_streak": 0,
            "cycle_pnl": 0,
            "total_pnl": 0,
            "og_stake": 1,
            "last_pred": None
        } for b in BOT_SPECS
    }

    for i, actual in enumerate(history_hands):
        past = history_hands[:i]
        for b in BOT_SPECS:
            name = b["name"]
            lag = b["lag"]
            opp = b["opp"]
            
            pred = None
            if len(past) >= lag:
                ref = past[-lag]
                pred = ('P' if ref == 'B' else 'B') if opp else ref
            
            if pred is not None:
                win = (actual == pred)
                stk = bot_stats[name]["og_stake"]
                if win:
                    bot_stats[name]["win_streak"] += 1
                    bot_stats[name]["loss_streak"] = 0
                    bot_stats[name]["cycle_pnl"] += stk
                    bot_stats[name]["total_pnl"] += stk
                    if bot_stats[name]["cycle_pnl"] >= 1:
                        bot_stats[name]["cycle_pnl"] = 0
                        bot_stats[name]["og_stake"] = 1
                    else:
                        needed = 1 - bot_stats[name]["cycle_pnl"]
                        bot_stats[name]["og_stake"] = min(stk + 1, needed)
                else:
                    bot_stats[name]["loss_streak"] += 1
                    bot_stats[name]["win_streak"] = 0
                    bot_stats[name]["cycle_pnl"] -= stk
                    bot_stats[name]["total_pnl"] -= stk
                    
    next_preds = {}
    for b in BOT_SPECS:
        name = b["name"]
        lag = b["lag"]
        opp = b["opp"]
        if len(history_hands) >= lag:
            ref = history_hands[-lag]
            next_preds[name] = ('P' if ref == 'B' else 'B') if opp else ref
        else:
            next_preds[name] = None

    return bot_stats, next_preds

# --- 3. THUẬT TOÁN ĐIỂM VÀO LỆNH & QUẢN LÝ VỐN CHUẨN XÁC ---
def get_system_signal(history_hands, bot_stats, next_preds, user_cycle_pnl, user_current_stake, last_bet_won):
    """
    Chuẩn hóa logic thực chiến của Mister Rafael:
    1. Cần tối thiểu 2 ván mồi đầu tiên (P/B). Ván thứ 3 vào lệnh ngay!
    2. Chỉ SKIP (No Bet) đúng 1 ván ngay sau khi vừa WIN chạm đích +1 unit chu kỳ.
    3. Hết ván SKIP là phải vào lệnh ngay theo nhịp chiếm ưu thế.
    """
    total_hands = len(history_hands)
    
    # Chưa đủ 2 ván mồi
    if total_hands < 2:
        return "NO BET", 0, f"Nhập đủ 2 ván mồi đầu tiên (Hiện tại: {total_hands}/2)"

    # Nếu vừa mới chiến thắng ở ván cược trước và chu kỳ đạt +1 unit -> Nghỉ đúng 1 ván (Free Hand)
    if last_bet_won and user_cycle_pnl == 0:
        return "NO BET", 0, "Chốt chu kỳ +1 unit -> Nghỉ quan sát 1 ván (Free hand)"

    # Phân loại dự đoán của các bot
    p_bots = [name for name, p in next_preds.items() if p == "P"]
    b_bots = [name for name, p in next_preds.items() if p == "B"]

    # Điểm ưu thế theo chuỗi thua (bắt đáy) và chuỗi thắng (bám trend)
    max_p_loss = max([bot_stats[b]["loss_streak"] for b in p_bots]) if p_bots else 0
    max_b_loss = max([bot_stats[b]["loss_streak"] for b in b_bots]) if b_bots else 0
    
    max_p_win = max([bot_stats[b]["win_streak"] for b in p_bots]) if p_bots else 0
    max_b_win = max([bot_stats[b]["win_streak"] for b in b_bots]) if b_bots else 0

    chosen_side = None
    reason = ""

    # Ưu tiên 1: Bắt đáy nếu có bot thua thông từ 2 ván trở lên
    if max_p_loss >= 2 and max_p_loss > max_b_loss:
        chosen_side = "PLAYER"
        reason = f"Bắt đáy phe Player (Bot thua thông {max_p_loss} ván)"
    elif max_b_loss >= 2 and max_b_loss > max_p_loss:
        chosen_side = "BANKER"
        reason = f"Bắt đáy phe Banker (Bot thua thông {max_b_loss} ván)"
    # Ưu tiên 2: Bám theo trend bot đang có phong độ thắng cao nhất
    elif max_p_win > max_b_win:
        chosen_side = "PLAYER"
        reason = f"Bám trend Player theo bot đang đỏ (Chuỗi thắng {max_p_win} ván)"
    elif max_b_win > max_p_win:
        chosen_side = "BANKER"
        reason = f"Bám trend Banker theo bot đang đỏ (Chuỗi thắng {max_b_win} ván)"
    # Mặc định: Theo ván liền kề trước (Follow Last - Tom)
    else:
        last_result = history_hands[-1]
        chosen_side = "PLAYER" if last_result == "P" else "BANKER"
        reason = f"Đánh theo nhịp ván gần nhất ({chosen_side})"

    # Tính số tiền cược theo Oscar's Grind
    stake = user_current_stake
    if user_cycle_pnl >= 0:
        stake = 1
    else:
        needed = 1 - user_cycle_pnl
        stake = min(user_current_stake, needed)

    return chosen_side, stake, reason

# --- 4. GIAO DIỆN CHÍNH (STREAMLIT UI) ---
st.markdown("<h2 style='text-align: center; color: #1F4E78;'>🎯 HỆ THỐNG BACCARAT 8-BOT OSCAR'S GRIND</h2>", unsafe_allow_html=True)
st.caption("<div style='text-align: center;'>Thuật toán chuẩn Mister Rafael | Vào lệnh ngay sau 2 ván mồi</div>", unsafe_allow_html=True)

cfg = load_config()
today_vn = get_current_vn_date()

with st.sidebar:
    st.markdown("### 💼 Quản Lý Vốn Lãi Kép")
    acc_bal = st.number_input("Tổng số dư tài khoản ($):", min_value=10, value=int(cfg["account_balance"]), step=50)
    risk_bal = st.number_input("Vốn chịu rủi ro phiên ($):", min_value=10, value=int(cfg["risk_bankroll"]), step=50)
    target_pct = st.number_input("Mục tiêu lãi kép (%):", min_value=1.0, max_value=20.0, value=float(cfg["target_percent"]), step=0.5)
    unit_val = st.number_input("Giá trị 1 Unit ($):", min_value=1, value=int(cfg["unit_size"]), step=1)
    
    target_profit = int(risk_bal * (target_pct / 100.0))
    target_balance = acc_bal + target_profit
    
    if (acc_bal != cfg["account_balance"] or risk_bal != cfg["risk_bankroll"] or 
        target_pct != cfg["target_percent"] or unit_val != cfg["unit_size"]):
        save_config({
            "account_balance": acc_bal,
            "risk_bankroll": risk_bal,
            "target_percent": target_pct,
            "unit_size": unit_val
        })
    
    st.markdown("---")
    st.markdown(f"**Mục tiêu lợi nhuận:** `+{target_profit}$` ({target_pct}%)")
    st.markdown(f"**Số dư đích đến:** `{target_balance:,}$`")

c_date, c_sess = st.columns(2)
with c_date:
    selected_date = st.date_input("Ngày (GMT+7):", today_vn)
with c_sess:
    selected_session = st.selectbox("Phiên chơi:", ["Phien 1", "Phien 2", "Phien 3", "Phien 4"])

all_records = load_all_history()
if all_records:
    df_all = pd.DataFrame(all_records)
    df_cur = df_all[(df_all["session_date"] == str(selected_date)) & (df_all["session_name"] == selected_session)].copy()
else:
    df_all = pd.DataFrame()
    df_cur = pd.DataFrame()

history_hands = []
if not df_cur.empty:
    history_hands = [h for h in df_cur["actual_result"].tolist() if h in ["P", "B"]]

session_pnl = int(df_cur["money_pnl"].sum()) if not df_cur.empty else 0
current_acc_balance = acc_bal + session_pnl

# Tính trạng thái chu kỳ Oscar's Grind của người dùng
user_cycle_pnl = 0
user_current_stake = 1
last_bet_won = False

for _, row in df_cur.iterrows():
    if row["action"] in ["PLAYER", "BANKER"]:
        pnl = row["money_pnl"]
        user_cycle_pnl += pnl
        if pnl > 0:
            last_bet_won = True
            if user_cycle_pnl >= 1:
                user_cycle_pnl = 0
                user_current_stake = 1
            else:
                user_current_stake = min(user_current_stake + 1, 1 - user_cycle_pnl)
        else:
            last_bet_won = False
    elif row["action"] == "NO BET":
        # Sau ván skip thì không tính là vừa win nữa để mở khóa vào lệnh ván kế
        last_bet_won = False

is_session_achieved = session_pnl >= target_profit

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Số dư hiện tại", f"{current_acc_balance:,}$", delta=f"{'+' if session_pnl>=0 else ''}{session_pnl}$")
kpi2.metric("Mục tiêu phiên (+5%)", f"+{target_profit}$", f"Đích: {target_balance:,}$")
kpi3.metric("Số tay bài đã nhập", len(df_cur), f"P: {history_hands.count('P')} | B: {history_hands.count('B')}")

st.markdown("---")

bot_stats, next_preds = simulate_bots(history_hands)
signal_side, signal_units, signal_desc = get_system_signal(history_hands, bot_stats, next_preds, user_cycle_pnl, user_current_stake, last_bet_won)
signal_money = signal_units * unit_val

# Khống chế tiền cược sát mốc Target phiên
if not is_session_achieved and signal_side in ["PLAYER", "BANKER"]:
    remaining_profit = target_profit - session_pnl
    if remaining_profit > 0 and signal_money > remaining_profit:
        signal_money = remaining_profit
        signal_units = max(1, remaining_profit // unit_val)

if is_session_achieved:
    st.success(f"🏆 **ĐÃ HOÀN THÀNH MỤC TIÊU PHIÊN!** Lợi nhuận: **+{session_pnl}$**")
    st.markdown("""
    <div style='background-color: #D1E7DD; padding: 20px; border-radius: 12px; border: 2px solid #0F5132; text-align: center;'>
        <h2 style='margin:0; color: #0F5132;'>🔒 PHIÊN NÀY ĐÃ ĐƯỢC KHÓA LÃI</h2>
        <p style='margin: 8px 0 0 0; font-size: 16px; color: #155724;'>
            Mục tiêu 5% đã đạt. Đóng bàn và dừng phiên ngay lập tức để bảo toàn 100% lợi nhuận!
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    if signal_side == "NO BET":
        st.markdown(f"""
        <div style='background-color: #F8F9FA; padding: 15px; border-radius: 10px; border: 2px solid #6C757D; text-align: center;'>
            <h3 style='margin:0; color: #6C757D;'>⏳ TÍN HIỆU: <b>NO BET (SKIP / ĐỨNG NGOÀI)</b></h3>
            <p style='margin: 5px 0 0 0; font-size: 14px; color: #495057;'>{signal_desc}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        bg_col = "#D4EDDA" if signal_side == "PLAYER" else "#F8D7DA"
        text_col = "#0D6EFD" if signal_side == "PLAYER" else "#DC3545"
        border_col = "#0D6EFD" if signal_side == "PLAYER" else "#DC3545"
        
        st.markdown(f"""
        <div style='background-color: {bg_col}; padding: 16px; border-radius: 12px; border: 2px solid {border_col}; text-align: center;'>
            <h4 style='margin:0; color: #333;'>👉 TÍN HIỆU VÁN TIẾP THEO</h4>
            <h1 style='margin: 6px 0; color: {text_col}; font-size: 42px;'>
                ĐÁNH {signal_side} - {signal_money}$ ({signal_units}u)
            </h1>
            <p style='margin:0; font-size: 14px; color: #333;'>{signal_desc} | Chu kỳ PnL: <b>{user_cycle_pnl}u</b></p>
        </div>
        """, unsafe_allow_html=True)

st.write("")

if not is_session_achieved:
    st.markdown("##### 📥 Nhập kết quả mở thưởng bài:")
    btn_p, btn_b, btn_t = st.columns(3)
    
    def process_hand(result_hand):
        all_recs = load_all_history()
        stt = len(df_cur) + 1
        
        if result_hand == "T":
            pnl_money = 0
            res_str = "TIE (HÒA)"
        else:
            if signal_side in ["PLAYER", "BANKER"]:
                win = (signal_side[0] == result_hand)
                pnl_money = signal_money if win else -signal_money
                res_str = "WIN" if win else "LOSE"
            else:
                pnl_money = 0
                res_str = "MỒI / SKIP"
                
        new_row = {
            "session_date": str(selected_date),
            "session_name": selected_session,
            "stt": stt,
            "actual_result": result_hand,
            "action": signal_side,
            "stake_units": signal_units if signal_side != "NO BET" else 0,
            "stake_money": signal_money if signal_side != "NO BET" else 0,
            "result": res_str,
            "money_pnl": pnl_money,
            "balance_after": current_acc_balance + pnl_money
        }
        all_recs.append(new_row)
        save_all_history(all_recs)
        st.rerun()

    with btn_p:
        if st.button("🔵 PLAYER (P)", use_container_width=True, type="primary"):
            process_hand("P")
    with btn_b:
        if st.button("🔴 BANKER (B)", use_container_width=True, type="secondary"):
            process_hand("B")
    with btn_t:
        if st.button("🟢 TIE (HÒA)", use_container_width=True):
            process_hand("T")

with st.expander("📊 Bảng theo dõi trạng thái 8 Bot Ảo (Thời gian thực)", expanded=True):
    bot_display = []
    for b in BOT_SPECS:
        name = b["name"]
        stt_info = bot_stats[name]
        nxt_pred = next_preds[name]
        pred_label = "PLAYER" if nxt_pred == "P" else ("BANKER" if nxt_pred == "B" else "-")
        bot_display.append({
            "Bot": name,
            "Cặp Độ Trễ": f"Lag {b['lag']} ({'Nghịch' if b['opp'] else 'Thuận'})",
            "Dự Đoán Tiếp": pred_label,
            "Chuỗi Thua": f"{stt_info['loss_streak']} ván",
            "Chuỗi Thắng": f"{stt_info['win_streak']} ván",
            "Bậc Oscar's Grind": f"{stt_info['og_stake']}u",
            "PnL Chu Kỳ": f"{stt_info['cycle_pnl']}u"
        })
    st.dataframe(pd.DataFrame(bot_display), use_container_width=True, hide_index=True)

st.markdown("---")
b_c1, b_c2, b_c3 = st.columns([1, 1, 2])
with b_c1:
    if st.button("↩️ Xóa ván gần nhất", use_container_width=True):
        all_recs = load_all_history()
        for idx in range(len(all_recs) - 1, -1, -1):
            if all_recs[idx]["session_date"] == str(selected_date) and all_recs[idx]["session_name"] == selected_session:
                all_recs.pop(idx)
                save_all_history(all_recs)
                st.rerun()
                break
with b_c2:
    if st.button("🗑️ Xóa sạch phiên này", use_container_width=True):
        all_recs = load_all_history()
        all_recs = [x for x in all_recs if not (x["session_date"] == str(selected_date) and x["session_name"] == selected_session)]
        save_all_history(all_recs)
        st.rerun()
with b_c3:
    if not df_cur.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_cur.to_excel(writer, index=False, sheet_name=selected_session)
        excel_data = output.getvalue()
        st.download_button(
            label="📥 Tải lịch sử phiên về Excel",
            data=excel_data,
            file_name=f"Baccarat_{selected_session}_{selected_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

st.markdown(f"#### 📋 Nhật ký chi tiết phiên ({selected_session})")
if not df_cur.empty:
    view_df = df_cur[["stt", "actual_result", "action", "stake_money", "result", "money_pnl", "balance_after"]].copy()
    view_df.columns = ["Ván", "Kết Quả Ra", "Lệnh Cược", "Tiền Cược ($)", "W/L", "Lãi/Lỗ ($)", "Số Dư Sau Ván ($)"]
    st.dataframe(view_df, use_container_width=True, hide_index=True)
else:
    st.info("Chưa có ván nào trong phiên này. Hãy nhập 2 ván mồi đầu tiên để bắt đầu!")
