"""
LLM 辅助模块 - 字幕优化和文案生成
"""
import os
import re
from typing import List, Dict, Optional
from openai import OpenAI


class LLMSubtitleRefiner:
    """使用 LLM 优化字幕和生成小红书文案"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        """
        初始化 LLM 客户端
        
        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.base_url = base_url

    def optimize_subtitle(self, srt_content: str, humor_level: str = "none") -> str:
        """
        优化字幕内容：修正错别字、标点符号、断句，使其更流畅。
        支持知识类内容的专业纠错，以及可选的趣味性增强。
        
        Args:
            srt_content: 原始 SRT 字幕文本
            humor_level: 趣味级别
                - "none": 仅纠错
                - "moderate": 适度趣味
                - "high": 幽默风趣
        
        Returns:
            优化后的 SRT 字幕文本
        """
        
        # 分块处理
        lines = srt_content.strip().split('\n\n')
        chunks = []
        current_chunk = []
        
        for line in lines:
            if len(current_chunk) >= 20: # 每 20 个字幕块处理一次
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
            current_chunk.append(line)
        
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
            
        optimized_srt = ""
        print(f"开始优化字幕，模式: {humor_level}，共 {len(chunks)} 个分块...")
        
        # 构建 System Prompt
        system_prompt = "你是一个专业的知识类视频字幕编辑专家。"
        
        base_instruction = """
**核心任务：**
1.  **精准纠错**：修正语音识别中的错别字、同音词错误（特别是专业术语）。
2.  **口语顺滑**：去除无意义的口头禅（如“那个”、“呃”、“就是说”），将过于口语化的表达修改为书面语或流畅的口语，但保持原意不变。
3.  **标点规范**：添加符合中文语法的标点符号。
4.  **格式严格**：**绝对保持** SRT格式（序号、时间轴）完全不变！不要合并或拆分时间轴。
"""

        humor_instruction = ""
        if humor_level == "moderate":
            humor_instruction = """
**趣味增强（适度）：**
- 在不改变原意和专业性的前提下，适当使用 1-2 个网络热梗或幽默表达来活跃气氛。
- 可以在括号中添加简短的吐槽或补充说明，例如：(这里翻车了)、(划重点)。
"""
        elif humor_level == "high":
            humor_instruction = """
**趣味增强（高）：**
- 风格更加活泼幽默，多用网络流行语。
- 对于枯燥的知识点，尝试用生动的比喻或段子来解释。
- 积极使用括号添加“内心戏”或“官方吐槽”。
"""

        for i, chunk in enumerate(chunks):
            user_prompt = f"""
{base_instruction}
{humor_instruction}

**待优化字幕片段：**
{chunk}

**请直接输出优化后的 SRT 内容：**
"""
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.4 if humor_level == "none" else 0.7 # 趣味模式下增加随机性
                )
                optimized_chunk = response.choices[0].message.content.strip()
                # 清理可能的 markdown
                optimized_chunk = optimized_chunk.replace("```srt", "").replace("```", "")
                
                if i > 0:
                    optimized_srt += "\n\n"
                optimized_srt += optimized_chunk
                
            except Exception as e:
                print(f"分块 {i} 优化失败: {e}")
                # Fallback to original
                if i > 0:
                    optimized_srt += "\n\n"
                optimized_srt += chunk
                
        return optimized_srt

    def generate_study_note(self, srt_content: str) -> str:
        """
        根据字幕内容生成结构化知识笔记 (Markdown 格式)，适合小红书发布
        
        Args:
            srt_content: SRT 字幕文本内容
        
        Returns:
            小红书风格的 Markdown 文案
        """
        # 1. 预处理字幕：去除时间轴，提取纯文本
        simplified_lines = []
        lines = srt_content.split('\n\n')
        for block in lines:
            parts = block.split('\n')
            if len(parts) >= 3:
                # 假设 parts[2:] 都是文本（有时可能会有换行）
                text = " ".join(parts[2:])
                simplified_lines.append(text)
        
        full_text = "\n".join(simplified_lines)
        
        # 限制长度 (保留前 30000 字符)
        if len(full_text) > 30000:
            full_text = full_text[:30000] + "\n...(后续内容截断)"

        prompt = f"""
你是一个专业的小红书爆款文案写手。请将以下视频字幕内容整理成一篇**极具吸引力、符合小红书风格的图文笔记文案**。

**小红书文案风格要求 (重要)：**
1.  **标题 (Title)**：
    *   必须包含表情符号 (Emoji)。
    *   采用“二极管”标题法：制造焦虑、强列反差、干货预警、保姆级教程等风格。
    *   例如：“😭后悔没早点知道...”、“🔥保姆级教程！一文看懂...”、“绝了！😍...”。
    *   生成 3 个备选标题。

2.  **正文 (Content)**：
    *   **语气**：亲切、活泼、像闺蜜聊天，多用“宝子们”、“家人们”、“集美们”、“绝绝子”。
    *   **排版**：多分段，每段不超过 3 行。多用 Emoji (✨, 💡, 📌, ✅) 分割要点。
    *   **结构**：
        *   💡 **开头**：痛点引入 + 吸引眼球。
        *   📦 **干货**：提炼视频核心知识点，用列表形式清晰呈现。
        *   🎬 **结尾**：引导互动（“点赞收藏不迷路”、“评论区告诉我...”）。

3.  **标签 (Tags)**：
    *   文末添加 10-15 个热门话题标签 (Hashtags)，例如 #知识分享 #干货 #自媒体 #学习笔记 等。

**待整理内容：**
{full_text}

**输出格式：**
请直接输出整理后的文案内容，无需 Markdown 代码块标记。
"""
        try:
            print(f"正在调用 LLM 生成小红书文案: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的知识整理与写作助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM 生成知识笔记失败: {e}")
            return f"生成失败: {str(e)}"

    def generate_summary(self, srt_content: str) -> str:
        """
        根据字幕内容生成内容摘要，适合B站视频简介
        
        Args:
            srt_content: SRT 字幕文本内容
        
        Returns:
            100-200 字的内容摘要
        """
        # 预处理字幕：去除时间轴，提取纯文本
        simplified_lines = []
        lines = srt_content.split('\n\n')
        for block in lines:
            parts = block.split('\n')
            if len(parts) >= 3:
                text = " ".join(parts[2:])
                simplified_lines.append(text)
        
        full_text = "\n".join(simplified_lines)
        
        # 限制长度
        if len(full_text) > 15000:
            full_text = full_text[:15000] + "\n...(内容截断)"

        prompt = f"""
请根据以下视频字幕内容，生成一段简洁的视频简介。

**要求：**
1. 字数控制在 100-200 字
2. 提炼视频核心内容和价值点
3. 语言简洁流畅，适合作为B站视频简介
4. 不要使用 emoji 或标签
5. 直接输出摘要内容，不需要任何前缀

**字幕内容：**
{full_text}
"""
        try:
            print(f"正在生成内容摘要: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的内容摘要专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"生成摘要失败: {e}")
            return f"生成失败: {str(e)}"
