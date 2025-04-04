import tkinter as tk
from tkinter import ttk, scrolledtext
import tkinterdnd2 as tkdnd
import json
import os
import requests
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from openai import OpenAI

def chat_completion(messages):
    """调用API: https://siliconflow.cn/zh-cn/models"""
    API_KEY = "API-key"
    API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    model = "deepseek-ai/DeepSeek-R1"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
        "response_format": {"type": "text"}
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"API请求失败: {str(e)}")
        return None

def save_conversation_to_markdown(conversation, filename):
    """将AI助手的回复保存为文本文件，每行一个回答，跳过第一个"收到"的回复"""
    with open(filename, 'w', encoding='utf-8') as f:
        # 跳过第一个"收到"的回复
        assistant_responses = [msg for msg in conversation if msg["role"] == "assistant"][1:]
        for msg in assistant_responses:
            f.write(f"{msg['content']}\n")

class TranslatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("学术论文翻译助手")
        self.root.geometry("1200x900")  # 增加窗口大小
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置主框架的网格权重
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
        # 创建左侧框架
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 配置左侧框架的网格权重
        self.left_frame.columnconfigure(0, weight=1)
        self.left_frame.rowconfigure(1, weight=1)  # 让文件队列区域可以扩展
        
        # 创建拖放区域（左侧上方）
        self.drop_frame = ttk.LabelFrame(self.left_frame, text="拖放文件到这里", padding="10")
        self.drop_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.drop_label = ttk.Label(self.drop_frame, text="将markdown文件拖放到这里（支持多个文件）")
        self.drop_label.grid(row=0, column=0, padx=5, pady=5)
        
        # 创建文件队列显示区域（左侧中间）
        self.queue_frame = ttk.LabelFrame(self.left_frame, text="文件队列", padding="10")
        self.queue_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 创建Canvas和Scrollbar用于文件队列显示
        self.queue_canvas = tk.Canvas(self.queue_frame)
        self.queue_scrollbar = ttk.Scrollbar(self.queue_frame, orient="vertical", command=self.queue_canvas.yview)
        self.queue_canvas.configure(yscrollcommand=self.queue_scrollbar.set)
        
        # 添加鼠标滚轮支持
        def _on_mousewheel(event):
            self.queue_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.queue_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 创建文件队列容器
        self.queue_container = ttk.Frame(self.queue_canvas)
        self.queue_container.bind(
            "<Configure>",
            lambda e: self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all"))
        )
        
        # 将容器放在Canvas中
        self.queue_canvas.create_window((0, 0), window=self.queue_container, anchor="nw")
        
        # 布局Canvas和Scrollbar
        self.queue_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.queue_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置队列框架的网格权重
        self.queue_frame.columnconfigure(0, weight=1)
        self.queue_frame.rowconfigure(0, weight=1)
        
        # 创建参数设置区域（左侧下方）
        self.param_frame = ttk.LabelFrame(self.left_frame, text="参数设置", padding="10")
        self.param_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # 创建参数设置的网格布局
        self.param_frame.columnconfigure(1, weight=1)
        
        # API选择
        ttk.Label(self.param_frame, text="API提供商:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.api_provider = ttk.Combobox(self.param_frame, values=["硅基流动", "Deepseek"], state="readonly")
        self.api_provider.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.api_provider.set("硅基流动")
        self.api_provider.bind('<<ComboboxSelected>>', self.on_api_provider_change)
        
        # API设置
        ttk.Label(self.param_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.api_key = ttk.Entry(self.param_frame, width=50)
        self.api_key.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        self.api_key.insert(0, "sk-jpfjilbfchmvhucojngxmzqabmyhcgkfphkgrzyrzehxzfpm")
        
        # 模型设置
        ttk.Label(self.param_frame, text="模型:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.model = ttk.Combobox(self.param_frame, width=50, state="readonly")
        self.model.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        self.update_model_options()
        
        # 温度设置
        ttk.Label(self.param_frame, text="温度:").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.temperature = ttk.Entry(self.param_frame, width=50)
        self.temperature.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        self.temperature.insert(0, "0.7")
        
        # 最大token设置
        ttk.Label(self.param_frame, text="最大Token:").grid(row=4, column=0, sticky=tk.W, padx=5)
        self.max_tokens = ttk.Entry(self.param_frame, width=50)
        self.max_tokens.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5)
        self.max_tokens.insert(0, "1024")
        
        # 并行数设置
        ttk.Label(self.param_frame, text="最大并行章节数:").grid(row=5, column=0, sticky=tk.W, padx=5)
        self.parallel_count = ttk.Spinbox(self.param_frame, from_=1, to=10, width=10)
        self.parallel_count.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=5)
        self.parallel_count.set(3)  # 默认值
        
        # 创建右侧框架
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置右侧框架的网格权重
        self.right_frame.columnconfigure(0, weight=1)
        self.right_frame.rowconfigure(0, weight=1)  # 让输出区域可以扩展
        self.right_frame.rowconfigure(1, weight=1)  # 让进度区域可以扩展
        
        # 创建输出区域（右侧上方）
        self.output_frame = ttk.LabelFrame(self.right_frame, text="输出信息", padding="10")
        self.output_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.output_text = scrolledtext.ScrolledText(self.output_frame, height=20)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置输出框架的网格权重
        self.output_frame.columnconfigure(0, weight=1)
        self.output_frame.rowconfigure(0, weight=1)
        
        # 创建章节进度区域（右侧中间）
        self.progress_frame = ttk.LabelFrame(self.right_frame, text="章节进度", padding="10")
        self.progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 创建Canvas和Scrollbar
        self.progress_canvas = tk.Canvas(self.progress_frame)
        self.progress_scrollbar = ttk.Scrollbar(self.progress_frame, orient="vertical", command=self.progress_canvas.yview)
        self.progress_canvas.configure(yscrollcommand=self.progress_scrollbar.set)
        
        # 添加鼠标滚轮支持
        def _on_mousewheel(event):
            self.progress_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.progress_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 创建章节进度条容器
        self.chapter_progress_container = ttk.Frame(self.progress_canvas)
        self.chapter_progress_container.bind(
            "<Configure>",
            lambda e: self.progress_canvas.configure(scrollregion=self.progress_canvas.bbox("all"))
        )
        
        # 将容器放在Canvas中
        self.progress_canvas.create_window((0, 0), window=self.chapter_progress_container, anchor="nw")
        
        # 布局Canvas和Scrollbar
        self.progress_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.progress_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置进度框架的网格权重
        self.progress_frame.columnconfigure(0, weight=1)
        self.progress_frame.rowconfigure(0, weight=1)
        
        # 创建总进度条区域（右侧下方）
        self.total_progress_frame = ttk.LabelFrame(self.right_frame, text="总进度", padding="10")
        self.total_progress_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # 创建总进度条
        self.total_progress_var = tk.DoubleVar()
        self.total_progress_bar = ttk.Progressbar(self.total_progress_frame, variable=self.total_progress_var, maximum=100, length=400)
        self.total_progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        
        # 添加当前处理章节标签
        self.current_chapter_label = ttk.Label(self.total_progress_frame, text="")
        self.current_chapter_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 配置总进度框架的网格权重
        self.total_progress_frame.columnconfigure(0, weight=1)
        
        # 创建底部按钮框架
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # 创建开始按钮
        self.start_button = ttk.Button(self.button_frame, text="开始翻译", command=self.start_translation)
        self.start_button.grid(row=0, column=0, sticky=tk.N)
        
        # 配置按钮框架的网格权重
        self.button_frame.columnconfigure(0, weight=1)
        
        # 设置拖放功能
        self.drop_label.drop_target_register(tkdnd.DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)
        
        # 保存文件队列
        self.file_queue = []
        self.current_file_index = -1
        self.file_status_labels = {}  # 存储文件状态标签
        
        # 添加线程控制变量
        self.translation_thread = None
        self.is_translating = False
        
        # 创建日志队列
        self.log_queue = Queue()
        
        # 章节进度条字典
        self.chapter_progress_vars = {}
        self.chapter_progress_bars = {}
        self.chapter_labels = {}
        
        # 添加总段落计数变量
        self.total_paragraphs = 0
        self.completed_paragraphs = 0
        
        # 添加翻译结果存储
        self.translation_results = {}
        
    def create_chapter_progress(self, chapter_index, title):
        """为每个章节创建进度条"""
        # 创建章节进度框架
        chapter_frame = ttk.Frame(self.chapter_progress_container)
        chapter_frame.grid(row=chapter_index-1, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # 创建章节标签
        label = ttk.Label(chapter_frame, text=f"第{chapter_index}章: {title[:20]}...")
        label.grid(row=0, column=0, sticky=tk.W)
        self.chapter_labels[chapter_index] = label
        
        # 创建进度条
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(chapter_frame, variable=progress_var, maximum=100)
        progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # 保存进度条变量
        self.chapter_progress_vars[chapter_index] = progress_var
        self.chapter_progress_bars[chapter_index] = progress_bar
        
    def update_chapter_progress(self, chapter_index, value):
        """更新指定章节的进度条"""
        if chapter_index in self.chapter_progress_vars:
            self.root.after(0, self._update_chapter_progress, chapter_index, value)
    
    def _update_chapter_progress(self, chapter_index, value):
        """在主线程中更新章节进度条"""
        self.chapter_progress_vars[chapter_index].set(value)
    
    def update_total_progress(self, completed_paragraphs, total_paragraphs):
        """更新总进度条"""
        self.root.after(0, self._update_total_progress, completed_paragraphs, total_paragraphs)
    
    def _update_total_progress(self, completed_paragraphs, total_paragraphs):
        """在主线程中更新总进度条"""
        self.completed_paragraphs = completed_paragraphs
        self.total_paragraphs = total_paragraphs
        if total_paragraphs > 0:
            progress = (completed_paragraphs / total_paragraphs) * 100
            self.total_progress_var.set(progress)
            self.current_chapter_label.config(text=f"已翻译: {completed_paragraphs}/{total_paragraphs} 段")
    
    def clear_chapter_progress(self):
        """清除所有章节进度条"""
        for widget in self.chapter_progress_container.winfo_children():
            widget.destroy()
        self.chapter_progress_vars.clear()
        self.chapter_progress_bars.clear()
        self.chapter_labels.clear()
    
    def add_file_to_queue(self, file_path):
        """添加文件到队列并更新显示"""
        if file_path not in self.file_queue:
            self.file_queue.append(file_path)
            self.update_queue_display()
    
    def update_queue_display(self):
        """更新文件队列显示"""
        # 清除现有显示
        for widget in self.queue_container.winfo_children():
            widget.destroy()
        
        # 重新显示所有文件
        for i, file_path in enumerate(self.file_queue):
            file_frame = ttk.Frame(self.queue_container)
            file_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=2)
            
            # 显示文件名
            file_name = os.path.basename(file_path)
            file_label = ttk.Label(file_frame, text=file_name)
            file_label.grid(row=0, column=0, sticky=tk.W)
            
            # 显示状态
            status_label = ttk.Label(file_frame, text="")
            status_label.grid(row=0, column=1, sticky=tk.W, padx=5)
            self.file_status_labels[file_path] = status_label
            
            # 更新状态显示
            if i < self.current_file_index:
                status_label.config(text="已完成")
            elif i == self.current_file_index:
                status_label.config(text="翻译中")
            else:
                status_label.config(text="排队中")
    
    def update_file_status(self, file_path, status):
        """更新指定文件的状态显示"""
        if file_path in self.file_status_labels:
            self.root.after(0, self._update_file_status, file_path, status)
    
    def _update_file_status(self, file_path, status):
        """在主线程中更新文件状态"""
        if file_path in self.file_status_labels:
            self.file_status_labels[file_path].config(text=status)
    
    def handle_drop(self, event):
        # 检查是否正在翻译中
        if self.is_translating:
            self.log("翻译正在进行中，请等待翻译完成后再拖放新文件")
            return
            
        # 处理Windows拖放文件路径
        file_paths = event.data
        if not isinstance(file_paths, list):
            file_paths = [file_paths]
            
        for file_path in file_paths:
            # 移除可能的花括号和引号
            file_path = file_path.strip('{}')
            file_path = file_path.strip('"')
            
            if file_path.lower().endswith('.md'):
                self.add_file_to_queue(file_path)
                self.log(f"已将文件添加到队列: {file_path}")
            else:
                self.log(f"忽略非markdown文件: {file_path}")
    
    def filter_file_content(self):
        """过滤文件内容并显示结果"""
        try:
            # 读取文件内容
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 按行分割
            lines = content.split('\n')
            original_lines = len(lines)
            
            # 过滤空行，保留标题行
            filtered_lines = [line.strip() for line in lines if line.strip()]
            
            # 找到"# References"或"# ACKNOWLEDGEMENTS"的位置（不区分大小写）
            cutoff_index = -1
            for i, line in enumerate(filtered_lines):
                line_lower = line.lower()
                if line_lower == "# references" or line_lower == "# acknowledgements" or line_lower == "# acknowledgement" or line_lower == "# acknowledgment" or line_lower == "# bibliography":
                    cutoff_index = i
                    break
            
            # 如果找到截止点，只保留之前的内容
            if cutoff_index != -1:
                filtered_lines = filtered_lines[:cutoff_index]
            
            # 按标题分批处理内容
            current_batch = []
            batches = []
            current_title = None
            
            # 确保第一个标题被正确处理
            if filtered_lines and filtered_lines[0].startswith('#'):
                current_title = filtered_lines[0]
                filtered_lines = filtered_lines[1:]
            
            for line in filtered_lines:
                if line.startswith('#'):
                    # 保存当前批次，即使它是空的
                    batches.append((current_title, current_batch))
                    current_title = line
                    current_batch = []
                else:
                    current_batch.append(line)
            
            # 添加最后一个批次，即使它是空的
            if current_title:
                batches.append((current_title, current_batch))
            
            total_chapters = len(batches)
            
            # 计算总段落数（不包括标题行）
            total_paragraphs = sum(len(batch_lines) for _, batch_lines in batches)
            
            # 显示过滤结果
            self.log(f"\n{'='*60}")
            self.log("文件处理情况:")
            self.log(f"{'─'*30}")
            self.log(f"原始行数: {original_lines}")
            self.log(f"过滤后行数: {len(filtered_lines)}")
            self.log(f"删除行数: {original_lines - len(filtered_lines)}")
            self.log(f"{'─'*30}")
            
            self.log(f"\n{'='*60}")
            self.log("章节信息:")
            self.log(f"{'─'*30}")
            self.log(f"总章节数: {total_chapters}")
            self.log(f"总段落数: {total_paragraphs}")
            self.log(f"{'─'*30}")
            
            # 显示各章节信息
            for i, (title, batch_lines) in enumerate(batches):
                self.log(f"第 {i+1} 章: {title}")
                self.log(f"段落数: {len(batch_lines)}")
            
            # 保存过滤后的内容供后续使用
            self.filtered_batches = batches
            self.total_paragraphs = total_paragraphs
            
        except Exception as e:
            self.log(f"\n{'='*60}")
            self.log("文件过滤出错:")
            self.log(f"{'─'*30}")
            self.log(str(e))
            self.log(f"{'─'*30}")
    
    def log(self, message):
        # 将日志消息放入队列
        self.log_queue.put(message)
        # 使用after方法在主线程中处理日志
        self.root.after(100, self._process_log_queue)
    
    def _process_log_queue(self):
        # 处理日志队列中的所有消息
        while not self.log_queue.empty():
            message = self.log_queue.get()
            self._log(message)
        # 如果还在翻译，继续检查队列
        if self.is_translating:
            self.root.after(100, self._process_log_queue)
    
    def _log(self, message):
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)
    
    def update_model_options(self):
        """根据选择的API提供商更新模型选项"""
        provider = self.api_provider.get()
        if provider == "硅基流动":
            self.model['values'] = [
                "Qwen/QwQ-32B",
                "Pro/deepseek-ai/DeepSeek-R1",
                "Pro/deepseek-ai/DeepSeek-V3",
                "deepseek-ai/DeepSeek-R1",
                "deepseek-ai/DeepSeek-V3",
                "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
                "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
                "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
                "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
                "Pro/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
                "Pro/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
                "deepseek-ai/DeepSeek-V2.5",
                "Qwen/Qwen2.5-72B-Instruct-128K",
                "Qwen/Qwen2.5-72B-Instruct",
                "Qwen/Qwen2.5-32B-Instruct",
                "Qwen/Qwen2.5-14B-Instruct",
                "Qwen/Qwen2.5-7B-Instruct",
                "Qwen/Qwen2.5-Coder-32B-Instruct",
                "Qwen/Qwen2.5-Coder-7B-Instruct",
                "Qwen/Qwen2-7B-Instruct",
                "Qwen/Qwen2-1.5B-Instruct",
                "Qwen/QwQ-32B-Preview",
                "TeleAI/TeleChat2",
                "THUDM/glm-4-9b-chat",
                "Vendor-A/Qwen/Qwen2.5-72B-Instruct",
                "internlm/internlm2_5-7b-chat",
                "internlm/internlm2_5-20b-chat",
                "Pro/Qwen/Qwen2.5-7B-Instruct",
                "Pro/Qwen/Qwen2-7B-Instruct",
                "Pro/Qwen/Qwen2-1.5B-Instruct",
                "Pro/THUDM/chatglm3-6b",
                "Pro/THUDM/glm-4-9b-chat"
            ]
            self.model.set("deepseek-ai/DeepSeek-R1")  # 设置默认值
        elif provider == "Deepseek":
            self.model['values'] = [
                "deepseek-chat",
                "deepseek-reasoner"
            ]
            self.model.set("deepseek-chat")  # 设置默认值
    
    def on_api_provider_change(self, event):
        """当API提供商改变时更新模型选项"""
        self.update_model_options()
    
    def chat_completion(self, messages):
        """根据选择的API提供商调用相应的API"""
        provider = self.api_provider.get()
        api_key = self.api_key.get()
        model = self.model.get()
        temperature = float(self.temperature.get())
        max_tokens = int(self.max_tokens.get())
        
        try:
            if provider == "硅基流动":
                # 原有的硅基流动API调用代码
                response = chat_completion(messages)
                return response
            elif provider == "Deepseek":
                # Deepseek API调用
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
        except Exception as e:
            self.log(f"API调用出错: {str(e)}")
            return None
    
    def translate_chapter(self, chapter_index, title, batch_lines):
        """翻译单个章节的函数"""
        try:
            # 开始翻译
            conversation = []
            messages = []
            
            # 发送翻译指令
            translation_instruction = "请将经济学论文英译中，要求：1. 严格忠实原文，不增删内容；2. 保留Markdown代码；3. 润色语言流畅度，用词通顺易懂，表达清晰，切合中文表达习惯；4.仅输出翻译结果（使用中文标点），不要输出任何其他内容。收到含【翻译】的文本前回复“收到”。"
            
            self.log(f"\n{'='*60}")
            self.log(f"开始处理第 {chapter_index} 章: {title}")
            self.log(f"{'='*60}")
            
            messages.append({"role": "user", "content": translation_instruction})
            conversation.append({"role": "user", "content": translation_instruction})
            
            self.log("等待确认...")
            response = self.chat_completion(messages)
            
            if response:
                messages.append({"role": "assistant", "content": response})
                # 不将"收到"保存到conversation中
                self.log("确认完成")
                self.log(f"{'-'*60}")
            
            # 计算总段落数
            total_paragraphs = len(batch_lines)
            completed_paragraphs = 0
            
            # 翻译每个段落
            for user_input in batch_lines:
                max_retries = 3  # 最大重试次数
                retry_count = 0
                translation_success = False
                
                while not translation_success and retry_count < max_retries:
                    try:
                        self.log(f"\n原文:")
                        self.log(f"{'─'*30}")
                        self.log(user_input)
                        self.log(f"{'─'*30}")
                        
                        messages.append({"role": "user", "content": user_input})
                        conversation.append({"role": "user", "content": user_input})
                        
                        self.log("思考中...")
                        response = self.chat_completion(messages)
                        
                        if response:
                            messages.append({"role": "assistant", "content": response})
                            conversation.append({"role": "assistant", "content": response})
                            
                            self.log("\n译文:")
                            self.log(f"{'─'*30}")
                            self.log(response)
                            self.log(f"{'─'*30}")
                            
                            # 更新进度
                            completed_paragraphs += 1
                            remaining_paragraphs = total_paragraphs - completed_paragraphs
                            progress_percentage = (completed_paragraphs / total_paragraphs) * 100
                            
                            # 更新章节进度条
                            self.update_chapter_progress(chapter_index, progress_percentage)
                            
                            # 更新总进度（使用固定的总段落数）
                            self.update_total_progress(self.completed_paragraphs + 1, self.total_paragraphs)
                            
                            # 显示进度信息
                            self.log("\n翻译进度:")
                            self.log(f"总段落数: {total_paragraphs}")
                            self.log(f"已完成: {completed_paragraphs}")
                            self.log(f"剩余: {remaining_paragraphs}")
                            self.log(f"完成度: {progress_percentage:.1f}%")
                            
                            self.log(f"{'-'*60}")
                            translation_success = True
                        else:
                            retry_count += 1
                            if retry_count < max_retries:
                                self.log(f"警告: 第 {chapter_index} 章的第 {completed_paragraphs + 1} 段翻译失败，正在进行第 {retry_count + 1} 次重试...")
                            else:
                                self.log(f"警告: 第 {chapter_index} 章的第 {completed_paragraphs + 1} 段翻译失败，已达到最大重试次数")
                                conversation.append({"role": "assistant", "content": "【翻译失败】"})
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            self.log(f"警告: 第 {chapter_index} 章的第 {completed_paragraphs + 1} 段翻译出错: {str(e)}，正在进行第 {retry_count + 1} 次重试...")
                        else:
                            self.log(f"警告: 第 {chapter_index} 章的第 {completed_paragraphs + 1} 段翻译出错: {str(e)}，已达到最大重试次数")
                            conversation.append({"role": "assistant", "content": f"【翻译出错: {str(e)}】"})
                        continue
                
                if not translation_success:
                    self.log(f"警告: 第 {chapter_index} 章的第 {completed_paragraphs + 1} 段翻译最终失败，将继续处理下一段")
            
            # 保存翻译结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}_chapter_{chapter_index}.md"
            save_conversation_to_markdown(conversation, filename)
            self.log(f"\n第 {chapter_index} 章翻译记录已保存到: {filename}")
            
            # 保存翻译结果到内存
            self.translation_results[chapter_index] = {
                'title': title,
                'conversation': conversation,
                'filename': filename  # 保存文件名以便后续删除
            }
            
            return True
        except Exception as e:
            self.log(f"第 {chapter_index} 章翻译出错: {str(e)}")
            # 即使出错也保存部分结果
            if 'conversation' in locals():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"conversation_{timestamp}_chapter_{chapter_index}_error.md"
                save_conversation_to_markdown(conversation, filename)
                self.log(f"\n第 {chapter_index} 章部分翻译记录已保存到: {filename}")
                
                self.translation_results[chapter_index] = {
                    'title': title,
                    'conversation': conversation,
                    'filename': filename
                }
            return False
    
    def merge_translation_results(self):
        """合并所有章节的翻译结果"""
        try:
            # 按章节顺序合并内容
            merged_content = []
            
            # 检查是否有遗漏的章节
            expected_chapters = len(self.filtered_batches)
            translated_chapters = len(self.translation_results)
            
            if translated_chapters < expected_chapters:
                self.log(f"\n{'='*60}")
                self.log("警告: 部分章节未被翻译")
                self.log(f"{'─'*30}")
                self.log(f"总章节数: {expected_chapters}")
                self.log(f"已翻译章节数: {translated_chapters}")
                self.log(f"遗漏章节数: {expected_chapters - translated_chapters}")
                self.log(f"{'─'*30}")
            
            # 按章节顺序合并内容
            for chapter_index in range(1, expected_chapters + 1):
                if chapter_index in self.translation_results:
                    result = self.translation_results[chapter_index]
                    # 添加章节标题
                    merged_content.append(result['title'])
                    merged_content.append('')  # 标题后添加空行
                    
                    # 添加翻译内容
                    for msg in result['conversation']:
                        if msg['role'] == 'assistant':
                            # 确保每个段落之间有空行
                            content = msg['content'].strip()
                            if content:  # 只添加非空内容
                                merged_content.append(content)
                                merged_content.append('')  # 段落后添加空行
                else:
                    # 对于未翻译的章节，添加原始标题和提示
                    title = self.filtered_batches[chapter_index - 1][0]
                    merged_content.append(title)
                    merged_content.append('')  # 标题后添加空行
                    merged_content.append("【注意：此章节未被翻译】")
                    merged_content.append('')  # 提示后添加空行
                
                # 章节之间添加额外的空行
                merged_content.append('')
            
            # 保存合并后的文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            merged_filename = f"translation_{timestamp}_merged.md"
            with open(merged_filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(merged_content))
            
            self.log(f"\n{'='*60}")
            self.log("文件处理完成:")
            self.log(f"{'─'*30}")
            self.log(f"合并后的翻译结果已保存到: {merged_filename}")
            
            # 删除各章节的独立翻译文件
            for chapter_index, result in self.translation_results.items():
                try:
                    if os.path.exists(result['filename']):
                        os.remove(result['filename'])
                        self.log(f"已删除第 {chapter_index} 章的独立翻译文件")
                except Exception as e:
                    self.log(f"删除第 {chapter_index} 章的独立翻译文件时出错: {str(e)}")
            self.log(f"{'─'*30}")
            
        except Exception as e:
            self.log(f"\n{'='*60}")
            self.log("合并翻译结果时出错:")
            self.log(f"{'─'*30}")
            self.log(str(e))
            self.log(f"{'─'*30}")
    
    def start_translation(self):
        if not self.file_queue:
            self.log("请先拖放markdown文件")
            return
            
        if self.is_translating:
            self.log("翻译正在进行中，请等待...")
            return
            
        # 禁用开始按钮
        self.start_button.state(['disabled'])
        self.is_translating = True
        
        # 在新线程中运行翻译过程
        self.translation_thread = threading.Thread(target=self.translation_process)
        self.translation_thread.daemon = True
        self.translation_thread.start()
    
    def translation_process(self):
        try:
            # 遍历文件队列
            for i, file_path in enumerate(self.file_queue):
                self.current_file_index = i
                self.file_path = file_path
                
                # 更新文件状态
                self.update_file_status(file_path, "翻译中")
                self.update_queue_display()
                
                # 清除之前的输出信息
                self.output_text.delete(1.0, tk.END)
                
                # 重置进度条
                self.total_progress_var.set(0)
                self.current_chapter_label.config(text="")
                
                # 清除之前的进度条
                self.clear_chapter_progress()
                
                self.log(f"\n开始翻译文件: {file_path}")
                
                # 执行文件过滤
                self.filter_file_content()
                
                # 获取参数
                api_key = self.api_key.get()
                model = self.model.get()
                temperature = float(self.temperature.get())
                max_tokens = int(self.max_tokens.get())
                parallel_count = int(self.parallel_count.get())
                
                # 检查是否已经过滤了文件内容
                if not hasattr(self, 'filtered_batches') or not self.filtered_batches:
                    self.log("文件过滤失败，跳过此文件")
                    continue
                
                batches = self.filtered_batches
                total_chapters = len(batches)
                total_paragraphs = self.total_paragraphs
                self.completed_paragraphs = 0
                
                self.log(f"\n{'='*60}")
                self.log("翻译任务信息:")
                self.log(f"{'─'*30}")
                self.log(f"总章节数: {total_chapters}")
                self.log(f"并行翻译章节数: {parallel_count}")
                self.log(f"总段落数: {total_paragraphs}")
                self.log(f"{'─'*30}")
                
                # 创建章节进度条
                for i, (title, _) in enumerate(batches):
                    self.create_chapter_progress(i+1, title)
                
                # 使用线程池并行处理章节
                with ThreadPoolExecutor(max_workers=parallel_count) as executor:
                    # 提交所有任务
                    future_to_chapter = {
                        executor.submit(self.translate_chapter, i+1, title, [f"【翻译】：{line}" for line in batch_lines]): i+1 
                        for i, (title, batch_lines) in enumerate(batches)
                    }
                    
                    # 等待所有任务完成
                    for future in as_completed(future_to_chapter):
                        chapter_index = future_to_chapter[future]
                        try:
                            success = future.result()
                        except Exception as e:
                            self.log(f"第 {chapter_index} 章处理失败: {str(e)}")
                
                # 合并翻译结果
                self.merge_translation_results()
                
                # 更新文件状态
                self.update_file_status(file_path, "已完成")
                
                self.log(f"\n{'='*60}")
                self.log(f"文件 {file_path} 翻译完成！")
                self.log(f"{'='*60}")
            
            self.log(f"\n{'='*60}")
            self.log("所有文件翻译完成！")
            self.log(f"{'='*60}")
            
        except Exception as e:
            self.log(f"\n{'='*60}")
            self.log("错误信息:")
            self.log(f"{'─'*30}")
            self.log(str(e))
            self.log(f"{'─'*30}")
        finally:
            # 恢复开始按钮状态
            self.root.after(0, self._reset_button)
    
    def _reset_button(self):
        self.start_button.state(['!disabled'])
        self.is_translating = False
        self.current_file_index = -1

def main():
    root = tkdnd.TkinterDnD.Tk()
    app = TranslatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 