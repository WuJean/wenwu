import subprocess
import json
import pandas as pd
from openpyxl import Workbook
from tqdm import tqdm
from time import sleep

# 基础 URL
BASE_URL = "https://media.britishmuseum.org/media/"

# 提取信息的函数
def extract_info(record):
    source = record["_source"]
    
    # 唯一对象 ID
    unique_object_id = None
    for identifier in source["identifier"]:
        if identifier.get("type") == "unique object id":
            unique_object_id = identifier.get("unique_object_id")
            break
    
    # 描述
    description = None
    for multimedia in source.get("multimedia", []):
        if "description" in multimedia and multimedia["description"]:
            if multimedia["description"][0].get("primary"):
                description = multimedia["description"][0].get("value")
                break

    # 名称
    names = [name.get("value") for name in source.get("name", [])]
    
    # 图片路径
    image_path = None
    for media in source.get("multimedia", []):
        if media.get("processed", {}).get("preview", {}).get("location_is_relative"):
            image_path = media["processed"]["preview"]["location"]
            break
    
    # 生成完整图片 URL
    full_image_url = BASE_URL + image_path if image_path else None
    
    return {
        "unique_object_id": unique_object_id,
        "description": description,
        "names": ", ".join(names),  # 将名称列表转换为字符串
        "image_url": full_image_url
    }

# 执行 curl 命令并获取数据的函数
def fetch_data(keyword, page, cookie_value):
    curl_command = [
        'curl', f'https://www.britishmuseum.org/api/_search?keyword[]={keyword}&view=grid&sort=object_name__asc&page={page}',
        '-X', 'POST',
        '-H', 'accept: application/json, text/plain, */*',
        '-H', 'accept-language: zh-CN,zh;q=0.9',
        '-H', 'content-length: 0',
        '-H', 'content-type: application/json',
        '-H', f'cookie: {cookie_value}',  # 使用参数化的 cookie
        '-H', 'origin: https://www.britishmuseum.org',
        '-H', 'priority: u=1, i',
        '-H', 'referer: https://www.britishmuseum.org/collection/search?keyword=china',
        '-H', 'sec-ch-ua: "Google Chrome";v="131", "Chromium";v="131", "Not:A-Brand";v="24"',
        '-H', 'sec-ch-ua-mobile: ?0',
        '-H', 'sec-ch-ua-platform: "macOS"',
        '-H', 'sec-fetch-dest: empty',
        '-H', 'sec-fetch-mode: cors',
        '-H', 'sec-fetch-site: same-origin',
        '-H', 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        '--proxy', 'http://127.0.0.1:7890',  # 使用代理

    ]
    
    # 执行 curl 命令
    result = subprocess.run(curl_command, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error fetching data for page {page}: {result.stderr}")
        return None
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Failed to decode JSON for page {page}")
        return None

# 主函数
def main():
    cookie_value = None  # 替换为实际的 cookie 值
    keyword = "景德镇"  # 搜索关键词
    total_pages = 20  # 假设爬取 5 页数据
    all_results = []

    for page in tqdm(range(1, total_pages + 1)):
        print(f"Fetching data for page {page}...")
        data = fetch_data(keyword, page, cookie_value)
        # print(data)
        
        if data and "hits" in data and "hits" in data["hits"]:
            for hit in data["hits"]["hits"]:
                all_results.append(extract_info(hit))
        else:
            print(f"No data found for page {page}")

    # 将结果保存到 Excel 文件
    if all_results:
        df = pd.DataFrame(all_results)
        df.to_excel(f"data/大英/{keyword}.xlsx", index=False)
        print("Data saved to british_museum_data.xlsx")
    else:
        print("No data to save.")

if __name__ == "__main__":
    main()