import requests
import os
import re
from bs4 import BeautifulSoup

# --- 設定 ---
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID")
RAKUTEN_AFF_ID = os.getenv("RAKUTEN_AFFILIATE_ID")
HISTORY_FILE = "sent_products.txt"

# 巡回するLIPSのカテゴリURLリスト
LIPS_URLS = {
    "メイクアップ": "https://lipscosme.com/product_categories/1",
    "スキンケア": "https://lipscosme.com/product_categories/2",
    "ヘアケア": "https://lipscosme.com/product_categories/4",
    "ボディケア": "https://lipscosme.com/product_categories/3"
}

# PR TIMESの美容カテゴリ
PRTIMES_URL = "https://prtimes.jp/main/html/searchrlp/ct/cosme"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    return set()

def save_history(product_name):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(product_name + "\n")

def get_rakuten_info(keyword):
    if not RAKUTEN_APP_ID: return None, None
    # 検索精度を上げるため、商品名を短くトリミング
    clean_keyword = keyword.split(' / ')[0][:30]
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "affiliateId": RAKUTEN_AFF_ID,
        "keyword": clean_keyword,
        "sort": "+itemPrice",
        "hits": 1
    }
    try:
        res = requests.get(url, params=params).json()
        if "Items" in res and res["Items"]:
            item = res["Items"][0]["Item"]
            return item["itemPrice"], item["affiliateUrl"]
    except:
        pass
    return None, None

def scan_lips(sent_list):
    """LIPSの各カテゴリをスキャン"""
    for cat_name, url in LIPS_URLS.items():
        print(f"--- LIPS {cat_name} カテゴリをスキャン中 ---")
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.find_all("div", class_="style_productCard__N_7_L")
        
        for item in items:
            name_tag = item.find("div", class_="style_productName__m6m_e")
            if not name_tag: continue
            name = name_tag.get_text().strip()
            
            if name in sent_list: continue

            clip_tag = item.find("span", class_="style_clipCount__IeR_P")
            clip_count = int(re.sub(r'\D', '', clip_tag.get_text())) if clip_tag else 0
            
            # 人気がある、または新作・限定
            if clip_count >= 150 or "新作" in name or "限定" in name:
                process_found_item(name, f"LIPS({cat_name})", clip_count)

def scan_prtimes(sent_list):
    """PR TIMESの新着プレスリリースをスキャン"""
    print("--- PR TIMES 公式速報をスキャン中 ---")
    res = requests.get(PRTIMES_URL)
    soup = BeautifulSoup(res.text, "html.parser")
    # 記事タイトルの要素を取得（PR TIMESの構造に合わせる）
    articles = soup.find_all("a", class_="link-title-item")
    
    for art in articles[:10]: # 最新10件に絞る
        title = art.get_text().strip()
        # プレスリリース名から商品名っぽい部分を推測（簡易的）
        # 例：「〇〇から新作『△△』が登場」→『△△』の部分
        match = re.search(r'『(.*?)』', title)
        product_name = match.group(1) if match else title[:20]

        if product_name in sent_list: continue
        
        process_found_item(product_name, "PR TIMES(公式速報)", None, title)

def process_found_item(name, source, popularity=None, full_title=None):
    price, aff_url = get_rakuten_info(name)
    if price:
        msg = f"🚀 **【最速検知】{source}**\n"
        msg += f"**{name}**\n"
        if popularity: msg += f"📊 人気: {popularity} clips\n"
        if full_title: msg += f"📢 内容: {full_title[:50]}...\n"
        msg += f"💰 楽天最安: ￥{price:,}\n"
        msg += f"🔗 [楽天で詳細を見る]({aff_url})\n※PR"
        
        requests.post(WEBHOOK_URL, json={"content": msg})
        save_history(name)
        print(f"通知送信: {name}")

def main():
    sent_list = load_history()
    scan_lips(sent_list)
    scan_prtimes(sent_list)

if __name__ == "__main__":
    main()