#!/usr/bin/env python3
import os
import json
import requests
from datetime import datetime

def main():
    print("--- Start GOLD & MAJOR Status Updater ---")
    
    # -------------------------------------------------------------------------
    # 【設定】環境変数と出力ファイルパスの整理
    # -------------------------------------------------------------------------
    gold_status_file = "status_gold.txt"
    gold_meta_file = "status_gold.json"
    major_status_file = "status_major.txt"
    major_meta_file = "status_major.json"
    
    # 初期判定はすべて稼働（START）
    gold_status = "START"
    gold_reason = "GOLD market is stable."
    
    major_status = "START"
    major_reason = "Major currency markets are stable."
    
    # -------------------------------------------------------------------------
    # 1. ゴールド（XAU/USD）の判定（※従来のロジックを維持）
    # -------------------------------------------------------------------------
    gold_change_24h = 0.0
    try:
        url = "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=XAU&tsyms=USD"
        res = requests.get(url, timeout=10).json()
        raw_data = res.get("RAW", {}).get("XAU", {}).get("USD", {})
        gold_change_24h = raw_data.get("CHANGEPCT24HOUR", 0.0)
        print(f"GOLD 24h Change: {gold_change_24h:.2f}%")
        
        if abs(gold_change_24h) >= 2.5:
            gold_status = "STOP"
            gold_reason = f"High GOLD volatility detected. 24h change: {gold_change_24h:.2f}%"
    except Exception as e:
        print(f"Failed to fetch GOLD market data: {e}")

    # -------------------------------------------------------------------------
    # 2. メジャー通貨（為替全体）のボラティリティ判定
    #    ※ドル円(USDJPY)やユーロドル(EURUSD)の急変をチェック
    # -------------------------------------------------------------------------
    try:
        forex_url = "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=USD,EUR&tsyms=JPY,USD"
        forex_res = requests.get(forex_url, timeout=10).json()
        
        # ドル円（USD/JPY）の24時間変動率
        jpy_change = forex_res.get("RAW", {}).get("USD", {}).get("JPY", {}).get("CHANGEPCT24HOUR", 0.0)
        # ユーロドル（EUR/USD）の24時間変動率
        eur_change = forex_res.get("RAW", {}).get("EUR", {}).get("USD", {}).get("CHANGEPCT24HOUR", 0.0)
        
        print(f"USD/JPY 24h Change: {jpy_change:.2f}%")
        print(f"EUR/USD 24h Change: {eur_change:.2f}%")
        
        # 為替は1日で±0.8%以上動くとボラティリティが高いと判断（EA保護のため）
        if abs(jpy_change) >= 0.8 or abs(eur_change) >= 0.8:
            major_status = "STOP"
            major_reason = f"High Forex volatility detected. USDJPY: {jpy_change:.2f}%, EURUSD: {eur_change:.2f}%"
    except Exception as e:
        print(f"Failed to fetch Forex market data: {e}")

    # -------------------------------------------------------------------------
    # 3. 経済ニュース・指標リスクのチェック（ゴールド用 ＆ メジャー通貨用）
    # -------------------------------------------------------------------------
    try:
        # カテゴリを「コモディティ」に加えて「法定通貨(Fiat), 経済(Asia, Europe, USA)」に拡大
        news_url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories=Commodity,Market,Fiat"
        news_res = requests.get(news_url, timeout=10).json()
        articles = news_res.get("Data", [])
        
        # キーワードリスト
        gold_ng_words = ["fomc", "cpi", "nfp", "employment report", "interest rate", "fed chair", "powell"]
        major_ng_words = ["fomc", "cpi", "nfp", "boj", "ecb", "interest rate", "lagarde", "ueda", "fed", "central bank"]
        
        for article in articles[:12]:  # メジャー通貨もカバーするため件数を12件に拡大
            title = article.get("title", "").lower()
            body = article.get("body", "").lower()
            
            # ゴールドのニュース判定
            if gold_status == "START":
                for word in gold_ng_words:
                    if word in title or word in body:
                        gold_status = "STOP"
                        gold_reason = f"Urgent GOLD Macro Risk: '{word}' found in headlines."
                        break
                        
            # メジャー通貨のニュース判定（日銀、ECB、中央銀行総裁発言などもチェック）
            if major_status == "START":
                for word in major_ng_words:
                    if word in title or word in body:
                        major_status = "STOP"
                        major_reason = f"Urgent Forex Macro Risk: '{word}' found in headlines."
                        break

    except Exception as e:
        print(f"Failed to fetch financial news data: {e}")

    # -------------------------------------------------------------------------
    # 4. ファイルへの書き込み（ゴールドとメジャーをそれぞれ独立出力）
    # -------------------------------------------------------------------------
    # --- ゴールド出力 ---
    print(f"Final Decision for GOLD: {gold_status} ({gold_reason})")
    with open(gold_status_file, "w", encoding="utf-8") as f:
        f.write(gold_status)
    with open(gold_meta_file, "w", encoding="utf-8") as f:
        json.dump({"status": gold_status, "reason": gold_reason, "generated_at_utc": datetime.utcnow().isoformat() + "Z"}, f, indent=2)

    # --- メジャー通貨出力 ---
    print(f"Final Decision for MAJOR: {major_status} ({major_reason})")
    with open(major_status_file, "w", encoding="utf-8") as f:
        f.write(major_status)
    with open(major_meta_file, "w", encoding="utf-8") as f:
        json.dump({"status": major_status, "reason": major_reason, "generated_at_utc": datetime.utcnow().isoformat() + "Z"}, f, indent=2)

if __name__ == "__main__":
    main()
