import os
import json
import pandas as pd
import logging
from dify_api.apis import get_llm_result

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_data_from_excel(file_path):
    """
    从指定的Excel文件路径中读取数据，并返回DataFrame。

    参数:
    file_path (str): Excel文件的路径。

    返回:
    pd.DataFrame: 读取到的数据内容。
    """
    try:
        data = pd.read_excel(file_path)
        return data
    except FileNotFoundError as e:
        logging.error(f"文件未找到错误: {e}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"读取Excel文件时出现其他错误: {e}")
        return pd.DataFrame()

def parse_image_field(image_value):
    """
    解析 Image 字段的值，返回第一个有效的 URL。
    """
    if pd.isna(image_value) or not image_value:
        return None

    # 尝试解析为 JSON 数组
    try:
        image_urls = json.loads(image_value)
        if isinstance(image_urls, list) and len(image_urls) > 0:
            return image_urls[0]  # 返回第一个 URL
    except json.JSONDecodeError:
        pass  # 如果不是 JSON 数组，继续尝试其他逻辑

    # 如果直接是 URL 字符串，直接返回
    if isinstance(image_value, str) and image_value.startswith(("http://", "https://")):
        return image_value

    # 如果无法解析，返回 None
    return None

def process_data(data, user_id, api_key, base_url):
    """
    处理给定的DataFrame数据，调用API获取结果并更新DataFrame内容。

    参数:
    data (pd.DataFrame): 需要处理的数据。
    user_id (str): 用户标识。
    api_key (str): API密钥。
    base_url (str): 服务的基础URL。

    返回:
    pd.DataFrame: 更新后的DataFrame数据。
    """
    # for i in range(len(data)):
    for i in range(10):
        logging.info(f"处理数据行 {i}")
        try:
            row = data.iloc[i]
            row = row.where(pd.notnull(row), None)

            # 清理输入数据
            # inputs = {
            #     "Name": row['Name'] if pd.notna(row['Name']) else "未知",
            #     "Category": row['Category'] if pd.notna(row['Category']) else "未知",
            #     "Dynasty": row['Dynasty'] if pd.notna(row['Dynasty']) else "未知",
            #     "Describe": row['Description'] if pd.notna(row['Description']) else "未知",
            # }
            # img only
            inputs = {}

            # 调用 API
            result = get_llm_result(
                api_key=api_key,
                inputs=inputs,
                user_id=user_id,
                image_url=row['Image'],
                upload_file_id=None,
                workflow_url=base_url + "/workflows/run"
            )

            if result:
                result = result["data"]['outputs']
                if "text" in result and "data" in result["text"]:
                    res = result["text"]["data"]
                    Name = res.get("Name", row['Name'])
                    Category = res.get("Category", row['Category'])
                    Dynasty = res.get("Dynasty", row['Dynasty'])
                    Describe = res.get("Describe", row['Description'])
                    MotifAndPattern = res.get("MotifAndPattern", "未知")
                    FormAndStructure = res.get("FormAndStructure", "未知")

                    # 解析 Image 字段
                    image_url = parse_image_field(row['Image'])
                    data.loc[i, 'Image'] = image_url

                    # 更新数据
                    data.loc[i, 'Name'] = Name
                    data.loc[i, 'Category'] = Category
                    data.loc[i, 'Dynasty'] = Dynasty
                    data.loc[i, 'Description'] = Describe
                    data.loc[i, 'MotifAndPattern'] = str(MotifAndPattern)
                    data.loc[i, 'FormAndStructure'] = str(FormAndStructure)

        except (KeyError, TypeError, SyntaxError) as e:
            logging.error(f"处理数据行 {i} 时出现错误: {e}，跳过该行处理")
            continue
        except Exception as e:
            logging.error(f"处理数据行 {i} 时出现未知错误: {e}，跳过该行处理")
            continue

    return data

if __name__ == "__main__":
    # 从环境变量中读取配置
    user_id = os.getenv("USER_ID", "请输入user_id")
    api_key = os.getenv("API_KEY", "请输入api_key")
    base_url = os.getenv("BASE_URL", "请输入服务的URL")

    # 读取原始数据
    file_path = "/Users/wujean/workspace/wjd/wenwu/data/省博/陶瓷.xlsx"
    data = read_data_from_excel(file_path)
    if not data.empty:
        # 处理数据
        updated_data = process_data(data, user_id, api_key, base_url)
        # 将更新后的数据保存到新的Excel文件
        updated_data.to_excel("/Users/wujean/workspace/wjd/wenwu/data/test/test.xlsx", index=False)