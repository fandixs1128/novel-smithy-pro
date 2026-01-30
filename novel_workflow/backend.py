from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Backend is running!"}

# --- 数据模型定义 ---

class AnalyzeRequest(BaseModel):
    api_key: str
    model: str
    text_sample: str 
    genre: str

class RewriteRequest(BaseModel):
    api_key: str
    model: str
    text_chunk: str
    genre_prompt: str
    strength: str
    custom_prompt: str
    prev_context: str
    name_map: str

class EstimateRequest(BaseModel):
    text: str

# --- 接口 1: AI 智能分析名字 (这是你缺失的接口) ---
@app.post("/analyze_names")
def analyze_names(req: AnalyzeRequest):
    client = OpenAI(api_key=req.api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    # 分析指令
    system_prompt = f"""
    You are a Lead Editor analyzing a novel draft.
    TARGET GENRE: {req.genre}
    
    TASK:
    1. Identify Main Protagonists and key Side Characters.
    2. Identify Nicknames (e.g., 'Isabella' -> 'Bella').
    3. Generate NEW names that fit the '{req.genre}' genre.
    
    OUTPUT FORMAT (Strictly one per line, 'OldName=NewName'):
    Isabella=Seraphina
    Matteo=Dante
    
    RULES:
    - Only output the mapping list.
    - Map the MAIN name.
    """
    
    try:
        # 读取文本进行分析
        resp = client.chat.completions.create(
            model=req.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this text:\n\n{req.text_sample}"}
            ],
            temperature=0.7
        )
        return {"name_map": resp.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 接口 2: 估价 ---
@app.post("/estimate")
def estimate_cost(req: EstimateRequest):
    length = len(req.text)
    cost = (length / 1000) * 0.02
    return {"length": length, "cost": cost}

# --- 接口 3: 核心改写 ---
@app.post("/rewrite_chunk")
def rewrite_chunk(req: RewriteRequest):
    client = OpenAI(api_key=req.api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    # 强制改名指令
    renaming_instruction = ""
    if req.name_map and req.name_map.strip():
        renaming_instruction = "\n\n### 🔴 MANDATORY CHARACTER RENAMING\n"
        renaming_instruction += "You MUST rename the characters based on this list:\n"
        for line in req.name_map.split('\n'):
            if '=' in line:
                parts = line.split('=', 1)
                old = parts[0].strip()
                new = parts[1].strip()
                if old and new:
                    renaming_instruction += f"- REPLACE '{old}' WITH '{new}'\n"
        renaming_instruction += "⚠️ OUTPUT CONSTRAINT: Use ONLY the NEW names.\n"

    # 改写强度
    if req.strength == "High":
        base_instruction = "ACT AS A GHOSTWRITER. Rewrite completely. Change structure and pacing."
        temp = 0.95
    elif req.strength == "Medium":
        base_instruction = "Rewrite creatively. Enhance descriptions and flow."
        temp = 0.8
    else:
        base_instruction = "Polish the text. Fix grammar."
        temp = 0.7

    system_prompt = f"""You are a professional fiction writer.
{base_instruction}
TARGET GENRE: {req.genre_prompt}
{renaming_instruction}
"""
    
    user_prompt = f"""
    [Context]: ...{req.prev_context}
    [Original Text]:
    {req.text_chunk}
    [Extra Instructions]: {req.custom_prompt}
    """

    try:
        resp = client.chat.completions.create(
            model=req.model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=temp
        )
        return {"rewritten_text": resp.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)