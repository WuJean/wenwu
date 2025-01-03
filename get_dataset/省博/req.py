import requests
import pandas as pd
import os

def fetch_data(current, size, search, year, type_, image, threeType):
    url = 'https://de.hnmuseum.com/zgww/collectionIndex/publishList'
    
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    }
    
    params = {
        'current': current,
        'size': size,
        'search': search,
        'year': year,
        'type': type_,
        'image': image,
        'threeType': threeType,
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def parse_and_save_to_excel(response_data, output_file):
    """
    解析响应体中的数据，提取 Name, Category, Dynasty, Description, Image，并保存到 Excel 文件中。

    :param response_data: 请求返回的 JSON 数据
    :param output_file: 输出的 Excel 文件路径
    """
    # 提取 records 数据
    records = response_data.get('data', {}).get('records', [])
    
    # 初始化一个空列表，用于存储解析后的数据
    parsed_data = []
    
    # 遍历每条记录
    for record in records:
        id = record.get('id', '')
        name = record.get('collection_name', '')
        category = record.get('collection_texture', '')
        dynasty = record.get('collection_years', '')
        description = record.get('collection_size', '')
        image = record.get('thumb_path', '')
        
        # 将解析后的数据添加到列表中
        parsed_data.append({
            'ID': id,
            'Name': name,
            'Category': category,
            'Dynasty': dynasty,
            'Description': description,
            'Image': image
        })
    
    # 将数据转换为 DataFrame
    df = pd.DataFrame(parsed_data)
    
    # 如果文件夹不存在，则创建
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    
    # 保存到 Excel 文件
    df.to_excel(output_file, index=False)
    print(f"数据已成功保存到 {output_file}")

# 定义类别和对应的 type_ 值
categories = {
    "陶瓷": "969282295133372416",
    "漆器": "1002227556088283136",
    "金属": "969252830474928128",
    "玉石": "1002227492125147136"
}

# 遍历每个类别
for category_name, type_ in categories.items():
    print(f"正在抓取 {category_name} 数据...")
    
    # 初始化一个空列表，用于存储所有分页的数据
    all_data = []
    
    # 第一次请求，获取总页数
    first_page_data = fetch_data(
        current=1,
        size=500,
        search='',
        year='',
        type_=type_,
        image='',
        threeType='否',
    )
    
    if not first_page_data.get('status'):
        print(f"{category_name} 数据请求失败，跳过该类别。")
        continue
    
    # 获取总页数
    total_pages = int(first_page_data.get('data', {}).get('pages', 1))
    print(f"{category_name} 总页数: {total_pages}")
    
    # 将第一页的数据添加到 all_data 中
    if first_page_data.get('data', {}).get('records'):
        all_data.extend(first_page_data['data']['records'])
    
    # 从第二页开始抓取剩余页的数据
    for page in range(2, total_pages + 1):
        print(f"正在抓取第 {page} 页数据...")
        
        # 调用 fetch_data 获取当前页的数据
        data = fetch_data(
            current=page,
            size=500,
            search='',
            year='',
            type_=type_,
            image='',
            threeType='否',
        )
        
        # 将当前页的数据添加到 all_data 中
        if data.get('status') and data.get('data', {}).get('records'):
            all_data.extend(data['data']['records'])
        else:
            print(f"第 {page} 页数据为空或请求失败，跳过该页。")
    
    # 将抓取到的所有数据保存到 Excel 文件
    if all_data:
        # 定义输出文件路径
        output_file = f'data/省博/{category_name}.xlsx'
        
        # 调用 parse_and_save_to_excel 保存数据
        parse_and_save_to_excel({'status': True, 'msg': 'success', 'data': {'records': all_data}}, output_file)
        
        print(f"{category_name} 数据已保存到 {output_file}\n")
    else:
        print(f"{category_name} 数据为空，未生成文件。\n")

print("所有类别数据抓取完成！")