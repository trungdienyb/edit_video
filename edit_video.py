import os
import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx, afx
from moviepy.video.fx import all as vfx_all
import numpy as np
from skimage import metrics
from PIL import Image, ImageTk
import mutagen
from mutagen.mp4 import MP4
import time
import threading

class VideoEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Video Editor (30% Difference)")
        self.root.geometry("900x700")
        
        # Variables
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.target_diff = tk.IntVar(value=30)
        self.progress = tk.DoubleVar()
        self.status = tk.StringVar(value="Ready")
        self.log_text = tk.StringVar()
        self.preview_frame = None
        
        # Create GUI
        self.create_widgets()
        
    def create_widgets(self):
        # Input/Output Section
        input_frame = ttk.LabelFrame(self.root, text="Input/Output")
        input_frame.pack(pady=10, padx=10, fill="x")
        
        ttk.Label(input_frame, text="Input Video:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(input_frame, textvariable=self.input_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(input_frame, text="Browse", command=self.browse_input).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Output Video:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(input_frame, textvariable=self.output_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(input_frame, text="Browse", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)
        
        # Settings Section
        settings_frame = ttk.LabelFrame(self.root, text="Settings")
        settings_frame.pack(pady=10, padx=10, fill="x")
        
        ttk.Label(settings_frame, text="Target Difference (%):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Spinbox(settings_frame, from_=30, to=100, textvariable=self.target_diff, width=5).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Preview Section
        preview_frame = ttk.LabelFrame(self.root, text="Preview")
        preview_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(self.root, text="Progress")
        progress_frame.pack(pady=10, padx=10, fill="x")
        
        ttk.Label(progress_frame, textvariable=self.status).pack(pady=5, padx=5, anchor="w")
        ttk.Progressbar(progress_frame, variable=self.progress, maximum=100).pack(pady=5, padx=5, fill="x")
        
        # Log Section
        log_frame = ttk.LabelFrame(self.root, text="Processing Log")
        log_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.log_textbox = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_textbox.pack(pady=5, padx=5, fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_textbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_textbox.config(yscrollcommand=scrollbar.set)
        
        # Button Section
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10, padx=10, fill="x")
        
        ttk.Button(button_frame, text="Process Video", command=self.start_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
    
    def browse_input(self):
        filepath = filedialog.askopenfilename(
            title="Select Input Video",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv"), ("All Files", "*.*")]
        )
        if filepath:
            self.input_path.set(filepath)
            if not self.output_path.get():
                base, ext = os.path.splitext(filepath)
                self.output_path.set(f"{base}_edited{ext}")
            self.show_preview()
    
    def browse_output(self):
        filepath = filedialog.asksaveasfilename(
            title="Save Output Video",
            defaultextension=".mp4",
            filetypes=[("MP4 Files", "*.mp4"), ("All Files", "*.*")]
        )
        if filepath:
            self.output_path.set(filepath)
    
    def show_preview(self):
        try:
            clip = VideoFileClip(self.input_path.get())
            frame = clip.get_frame(0)  # Get first frame
            
            # Convert numpy array to PIL Image
            img = Image.fromarray(frame)
            img.thumbnail((400, 400))  # Resize for preview
            self.preview_frame = ImageTk.PhotoImage(img)
            
            self.preview_label.config(image=self.preview_frame)
            clip.close()
        except Exception as e:
            self.log(f"Preview error: {str(e)}")
    
    def log(self, message):
        self.log_textbox.insert(tk.END, f"{message}\n")
        self.log_textbox.see(tk.END)
        self.root.update()
    
    def update_status(self, message):
        self.status.set(message)
        self.log(message)
        self.root.update()
    
    def update_progress(self, value):
        self.progress.set(value)
        self.root.update()
    
    def start_processing(self):
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select an input video file")
            return
        
        if not self.output_path.get():
            messagebox.showerror("Error", "Please select an output video file")
            return
        
        # Disable buttons during processing
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state=tk.DISABLED)
        
        # Start processing in a separate thread
        processing_thread = threading.Thread(target=self.process_video)
        processing_thread.daemon = True
        processing_thread.start()
    
    def cancel_processing(self):
        self.update_status("Processing cancelled by user")
        # In a real application, you would need to implement proper thread cancellation
    
    def calculate_video_difference(self, original_path, edited_path):
        """Calculate the percentage difference between two videos"""
        self.update_status("Calculating difference between videos...")
        
        original = VideoFileClip(original_path)
        edited = VideoFileClip(edited_path)
        
        # Compare frames at regular intervals for efficiency
        sample_points = 10
        step = original.duration / (sample_points + 1)
        differences = []
        
        for i in range(1, sample_points + 1):
            t = i * step
            try:
                orig_frame = original.get_frame(t)
                edited_frame = edited.get_frame(t)
                
                # Calculate structural similarity index
                ssim = metrics.structural_similarity(
                    orig_frame, edited_frame, 
                    multichannel=True, 
                    win_size=min(7, min(orig_frame.shape[0], orig_frame.shape[1])-1),
                    channel_axis=2
                )
                differences.append(1 - ssim)
                
                # Update progress
                self.update_progress((i / (sample_points + 1)) * 100)
            except Exception as e:
                self.log(f"Error comparing frame at {t:.2f}s: {str(e)}")
                continue
        
        original.close()
        edited.close()
        
        avg_diff = np.mean(differences) * 100
        self.log(f"Video difference calculation complete: {avg_diff:.2f}%")
        return avg_diff
    
    def modify_metadata(self, filepath):
        """Completely modify video metadata"""
        self.update_status("Modifying video metadata...")
        
        try:
            if filepath.lower().endswith('.mp4'):
                # For MP4 files
                video = MP4(filepath)
                
                # Clear all existing metadata
                video.clear()
                
                # Add new random metadata
                video['\xa9nam'] = "Edited Video"
                video['\xa9alb'] = "Modified Content"
                video['\xa9ART'] = "Video Editor"
                video['\xa9day'] = str(random.randint(2000, 2023))
                video['\xa9cmt'] = "This video has been modified"
                video['\xa9gen'] = "Edited"
                video['\xa9grp'] = "Modified"
                video['\xa9too'] = "Python Video Editor"
                video['\xa9wrt'] = "Anonymous"
                
                video.save()
            else:
                # For other formats, we'll use mutagen's generic file handling
                video = mutagen.File(filepath, easy=True)
                if video is not None:
                    video.delete()
                    video['title'] = "Edited Video"
                    video['artist'] = "Video Editor"
                    video.save()
        except Exception as e:
            self.log(f"Metadata modification error: {str(e)}")
    
    def process_video(self):
        try:
            input_path = self.input_path.get()
            output_path = self.output_path.get()
            target_diff = self.target_diff.get()
            
            if not os.path.exists(input_path):
                self.update_status(f"Input file {input_path} not found!")
                return
            
            self.update_status("Starting video processing...")
            self.update_progress(0)
            
            # Load original video and remove audio
            self.update_status("Loading video and removing audio...")
            clip = VideoFileClip(input_path)
            clip = clip.without_audio()  # Remove all audio
            
            # Apply transformations
            transformations = [
                {"name": "Speed Change", "func": lambda c: c.fx(vfx_all.speedx, random.uniform(0.7, 1.5))},
                {"name": "Color Adjustment", "func": lambda c: c.fx(vfx_all.colorx, random.uniform(0.7, 1.3))},
                {"name": "Brightness/Contrast", "func": lambda c: c.fx(vfx_all.lum_contrast, 
                                                                     lum=random.uniform(-0.3, 0.3), 
                                                                     contrast=random.uniform(0.7, 1.5))},
                {"name": "Rotation", "func": lambda c: c.fx(vfx_all.rotate, random.uniform(-15, 15))},
                {"name": "Horizontal Flip", "func": lambda c: c.fx(vfx_all.mirror_x)},
                {"name": "Vertical Flip", "func": lambda c: c.fx(vfx_all.mirror_y)},
                {"name": "Cropping", "func": lambda c: c.fx(vfx_all.crop, 
                                                          x1=random.uniform(0, 0.2)*c.w, 
                                                          y1=random.uniform(0, 0.2)*c.h,
                                                          x2=random.uniform(0.8, 1)*c.w,
                                                          y2=random.uniform(0.8, 1)*c.h)},
                {"name": "Fade In", "func": lambda c: c.fx(vfx_all.fadein, random.uniform(0.5, 2))},
                {"name": "Fade Out", "func": lambda c: c.fx(vfx_all.fadeout, random.uniform(0.5, 2))},
                {"name": "Black & White", "func": lambda c: c.fx(vfx_all.blackwhite)},
                {"name": "Gamma Correction", "func": lambda c: c.fx(vfx_all.gamma_corr, random.uniform(0.5, 1.5))},
            ]
            
            edited_clip = clip
            applied_transforms = []
            temp_path = "temp_edited.mp4"
            
            # Apply transformations until target difference is reached
            attempts = 0
            max_attempts = 15  # Safety limit
            
            while attempts < max_attempts:
                # Select and apply random transformation
                transform = random.choice(transformations)
                self.update_status(f"Applying {transform['name']}...")
                
                try:
                    edited_clip = transform["func"](edited_clip)
                    applied_transforms.append(transform['name'])
                    
                    # Write temporary file to check difference
                    self.update_status("Writing temporary file for difference check...")
                    edited_clip.write_videofile(temp_path, codec='libx264', audio_codec='aac', 
                                              threads=4, preset='fast', logger='bar')
                    
                    # Calculate difference
                    self.update_status("Calculating difference from original...")
                    current_diff = self.calculate_video_difference(input_path, temp_path)
                    self.log(f"Attempt {attempts + 1}: Difference = {current_diff:.2f}%")
                    self.update_progress((attempts + 1) * (100 / max_attempts))
                    
                    if current_diff >= target_diff:
                        break
                    
                    attempts += 1
                except Exception as e:
                    self.log(f"Error applying transformation: {str(e)}")
                    attempts += 1
                    continue
            
            # Final save
            self.update_status("Writing final output file...")
            edited_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', 
                                      threads=4, preset='fast', logger='bar')
            
            # Modify metadata
            self.modify_metadata(output_path)
            
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            clip.close()
            edited_clip.close()
            
            self.update_status(f"Processing complete! Final difference: {current_diff:.2f}%")
            self.update_progress(100)
            self.log("\nApplied transformations:")
            for i, transform in enumerate(applied_transforms, 1):
                self.log(f"{i}. {transform}")
            
            messagebox.showinfo("Success", "Video processing completed successfully!")
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            # Re-enable buttons
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Button):
                    widget.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoEditorApp(root)
    root.mainloop()
