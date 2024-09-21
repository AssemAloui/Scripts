import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cups
import subprocess
from io import BytesIO
import os

def print_image(image_path, color_mode):
    # Connect to the CUPS server
    conn = cups.Connection()

    # Get list of printers
    printers = conn.getPrinters()

    # Use the first printer
    printer_name = list(printers.keys())[0]

    # Define printing options based on color mode
    if color_mode == "Black & White":
        img = Image.open(image_path).convert('L')  # Convert to grayscale
        grayscale_path = "/tmp/grayscale_image.png"
        img.save(grayscale_path)  # Save the grayscale image temporarily
        image_path = grayscale_path

    # Print the image
    conn.printFile(printer_name, image_path, "Photo Print", {})

    # Remove temporary file if grayscale was used
    if color_mode == "Black & White":
        os.remove(grayscale_path)

def save_as_pdf(image_path, output_path, color_mode):
    img = Image.open(image_path)
    if color_mode == "Black & White":
        img = img.convert('L')  # Convert to grayscale
    img.save(output_path, "PDF", resolution=100.0)

def handle_print(selected_img, color_mode, output_option):
    try:
        if output_option.get() == "Printer":
            print_image(selected_img, color_mode.get())
            messagebox.showinfo("Success", "Photo sent to the printer!")
        elif output_option.get() == "PDF":
            save_location = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save as PDF"
            )
            if save_location:
                save_as_pdf(selected_img, save_location, color_mode.get())
                messagebox.showinfo("Success", "Image saved as PDF!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to print or save as PDF: {e}")

def browse_file(img_display_label):
    # Open file dialog to select a photo
    file_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
    )
    if file_path:
        img = Image.open(file_path)
        img.thumbnail((200, 200))  # Resize for thumbnail
        img_display = ImageTk.PhotoImage(img)
        img_display_label.config(image=img_display)
        img_display_label.image = img_display  # Keep a reference to avoid garbage collection

        return file_path
    return None

def paste_image_from_clipboard(img_display_label):
    # Use xclip to get the image from the clipboard (on Linux)
    try:
        process = subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'], stdout=subprocess.PIPE)
        if process.returncode == 0:
            img_data = process.stdout
            img = Image.open(BytesIO(img_data))
            
            # Convert to 'RGB' if the image is in 'RGBA' mode
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            # Check the image size and adjust thumbnail size if necessary
            img_display = ImageTk.PhotoImage(img)
            img_display_label.config(image=img_display)
            img_display_label.image = img_display  # Keep a reference to avoid garbage collection
            
            # Save the clipboard image to a temporary file with high quality
            clipboard_img_path = "/tmp/clipboard_image.png"
            img.save(clipboard_img_path, "PNG", quality=95)  # Adjust quality if needed

            return clipboard_img_path
        else:
            raise Exception("No image in clipboard")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to paste image: {e}")
    return None

def create_gui():
    # Create the main window
    window = tk.Tk()
    window.title("Photo Print")

    # Create a frame for the image and scrollbar
    img_frame = tk.Frame(window)
    img_frame.pack(fill=tk.BOTH, expand=True)

    # Create a canvas for the image
    canvas = tk.Canvas(img_frame)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create a scrollbar for the canvas
    scrollbar = tk.Scrollbar(img_frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.config(yscrollcommand=scrollbar.set)

    # Create an image preview label on the canvas
    img_display_label = tk.Label(canvas)
    canvas.create_window((0, 0), window=img_display_label, anchor="nw")

    # Set the image size update function
    def update_image_size(event):
        canvas.config(scrollregion=canvas.bbox("all"))

    # Bind the size update to canvas resizing
    canvas.bind("<Configure>", update_image_size)

    selected_img = None

    # Browse button
    browse_button = tk.Button(window, text="Browse", command=lambda: set_img(browse_file(img_display_label)))
    browse_button.pack(padx=10, pady=5)

    # Paste button to paste image from clipboard
    paste_button = tk.Button(window, text="Paste from Clipboard", command=lambda: set_img(paste_image_from_clipboard(img_display_label)))
    paste_button.pack(padx=10, pady=5)

    # Label for color selection
    color_label = tk.Label(window, text="Choose Printing Mode:")
    color_label.pack(padx=10, pady=5)

    # Dropdown menu for color/black-and-white selection
    color_mode = tk.StringVar(window)
    color_mode.set("Color")  # Default value
    color_menu = tk.OptionMenu(window, color_mode, "Color", "Black & White")
    color_menu.pack(padx=10, pady=5)

    # Label for output selection
    output_label = tk.Label(window, text="Choose Output:")
    output_label.pack(padx=10, pady=5)

    # Dropdown menu for printer/PDF output
    output_option = tk.StringVar(window)
    output_option.set("Printer")  # Default value
    output_menu = tk.OptionMenu(window, output_option, "Printer", "PDF")
    output_menu.pack(padx=10, pady=5)

    # Print button
    print_button = tk.Button(window, text="Print", command=lambda: handle_print(selected_img, color_mode, output_option))
    print_button.pack(pady=20)

    # Function to set the selected image
    def set_img(img):
        nonlocal selected_img
        selected_img = img

    # Run the GUI event loop
    window.mainloop()

if __name__ == "__main__":
    create_gui()
