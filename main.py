import asyncio
import io
import re
import json
import os
import sys
import webbrowser
import threading
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import docx
import pdfplumber
import openai
from openai import AsyncOpenAI

app = FastAPI()

def get_resource_path(relative_path):
    """PyInstaller 打包后使用 sys._MEIPASS 定位资源，开发时使用当前目录"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

class ExtractRequest(BaseModel):
    text: str
    api_key: str = None
    base_url: str = None
    model: str = None

def split_text_by_safe_boundary(text: str, max_length: int = 2000) -> list[str]:
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_length = 0

    # 预判下一行是新题目的正则（如：1. 1、 1． 一、）
    question_pattern = re.compile(r'^\s*(\d+[\.、．]|[一二三四五六七八九十]+[、])')

    for i, line in enumerate(lines):
        current_chunk.append(line)
        current_length += len(line) + 1  # +1 for newline

        # 如果接近或超过 max_length，开始寻找安全边界
        if current_length >= max_length:
            # 边界1：遇到连续空行
            # 边界2：下一行是新题目的开头
            is_boundary = False
            
            # 判断当前行是否为空行，或者是文件末尾
            if not line.strip() or i == len(lines) - 1:
                is_boundary = True
            elif i + 1 < len(lines):
                next_line = lines[i + 1]
                if question_pattern.match(next_line):
                    is_boundary = True

            if is_boundary:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_length = 0

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks

def clean_text(text: str) -> str:
    """
    清理文本：
    1. 统一换行符为 \n
    2. 保留 \n 的前提下，去除多余的连续空白符（如空格、制表符等）
    3. 去除每行首尾的空格
    """
    # 统一换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 将除了换行符以外的连续空白符替换为一个空格
    # [^\S\n] 匹配任何空白字符（[^\S]）但不匹配换行符（\n）
    text = re.sub(r'[^\S\n]+', ' ', text)
    
    # 进一步清理每一行首尾的空格
    cleaned_lines = [line.strip() for line in text.split('\n')]
    
    return '\n'.join(cleaned_lines)

@app.post("/api/upload_and_read")
async def upload_and_read(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
        
    filename = file.filename.lower()
    content = await file.read()
    
    extracted_text = ""
    
    try:
        if filename.endswith(".docx"):
            doc = docx.Document(io.BytesIO(content))
            extracted_text = '\n'.join([para.text for para in doc.paragraphs])
            
        elif filename.endswith(".pdf"):
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages_text = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                extracted_text = '\n'.join(pages_text)
                
        else:
            raise HTTPException(status_code=400, detail="仅支持 .docx 和 .pdf 文件格式")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析文件失败: {str(e)}")
        
    # 清理文本空白符并返回长字符串
    final_text = clean_text(extracted_text)
    
    return {"text": final_text}

@app.post("/api/extract_to_json")
async def extract_to_json(req: ExtractRequest):
    system_prompt = """你是一个严格的试卷数据清洗器。请从下述文本中识别出所有的题目。不要自己编造题目，仅做格式转换。
将识别到的内容严格输出为如下 JSON 格式：
{"questions": [{"id": 1, "type": "single", "content": "提取到的题干", "options": ["A. 选项", "B. 选项"], "answer": "提取到的答案(如果有)", "analysis": "提取到的解析(如果有)"}]}

支持的题型(type)及规则如下：
1. "single" (单选题): 必须提取选项放入 options 数组。
2. "multiple" (多选题): 必须提取选项放入 options 数组。
3. "judge" (判断题): options 通常设为 ["正确", "错误"]，或根据原文选项提取。
4. "fill" (填空题): options 必须设为空数组 []。
(如有简答题可设为 "essay"，options 设为空数组 [])。

【绝对指令】
你必须直接输出纯净的 JSON 字符串！
不要输出任何前言、后记、解释！
必须确保 JSON 格式合法（所有的双引号闭合正确，不要包含未转义的特殊字符）。"""
    
    try:
        api_key = req.api_key or os.environ.get("OPENAI_API_KEY")
        base_url = req.base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model_name = req.model or os.environ.get("LLM_MODEL", "gpt-3.5-turbo")

        if not api_key:
            raise HTTPException(status_code=400, detail="未提供 API Key，请在设置中填写")

        local_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )

        chunks = split_text_by_safe_boundary(req.text, max_length=2000)
        all_questions = []

        chunk_prompt = system_prompt + "\n\n【注意】这是长试卷的一个片段，请提取这部分包含的完整题目。如果这个片段全是废话或没有题目，请直接返回 {\"questions\": []}，不要捏造。"

        async def process_chunk(chunk_text):
            try:
                response = await local_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": chunk_prompt},
                        {"role": "user", "content": chunk_text}
                    ],
                    temperature=0.1,
                    max_tokens=8192
                )
                
                raw_result = response.choices[0].message.content
                
                # 强力清理 <think>...</think>
                clean_text = re.sub(r'<think>[\s\S]*?</think>', '', raw_result, flags=re.IGNORECASE).strip()
                
                # 匹配 markdown
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', clean_text, re.IGNORECASE)
                if match:
                    clean_text = match.group(1).strip()
                else:
                    first_brace = clean_text.find('{')
                    last_brace = clean_text.rfind('}')
                    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                        clean_text = clean_text[first_brace:last_brace+1]
                
                # 清除可能导致 parse 失败的非法换行
                clean_text = re.sub(r'[\n\r\t]+', ' ', clean_text)
                
                parsed_json = json.loads(clean_text)
                return parsed_json.get("questions", [])
            except openai.AuthenticationError:
                raise HTTPException(status_code=401, detail="大模型 API 调用失败：API Key 错误或无权限")
            except openai.RateLimitError:
                raise HTTPException(status_code=429, detail="大模型 API 调用失败：余额不足或请求频率超载")
            except Exception as e:
                print(f"Chunk processing error: {e}")
                return [] # 局部失败不阻断整体，返回空列表

        # 限制并发数处理，避免触发大模型速率限制
        sem = asyncio.Semaphore(2)
        async def sem_process(chunk):
            async with sem:
                return await process_chunk(chunk)

        tasks = [sem_process(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks)

        for q_list in results:
            if isinstance(q_list, list):
                all_questions.extend(q_list)

        # 重新编排 ID
        for idx, q in enumerate(all_questions):
            q["id"] = idx + 1

        return {"questions": all_questions}
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

# ========== 静态文件挂载（必须放在所有 /api 路由的最下方） ==========
dist_path = get_resource_path('dist')
assets_path = os.path.join(dist_path, 'assets')

if os.path.isdir(assets_path):
    app.mount('/assets', StaticFiles(directory=assets_path), name='static-assets')

@app.get('/{catchall:path}')
async def serve_frontend(catchall: str):
    """Vue SPA 通配符路由：所有未匹配 /api 的请求都返回 index.html"""
    index_file = os.path.join(dist_path, 'index.html')
    # 先尝试返回 dist 目录下的具体文件（如 favicon.ico 等）
    requested = os.path.join(dist_path, catchall)
    if os.path.isfile(requested):
        return FileResponse(requested)
    # 否则返回 index.html 支持 Vue Router History 模式
    if os.path.isfile(index_file):
        return FileResponse(index_file)
    return {"detail": "Frontend not built. Run 'npm run build' first."}

# ========== EXE 启动入口 ==========
if __name__ == '__main__':
    import uvicorn
    print('='*50)
    print('  智能做题系统 正在启动...')
    print('  浏览器将自动打开: http://127.0.0.1:8000')
    print('  关闭此窗口即可停止服务')
    print('='*50)
    threading.Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:8000')).start()
    uvicorn.run(app, host='127.0.0.1', port=8000)
