import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv

# --- 設定 ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1489188957907456051/MP4H-RWHtt697rRatyHg8kCju2ih-wgcICpr9uci9i99S2IiCCm9RTF2K-loryB4w1Z5"
TARGET_URL = "https://lipscosme.com/new_items" # LIPSの新作ページ
HEADERS = {"User-Agent": "Mozilla/5.0"}

def send_discord(message):
    requests.post(WEBHOOK_URL, json={"content": message})

# --- 実行 ---
response = requests.get(TARGET_URL, headers=HEADERS)
response.encoding = response.apparent_encoding
soup = BeautifulSoup(response.text, "html.parser")

# LIPSの各商品が入っている「箱」を探す
# ※サイトのデザインが変わるとここも微調整が必要になります
items = soup.find_all("div", class_="ProductCard_container__Y6p4_") # 2026年現在のLIPSの構造

# 話題性を判定するための「バズワード」リスト
buzz_keywords = ["限定", "バズ", "話題", "予約", "完売", "新作", "韓国", "日本"]

print(f"--- LIPSから『話題のコスメ』を捜索中 ---")

found_count = 0
with open("cosme_data.csv", "a", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    
    for item in items:
        # 商品名とブランド名を取得
        name = item.find("p", class_="ProductCard_name__pB86m").get_text(strip=True) if item.find("p", class_="ProductCard_name__pB86m") else "不明"
        brand = item.find("p", class_="ProductCard_brand__kRz_4").get_text(strip=True) if item.find("p", class_="ProductCard_brand__kRz_4") else "不明"
        link_tag = item.find("a")
        href = "https://lipscosme.com" + link_tag.get("href") if link_tag else "URLなし"

        # バズワードが含まれているかチェック
        is_buzz = any(word in name or word in brand for word in buzz_keywords)
        
        if is_buzz:
            found_count += 1
            now = datetime.now().strftime('%Y/%m/%d %H:%M')
            
            # 1. 保存
            writer.writerow([now, brand, name, href])
            
            # 2. Discordに通知（ちょっと豪華な見た目にする）
            msg = f"✨ **【コスメ新作/話題】** ✨\n**ブランド:** {brand}\n**アイテム:** {name}\n🔗 {href}"
            send_discord(msg)
            print(f"【発見】 {brand} / {name}")

if found_count == 0:
    print("今日は特に『バズりそう』な新作は見当たりませんでした。")
else:
    print(f"\n合計 {found_count} 件のコスメ情報を送信しました。")