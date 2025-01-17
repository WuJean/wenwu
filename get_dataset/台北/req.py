import asyncio
from playwright.async_api import async_playwright
from tqdm import tqdm
from bs4 import BeautifulSoup
import pandas as pd
import yaml
import os

# 异步爬取
async def async_craw(page, f, t, step):
    all_data = []

    for i in tqdm(range(f, t, step)):
        uid = i
        try:
            url = f'https://digitalarchive.npm.gov.tw/Antique/Content?uid={i}&Dept=U'
            await page.goto(url,timeout=20000)  # 超时时间设置为10秒

            # 等待指定的表格加载完成
            await page.wait_for_selector('//*[@id="collapseExample"]/div/div[1]/table/tbody', timeout=10000)

            # 获取页面内容
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # 提取图片链接
            image_elements = soup.find_all('div', class_='ug-item-wrapper')
            image_urls = [
                'https://digitalarchive.npm.gov.tw' + image.find('img')['src'].replace('amp;', '')
                for image in image_elements
                if image.find('img')
            ]

            # 提取文物信息
            tbody_element = soup.select_one('#collapseExample table tbody')
            rows = tbody_element.find_all('tr') if tbody_element else []
            name, category, dynasty, description = '', '', '', ''

            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if label == '品名':
                        name = value
                    elif label == '分類':
                        category = value
                    elif label == '時代':
                        dynasty = value
                    elif label == '說明':
                        description = value

            # 保存数据
            all_data.append({
                'ID': uid,
                'Name': name,
                'Category': category,
                'Dynasty': dynasty,
                'Description': description,
                'Image': image_urls,
            })

        except Exception as e:
            print(f"UID {i}: 爬取时发生异常，异常信息: {e}")
            continue

    return all_data

# 写入 Excel 文件
def to_excel(filename, all_data):
    print(f"共爬取到 {len(all_data)} 条数据")
    df = pd.DataFrame(all_data)
    if '/' in filename:
        folder = filename.rsplit('/', 1)[0]
        os.makedirs(folder, exist_ok=True)
    df.to_excel(filename, index=False)
    print(f"数据已写入到 {filename}")

# 异步处理配置
async def async_process_config(config):
    print("异步爬取开始")
    all_data = []
    step = config['step']
    semaphore = asyncio.Semaphore(5)  # 限制并发数为4

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False,proxy={'server': 'http://127.0.0.1:7890'})
        context = await browser.new_context()  # 创建上下文
        tasks = []

        async def process_range(start, end):
            async with semaphore:
                page = await context.new_page()
                try:
                    print(f"异步爬取 UID {start} 到 {end}...")
                    result = await async_craw(page, start, end, config['skip'])
                    return result
                except Exception as e:
                    print(f"爬取 UID {start} 到 {end} 时发生错误: {e}")
                    return []
                finally:
                    await page.close()  # 确保页面关闭

        # 创建所有任务
        for i in range(config['range_start'], config['range_end'], step):
            tasks.append(process_range(i, min(i + step, config['range_end'])))

        # 并发运行任务
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result:
                all_data.extend(result)

        await context.close()  # 关闭上下文
        await browser.close()  # 关闭浏览器

    # 保存数据到 Excel
    to_excel(f"data/台北/{config['filename']}", all_data)
    print(f"完成所有爬取，数据已保存到 {config['filename']}")

# 主函数
async def main():
    config_path = 'config/data_config'
    for config_file in os.listdir(config_path):
        with open(f'{config_path}/{config_file}', 'r') as f:
            config = yaml.safe_load(f)
        await async_process_config(config)

if __name__ == "__main__":
    asyncio.run(main())