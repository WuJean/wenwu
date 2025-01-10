import gradio as gr
import os
from dify_api.apis import *
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中读取配置
user_id = os.getenv("USER_ID", "请输入user_id")
api_key = os.getenv("API_KEY", "请输入api_key")
base_url = os.getenv("BASE_URL", "请输入服务的URL")

# 创建 Gradio 界面
with gr.Blocks() as demo:
    gr.Markdown("### 文物信息录入系统")

    # 创建 Gradio 组件
    with gr.Row():
        api_key = gr.Textbox(label="API Key", type="text", value=api_key)  # 预填充环境变量的值
        user_id = gr.Textbox(label="User ID", type="text", value=user_id)  # 预填充环境变量的值
        base_url = gr.Textbox(label="Base URL", type="text", value=base_url)  # 预填充环境变量的值

    with gr.Row():
        upload_type = gr.Radio([
            "url",
            "local_file"
        ], value="url", label="选择上传方式",)
        image_input = gr.Image(label="上传本地图片", type="filepath", visible=False)
        image_url_input = gr.Textbox(label="图片 URL", visible=True)
        upload_status = gr.Textbox(label="上传状态", interactive=False)
        image_identifier = gr.Textbox(label="图片标识", interactive=False, visible=False)

    with gr.Row():
        artifact_name = gr.Textbox(label="文物名称*", placeholder="请输入文物名称")
        category = gr.Textbox(label="文物分类*", placeholder="请输入文物分类")
        dynasty = gr.Textbox(label="年代*", placeholder="请输入文物年代")
    describe = gr.Textbox(label="描述*", lines=3, placeholder="请输入描述")

    submit_button = gr.Button("提交")
    result_status = gr.Textbox(label="处理状态", interactive=False,visible=False)
    with gr.Row():
        MotifAndPattern_tags = gr.HTML(label="文物标签")
        FormAndStructure_tags = gr.HTML(label="文物标签")

    # 动态切换输入方式
    def toggle_input(upload_type):
        return gr.update(visible=(upload_type == "local_file")), gr.update(visible=(upload_type == "url"))

    upload_type.change(
        fn=toggle_input,
        inputs=[upload_type],
        outputs=[image_input, image_url_input]
    )

    # 上传图片
    def upload_and_refresh(api_key, user_id, base_url, image_input, image_url_input):
        # 调用上传图片的函数
        image_id, status = upload_image_and_get_id(api_key, user_id, base_url, image_input, image_url_input)
        
        # 返回结果并刷新页面
        return image_id, status, gr.update(value=""), gr.update(value=""), gr.update(value=""), gr.update(value=""), gr.update(value=""), gr.update(value="")

    image_input.change(
        fn=upload_and_refresh,
        inputs=[api_key, user_id, base_url, image_input, image_url_input],
        outputs=[image_identifier, upload_status, artifact_name, category, dynasty, describe, MotifAndPattern_tags, FormAndStructure_tags]
    )
    image_url_input.change(
        fn=upload_and_refresh,
        inputs=[api_key, user_id, base_url, image_input, image_url_input],
        outputs=[image_identifier, upload_status, artifact_name, category, dynasty, describe, MotifAndPattern_tags, FormAndStructure_tags]
    )

    # 提交并获取结果
    submit_button.click(
        fn=process_and_get_result,
        # fn=process_and_get_result_mock,
        inputs=[
            image_identifier, artifact_name, category, dynasty, describe, upload_type, api_key, user_id, base_url
        ],
        outputs=[result_status, artifact_name, category, dynasty, describe, MotifAndPattern_tags, FormAndStructure_tags]
    )

# 启动 Gradio 应用
if __name__ == "__main__":
    demo.launch()