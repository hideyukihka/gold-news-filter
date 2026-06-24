#!/usr/bin/env python3
import os
import json
import requests
from datetime import datetime

def main():
    print("--- Start GOLD Status Updater ---")
    
    # 1. 環境変数の読み込み (ゴールド用ファイル名にデフォルト値を設定)
    status_file = os.environ.get("STATUS_FILE_PATH", "status_gold.txt")
    meta_file = os.environ.get("STATUS_META_PATH", "status_gold.json")
    
    print(f"Target files: {status_file}, {meta_file}")
    
    current_status = "START"
    reason = "GOLD market is stable."
    gold_change_24h = 0.0
    
    # 2. ゴールド（XAU/USD）の価格と24時間変動率を取得 (CryptoCompareまたは代替APIを利用)
    # ※ゴールドはボラティリティがBTCより低いため、±2.5%を超えたら異常事態（STOP）とします
    try:
        url = "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=XAU&tsyms=USD"
        res = requests.get(url, timeout=10).json()
        
        # データの抽出
        raw_data = res.get("RAW", {}).get("XAU", {}).get("USD", {})
        gold_change_24h = raw_data.get("CHANGEPCT24HOUR", 0.0)
        print(f"GOLD 24h Change: {gold_change_24h:.2f}%")
        
        if abs(gold_change_24h) >= 2.5:
            current_status = "STOP"
            reason = f"High GOLD volatility detected. 24h change: {gold_change_24h:.2f}%"
            
    except Exception as e:
        print(f"Failed to fetch GOLD market data: {e}")

    # 3. 経済ニュース・指標リスクの簡易チェック (重要ワード)
    try:
        # 一般的な金融・マクロ経済ニュースを取得
        news_url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories=Commodity,Market"
        news_res = requests.get(news_url, timeout=10).json()
        articles = news_res.get("Data", [])
        
        # ゴールド相場を急変動させるNGキーワード
        ng_words = ["fomc", "cpi", "nfp", "employment report", "interest rate", "fed chair", "powell"]
        for article in articles[:8]:  # 直近8件を広めにチェック
            title = article.get("title", "").lower()
            body = article.get("body", "").lower()
            
            for word in ng_words:
                if word in title or word in body:
                    current_status = "STOP"
                    reason = f"Urgent Macro Risk detected: '{word}' found in financial headlines."
                    break
            if current_status == "STOP":
                break
    except Exception as e:
        print(f"Failed to fetch financial news data: {e}")

    print(f"Final Decision for GOLD: {current_status} ({reason})")

    # 4. status_gold.txt の書き込み
    with open(status_file, "w", encoding="utf-8") as f:
        f.write(current_status)
    print(f"Updated {status_file}")

    # 5. status_gold.json の書き込み
    meta_data = {
        "status": current_status,
        "generated_at_utc": datetime.utcnow().isoformat() + "Z",
        "reason": reason,
        "gold_24h_change_pct": round(gold_change_24h, 2)
    }
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=2, ensure_ascii=False)
    print(f"Updated {meta_file}")

if __name__ == "__main__":
    main()
