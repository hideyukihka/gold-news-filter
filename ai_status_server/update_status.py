#!/usr/bin/env python3
import os
import json
import requests
from datetime import datetime, timedelta

# =============================================================================
# 【設定】Finnhub APIキー と フィルター条件
# =============================================================================
# 🚨 取得した無料のAPIキーをここに貼り付けてください
FINNHUB_API_KEY = "d8v6ja1r01qrt65vk4g0d8v6ja1r01qrt65vk4gg"

# 指標発表の「何時間前」から「何時間後」までEAを停止するか
PRE_EVENT_HOURS = 3   # 3時間前から停止
POST_EVENT_HOURS = 2  # 2時間後まで停止

def fetch_economic_calendar():
    """Finnhubから本日を含む前後3日間の経済指標スケジュールを取得する"""
    if FINNHUB_API_KEY == "YOUR_FREE_FINNHUB_API_KEY" or not FINNHUB_API_KEY:
        print("Warning: Finnhub API Key is not configured.")
        return []

    today = datetime.utcnow().date()
    start_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    url = f"https://finnhub.io/api/v1/calendar/economic?from={start_date}&to={end_date}&token={FINNHUB_API_KEY}"
    
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            return res.json().get("economicCalendar", [])
        else:
            print(f"Finnhub API Error: Status Code {res.status_code}")
            return []
    except Exception as e:
        print(f"Failed to fetch economic calendar: {e}")
        return []

def main():
    print("--- Start High-Precision Calendar Status Updater (GOLD, MAJOR, BTC) ---")
    
    # ファイルパスの設定
    gold_status_file, gold_meta_file = "status_gold.txt", "status_gold.json"
    major_status_file, major_meta_file = "status_major.txt", "status_major.json"
    btc_status_file, btc_meta_file = "status_btc.txt", "status_btc.json"
    
    # デフォルトはすべて稼働状態（START）
    gold_status, gold_reason = "START", "GOLD market is stable."
    major_status, major_reason = "START", "Major currency markets are stable."
    btc_status, btc_reason = "START", "BTC market is stable."
    
    current_time_utc = datetime.utcnow()
    print(f"Current UTC Time: {current_time_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 🌟 経済指標スケジュールの取得
    events = fetch_economic_calendar()
    print(f"Fetched {len(events)} economic events for the period.")
    
    for event in events:
        event_time_str = event.get("time", "")  # 例: "2026-06-26 12:30:00"
        country = event.get("country", "").upper()
        impact = event.get("impact", "").lower() # "high", "medium", "low"
        event_name = event.get("event", "")
        
        if not event_time_str:
            continue
            
        try:
            if "T" in event_time_str:
                event_time_str = event_time_str.replace("Z", "").split(".")[0]
                event_time_utc = datetime.strptime(event_time_str, "%Y-%m-%dT%H:%M:%S")
            else:
                event_time_utc = datetime.strptime(event_time_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue

        # 停止対象時間の計算（発表前後のウィンドウ）
        stop_start_time = event_time_utc - timedelta(hours=PRE_EVENT_HOURS)
        stop_end_time = event_time_utc + timedelta(hours=POST_EVENT_HOURS)
        
        # 現在時刻が「停止ウィンドウ」に入っているか判定
        if stop_start_time <= current_time_utc <= stop_end_time:
            
            # --- 判定A: ゴールド（GOLD）の停止条件 ---
            # 米国(US)の最高重要度(high)指標
            if country == "US" and impact == "high":
                gold_status = "STOP"
                gold_reason = f"US High Impact Event Alert: {event_name} at {event_time_str} UTC"
            
            # --- 判定B: メジャー通貨（ALL-Ai）の停止条件 ---
            # 主要5カ国(US, JP, EU, GB, AU)の最高重要度(high)指標
            if country in ["US", "JP", "EU", "GB", "AU"] and impact == "high":
                major_status = "STOP"
                major_reason = f"Forex High Impact Event Alert ({country}): {event_name} at {event_time_str} UTC"
                
            # --- 判定C: ビットコイン（BTC）の停止条件 ---
            # 暗号資産市場は「米国の金融政策（利下げ・利上げ・CPI・FOMC）」に極めて敏感です。
            # そのため、米国(US)の最高重要度(high)指標、およびデジタル通貨に関連する重要なイベントをトリガーにします。
            if country == "US" and impact == "high":
                btc_status = "STOP"
                btc_reason = f"US Macro Event Alert for BTC: {event_name} at {event_time_str} UTC"

    # -------------------------------------------------------------------------
    # 各ファイルへの書き込み
    # -------------------------------------------------------------------------
    # --- ゴールド出力 ---
    print(f"Final Decision for GOLD: {gold_status} ({gold_reason})")
    with open(gold_status_file, "w", encoding="utf-8") as f: f.write(gold_status)
    with open(gold_meta_file, "w", encoding="utf-8") as f:
        json.dump({"status": gold_status, "reason": gold_reason, "generated_at_utc": current_time_utc.isoformat() + "Z"}, f, indent=2)

    # --- メジャー通貨出力 ---
    print(f"Final Decision for MAJOR: {major_status} ({major_reason})")
    with open(major_status_file, "w", encoding="utf-8") as f: f.write(major_status)
    with open(major_meta_file, "w", encoding="utf-8") as f:
        json.dump({"status": major_status, "reason": major_reason, "generated_at_utc": current_time_utc.isoformat() + "Z"}, f, indent=2)

    # --- ビットコイン出力 (★追加) ---
    print(f"Final Decision for BTC: {btc_status} ({btc_reason})")
    with open(btc_status_file, "w", encoding="utf-8") as f: f.write(btc_status)
    with open(btc_meta_file, "w", encoding="utf-8") as f:
        json.dump({"status": btc_status, "reason": btc_reason, "generated_at_utc": current_time_utc.isoformat() + "Z"}, f, indent=2)

if __name__ == "__main__":
    main()
