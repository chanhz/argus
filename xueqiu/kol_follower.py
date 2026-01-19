import json
import os
import time
from datetime import datetime
import requests

from notify import send_dingtalk_message as send_dingtalk

# === 配置区 ===
UID_WatchList = {"福禄娃爷爷": "4046363970", "96余哥": "6890047388"} # 关注的 KOL 列表
API_URL_TEMPLATE = "https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json?pid=-1&category=1&size=1000&uid={uid}"
payload = {}
headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "dnt": "1",
    "origin": "https://xueqiu.com",
    "priority": "u=1, i",
    "referer": "https://xueqiu.com/u/6890047388",
    "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Xueqiu iPhone 14.55",
    "Cookie": "{YOUR_XUEQIU_COOKIE_HERE}", # 请替换为你的雪球 Cookie
}



# === 工具函数 ===
def timestamp_to_str(ts_ms):
    return datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def fetch_stock_list(uid):
    url = API_URL_TEMPLATE.format(uid=uid)
    headers_dynamic = headers.copy()
    headers_dynamic["referer"] = f"https://xueqiu.com/u/{uid}"
    try:
        resp = requests.request("GET", url, headers=headers_dynamic, data=payload)
        # resp = requests.get(API_URL, headers=headers)
        data = resp.json()
        if data.get("error_code") == 0:
            return data["data"]["stocks"]
        else:
            print(f"API 返回错误 for {uid}:", data)
            return None
    except Exception as e:
        print(f"请求失败 for {uid}:", e)
        return None


def load_cached_stocks(uid):
    file_path = f"stock_cache_{uid}.json"
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_stocks(stocks, uid):
    file_path = f"stock_cache_{uid}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)


def get_symbol_set(stocks):
    return {s["symbol"] for s in stocks}


# === 主逻辑 ===
def main():
    for name, uid in UID_WatchList.items():
        current_stocks = fetch_stock_list(uid)
        if current_stocks is None:
            print(f"无法获取 {name} 的当前股票列表，跳过本次检查")
            continue

        cached_stocks = load_cached_stocks(uid)
        # 区分：None 表示缓存文件不存在（首次运行），[] 表示已存在但关注列表为空
        if cached_stocks is None:
            # 首次运行
            if current_stocks:
                # 只有在有关注股票时才发送初始化通知
                msg = f"{name} 关注股票列表：\n"
                for s in current_stocks:
                    code = s["symbol"][2:]  # 去掉 SZ/SH 前缀
                    name_stock = s["name"]
                    watch_time = timestamp_to_str(s["watched"])
                    msg += f"股票：{name_stock}（{code}）\n关注时间：{watch_time}\n\n"
                send_dingtalk(msg.strip())
                print(f"✅ {name} 初始化完成，已保存缓存并发送通知")
            else:
                # 首次运行且关注列表为空：不发送通知，但仍写入空缓存以避免重复通知
                print(f"ℹ️ {name} 首次运行，关注列表为空，已保存空缓存（不通知）")
            save_stocks(current_stocks, uid)
        else:
            cached_symbols = get_symbol_set(cached_stocks)
            current_symbols = get_symbol_set(current_stocks)

            # 构建 symbol -> stock 映射
            current_map = {s["symbol"]: s for s in current_stocks}
            cached_map = {s["symbol"]: s for s in cached_stocks}
            # 检查新增股票（在当前但不在缓存中）
            new_symbols = current_symbols - cached_symbols
            # 检查取消关注的股票（在缓存中但不在当前）
            removed_symbols = cached_symbols - current_symbols
            if new_symbols or removed_symbols:
                msg = f"{name} 的关注的股票列表有变动了：\n"
                if new_symbols:
                    msg += "新增关注：\n"
                    for sym in sorted(new_symbols):
                        stock = current_map[sym]
                        code = stock["symbol"][2:]
                        name_stock = stock["name"]
                        watch_time = timestamp_to_str(stock["watched"])
                        msg += f"股票：{name_stock}（{code}）\n关注时间：{watch_time}\n\n"
                if removed_symbols:
                    msg += "取消关注：\n"
                    for sym in sorted(removed_symbols):
                        stock = cached_map[sym]
                        code = stock["symbol"][2:]
                        name_stock = stock["name"]
                        watch_time = timestamp_to_str(stock["watched"])
                        msg += f"股票：{name_stock}（{code}）\n关注时间：{watch_time}\n\n"
                send_dingtalk(msg.strip())
                print(f"✅ {name} 发现变动，已通知")
            else:
                print(f"ℹ️ {name} 无变动")

            # 更新缓存（可选：只追加 or 全量覆盖）
            save_stocks(current_stocks, uid)


if __name__ == "__main__":
    while True:
        main()
        time.sleep(10)
