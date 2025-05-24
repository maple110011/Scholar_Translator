import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import tkinterdnd2 as tkdnd
import json
import os
import requests
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
from openai import OpenAI
import time

def chat_completion(messages, api_key):
    """调用API: https://siliconflow.cn/zh-cn/models"""
    API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    model = "deepseek-ai/DeepSeek-R1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
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

class TranslatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("学术论文翻译助手")
        self.root.geometry("1200x900")  # 增加窗口大小
        
        # 添加窗口状态变化事件处理
        self.root.bind('<Unmap>', self.on_window_minimize)  # 窗口最小化事件
        self.root.bind('<Map>', self.on_window_restore)     # 窗口恢复事件
        
        # 添加线程控制变量
        self.translation_thread = None
        self.is_translating = False
        self.is_paused = False
        self.should_stop = False
        
        # 修改日志限制相关变量
        self.max_log_lines = 500  # 增加最大日志行数
        self.log_update_interval = 1000  # 增加日志更新间隔到1秒
        self.progress_update_interval = 100  # 减少进度更新间隔
        self.last_log_update = 0
        self.last_progress_update = 0
        self.log_batch_size = 50  # 增加日志批处理大小
        self.log_buffer = []  # 添加日志缓冲区
        self.last_log_update_time = time.time()  # 添加最后日志更新时间
        
        # 创建UI更新队列
        self.ui_queue = Queue()
        
        # 启动UI更新循环
        self._process_ui_updates()
        
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
        self.api_provider.set("Deepseek")
        self.api_provider.bind('<<ComboboxSelected>>', self.on_api_provider_change)
        
        # API设置
        ttk.Label(self.param_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.api_key = ttk.Entry(self.param_frame, width=50)
        self.api_key.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        self.api_key.insert(0, "your API key")
        
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

        # 翻译结果保存路径设置
        ttk.Label(self.param_frame, text="翻译结果保存路径:").grid(row=6, column=0, sticky=tk.W, padx=5)
        self.result_path_frame = ttk.Frame(self.param_frame)
        self.result_path_frame.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=5)
        self.result_path = ttk.Entry(self.result_path_frame, width=40)
        self.result_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.result_path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "TranslateResult"))
        self.result_path_button = ttk.Button(self.result_path_frame, text="浏览", command=self.browse_result_path)
        self.result_path_button.pack(side=tk.RIGHT, padx=5)

        # 缓存文件保存路径设置
        ttk.Label(self.param_frame, text="缓存文件保存路径:").grid(row=7, column=0, sticky=tk.W, padx=5)
        self.cache_path_frame = ttk.Frame(self.param_frame)
        self.cache_path_frame.grid(row=7, column=1, sticky=(tk.W, tk.E), padx=5)
        self.cache_path = ttk.Entry(self.cache_path_frame, width=40)
        self.cache_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.cache_path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache"))
        self.cache_path_button = ttk.Button(self.cache_path_frame, text="浏览", command=self.browse_cache_path)
        self.cache_path_button.pack(side=tk.RIGHT, padx=5)
        
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
        
        self.output_text = scrolledtext.ScrolledText(self.output_frame, height=20, state='disabled')
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 禁用所有鼠标事件，只保留滚动功能
        self.output_text.bind('<Button-1>', lambda e: 'break')
        self.output_text.bind('<Button-2>', lambda e: 'break')
        self.output_text.bind('<Button-3>', lambda e: 'break')
        self.output_text.bind('<B1-Motion>', lambda e: 'break')
        self.output_text.bind('<ButtonRelease-1>', lambda e: 'break')
        self.output_text.bind('<Double-Button-1>', lambda e: 'break')
        self.output_text.bind('<Triple-Button-1>', lambda e: 'break')
        
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
        
        # 创建日志队列
        self.log_queue = Queue()
        
        # 章节进度条字典
        self.chapter_progress_vars = {}
        self.chapter_progress_bars = {}
        self.chapter_labels = {}
        
        # 添加总段落计数变量
        self.total_paragraphs = 0
        self.completed_paragraphs = 0
        
        # 添加翻译结果缓存控制
        self.translation_results = {}
        self.max_cached_chapters = 5  # 最大缓存章节数
        self.chapter_cache = {}  # 章节缓存

    def _process_ui_updates(self):
        """处理UI更新队列"""
        try:
            while not self.ui_queue.empty():
                update_func = self.ui_queue.get_nowait()
                update_func()
        except Empty:
            pass
        finally:
            # 继续处理队列
            self.root.after(50, self._process_ui_updates)

    def _queue_ui_update(self, update_func):
        """将UI更新函数加入队列"""
        self.ui_queue.put(update_func)

    def _process_log_queue(self):
        """处理日志队列"""
        try:
            if not self.root.winfo_exists():
                return
                
            current_time = time.time()
            # 只有当距离上次更新超过指定时间间隔时才更新UI
            if current_time - self.last_log_update_time >= self.log_update_interval / 1000:
                # 处理队列中的消息
                messages = []
                while not self.log_queue.empty() and len(messages) < self.log_batch_size:
                    messages.append(self.log_queue.get())
                
                if messages:
                    # 批量更新日志
                    self._log_batch(messages)
                    self.last_log_update_time = current_time
            
            # 如果还在翻译，继续检查队列
            if self.is_translating:
                self.root.after(self.log_update_interval, self._process_log_queue)
                
        except Exception as e:
            print(f"处理日志队列时出错: {str(e)}")
            # 出错后重新安排处理
            if self.is_translating:
                self.root.after(self.log_update_interval, self._process_log_queue)

    def _log_batch(self, messages):
        """批量添加日志到输出区域，并限制日志数量"""
        def update():
            try:
                if not self.root.winfo_exists():
                    return
                    
                # 临时启用文本框以更新内容
                self.output_text.config(state='normal')
                
                # 批量插入日志
                self.output_text.insert(tk.END, '\n'.join(messages) + '\n')
                
                # 获取当前行数
                line_count = int(self.output_text.index('end-1c').split('.')[0])
                
                # 如果超过最大行数，批量删除旧日志
                if line_count > self.max_log_lines:
                    delete_count = line_count - self.max_log_lines
                    self.output_text.delete('1.0', f'{delete_count + 1}.0')
                
                # 只有在用户没有手动滚动时才自动滚动到底部
                if self.output_text.yview()[1] >= 0.99:
                    self.output_text.see(tk.END)
                
                # 重新禁用文本框
                self.output_text.config(state='disabled')
                
            except Exception as e:
                print(f"添加日志时出错: {str(e)}")
        
        self._queue_ui_update(update)

    def log(self, message):
        """添加日志消息到队列"""
        try:
            # 将日志消息放入队列
            self.log_queue.put(message)
            # 使用after方法在主线程中处理日志
            self.root.after(100, self._process_log_queue)
        except Exception as e:
            print(f"添加日志消息时出错: {str(e)}")

    def _check_translation_progress(self):
        """定期检查翻译进度并更新UI"""
        if not self.is_translating:
            return
            
        try:
            # 更新队列显示
            self.update_queue_display()
            
            # 更新进度显示
            self.update_progress_display()
            
            # 检查翻译线程是否还在运行
            if self.translation_thread and self.translation_thread.is_alive():
                # 继续检查
                self.root.after(self.progress_update_interval, self._check_translation_progress)
            else:
                # 翻译线程结束，但等待合并完成
                if self.is_translating:
                    self.root.after(self.progress_update_interval, self._check_translation_progress)
        except Exception as e:
            print(f"检查翻译进度时出错: {str(e)}")
            # 出错时也继续检查
            self.root.after(self.progress_update_interval, self._check_translation_progress)

    def save_conversation_to_markdown(self, conversation, filename):
        """将AI助手的回复保存为markdown文件"""
        # 确保缓存目录存在
        cache_dir = self.cache_path.get()
        os.makedirs(cache_dir, exist_ok=True)
        
        file_path = os.path.join(cache_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            # 跳过第一个"收到"的回复
            assistant_responses = [msg for msg in conversation if msg["role"] == "assistant"][1:]
            for msg in assistant_responses:
                f.write(f"{msg['content']}\n\n")

    def create_chapter_progress(self, chapter_index, title):
        """为每个章节创建进度条"""
        try:
            if not self.root.winfo_exists():
                return
            # 创建章节进度框架
            if not hasattr(self, 'chapter_progress_container') or not self.chapter_progress_container.winfo_exists():
                return
                
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
            
            # 更新Canvas的滚动区域
            if hasattr(self, 'progress_canvas') and self.progress_canvas.winfo_exists():
                self.progress_canvas.configure(scrollregion=self.progress_canvas.bbox("all"))
        except Exception as e:
            print(f"创建进度条时出错: {str(e)}")
    
    def update_chapter_progress(self, chapter_index, value):
        """更新指定章节的进度条"""
        if not self.root.winfo_exists():
            return
            
        self.root.after(0, lambda: self._update_chapter_progress(chapter_index, value))
    
    def update_total_progress(self, completed_paragraphs, total_paragraphs):
        """更新总进度条"""
        if not self.root.winfo_exists():
            return
            
        self.root.after(0, lambda: self._update_total_progress(completed_paragraphs, total_paragraphs))
    
    def clear_chapter_progress(self):
        """清除所有章节进度条"""
        try:
            if not self.root.winfo_exists():
                return
            # 清除进度条变量
            self.chapter_progress_vars.clear()
            self.chapter_progress_bars.clear()
            self.chapter_labels.clear()
            
            # 清除Canvas中的内容
            if hasattr(self, 'chapter_progress_container') and self.chapter_progress_container.winfo_exists():
                for widget in self.chapter_progress_container.winfo_children():
                    if widget.winfo_exists():
                        widget.destroy()
                
                # 更新Canvas的滚动区域
                if hasattr(self, 'progress_canvas') and self.progress_canvas.winfo_exists():
                    self.progress_canvas.configure(scrollregion=self.progress_canvas.bbox("all"))
        except Exception as e:
            print(f"清除进度条时出错: {str(e)}")
    
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
    
    def update_progress_display(self):
        """更新所有进度显示"""
        def update():
            try:
                # 更新总进度
                if hasattr(self, 'total_paragraphs') and self.total_paragraphs > 0:
                    progress = (self.completed_paragraphs / self.total_paragraphs) * 100
                    self.total_progress_var.set(progress)
                    self.current_chapter_label.config(text=f"已翻译: {self.completed_paragraphs}/{self.total_paragraphs} 段")
                
                # 更新章节进度
                for chapter_index, progress_var in self.chapter_progress_vars.items():
                    if chapter_index in self.translation_results:
                        result = self.translation_results[chapter_index]
                        if 'conversation' in result:
                            assistant_messages = [msg for msg in result['conversation'] if msg['role'] == 'assistant'][1:]
                            completed = len(assistant_messages)
                            total = len([msg for msg in result['conversation'] if msg['role'] == 'user'][1:])
                            if total > 0:
                                progress = (completed / total) * 100
                                progress_var.set(progress)
            except Exception as e:
                print(f"更新进度显示时出错: {str(e)}")
        
        self._queue_ui_update(update)

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
                # 使用传入的API_KEY调用硅基流动API
                response = chat_completion(messages, api_key)
                return response
            elif provider == "Deepseek":
                # Deepseek API调用
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                
                # 添加请求延迟
                time.sleep(1)  # 每次请求前等待1秒
                
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    self.log(f"Deepseek API请求失败: {str(e)}")
                    # 如果是速率限制错误，等待更长时间后重试
                    if "rate limit" in str(e).lower():
                        time.sleep(5)  # 等待5秒后重试
                        try:
                            response = client.chat.completions.create(
                                model=model,
                                messages=messages,
                                temperature=temperature,
                                max_tokens=max_tokens
                            )
                            return response.choices[0].message.content
                        except Exception as retry_error:
                            self.log(f"Deepseek API重试失败: {str(retry_error)}")
                            return None
                    return None
        except Exception as e:
            self.log(f"API调用出错: {str(e)}")
            return None
    
    def translate_chapter(self, chapter_index, title, batch_lines):
        """翻译单个章节的函数"""
        try:
            # 开始翻译
            messages = []
            cache_file = None
            last_block_context = []  # 存储上一个块的最后几个段落
            
            # 发送翻译指令
            translation_instruction = "请将经济学论文英译中，要求：1. 严格忠实原文，不增删内容；2. 保留Markdown代码；3. 润色语言流畅度，用词通顺易懂，表达清晰，切合中文表达习惯；4.仅输出翻译结果（使用中文标点），不要输出任何其他内容，不要输出任何对翻译结果的说明。收到含【翻译】的文本前回复“收到”。"
            
            self.log(f"\n{'='*60}")
            self.log(f"开始处理第 {chapter_index} 章: {title}")
            self.log(f"{'='*60}")
            
            messages.append({"role": "user", "content": translation_instruction})
            
            self.log("等待确认...")
            response = self.chat_completion(messages)
            
            if response:
                messages.append({"role": "assistant", "content": response})
                self.log("确认完成")
                self.log(f"{'-'*60}")
                
                # 创建缓存文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"conversation_{timestamp}_chapter_{chapter_index}.md"
                cache_file = os.path.join(self.cache_path.get(), filename)
                
                # 确保缓存目录存在
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                
                # 写入标题和确认信息
                with open(cache_file, 'w', encoding='utf-8') as f:
                    f.write(f"{title}\n\n")
                    f.write(f"{response}\n\n")
            
            # 计算总段落数
            total_paragraphs = len(batch_lines)
            completed_paragraphs = 0
            
            # 设置每个块的最大段落数
            max_paragraphs_per_block = 32
            
            # 将段落分成多个块
            blocks = [batch_lines[i:i + max_paragraphs_per_block] 
                     for i in range(0, len(batch_lines), max_paragraphs_per_block)]
            
            # 处理每个块
            for block_index, block in enumerate(blocks):
                if self.should_stop:
                    break
                
                # 如果是新的块（不是第一个块），添加上下文
                if block_index > 0 and last_block_context:
                    context_message = "以下是上一部分的最后几个段落，请参考它们来保持翻译的连贯性：\n\n"
                    for i, (original, translated) in enumerate(last_block_context):
                        context_message += f"原文{i+1}：{original}\n"
                        context_message += f"译文{i+1}：{translated}\n\n"
                    context_message += "现在请继续翻译下一部分，保持相同的翻译风格和术语一致性。"
                    
                    messages.append({"role": "user", "content": context_message})
                    messages.append({"role": "assistant", "content": "好的，我会参考上一部分的翻译来保持连贯性。"})
                
                # 翻译块内的每个段落
                current_block_translations = []  # 存储当前块的翻译结果
                for user_input in block:
                    if self.should_stop:
                        break
                        
                    max_retries = 3
                    retry_count = 0
                    translation_success = False
                    
                    while not translation_success and retry_count < max_retries:
                        try:
                            self.log(f"\n原文:")
                            self.log(f"{'─'*30}")
                            self.log(user_input)
                            self.log(f"{'─'*30}")
                            
                            messages.append({"role": "user", "content": user_input})
                            
                            self.log("思考中...")
                            response = self.chat_completion(messages)
                            
                            if response:
                                messages.append({"role": "assistant", "content": response})
                                
                                # 保存翻译结果
                                current_block_translations.append((user_input, response))
                                
                                # 立即写入文件
                                if cache_file:
                                    with open(cache_file, 'a', encoding='utf-8') as f:
                                        f.write(f"{response}\n\n")
                                
                                self.log("\n译文:")
                                self.log(f"{'─'*30}")
                                self.log(response)
                                self.log(f"{'─'*30}")
                                
                                # 更新进度
                                completed_paragraphs += 1
                                progress_percentage = (completed_paragraphs / total_paragraphs) * 100
                                
                                # 更新章节进度条
                                self._update_chapter_progress(chapter_index, progress_percentage)
                                
                                # 更新总进度
                                self._update_total_progress(self.completed_paragraphs + 1, self.total_paragraphs)
                                
                                translation_success = True
                            else:
                                retry_count += 1
                                if retry_count < max_retries:
                                    self.log(f"警告: 第 {chapter_index} 章的第 {completed_paragraphs + 1} 段翻译失败，正在进行第 {retry_count + 1} 次重试...")
                                else:
                                    self.log(f"警告: 第 {chapter_index} 章的第 {completed_paragraphs + 1} 段翻译失败，已达到最大重试次数")
                                    if cache_file:
                                        with open(cache_file, 'a', encoding='utf-8') as f:
                                            f.write("【翻译失败】\n\n")
                        except Exception as e:
                            retry_count += 1
                            if retry_count < max_retries:
                                self.log(f"警告: 第 {chapter_index} 章的第 {completed_paragraphs + 1} 段翻译出错: {str(e)}，正在进行第 {retry_count + 1} 次重试...")
                            else:
                                self.log(f"警告: 第 {chapter_index} 章的第 {completed_paragraphs + 1} 段翻译出错: {str(e)}，已达到最大重试次数")
                                if cache_file:
                                    with open(cache_file, 'a', encoding='utf-8') as f:
                                        f.write(f"【翻译出错: {str(e)}】\n\n")
                            continue
                    
                    if not translation_success:
                        self.log(f"警告: 第 {chapter_index} 章的第 {completed_paragraphs + 1} 段翻译最终失败，将继续处理下一段")
                
                # 更新上一个块的上下文（保留最后3个段落）
                last_block_context = current_block_translations[-3:] if current_block_translations else []
                
                # 在块之间清理消息历史，只保留最近的几条消息
                if len(messages) > 10:  # 保留最近的10条消息
                    messages = messages[:2] + messages[-8:]  # 保留开头的2条和最近的8条
            
            # 记录缓存文件路径
            self.translation_results[chapter_index] = {
                'title': title,
                'filename': os.path.basename(cache_file) if cache_file else None
            }
            
            return True
        except Exception as e:
            self.log(f"第 {chapter_index} 章翻译出错: {str(e)}")
            return False

    def _cleanup_chapter_cache(self):
        """清理过期的章节缓存"""
        if len(self.chapter_cache) > self.max_cached_chapters:
            # 删除最旧的缓存
            oldest_chapter = min(self.chapter_cache.keys())
            del self.chapter_cache[oldest_chapter]

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
                    
                    # 从文件读取翻译内容
                    cache_file = os.path.join(self.cache_path.get(), result['filename'])
                    if os.path.exists(cache_file):
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 跳过第一个"收到"的回复
                            lines = content.split('\n')
                            start_index = 0
                            for i, line in enumerate(lines):
                                if line.strip() == "收到":
                                    start_index = i + 1
                                    break
                            # 添加翻译内容
                            merged_content.extend(lines[start_index:])
                else:
                    # 对于未翻译的章节，添加原始标题和提示
                    title = self.filtered_batches[chapter_index - 1][0]
                    merged_content.append(title)
                    merged_content.append('')  # 标题后添加空行
                    merged_content.append("【注意：此章节未被翻译】")
                    merged_content.append('')  # 提示后添加空行
                
                # 章节之间添加额外的空行
                merged_content.append('')
            
            # 确保结果目录存在
            result_dir = self.result_path.get()
            os.makedirs(result_dir, exist_ok=True)
            
            # 保存合并后的文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            merged_filename = f"translation_{timestamp}_merged.md"
            merged_file_path = os.path.join(result_dir, merged_filename)
            with open(merged_file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(merged_content))
            
            self.log(f"\n{'='*60}")
            self.log("文件处理完成:")
            self.log(f"{'─'*30}")
            self.log(f"合并后的翻译结果已保存到: {merged_file_path}")
            
            # 标记翻译完成
            self.is_translating = False
            
            # 在主线程中处理完成后的操作
            self.root.after(0, self._handle_translation_complete)
            
        except Exception as e:
            self.log(f"\n{'='*60}")
            self.log("合并翻译结果时出错:")
            self.log(f"{'─'*30}")
            self.log(str(e))
            self.log(f"{'─'*30}")
            # 即使出错也标记翻译完成
            self.is_translating = False
            self.root.after(0, self._handle_translation_complete)

    def _handle_translation_complete(self):
        """处理翻译完成后的操作"""
        try:
            # 重置按钮状态
            self._reset_button()
            
            # 如果翻译正常完成（不是手动停止），询问是否删除缓存文件
            if not self.should_stop:
                self.root.after(500, lambda: self._ask_delete_cache(self.cache_path.get()))
        except Exception as e:
            print(f"处理翻译完成时出错: {str(e)}")

    def _reset_button(self):
        """重置按钮状态"""
        try:
            if self.root.winfo_exists():
                self.start_button.state(['!disabled'])
                self.root.update_idletasks()  # 强制更新UI
                self.is_translating = False
                self.is_paused = False
                self.should_stop = False
                self.current_file_index = -1
        except Exception as e:
            print(f"重置按钮状态时出错: {str(e)}")

    def _ask_delete_cache(self, cache_dir):
        """询问用户是否删除缓存目录中的文件"""
        try:
            if not self.root.winfo_exists():
                return
                
            response = tk.messagebox.askyesno(
                "删除缓存文件",
                "所有文件翻译已完成，是否删除翻译过程中的缓存文件？"
            )
            
            if response:
                try:
                    if os.path.exists(cache_dir):
                        # 删除目录中的所有文件
                        for file_name in os.listdir(cache_dir):
                            file_path = os.path.join(cache_dir, file_name)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                self.log(f"已删除缓存文件: {file_name}")
                        self.log("所有缓存文件已删除")
                except Exception as e:
                    self.log(f"删除缓存文件时出错: {str(e)}")
            else:
                self.log("已保留缓存文件")
        except Exception as e:
            print(f"询问删除缓存文件时出错: {str(e)}")

    def browse_result_path(self):
        """浏览并选择翻译结果保存路径"""
        try:
            if not self.root.winfo_exists():
                return
            path = filedialog.askdirectory()
            if path:
                self.result_path.delete(0, tk.END)
                self.result_path.insert(0, path)
        except Exception as e:
            print(f"选择结果保存路径时出错: {str(e)}")

    def browse_cache_path(self):
        """浏览并选择缓存文件保存路径"""
        try:
            if not self.root.winfo_exists():
                return
            path = filedialog.askdirectory()
            if path:
                self.cache_path.delete(0, tk.END)
                self.cache_path.insert(0, path)
        except Exception as e:
            print(f"选择缓存保存路径时出错: {str(e)}")

    def translation_process(self):
        """翻译处理主函数"""
        try:
            # 遍历文件队列
            for i, file_path in enumerate(self.file_queue):
                if self.should_stop:
                    break
                    
                self.current_file_index = i
                self.file_path = file_path
                
                # 更新文件状态
                self.update_file_status(file_path, "翻译中")
                
                # 清除之前的输出信息
                if self.root.winfo_exists():
                    self.output_text.delete(1.0, tk.END)
                
                # 重置进度条
                if self.root.winfo_exists():
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
                        if self.should_stop:
                            break
                        chapter_index = future_to_chapter[future]
                        try:
                            success = future.result()
                        except Exception as e:
                            self.log(f"第 {chapter_index} 章处理失败: {str(e)}")
                
                if self.should_stop:
                    self.log("翻译任务已停止")
                    break
                
                # 合并翻译结果
                self.merge_translation_results()
                
                # 更新文件状态
                self.update_file_status(file_path, "已完成")
                
                self.log(f"\n{'='*60}")
                self.log(f"文件 {file_path} 翻译完成！")
                self.log(f"{'='*60}")
            
            if not self.should_stop:
                self.log(f"\n{'='*60}")
                self.log("所有文件翻译完成！")
                self.log(f"{'='*60}")
            
        except Exception as e:
            self.log(f"\n{'='*60}")
            self.log("错误信息:")
            self.log(f"{'─'*30}")
            self.log(str(e))
            self.log(f"{'─'*30}")

    def on_window_minimize(self, event):
        """窗口最小化时的处理"""
        # 最小化时不暂停翻译，只记录日志
        self.log("程序已最小化，翻译将继续在后台运行...")

    def on_window_restore(self, event):
        """窗口恢复时的处理"""
        # 窗口恢复时更新UI，但不重复记录日志
        if self.is_translating:
            self.update_queue_display()
            self.update_progress_display()

    def start_translation(self):
        """开始翻译过程"""
        if not self.file_queue:
            self.log("请先拖放markdown文件")
            return
            
        if self.is_translating:
            self.log("翻译正在进行中，请等待...")
            return
            
        try:
            # 禁用开始按钮并立即更新UI
            self.start_button.state(['disabled'])
            self.root.update_idletasks()  # 强制更新UI
            
            # 设置翻译状态
            self.is_translating = True
            self.is_paused = False
            self.should_stop = False
            
            # 清除之前的进度条
            self.clear_chapter_progress()
            
            # 在新线程中运行翻译过程
            self.translation_thread = threading.Thread(target=self._run_translation)
            self.translation_thread.daemon = True
            self.translation_thread.start()
            
            # 启动进度更新检查
            self._check_translation_progress()
            
        except Exception as e:
            self.log(f"启动翻译时出错: {str(e)}")
            self._reset_button()

    def _run_translation(self):
        """在新线程中运行翻译过程"""
        try:
            self.translation_process()
        except Exception as e:
            self.log(f"翻译过程出错: {str(e)}")
        finally:
            # 重置按钮状态
            self.root.after(0, self._reset_button)

    def _update_chapter_progress(self, chapter_index, value):
        """在主线程中更新章节进度条"""
        def update():
            try:
                if not self.root.winfo_exists():
                    return
                if chapter_index in self.chapter_progress_vars:
                    self.chapter_progress_vars[chapter_index].set(value)
            except Exception as e:
                print(f"更新章节进度条时出错: {str(e)}")
        
        self._queue_ui_update(update)
    
    def _update_total_progress(self, completed_paragraphs, total_paragraphs):
        """在主线程中更新总进度条"""
        def update():
            try:
                if not self.root.winfo_exists():
                    return
                self.completed_paragraphs = completed_paragraphs
                self.total_paragraphs = total_paragraphs
                if total_paragraphs > 0:
                    progress = (completed_paragraphs / total_paragraphs) * 100
                    self.total_progress_var.set(progress)
                    if hasattr(self, 'current_chapter_label') and self.current_chapter_label.winfo_exists():
                        self.current_chapter_label.config(text=f"已翻译: {completed_paragraphs}/{total_paragraphs} 段")
            except Exception as e:
                print(f"更新总进度条时出错: {str(e)}")
        
        self._queue_ui_update(update)

def main():
    root = tkdnd.TkinterDnD.Tk()
    app = TranslatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
