import os
import pandas as pd
from dify_api.apis import get_llm_result, process_input


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
        print(f"文件未找到错误: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"读取Excel文件时出现其他错误: {e}")
        return pd.DataFrame()


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
    for i in range(len(data)):
        try:
            row = data.iloc[i]
            if row['Description'] == '未知':
                continue
            row = row.where(pd.notnull(row), None)
            inputs = {
                "Name": row['Name'],
                "Category": row['Category'],
                "Dynasty": row['Dynasty'],
                "Describe": row['Description']
            }
            result = get_llm_result(
                api_key=api_key,
                inputs=inputs,
                user_id=user_id,
                image_url=None,
                upload_file_id=None,
                workflow_url=base_url + "/workflows/run"
            )
            if result:
                result = result["data"]['outputs']
                if "text" in result and "data" in result["text"]:
                    res = result["text"]["data"]
                    Name = res.get("Name", "未知")
                    Category = res.get("Category", "未知")
                    Dynasty = res.get("Dynasty", "未知")
                    Describe = res.get("Describe", "未知")
                    MotifAndPattern = res.get("MotifAndPattern", "未知")
                    FormAndStructure = res.get("FormAndStructure", "未知")
                    image_urls = eval(row['Image'])
                    data.loc[i, 'Name'] = Name
                    data.loc[i, 'Category'] = Category
                    data.loc[i, 'Dynasty'] = Dynasty
                    data.loc[i, 'Description'] = Describe
                    data.loc[i, 'Image'] = image_urls[0]
                    data.loc[i, 'MotifAndPattern'] = str(MotifAndPattern)
                    data.loc[i, 'FormAndStructure'] = str(FormAndStructure)
        except (KeyError, TypeError, SyntaxError) as e:
            print(f"处理数据行 {i} 时出现错误: {e}，跳过该行处理")
            continue
        except Exception as e:
            print(f"处理数据行 {i} 时出现未知错误: {e}，跳过该行处理")
            continue
    return data


if __name__ == "__main__":
    # 从环境变量中读取配置
    user_id = os.getenv("USER_ID", "请输入user_id")
    api_key = os.getenv("API_KEY", "请输入api_key")
    base_url = os.getenv("BASE_URL", "请输入服务的URL")

    # 读取原始数据
    file_path = "/Users/wujean/workspace/wjd/wenwu/data/台北/青铜器.xlsx"
    data = read_data_from_excel(file_path)
    if not data.empty:
        # 处理数据
        updated_data = process_data(data, user_id, api_key, base_url)
        # 将更新后的数据保存到新的Excel文件
        updated_data.to_excel("/Users/wujean/workspace/wjd/wenwu/data/台北/青铜器_tag.xlsx", index=False)