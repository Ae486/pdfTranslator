import os
import sys
import json
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pdf_to_markdown import pdf_to_markdown

app = Flask(__name__)

# 设置上传文件存储位置
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'converted'
ALLOWED_EXTENSIONS = {'pdf'}

# 创建必要的目录
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传大小为16MB

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """API首页"""
    return '''
    <html>
        <head>
            <title>PDF转Markdown工具</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                form { background: #f5f5f5; padding: 20px; border-radius: 5px; }
                .submit-btn { background: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
                .submit-btn:hover { background: #45a049; }
            </style>
        </head>
        <body>
            <h1>PDF转Markdown工具</h1>
            <form action="/convert" method="post" enctype="multipart/form-data">
                <p><input type="file" name="file" accept=".pdf" required></p>
                <p><input type="submit" value="开始转换" class="submit-btn"></p>
            </form>
        </body>
    </html>
    '''

@app.route('/convert', methods=['POST'])
def convert_pdf():
    """处理PDF转换请求"""
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
    
    file = request.files['file']
    
    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'}), 400
    
    # 检查文件类型
    if not allowed_file(file.filename):
        return jsonify({'status': 'error', 'message': '不支持的文件类型，只允许PDF文件'}), 400
    
    try:
        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 创建唯一的输出目录
        name_without_ext = os.path.splitext(filename)[0]
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], name_without_ext)
        
        # 转换PDF到Markdown
        result = pdf_to_markdown(file_path, output_dir)
        
        if result['status'] == 'success':
            # 返回成功响应和下载链接
            markdown_filename = os.path.basename(result['markdown'])
            download_url = f"/download/{name_without_ext}/{markdown_filename}"
            
            return jsonify({
                'status': 'success',
                'message': 'PDF转换成功',
                'download_url': download_url,
                'markdown_filename': markdown_filename
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('message', '转换过程中发生错误')
            }), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500

@app.route('/download/<folder>/<filename>')
def download_file(folder, filename):
    """下载转换后的文件"""
    directory = os.path.join(app.config['OUTPUT_FOLDER'], folder)
    return send_file(os.path.join(directory, filename), as_attachment=True)

@app.route('/api/convert', methods=['POST'])
def api_convert():
    """API接口，用于程序调用"""
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有上传文件'}), 400
    
    file = request.files['file']
    
    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '未选择文件'}), 400
    
    # 检查文件类型
    if not allowed_file(file.filename):
        return jsonify({'status': 'error', 'message': '不支持的文件类型，只允许PDF文件'}), 400
    
    try:
        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 创建唯一的输出目录
        name_without_ext = os.path.splitext(filename)[0]
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], name_without_ext)
        
        # 转换PDF到Markdown
        result = pdf_to_markdown(file_path, output_dir)
        
        # 返回处理结果
        return jsonify(result)
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'服务器错误: {str(e)}'}), 500

if __name__ == '__main__':
    # 获取端口参数，默认为5000
    port = int(os.environ.get('PORT', 5000))
    
    # 启动服务
    print(f"PDF转Markdown服务已启动，访问 http://localhost:{port}/ 使用")
    app.run(host='0.0.0.0', port=port, debug=True) 