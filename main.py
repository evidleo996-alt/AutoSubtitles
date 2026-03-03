import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import os
import sys
from subtitle_generator import SubtitleGenerator

class SubtitleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 视频字幕生成工具")
        self.root.geometry("600x400")
        
        # 视频文件选择
        self.video_path_var = tk.StringVar()
        self.create_file_selection_ui()
        
        # 模型选择
        self.model_size_var = tk.StringVar(value="base")
        self.create_model_selection_ui()
        
        # 进度显示
        self.log_text = tk.Text(self.root, height=10, state="disabled")
        self.log_text.pack(pady=10, padx=10, fill="both", expand=True)
        
        # 生成按钮
        self.generate_btn = ttk.Button(self.root, text="生成字幕", command=self.start_generation)
        self.generate_btn.pack(pady=10)
        
        self.generator = None

    def create_file_selection_ui(self):
        frame = ttk.Frame(self.root)
        frame.pack(pady=10, padx=10, fill="x")
        
        ttk.Label(frame, text="视频文件:").pack(side="left")
        entry = ttk.Entry(frame, textvariable=self.video_path_var, width=50)
        entry.pack(side="left", padx=5, fill="x", expand=True)
        
        btn = ttk.Button(frame, text="选择文件", command=self.select_file)
        btn.pack(side="left")

    def create_model_selection_ui(self):
        frame = ttk.Frame(self.root)
        frame.pack(pady=5, padx=10, fill="x")
        
        ttk.Label(frame, text="模型大小:").pack(side="left")
        models = ["tiny", "base", "small", "medium", "large"]
        combobox = ttk.Combobox(frame, textvariable=self.model_size_var, values=models, state="readonly")
        combobox.pack(side="left", padx=5)
        ttk.Label(frame, text="(越大的模型越准确，但也越慢)").pack(side="left")

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[("视频文件", "*.mp4 *.mov *.avi *.mkv *.flv"), ("所有文件", "*.*")]
        )
        if file_path:
            self.video_path_var.set(file_path)

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def start_generation(self):
        video_path = self.video_path_var.get()
        if not video_path:
            messagebox.showwarning("警告", "请先选择视频文件！")
            return
        
        if not os.path.exists(video_path):
            messagebox.showerror("错误", "文件不存在！")
            return
            
        model_size = self.model_size_var.get()
        
        # 禁用按钮防止重复点击
        self.generate_btn.config(state="disabled")
        self.log(f"准备开始处理: {os.path.basename(video_path)}")
        
        # 在新线程中运行
        thread = threading.Thread(target=self.run_generation, args=(video_path, model_size))
        thread.start()

    def run_generation(self, video_path, model_size):
        try:
            # 初始化生成器
            if not self.generator or self.generator.model_size != model_size:
                self.generator = SubtitleGenerator(model_size=model_size, progress_callback=self.log_callback)
                self.generator.load_model()
            
            # 生成字幕
            output_path = self.generator.generate_subtitle(video_path)
            
            self.root.after(0, lambda: messagebox.showinfo("完成", f"字幕生成成功！\n保存路径: {output_path}"))
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"发生错误: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"生成失败: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.generate_btn.config(state="normal"))

    def log_callback(self, message):
        # 确保在主线程更新 UI
        self.root.after(0, lambda: self.log(message))

if __name__ == "__main__":
    root = tk.Tk()
    app = SubtitleApp(root)
    root.mainloop()
