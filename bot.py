import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ffmpeg
import os
import random
import logging
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

class VideoEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Video Metadata Editor with Watermark")
        self.root.geometry("900x700")
        self.root.configure(bg="#1e1e1e")

        # Thiết lập logging
        logging.basicConfig(
            filename='video_editor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # Cập nhật đường dẫn theo yêu cầu
        self.input_dir = r"D:\Auto_editvideo\Video_download"
        self.output_dir = r"D:\Auto_editvideo\Video_output"
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        self.selected_files = []
        self.processing = False

        # Giao diện
        self.create_ui()

        # Tạo watermark nếu chưa có
        self.create_watermark()

    def create_ui(self):
        # Frame chính
        main_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tiêu đề
        title_label = tk.Label(
            main_frame,
            text="VIDEO EDITOR TOOL",
            font=("Arial", 18, "bold"),
            fg="#4CAF50",
            bg="#1e1e1e"
        )
        title_label.pack(pady=10)

        # Hiển thị đường dẫn
        path_frame = tk.Frame(main_frame, bg="#1e1e1e")
        path_frame.pack(fill=tk.X, pady=5)

        input_path_label = tk.Label(
            path_frame,
            text=f"Input Directory: {self.input_dir}",
            fg="white",
            bg="#1e1e1e",
            font=("Arial", 9)
        )
        input_path_label.pack(anchor="w")

        output_path_label = tk.Label(
            path_frame,
            text=f"Output Directory: {self.output_dir}",
            fg="white",
            bg="#1e1e1e",
            font=("Arial", 9)
        )
        output_path_label.pack(anchor="w")

        # Frame chọn file
        file_frame = tk.Frame(main_frame, bg="#2d2d2d")
        file_frame.pack(fill=tk.X, pady=5)

        select_button = tk.Button(
            file_frame,
            text="Select Videos",
            command=self.select_videos,
            bg="#2196F3",
            fg="white",
            font=("Arial", 12),
            width=15
        )
        select_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.files_label = tk.Label(
            file_frame,
            text="No videos selected",
            fg="white",
            bg="#2d2d2d",
            font=("Arial", 10),
            width=50
        )
        self.files_label.pack(side=tk.LEFT, padx=5)

        # Frame options với scrollbar
        options_frame = tk.Frame(main_frame, bg="#2d2d2d")
        options_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(options_frame, bg="#2d2d2d")
        self.scrollbar = tk.Scrollbar(options_frame, orient="vertical", command=self.canvas.yview)
        self.options_container = tk.Frame(self.canvas, bg="#2d2d2d")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.create_window((0, 0), window=self.options_container, anchor="nw")
        self.options_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Tạo các option widgets
        self.create_option_widgets()

        # Nút xử lý
        button_frame = tk.Frame(main_frame, bg="#1e1e1e")
        button_frame.pack(fill=tk.X, pady=10)

        self.apply_button = tk.Button(
            button_frame,
            text="PROCESS VIDEOS",
            command=self.process_videos,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            state=tk.DISABLED,
            width=20
        )
        self.apply_button.pack(pady=5)

        # Thanh tiến trình
        self.progress = ttk.Progressbar(
            button_frame,
            orient=tk.HORIZONTAL,
            mode='determinate',
            style="green.Horizontal.TProgressbar"
        )
        self.progress.pack(fill=tk.X, pady=5)

        # Tạo style cho progressbar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("green.Horizontal.TProgressbar", 
                       background='#4CAF50',
                       troughcolor='#2d2d2d',
                       bordercolor='#2d2d2d',
                       lightcolor='#4CAF50',
                       darkcolor='#4CAF50')

    def create_option_widgets(self):
        # Các tùy chọn metadata
        self.options = {
            "VIDEO SETTINGS": [
                ("Resolution", ["Keep original", "1280x720 (HD)", "1920x1080 (Full HD)", "2560x1440 (2K)", "3840x2160 (4K)"]),
                ("Frame Rate", ["Keep original", "24fps", "30fps", "60fps", "120fps"]),
                ("Video Codec", ["Keep original", "H.264 (AVC)", "H.265 (HEVC)", "MPEG-4"]),
                ("Video Bitrate", ["Keep original", "1 Mbps", "3 Mbps", "5 Mbps", "8 Mbps", "12 Mbps"]),
            ],
            "AUDIO SETTINGS": [
                ("Audio Codec", ["Keep original", "AAC", "MP3", "AC3"]),
                ("Audio Bitrate", ["Keep original", "128 kbps", "192 kbps", "256 kbps", "320 kbps"]),
                ("Sample Rate", ["Keep original", "44.1 kHz", "48 kHz", "96 kHz"]),
            ],
            "METADATA": [
                ("Title", ["Custom Title", "My Video 1", "My Video 2"]),
                ("Artist", ["Custom Artist", "Artist 1", "Artist 2"]),
                ("Copyright", ["None", "© My Company"]),  # Cho phép nhập tùy ý
                ("Creation Date", ["Today", "2023-01-01", "2024-01-01"]),
            ],
            "WATERMARK": [
                ("Add Watermark", ["Yes", "No"]),
                ("Watermark Position", ["Random", "Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right"]),
                ("Watermark Opacity", ["50%", "30%", "70%", "100%"]),
            ]
        }

        self.option_vars = {}
        self.option_widgets = {}

        # Tạo widgets cho từng nhóm option
        for group_name, options in self.options.items():
            group_frame = tk.LabelFrame(
                self.options_container,
                text=group_name,
                bg="#2d2d2d",
                fg="#4CAF50",
                font=("Arial", 10, "bold"),
                padx=5,
                pady=5
            )
            group_frame.pack(fill=tk.X, padx=5, pady=5, ipady=5)

            for i, (option_name, values) in enumerate(options):
                frame = tk.Frame(group_frame, bg="#2d2d2d")
                frame.grid(row=i, column=0, sticky="w", padx=5, pady=2)

                # Riêng với "Add Watermark" thì dùng Radiobutton thay vì Checkbutton
                if option_name == "Add Watermark":
                    var = tk.StringVar(value=values[0])
                    for j, val in enumerate(values):
                        rb = tk.Radiobutton(
                            frame,
                            text=val,
                            variable=var,
                            value=val,
                            bg="#2d2d2d",
                            fg="white",
                            selectcolor="#2d2d2d",
                            activebackground="#2d2d2d",
                            command=self.update_apply_button
                        )
                        rb.pack(side=tk.LEFT, padx=5)
                    self.option_vars[option_name] = var
                    self.option_widgets[option_name] = var
                else:
                    var = tk.BooleanVar(value=False)
                    chk = tk.Checkbutton(
                        frame,
                        text=option_name,
                        variable=var,
                        bg="#2d2d2d",
                        fg="white",
                        selectcolor="#4CAF50",
                        activebackground="#2d2d2d",
                        command=self.update_apply_button
                    )
                    chk.pack(side=tk.LEFT)
                    self.option_vars[option_name] = var

                    if option_name == "Copyright":
                        entry = tk.Entry(
                            frame,
                            bg="#3c3c3c",
                            fg="white",
                            insertbackground="white",
                            width=25
                        )
                        entry.pack(side=tk.LEFT, padx=5)
                        self.option_widgets[option_name] = entry
                    else:
                        combo = ttk.Combobox(
                            frame,
                            values=values,
                            state="readonly",
                            width=20
                        )
                        combo.set(values[0])
                        combo.pack(side=tk.LEFT, padx=5)
                        self.option_widgets[option_name] = combo

    def update_apply_button(self):
        any_selected = any(var.get() for name, var in self.option_vars.items() if name != "Add Watermark")
        watermark_selected = self.option_vars.get("Add Watermark", tk.StringVar(value="No")).get() == "Yes"
        self.apply_button.config(state=tk.NORMAL if any_selected or watermark_selected else tk.DISABLED)

    def select_videos(self):
        if self.processing:
            messagebox.showwarning("Warning", "Processing in progress. Please wait.")
            return

        files = filedialog.askopenfilenames(
            initialdir=self.input_dir,
            title="Select Videos",
            filetypes=(
                ("Video files", "*.mp4 *.avi *.mkv *.mov *.flv *.webm"),
                ("All files", "*.*")
            )
        )

        if files:
            self.selected_files = files
            self.files_label.config(text=f"Selected: {len(files)} video(s) - {os.path.basename(files[0])}{'...' if len(files) > 1 else ''}")
            self.update_apply_button()

    def create_watermark(self):
        watermark_path = "watermark.png"
        if not os.path.exists(watermark_path):
            try:
                img = Image.new('RGBA', (300, 100), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                try:
                    font = ImageFont.truetype("arial.ttf", 40)
                except:
                    font = ImageFont.load_default().font_variant(size=40)
                
                # Tạo watermark với hiệu ứng
                draw.text((10, 10), "YOUR BRAND", font=font, fill=(255, 255, 255, 180))
                
                # Thêm border
                for i in range(1, 3):
                    draw.rectangle(
                        [(10-i, 10-i), (290+i, 90+i)],
                        outline=(255, 255, 255, 80),
                        width=1
                    )
                
                img.save(watermark_path)
                logging.info(f"Created watermark at {watermark_path}")
            except Exception as e:
                logging.error(f"Failed to create watermark: {str(e)}")
                messagebox.showerror("Error", f"Failed to create watermark: {str(e)}")

    def sanitize_filename(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename

    def get_watermark_position(self, width, height):
        position = self.option_widgets["Watermark Position"].get()
        watermark_width = 300
        watermark_height = 100

        if position == "Random":
            x = random.randint(20, max(20, width - watermark_width - 20))
            y = random.randint(20, max(20, height - watermark_height - 20))
        elif position == "Top-Left":
            x = 20
            y = 20
        elif position == "Top-Right":
            x = max(20, width - watermark_width - 20)
            y = 20
        elif position == "Bottom-Left":
            x = 20
            y = max(20, height - watermark_height - 20)
        elif position == "Bottom-Right":
            x = max(20, width - watermark_width - 20)
            y = max(20, height - watermark_height - 20)
        else:
            x = 20
            y = 20

        return x, y

    def process_videos(self):
        if not self.selected_files:
            messagebox.showwarning("Warning", "Please select at least one video!")
            return

        if self.processing:
            messagebox.showwarning("Warning", "Processing already in progress!")
            return

        self.processing = True
        self.apply_button.config(state=tk.DISABLED, text="PROCESSING...")
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.selected_files)
        self.root.update()

        try:
            # Chuẩn bị các tham số
            output_params = {
                'preset': 'fast',
                'crf': '23'  # Chất lượng mặc định
            }
            metadata = {}

            # Video settings
            if self.option_vars["Resolution"].get():
                res = self.option_widgets["Resolution"].get()
                if res != "Keep original":
                    output_params['s'] = res.split(' ')[0].replace('x', ':')

            if self.option_vars["Frame Rate"].get():
                fps = self.option_widgets["Frame Rate"].get()
                if fps != "Keep original":
                    output_params['r'] = fps.replace('fps', '')

            if self.option_vars["Video Codec"].get():
                codec = self.option_widgets["Video Codec"].get()
                if codec != "Keep original":
                    codec_map = {
                        "H.264 (AVC)": "libx264",
                        "H.265 (HEVC)": "libx265",
                        "MPEG-4": "mpeg4"
                    }
                    output_params['vcodec'] = codec_map.get(codec, "libx264")

            if self.option_vars["Video Bitrate"].get():
                bitrate = self.option_widgets["Video Bitrate"].get()
                if bitrate != "Keep original":
                    output_params['b:v'] = bitrate.split(' ')[0] + "k"  # Chuyển đổi thành 1000k

            # Audio settings
            if self.option_vars["Audio Codec"].get():
                codec = self.option_widgets["Audio Codec"].get()
                if codec != "Keep original":
                    codec_map = {
                        "AAC": "aac",
                        "MP3": "libmp3lame",
                        "AC3": "ac3"
                    }
                    output_params['acodec'] = codec_map.get(codec, "aac")

            if self.option_vars["Audio Bitrate"].get():
                bitrate = self.option_widgets["Audio Bitrate"].get()
                if bitrate != "Keep original":
                    output_params['b:a'] = bitrate.split(' ')[0]

            if self.option_vars["Sample Rate"].get():
                sr = self.option_widgets["Sample Rate"].get()
                if sr != "Keep original":
                    output_params['ar'] = sr.split(' ')[0].replace('.', '')

            # Metadata settings
            if self.option_vars["Title"].get():
                title = self.option_widgets["Title"].get()
                metadata['title'] = "My Video" if title == "Custom Title" else title

            if self.option_vars["Artist"].get():
                artist = self.option_widgets["Artist"].get()
                metadata['artist'] = "My Artist" if artist == "Custom Artist" else artist

            if self.option_vars["Copyright"].get():
                copyright_text = self.option_widgets["Copyright"].get()
                if copyright_text != "None":
                    metadata['copyright'] = copyright_text

            if self.option_vars["Creation Date"].get():
                date = self.option_widgets["Creation Date"].get()
                if date == "Today":
                    metadata['creation_time'] = datetime.now().strftime("%Y-%m-%d")
                elif date != "None":
                    metadata['creation_time'] = date

            # Kiểm tra xem có cần thêm watermark không
            add_watermark = self.option_vars.get("Add Watermark", tk.StringVar(value="No")).get() == "Yes"

            # Xử lý từng file
            for i, input_file in enumerate(self.selected_files):
                try:
                    output_file = os.path.join(
                        self.output_dir,
                        f"edited_{self.sanitize_filename(os.path.basename(input_file))}"
                    )

                    # Kiểm tra file đầu vào
                    if not os.path.exists(input_file):
                        logging.error(f"Input file not found: {input_file}")
                        continue

                    # Tạo FFmpeg command
                    input_stream = ffmpeg.input(input_file)
                    video = input_stream['v']
                    audio = input_stream['a']

                    # Áp dụng watermark nếu cần
                    if add_watermark:
                        watermark_path = "watermark.png"
                        if os.path.exists(watermark_path):
                            try:
                                probe = ffmpeg.probe(input_file)
                                video_stream = next(
                                    (s for s in probe['streams'] if s['codec_type'] == 'video'),
                                    None
                                )
                                
                                if video_stream:
                                    width = int(video_stream['width'])
                                    height = int(video_stream['height'])
                                    x, y = self.get_watermark_position(width, height)
                                    
                                    opacity = float(
                                        self.option_widgets["Watermark Opacity"].get().replace('%', '')
                                    ) / 100.0
                                    
                                    watermark = ffmpeg.input(watermark_path).filter('format', 'argb')
                                    watermark = watermark.filter('colorchannelmixer', aa=opacity)
                                    video = ffmpeg.overlay(video, watermark, x=x, y=y)
                            except Exception as e:
                                logging.error(f"Watermark error: {str(e)}")

                    # Thêm metadata
                    if metadata:
                        output_params.update({f'metadata:{k}': v for k, v in metadata.items()})

                    # Chạy FFmpeg
                    stream = ffmpeg.output(
                        video,
                        audio,
                        output_file,
                        **output_params
                    )

                    ffmpeg.run(stream, overwrite_output=True)

                    # Cập nhật tiến trình
                    self.progress["value"] = i + 1
                    self.root.update()

                    logging.info(f"Successfully processed: {input_file} -> {output_file}")

                except ffmpeg.Error as e:
                    error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
                    logging.error(f"FFmpeg error processing {input_file}: {error_msg}")
                    messagebox.showerror(
                        "Error",
                        f"Failed to process {os.path.basename(input_file)}:\n{error_msg}"
                    )
                except Exception as e:
                    logging.error(f"Error processing {input_file}: {str(e)}")
                    messagebox.showerror(
                        "Error",
                        f"Unexpected error processing {os.path.basename(input_file)}:\n{str(e)}"
                    )

            messagebox.showinfo(
                "Success",
                f"Processed {len(self.selected_files)} video(s) successfully!\n"
                f"Output directory: {self.output_dir}"
            )

        finally:
            self.processing = False
            self.apply_button.config(state=tk.NORMAL, text="PROCESS VIDEOS")
            self.progress["value"] = 0

if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = VideoEditorApp(root)
        root.mainloop()
    except Exception as e:
        logging.critical(f"Application error: {str(e)}")
        messagebox.showerror("Critical Error", f"The application encountered an error:\n{str(e)}")
