import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os  # ★OSの機能を使うために追加

# --- 設定（GitHubの「秘密の金庫」から読み込むように変更） ---
WEBHOOK_URL = os.getenv("WEBHOOK_URL") 
TARGET_URL = "https://lipscosme.com/new_items"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def send_discord(message):
    # 万が一URLが空（設定忘れ）だった場合にエラーで止まらないようにする
    if not WEBHOOK_URL:
        print("エラー: WEBHOOK_URLが設定されていません")
        return
    requests.post(WEBHOOK_URL, json={"content": message})

# --- 実行 ---
response = requests.get(TARGET_URL, headers=HEADERS)
response.encoding = response.apparent_encoding
soup = BeautifulSoup(response.text, "html.parser")

# 2026年現在のLIPSの構造に合わせて取得
items = soup.find_all("div", class_="ProductCard_container__Y6p4_")

buzz_keywords = ["限定", "バズ", "話題", "予約", "完売", "新作", "韓国", "日本"]

print(f"--- LIPSから『話題のコスメ』を捜索中 ---")

found_count = 0
with open("cosme_data.csv", "a", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    
    for item in items:
        name_tag = item.find("p", class_="ProductCard_name__pB86m")
        brand_tag = item.find("p", class_="ProductCard_brand__kRz_4")
        
        name = name_tag.get_text(strip=True) if name_tag else "不明"
        brand = brand_tag.get_text(strip=True) if brand_tag else "不明"
        
        link_tag = item.find("a")
        href = "https://lipscosme.com" + link_tag.get("href") if link_tag else "URLなし"

        is_buzz = any(word in name or word in brand for word in buzz_keywords)
        
        if is_buzz:
            found_count += 1
            now = datetime.now().strftime('%Y/%m/%d %H:%M')
            writer.writerow([now, brand, name, href])
            
            msg = f"✨ **【コスメ新作/話題】** ✨\n**ブランド:** {brand}\n**アイテム:** {name}\n🔗 {href}"
            send_discord(msg)
            print(f"【発見】 {brand} / {name}")

if found_count == 0:
    send_discord("🔍 本日は『バズりそうな新作』は見当たりませんでした。また明日チェックします！")
    print("今日は特に『バズりそう』な新作は見当たりませんでした。")
else:
       print(f"\n合計 {found_count} 件の情報を送信しました。")