import os
import sys
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageEnhance, ImageSequence

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Watermark Applicator")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        self.SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')

        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure("TSpinbox", arrowsize=15)
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        self.create_directories()

        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=BOTH, expand=True)

        ttk.Label(main_frame, text="Watermark Opacity:").grid(row=0, column=0, sticky=W, pady=10)
        self.opacity_var = DoubleVar(value=0.5)
        opacity_scale = ttk.Scale(main_frame, from_=0.0, to=1.0, orient=HORIZONTAL, variable=self.opacity_var)
        opacity_scale.grid(row=0, column=1, sticky=EW, pady=10, padx=5)
        opacity_spinbox = ttk.Spinbox(main_frame, from_=0.0, to=1.0, increment=0.05, textvariable=self.opacity_var, width=6)
        opacity_spinbox.grid(row=0, column=2, sticky=W, pady=10)

        ttk.Label(main_frame, text="Watermark Scale (%):").grid(row=1, column=0, sticky=W, pady=10)
        self.scale_var = DoubleVar(value=15.0)
        scale_scale = ttk.Scale(main_frame, from_=1.0, to=100.0, orient=HORIZONTAL, variable=self.scale_var)
        scale_scale.grid(row=1, column=1, sticky=EW, pady=10, padx=5)
        scale_spinbox = ttk.Spinbox(main_frame, from_=1.0, to=100.0, increment=1.0, textvariable=self.scale_var, width=6)
        scale_spinbox.grid(row=1, column=2, sticky=W, pady=10)

        ttk.Label(main_frame, text="Watermark Position:").grid(row=2, column=0, sticky=W, pady=10)
        self.position_var = StringVar(value='Bottom Right')
        positions = ['Top Left', 'Top Right', 'Bottom Left', 'Bottom Right', 'Center']
        position_menu = ttk.Combobox(main_frame, textvariable=self.position_var, values=positions, state='readonly')
        position_menu.grid(row=2, column=1, columnspan=2, sticky=EW, pady=10)

        ttk.Label(main_frame, text="Corner Margin (pixels):").grid(row=3, column=0, sticky=W, pady=10)
        self.margin_var = IntVar(value=10)
        margin_spinbox = ttk.Spinbox(main_frame, from_=0, to=200, textvariable=self.margin_var, width=6)
        margin_spinbox.grid(row=3, column=1, sticky=W, pady=10)

        ttk.Separator(main_frame, orient=HORIZONTAL).grid(row=4, columnspan=3, sticky=EW, pady=15)
        
        self.status_var = StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=SUNKEN, anchor=W, padding=5)
        status_label.grid(row=5, columnspan=3, sticky=EW, pady=(0, 10))

        apply_button = ttk.Button(main_frame, text="Apply Watermark to All Images", command=self.process_images)
        apply_button.grid(row=6, columnspan=3, sticky=EW, ipady=5)

        main_frame.columnconfigure(1, weight=1)

    def create_directories(self):

        for folder in ['input', 'output', 'watermark']:
            os.makedirs(os.path.join(self.base_path, folder), exist_ok=True)

    def process_images(self):

        self.status_var.set("Processing...")
        self.root.update_idletasks()

        input_dir = os.path.join(self.base_path, 'input')
        output_dir = os.path.join(self.base_path, 'output')
        watermark_dir = os.path.join(self.base_path, 'watermark')

        try:
            watermark_filename = next((f for f in os.listdir(watermark_dir) if f.lower().endswith(self.SUPPORTED_FORMATS)), None)
            if not watermark_filename:
                raise FileNotFoundError("No watermark image found. Please add one to the 'watermark' folder.")
            
            watermark_path = os.path.join(watermark_dir, watermark_filename)
            watermark_image = Image.open(watermark_path).convert("RGBA")

            image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(self.SUPPORTED_FORMATS)]
            if not image_files:
                 raise FileNotFoundError("No images found in 'input' folder.")

            processed_count = 0
            for filename in image_files:
                try:
                    base_image_path = os.path.join(input_dir, filename)

                    # work on copy
                    watermark_with_opacity = watermark_image.copy()
                    alpha = watermark_with_opacity.split()[3]
                    alpha = ImageEnhance.Brightness(alpha).enhance(self.opacity_var.get())
                    watermark_with_opacity.putalpha(alpha)
                    
                    # gif shit
                    if filename.lower().endswith('.gif'):
                        base_gif = Image.open(base_image_path)
                        duration = base_gif.info.get('duration', 100)
                        loop = base_gif.info.get('loop', 0)
                        
                        processed_frames = []
                        for frame in ImageSequence.Iterator(base_gif):
                            frame = frame.convert("RGBA")
                            
                            scale_percent = self.scale_var.get() / 100
                            target_width = int(frame.width * scale_percent)
                            w_percent = (target_width / float(watermark_with_opacity.size[0]))
                            h_size = int((float(watermark_with_opacity.size[1]) * float(w_percent)))
                            resized_watermark = watermark_with_opacity.resize((target_width, h_size), Image.Resampling.LANCZOS)
                            
                            margin = self.margin_var.get()
                            position = self.position_var.get()
                            bw, bh = frame.size
                            ww, wh = resized_watermark.size

                            if position == 'Top Left': pos = (margin, margin)
                            elif position == 'Top Right': pos = (bw - ww - margin, margin)
                            elif position == 'Bottom Left': pos = (margin, bh - wh - margin)
                            elif position == 'Center': pos = (int((bw - ww) / 2), int((bh - wh) / 2))
                            else: pos = (bw - ww - margin, bh - wh - margin)

                            frame.paste(resized_watermark, pos, resized_watermark)
                            processed_frames.append(frame)
                        
                        output_path = os.path.join(output_dir, os.path.splitext(filename)[0] + '.gif')
                        processed_frames[0].save(output_path, save_all=True, append_images=processed_frames[1:], duration=duration, loop=loop, disposal=2)

                    else: # static image
                        base_image = Image.open(base_image_path).convert("RGBA")
                        
                        scale_percent = self.scale_var.get() / 100
                        target_width = int(base_image.width * scale_percent)
                        w_percent = (target_width / float(watermark_with_opacity.size[0]))
                        h_size = int((float(watermark_with_opacity.size[1]) * float(w_percent)))
                        resized_watermark = watermark_with_opacity.resize((target_width, h_size), Image.Resampling.LANCZOS)

                        margin = self.margin_var.get()
                        position = self.position_var.get()
                        bw, bh = base_image.size
                        ww, wh = resized_watermark.size

                        if position == 'Top Left': pos = (margin, margin)
                        elif position == 'Top Right': pos = (bw - ww - margin, margin)
                        elif position == 'Bottom Left': pos = (margin, bh - wh - margin)
                        elif position == 'Center': pos = (int((bw - ww) / 2), int((bh - wh) / 2))
                        else: pos = (bw - ww - margin, bh - wh - margin)
                        
                        base_image.paste(resized_watermark, pos, resized_watermark)
                        final_image = base_image.convert("RGB") 

                        output_path = os.path.join(output_dir, os.path.splitext(filename)[0] + '.jpg')
                        final_image.save(output_path, 'jpeg')
                        
                    processed_count += 1
                except Exception as img_err:
                    print(f"Could not process {filename}: {img_err}")
            
            if processed_count == 0 and image_files:
                raise Exception("None of the files in the input folder could be processed.")

            self.status_var.set(f"Success! {processed_count} images processed.")
            messagebox.showinfo("Success", f"All {processed_count} valid images have been watermarked and saved to the 'output' folder.")

        except FileNotFoundError as e:
            self.status_var.set(f"Error: {e}")
            messagebox.showerror("Error", str(e))
        except Exception as e:
            self.status_var.set("An error occurred.")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    root = Tk()
    app = WatermarkApp(root)
    root.mainloop()


