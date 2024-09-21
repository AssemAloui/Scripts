import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cups
import subprocess
from io import BytesIO
import os

A4_WIDTH = 3508  # A4 width in pixels at 300 DPI
A4_HEIGHT = 2480  # A4 height in pixels at 300 DPI

def print_images(image1_path, image2_path, color_mode):
    conn = cups.Connection()
    printers = conn.getPrinters()
    printer_name = list(printers.keys())[0]

    img1 = Image.open(image1_path)
    img2 = Image.open(image2_path)

    if color_mode == "Black & White":
        img1 = img1.convert('L')
        img2 = img2.convert('L')

    img1 = img1.resize((A4_WIDTH // 2, A4_HEIGHT), Image.ANTIALIAS)
    img2 = img2.resize((A4_WIDTH // 2, A4_HEIGHT), Image.ANTIALIAS)

    combined_image = Image.new('RGB', (A4_WIDTH, A4_HEIGHT))
    combined_image.paste(img1, (0, 0))  # Left side
    combined_image.paste(img2, (A4_WIDTH // 2, 0))  # Right side

    combined_path = "/tmp/combined_image.png"
    combined_image.save(combined_path)

    conn.printFile(printer_name, combined_path, "Photo Print", {})

    os.remove(combined_path)

def save_as_pdf(image1_path, image2_path, output_path, color_mode):
    img1 = Image.open(image1_path)
    img2 = Image.open(image2_path)

    if color_mode == "Black & White":
        img1 = img1.convert('L')
        img2 = img2.convert('L')

    img1 = img1.resize((A4_WIDTH // 2, A4_HEIGHT), Image.ANTIALIAS)
    img2 = img2.resize((A4_WIDTH // 2, A4_HEIGHT), Image.ANTIALIAS)

    combined_image = Image.new('RGB', (A4_WIDTH, A4_HEIGHT))
    combined_image.paste(img1, (0, 0))
    combined_image.paste(img2, (A4_WIDTH // 2, 0))

    combined_image.save(output_path, "PDF", resolution=100.0)

def handle_print(image1_path, image2_path, color_mode, output_option):
    try:
        if output_option.get() == "Printer":
            print_images(image1_path, image2_path, color_mode.get())
            messagebox.showinfo("Success", "Photos sent to the printer!")
        elif output_option.get() == "PDF":
            save_location = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save as PDF"
            )
            if save_location:
                save_as_pdf(image1_path, image2_path, save_location, color_mode.get())
                messagebox.showinfo("Success", "Images saved as PDF!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to print or save as PDF: {e}")

def browse_file(img_display_label):
    file_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
    )
    if file_path:
        img = Image.open(file_path)
        img.thumbnail((200, 200))
        img_display = ImageTk.PhotoImage(img)
        img_display_label.config(image=img_display)
        img_display_label.image = img_display

        return file_path
    return None

def paste_image_from_clipboard(img_display_label, canvas_frame):
    try:
        process = subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'], stdout=subprocess.PIPE)
        if process.returncode == 0:
            img_data = process.stdout
            img = Image.open(BytesIO(img_data))

            if img.mode == 'RGBA':
                img = img.convert('RGB')

            img_display = ImageTk.PhotoImage(img)
            img_display_label.config(image=img_display)
            img_display_label.image = img_display

            img_width, img_height = img.size
            canvas_frame.config(scrollregion=(0, 0, img_width, img_height))

            clipboard_img_path = f"/tmp/clipboard_image_{img_display_label}.png"
            img.save(clipboard_img_path, "PNG", quality=95)

            return clipboard_img_path
        else:
            raise Exception("No image in clipboard")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to paste image: {e}")
    return None

def create_gui():
    window = tk.Tk()
    window.title("Two Photo Print")

    canvas_frame = tk.Canvas(window)
    canvas_frame.pack(fill=tk.BOTH, expand=True)

    scrollbar_y = tk.Scrollbar(window, orient="vertical", command=canvas_frame.yview)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

    scrollbar_x = tk.Scrollbar(window, orient="horizontal", command=canvas_frame.xview)
    scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

    canvas_frame.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

    img_frame = tk.Frame(canvas_frame)
    canvas_frame.create_window((0, 0), window=img_frame, anchor="nw")

    img1_display_label = tk.Label(img_frame, text="Image 1")
    img1_display_label.grid(row=0, column=0, padx=10, pady=10)

    img2_display_label = tk.Label(img_frame, text="Image 2")
    img2_display_label.grid(row=0, column=1, padx=10, pady=10)

    selected_img1 = None
    selected_img2 = None

    def set_img1(img):
        nonlocal selected_img1
        selected_img1 = img

    def set_img2(img):
        nonlocal selected_img2
        selected_img2 = img

    browse1_button = tk.Button(window, text="Browse Image 1", command=lambda: set_img1(browse_file(img1_display_label)))
    browse1_button.pack(padx=10, pady=5)

    paste1_button = tk.Button(window, text="Paste Image 1", command=lambda: set_img1(paste_image_from_clipboard(img1_display_label, canvas_frame)))
    paste1_button.pack(padx=10, pady=5)

    browse2_button = tk.Button(window, text="Browse Image 2", command=lambda: set_img2(browse_file(img2_display_label)))
    browse2_button.pack(padx=10, pady=5)

    paste2_button = tk.Button(window, text="Paste Image 2", command=lambda: set_img2(paste_image_from_clipboard(img2_display_label, canvas_frame)))
    paste2_button.pack(padx=10, pady=5)

    color_label = tk.Label(window, text="Choose Printing Mode:")
    color_label.pack(padx=10, pady=5)

    color_mode = tk.StringVar(window)
    color_mode.set("Color")
    color_menu = tk.OptionMenu(window, color_mode, "Color", "Black & White")
    color_menu.pack(padx=10, pady=5)

    output_label = tk.Label(window, text="Choose Output:")
    output_label.pack(padx=10, pady=5)

    output_option = tk.StringVar(window)
    output_option.set("Printer")
    output_menu = tk.OptionMenu(window, output_option, "Printer", "PDF")
    output_menu.pack(padx=10, pady=5)

    print_button = tk.Button(window, text="Print", command=lambda: handle_print(selected_img1, selected_img2, color_mode, output_option))
    print_button.pack(pady=20)

    window.mainloop()

if __name__ == "__main__":
    create_gui()
