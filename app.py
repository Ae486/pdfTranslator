import gradio as gr
import os
import base64
from main import run_full_process

# --- 全局设置 ---
OUTPUT_DIR = "web_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# --- Gradio 应用逻辑 ---

def create_pdf_embed_html(filepath):
    """根据文件路径，读取文件内容并生成用于嵌入PDF的Base64数据URI"""
    if not filepath or not os.path.exists(filepath):
        return "<div style='text-align:center; padding: 20px;'>PDF文件不存在或路径错误</div>"
    
    try:
        with open(filepath, "rb") as pdf_file:
            base64_pdf = base64.b64encode(pdf_file.read()).decode('utf-8')
        
        # 使用 <iframe> 和 Base64 数据URI来嵌入PDF
        return f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px" style="border: none;"></iframe>'
    except Exception as e:
        return f"<div style='text-align:center; padding: 20px;'>无法加载PDF进行预览: {e}</div>"

def show_uploaded_pdf(pdf_file):
    """当文件被上传时触发，显示原始PDF，并更新状态"""
    if pdf_file is None:
        return None, None
    new_path = pdf_file.name
    # 返回原始路径用于状态存储，和嵌入式HTML用于预览
    return new_path, create_pdf_embed_html(new_path)


def update_preview(choice, original_path, result_path):
    """根据单选按钮的选择，更新PDF预览窗口"""
    if choice == "原文件":
        return create_pdf_embed_html(original_path)
    elif choice == "翻译结果":
        return create_pdf_embed_html(result_path)
    return "<div><p style='text-align:center; padding: 20px;'>请选择一个文件进行预览</p></div>"


def process_pdf_from_web(pdf_file, skip_translation, keep_intermediate):
    """
    Web界面调用的主函数。这是一个生成器，逐步yield更新给Gradio界面。
    """
    if pdf_file is None:
        # gr.Warning("请先上传一个PDF文件！") # 新版Gradio的提示方式
        yield "错误：请先上传一个PDF文件。", None, gr.update(), gr.update(), None
        return

    log_history = ""
    final_pdf_path = None
    
    try:
        process_generator = run_full_process(
            pdf_file=pdf_file.name,
            output_dir=OUTPUT_DIR,
            skip_translation=skip_translation,
            keep_intermediate=keep_intermediate
        )
        
        while True:
            try:
                log_message = next(process_generator)
                log_history += log_message + "\n"
                # 在处理过程中，只更新日志区域
                yield log_history, gr.update(), gr.update(), gr.update(), gr.update()
            except StopIteration as e:
                final_pdf_path = e.value
                break
        
        # 处理完成，更新所有相关的输出组件
        yield log_history, final_pdf_path, create_pdf_embed_html(final_pdf_path), "翻译结果", final_pdf_path

    except Exception as e:
        import traceback
        error_message = f"处理过程中发生严重错误: {e}\n{traceback.format_exc()}"
        log_history += error_message
        yield log_history, None, None, gr.update(), None


# --- Gradio 界面定义 ---
with gr.Blocks(title="PDF处理工具", theme=gr.themes.Soft()) as demo:
    # 隐藏的状态，用于存储文件路径
    original_pdf_path_state = gr.State()
    result_pdf_path_state = gr.State()

    gr.Markdown("# PDF 转换、翻译与预览工具")
    
    with gr.Row():
        # --- 左侧控制面板 ---
        with gr.Column(scale=1, min_width=300):
            pdf_input = gr.File(label="上传PDF文件", file_types=[".pdf"])
            gr.Markdown("### 处理选项")
            skip_translation_checkbox = gr.Checkbox(label="跳过翻译步骤", value=False)
            keep_intermediate_checkbox = gr.Checkbox(label="保留中间文件 (.md, .html)", value=False)
            run_button = gr.Button("开始处理", variant="primary", scale=2)

        # --- 右侧显示区域 ---
        with gr.Column(scale=3):
            gr.Markdown("### 预览窗口")
            view_selector = gr.Radio(
                ["原文件", "翻译结果"], value="原文件", label="选择预览内容"
            )
            pdf_preview = gr.HTML(label="PDF预览")
            
            gr.Markdown("### 处理日志")
            log_output = gr.Textbox(
                label="日志", lines=10, interactive=False, autoscroll=True
            )
            
            gr.Markdown("### 下载结果")
            pdf_output = gr.File(label="下载处理后的PDF", interactive=False)

    # --- 事件监听与绑定 ---
    
    # 1. 上传文件后，更新预览和原始文件路径状态
    pdf_input.upload(
        fn=show_uploaded_pdf,
        inputs=[pdf_input],
        outputs=[original_pdf_path_state, pdf_preview]
    )
    
    # 2. 点击单选按钮，切换预览内容
    view_selector.change(
        fn=update_preview,
        inputs=[view_selector, original_pdf_path_state, result_pdf_path_state],
        outputs=[pdf_preview]
    )
    
    # 3. 点击"开始处理"按钮，执行主流程
    run_button.click(
        fn=process_pdf_from_web,
        inputs=[pdf_input, skip_translation_checkbox, keep_intermediate_checkbox],
        outputs=[
            log_output, 
            pdf_output, 
            pdf_preview, 
            view_selector, 
            result_pdf_path_state
        ]
    )

if __name__ == "__main__":
    demo.launch(inbrowser=True) 