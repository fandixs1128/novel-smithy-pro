import streamlit as st
import requests
import re
import time
import os
import shutil
import hashlib
import datetime

# ================= 1. 页面配置 =================

st.set_page_config(
    page_title="狡猾的老虎救救孩子", # 浏览器标签页标题
    page_icon="🐸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BACKEND_URL = "http://127.0.0.1:8000"
HISTORY_DIR = "./history_cache"

st.markdown("""
<style>
    /* 隐藏顶部干扰 */
    header[data-testid="stHeader"] {display: none !important;}
    .stDeployButton {display: none !important;}
    footer {visibility: hidden;}
    
    .stApp { background-color: #FAFAFA; }
    
    /* 标题样式定制 */
    .title-box {text-align: center; margin-bottom: 20px;}
    .title-main {font-size: 36px; font-weight: 800; color: #2c3e50; font-family: 'Microsoft YaHei', sans-serif;}
    .title-badge {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%); /* 青蛙绿 */
        color: white; 
        padding: 4px 12px; 
        border-radius: 20px; 
        font-size: 14px; 
        vertical-align: middle;
        margin-left: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* 对照框样式 */
    div[data-testid="stText"] {
        background-color: #F3F4F6; padding: 15px; border-radius: 8px; border: 1px solid #E5E7EB; 
        color: #374151; font-family: 'Georgia', serif; line-height: 1.6; white-space: pre-wrap; font-size: 14px;
    }
    
    /* 按钮与输入框 */
    .stButton button {border-radius: 8px; font-weight: bold;}
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important; border: 1px solid #E5E7EB !important; border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. 完整题材列表 (25个) =================

GENRE_MAP = {
    "⛓️ BDSM": "Genre: BDSM/Dark Romance. Key Elements: Dominance/Submission, Power exchange, Safe words. Style: Intense, psychological, sensory.",
    "🏢 办公室恋情 (Office Romance)": "Genre: Office Romance. Key Elements: CEO/Secretary, Forbidden relationship, Professional tension. Style: Snappy dialogue, stolen glances.",
    "👻 超自然 (Paranormal)": "Genre: Paranormal Romance. Key Elements: Ghosts, Magic, Unexplained phenomena. Style: Eerie, atmospheric, mysterious.",
    "🤰 带球跑 (Secret Baby)": "Genre: Secret Baby Trope. Key Elements: Hidden child, Single mother, Reunion after years. Style: Heart-wrenching, dramatic.",
    "🔥 复仇 (Revenge)": "Genre: Revenge Thriller. Key Elements: Betrayal, Calculated comeback, Face-slapping justice. Style: Cold, satisfying, sharp.",
    "🕶️ 黑手党 (Mafia)": "Genre: Mafia Romance. Key Elements: Crime lord, Danger, Loyalty vs Love, Possessiveness. Style: Gritty, high-stakes, dark.",
    "🧚 幻想 (Fantasy)": "Genre: High Fantasy. Key Elements: Magic systems, World-building, Destiny. Style: Epic, descriptive, formal tone.",
    "💍 婚恋言情 (Marriage)": "Genre: Domestic/Marriage Romance. Key Elements: Married life struggles, Intimacy, Daily life. Style: Realistic, slow-burn, warm.",
    "🚫 禁忌爱情 (Taboo)": "Genre: Taboo Romance. Key Elements: Forbidden relationship, Moral conflict, Guilt. Style: Tense, passionate, internal conflict.",
    "🐺 狼人 (Werewolf)": "Genre: Werewolf Romance. Key Elements: Alpha/Luna dynamic, Mate bond, Pack politics, Pheromones. Style: Visceral, intense, primal.",
    "👑 逆后宫 (Reverse Harem)": "Genre: Reverse Harem. Key Elements: One female lead/Multiple male interests, Distinct male archetypes. Style: Indulgent, character-focused.",
    "📉 年龄差 (Age Gap)": "Genre: Age Gap Romance. Key Elements: Maturity difference, Forbidden feel, Caretaking/Pampering. Style: Intimate, guiding.",
    "💔 虐恋 (Angst)": "Genre: High Angst/Abuse. Key Elements: Emotional torture, Misunderstanding, Unrequited love. Style: Heavy, tear-jerking, descriptive.",
    "📜 契约婚姻 (Contract Marriage)": "Genre: Contract Marriage. Key Elements: Fake relationship, Rules, Falling in love accidentally. Style: Transactional turning emotional.",
    "📐 三角恋 (Love Triangle)": "Genre: Love Triangle. Key Elements: Jealousy, Rivalry, Hard choices. Style: Conflicted, dramatic tension.",
    "🔞 色情 (Erotica)": "Genre: Erotica/Smut. Key Elements: Physical intimacy, Sensory details, Desire. Style: Explicit, focused on sensation (NSFW).",
    "🧛 吸血鬼 (Vampire)": "Genre: Vampire Romance. Key Elements: Bloodlust, Immortality, Predator/Prey dynamic. Style: Seductive, dangerous, gothic.",
    "💍 先婚后爱 (Arranged Marriage)": "Genre: Arranged Marriage. Key Elements: Strangers to lovers, Duty, Slow realization of feelings. Style: Awkward to sweet.",
    "🏫 校园言情 (Campus)": "Genre: Campus/School Romance. Key Elements: First love, Crushes, School hierarchy, Bullying. Style: Youthful, energetic, innocent.",
    "🌙 一夜情 (One Night Stand)": "Genre: One Night Stand. Key Elements: Impulse, Regret, Physical attraction, Awkward morning after. Style: Fast-paced, physical.",
    "💰 亿万富翁 (Billionaire)": "Genre: Billionaire Romance. Key Elements: Extreme wealth, Luxury, Cinderella trope, Arrogance. Style: Lavish, dramatic, soapy.",
    "👸 真假千金 (Identity Swap)": "Genre: Identity Swap/Real vs Fake Heiress. Key Elements: Family drama, Jealousy, Birthright secrets. Style: Dramatic, confrontational.",
    "🔄 重生 (Rebirth)": "Genre: Rebirth/Second Chance. Key Elements: Foresight, Regret, Changing fate, Avoiding past mistakes. Style: Reflective, determined.",
    "🔥 追妻火葬场 (Groveling)": "Genre: Groveling/Regretful Male Lead. Key Elements: Male lead messed up, Female lead cold, Desperate redemption. Style: Desperate, emotional.",
    "🏰 总裁豪门 (CEO/Wealthy)": "Genre: Wealthy Family Drama. Key Elements: Inheritance wars, Business power plays, Dominant CEO. Style: Dominant, luxurious."
}

# ================= 3. 逻辑函数 =================

def intelligent_chapter_split(text):
    pattern = r'(?:^\s*(?:Chapter|Part|Scene|Episode|Prologue|Epilogue|第[0-9一二三四五六七八九十百]+[章回]).*?$|^\s*\d+\.\s*.*?$)'
    parts = re.split(f"({pattern})", text, flags=re.MULTILINE)
    chapters = []
    current_chapter = ""
    if len(parts) < 3: return None 
    for part in parts:
        if re.match(pattern, part, flags=re.MULTILINE):
            if current_chapter.strip(): chapters.append(current_chapter.strip())
            current_chapter = part
        else: current_chapter += part
    if current_chapter.strip(): chapters.append(current_chapter.strip())
    return chapters

def fallback_split(text, limit=2000):
    return [text[i:i+limit] for i in range(0, len(text), limit)]

def get_cache_dir(filename):
    file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
    safe_name = re.sub(r'[^\w\-_\. ]', '_', filename)
    dir_path = os.path.join(HISTORY_DIR, f"{safe_name}_{file_hash}")
    if not os.path.exists(dir_path): os.makedirs(dir_path)
    return dir_path

def load_history(cache_dir, chunks):
    files = sorted([f for f in os.listdir(cache_dir) if f.startswith("chunk_") and f.endswith(".txt")], key=lambda x: int(x.split('_')[1].split('.')[0]))
    history_rewritten = []
    history_original = []
    last_index = -1
    for f in files:
        idx = int(f.split('_')[1].split('.')[0])
        with open(os.path.join(cache_dir, f), 'r', encoding='utf-8') as file: 
            history_rewritten.append(file.read())
        if chunks and idx < len(chunks):
            history_original.append(chunks[idx])
        last_index = idx
    return history_original, history_rewritten, last_index

def clear_cache(cache_dir):
    if os.path.exists(cache_dir): shutil.rmtree(cache_dir); os.makedirs(cache_dir)

# ================= 4. 界面构建 =================

# 🐸 定制标题 🐯
st.markdown("""
<div class="title-box">
    <span class="title-main">狡猾的老虎救救孩子</span>
    <span class="title-badge">之我是一个悲伤的青蛙版</span>
</div>
""", unsafe_allow_html=True)

# 顶部设置栏
c1, c2, c3 = st.columns([2, 1, 1])
with c1: 
    genre_key = st.selectbox("题材模式", list(GENRE_MAP.keys()))
with c2: 
    strength = st.select_slider("改写强度", options=["Low", "Medium", "High"], value="High")
with c3: 
    chunk_size = st.number_input("备用分段长度", 1000, 5000, 2500)

st.markdown("---")

# 左右分栏布局
col_left, col_right = st.columns([1, 2], gap="medium")

if "logs" not in st.session_state: st.session_state.logs = []
def add_log(msg): st.session_state.logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

# === 左栏：输入与控制 ===
with col_left:
    with st.expander("🔑 API 设置 (必填)", expanded=True):
        api_key = st.text_input("API Key", type="password")
        model = st.selectbox("Model", ["qwen-plus", "qwen-max", "qwen-long"], index=0, 
                           help="推荐使用 qwen-long 进行全本分析，支持超长上下文。")

    uploaded_file = st.file_uploader("上传 TXT", type="txt", label_visibility="collapsed")
    
    file_processed = False
    cache_dir = None
    chunks = []
    
    if uploaded_file:
        file_content = uploaded_file.getvalue().decode("utf-8")
        file_name = uploaded_file.name
        cache_dir = get_cache_dir(file_name)
        
        # 立即估算金额和字数
        try:
            est_payload = {"text": file_content}
            est_res = requests.post(f"{BACKEND_URL}/estimate", json=est_payload)
            if est_res.status_code == 200:
                est_data = est_res.json()
                st.info(f"📊 总字数: {est_data['length']}  |  💰 预估成本: ¥{est_data['cost']:.4f}")
            else:
                st.warning("⚠️ 无法连接后端进行估价")
        except:
            st.warning("⚠️ 后端未连接，无法估价")

        # --- 智能改名核心区域 ---
        with st.expander("🎭 角色更名 (全本智能识别)", expanded=True):
            if st.button("⚡ AI 自动分析全本并生成新名", help="点击后，AI将阅读整本小说，自动提取所有人名和昵称"):
                if not api_key:
                    st.error("请先输入 API Key")
                else:
                    with st.spinner("🤖 正在通读全书，分析人物关系与昵称..."):
                        try:
                            # 发送全本内容
                            an_payload = {
                                "api_key": api_key, "model": model, 
                                "text_sample": file_content, 
                                "genre": genre_key
                            }
                            an_res = requests.post(f"{BACKEND_URL}/analyze_names", json=an_payload)
                            if an_res.status_code == 200:
                                generated_map = an_res.json()["name_map"]
                                st.session_state["auto_names"] = generated_map
                                st.success("识别成功！")
                                time.sleep(0.5)
                                st.rerun() 
                            else:
                                st.error(f"分析失败: {an_res.text}")
                        except Exception as e:
                            st.error(f"连接错误: {e}")

            # 名字映射输入框
            default_names = st.session_state.get("auto_names", "")
            names_str = st.text_area("映射表 (自动填入/可修改)", value=default_names, height=150, 
                                   help="AI生成后会自动填入。格式：旧名=新名")
        
        # 分章处理
        detected = intelligent_chapter_split(file_content)
        if detected:
            chunks = detected
            st.success(f"✅ 智能分章：共 {len(chunks)} 章")
        else:
            chunks = fallback_split(file_content, chunk_size)
            st.warning(f"⚠️ 按字数分段：共 {len(chunks)} 段")
            
        file_processed = True
        
        # 缓存管理
        orig_hist, rewrite_hist, last_idx = load_history(cache_dir, chunks)
        if last_idx >= 0:
            st.info(f"📂 缓存进度：已完成 {last_idx + 1} 章")
            if st.button("♻️ 清除缓存并重写", type="secondary", use_container_width=True):
                clear_cache(cache_dir)
                st.session_state.pop("auto_names", None) 
                st.rerun()

    with st.expander("✨ 自定义指令"):
        custom_prompt = st.text_area("Prompt", height=80, label_visibility="collapsed")

    c_s, c_e = st.columns([3, 1])
    with c_s: start_btn = st.button("🚀 开始 / 继续", type="primary", use_container_width=True)
    with c_e: stop_btn = st.button("🛑 暂停", type="secondary", use_container_width=True)
    
    st.markdown("### 📟 日志")
    log_con = st.empty()
    log_con.code("\n".join(st.session_state.logs[-8:]), language="bash")

# === 右侧对照区 ===
with col_right:
    view_c1, view_c2 = st.columns(2)
    with view_c1: st.subheader("📄 原文")
    with view_c2: st.subheader("✨ 改写")
    
    orig_ph = view_c1.empty()
    rewr_ph = view_c2.empty()
    
    if file_processed:
        orig_hist, rewrite_hist, _ = load_history(cache_dir, chunks)
        full_orig = "\n\n".join(orig_hist)
        full_rewr = "\n\n".join(rewrite_hist)
        
        orig_ph.text_area("Orig", value=full_orig, height=600, label_visibility="collapsed")
        rewr_ph.text_area("Rewr", value=full_rewr, height=600, label_visibility="collapsed")
    else:
        orig_ph.info("等待上传...")
        rewr_ph.info("等待上传...")

# ================= 5. 执行循环 =================

if stop_btn: st.warning("已暂停")

if start_btn and file_processed and api_key:
    orig_hist, rewrite_hist, last_idx = load_history(cache_dir, chunks)
    buffer_orig = "\n\n".join(orig_hist)
    buffer_rewr = "\n\n".join(rewrite_hist)
    prev_context = rewrite_hist[-1][-400:] if rewrite_hist else ""
    start_idx = last_idx + 1
    total = len(chunks)
    
    if start_idx >= total:
        st.balloons()
    else:
        bar = st.progress(start_idx / total)
        for i in range(start_idx, total):
            chunk = chunks[i]
            add_log(f"正在改写第 {i+1} 章 ({len(chunk)}字)...")
            log_con.code("\n".join(st.session_state.logs[-8:]), language="bash")
            
            payload = {
                "api_key": api_key, "model": model, "text_chunk": chunk,
                "genre_prompt": GENRE_MAP.get(genre_key), "strength": strength,
                "custom_prompt": custom_prompt, "prev_context": prev_context,
                "name_map": names_str
            }
            
            try:
                res = requests.post(f"{BACKEND_URL}/rewrite_chunk", json=payload)
                if res.status_code == 200:
                    rewritten = res.json()["rewritten_text"]
                    
                    with open(os.path.join(cache_dir, f"chunk_{i}.txt"), 'w', encoding='utf-8') as f: 
                        f.write(rewritten)
                    
                    buffer_orig += "\n\n" + chunk
                    buffer_rewr += "\n\n" + rewritten
                    prev_context = rewritten[-400:]
                    
                    orig_ph.text_area("Orig", value=buffer_orig, height=600, label_visibility="collapsed")
                    rewr_ph.text_area("Rewr", value=buffer_rewr, height=600, label_visibility="collapsed")
                    add_log(f"✅ 第 {i+1} 章完成")
                else:
                    st.error(f"Error: {res.text}"); break
            except Exception as e: st.error(f"Connect Error: {e}"); break
            bar.progress((i+1)/total)
            
        with col_left: st.download_button("📥 下载全文", data=buffer_rewr, file_name=f"rewritten_{file_name}", type="primary")