import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
import yaml

import os

# 本地代理配置
LOCAL_PROXY = "http://127.0.0.1:7890"

# 配置 WebDriver
def start_browser_with_proxy():
    chrome_options = Options()
    chrome_options.add_argument(f"--proxy-server={LOCAL_PROXY}")
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service("./chromedriver")  # 替换为你的 ChromeDriver 路径
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# 爬取 f-t 范围的 URL 对应文物
def craw(driver, f, t ,step):
    all_data = []
    # 创建浏览器驱动（这里假设使用Chrome浏览器，你需要根据实际情况修改）

    try:
        # 间隔为2个文物
        for i in tqdm(range(f,t,step)):
            uid = i
            try:
                driver.get(f'https://digitalarchive.npm.gov.tw/Antique/Content?uid={i}&Dept=U')
                # 等待数据加载完成，适当增加等待时间，确保页面完全加载
                wait = WebDriverWait(driver, 10)
                # 等待页面中指定的tbody元素出现，表明数据已加载一部分
                tbody_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="collapseExample"]/div/div[1]/table/tbody')))
                # 获取tbody元素下的所有tr元素，通常每行对应文物的一项信息
                tr_elements = tbody_element.find_elements(By.TAG_NAME, "tr")

                # 获取页面源代码并使用BeautifulSoup进行解析，以便后续查找图片元素
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                # 找到所有符合条件的包含图片的img元素（根据实际网页结构调整选择器）
                image_elements = soup.find_all('div', class_='ug-item-wrapper')
                print(image_elements)
                image_urls = []
                for image in image_elements:
                    image = image.find('img')
                    image_url = 'https://digitalarchive.npm.gov.tw' + image['src']
                    # 修正图片链接中的转义字符
                    image_url = image_url.replace('amp;', '')
                    print(image_url)
                    image_urls.append(image_url)

                # 提取文物的各项信息（品名、分类、时代、说明等）
                name, category, dynasty, description = '', '', '', ''
                for tr in tr_elements:
                    tds = tr.find_elements(By.TAG_NAME, "td")
                    if len(tds) >= 2:
                        label = tds[0].text.strip()
                        value = tds[1].text.strip()
                        if label == '品名':
                            name = value
                        elif label == '分類':
                            category = value
                        elif label == '說明':
                            description = value
                        elif label == '時代':
                            dynasty = value

                dynasty = dynasty if dynasty else ''
                description = description if description else ''
                # 将当前文物的各项信息组合成字典，添加到结果列表中
                all_data.append({'ID': uid, 'Name': name, 'Category': category, 'Dynasty': dynasty, 'Description': description, 'Image': image_urls})

                time.sleep(1)  # 设置间隔，避免过多请求导致被限制

            except TimeoutException:
                print(f"UID {i}: 加载超时")
                continue
            except Exception as e:
                print(f"UID {i}: 出现异常，异常信息: {str(e)}")
                continue

    finally:
        driver.quit()

    return all_data

# 写入 Excel 文件
def to_excel(filename, all_data):
    print(f"共爬取到 {len(all_data)} 条数据")
    df = pd.DataFrame(all_data)
    # 创建文件名所在的文件夹
    if '/' in filename:
        folder = filename.rsplit('/', 1)[0]
        os.makedirs(folder, exist_ok=True)
    df.to_excel(filename, index=False)
    print(f"数据已写入到 {filename}")


def process_config(config):
    all_data = []
    step = config['step']
    for i in range(config['range_start'], config['range_end'], step):
        print(f"正在爬取 UID {i} 到 {min(i + step,config['range_end'])}...")

        driver = None
        try:
            driver = start_browser_with_proxy()
            batch_data = craw(driver, i, min(i + step,config['range_end']), config['skip'])
            all_data.extend(batch_data)
        except Exception as e:
            print(f"UID {i} 到 {i + step - 1} 爬取失败，原因: {e}")
        finally:
            if driver:
                driver.quit()

    to_excel(f'data/台北/{config['filename']}', all_data)
    print(f"完成所有爬取，数据已保存到 {config['filename']}")


def main():
    # 从config文件夹中读取配置
    config_path = 'config/data_config'
    for config_file in os.listdir(config_path):
        with open(f'{config_path}/{config_file}', 'r') as f:
            config = yaml.safe_load(f)
        process_config(config)

if __name__ == '__main__':
    main()