import shutil
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image, ImageTk
from tksvg import SvgImage as TkSvgImage


class ImageHandler:

    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
    MAX_DISPLAY_NAME_LENGTH = 60
    SVG_RASTER_SCALE = 2.0

    def __init__(self, images_dir):
        self.images_dir = images_dir

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            return ImageTk.getimage(svg_photo).convert("RGBA")
        except (FileNotFoundError, OSError, ValueError, RuntimeError):
            return None

    def create_ctk_icon(self, svg_filename, size, scale=None):
        if scale is None:
            scale = self.SVG_RASTER_SCALE

        svg_path = self.images_dir / svg_filename
        pil_image = self.load_svg_image(svg_path, scale=scale)

        if not pil_image:
            return None

        # Crop to content bounds
        try:
            alpha_channel = pil_image.getchannel("A")
            bbox = alpha_channel.getbbox()
        except (ValueError, OSError, AttributeError):
            bbox = None

        cropped_image = pil_image.crop(bbox) if bbox else pil_image

        # Resize if necessary
        if cropped_image.size != size:
            resample = getattr(Image.Resampling, "LANCZOS", 1)
            resized_image = cropped_image.resize(size, resample)
        else:
            resized_image = cropped_image

        return ctk.CTkImage(
            light_image=resized_image,
            dark_image=resized_image,
            size=size,
        )

    def resolve_image_path(self, image_path):
        if not image_path:
            return None

        candidate = Path(image_path)
        if not candidate.is_absolute():
            # Assume relative to project root (parent of parent of this file)
            base_dir = Path(__file__).resolve().parent.parent
            candidate = base_dir / candidate

        return candidate if candidate.exists() else None

    def create_detail_image(self, image_path, max_size):
        resolved_path = self.resolve_image_path(image_path)
        if not resolved_path:
            return None

        try:
            with Image.open(resolved_path) as img:
                prepared_image = img.convert("RGBA").copy()
        except (FileNotFoundError, OSError, ValueError):
            return None

        width, height = prepared_image.size
        if width <= 0 or height <= 0:
            return None

        # Calculate scale to fit within max size
        max_width, max_height = max_size
        scale = min(max_width / width, max_height / height, 1)

        if scale < 1:
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
            resample = getattr(Image.Resampling, "LANCZOS", 1)
            prepared_image = prepared_image.resize(new_size, resample)

        return ctk.CTkImage(
            light_image=prepared_image,
            dark_image=prepared_image,
            size=prepared_image.size,
        )

    def truncate_filename(self, name):
        if not name:
            return ""

        if len(name) > self.MAX_DISPLAY_NAME_LENGTH:
            return f"{name[:28]}...{name[-24:]}"

        return name

    def validate_image_extension(self, file_path):
        return file_path.suffix.lower() in self.ALLOWED_EXTENSIONS

    def copy_image_to_project(self, source_path):
        try:
            resolved_images_dir = self.images_dir.resolve()
            resolved_source = source_path.resolve()
        except OSError:
            resolved_images_dir = self.images_dir
            resolved_source = source_path

        # Check if already in images directory
        try:
            relative_sub_path = resolved_source.relative_to(resolved_images_dir)
            # Already in the directory
            return Path("recursos") / "imagenes" / relative_sub_path
        except ValueError:
            # Not in the directory, need to copy
            pass

        # Ensure images directory exists
        try:
            self.images_dir.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            messagebox.showerror(
                "Image Folder Error",
                f"Unable to create the images directory.\n\nDetails: {error}",
            )
            return None

        # Find unique filename
        candidate_name = source_path.name or "image.png"
        candidate_stem = source_path.stem or "image"
        candidate_suffix = source_path.suffix or ".png"

        destination_path = self.images_dir / candidate_name
        copy_index = 1
        while destination_path.exists():
            destination_path = (
                self.images_dir / f"{candidate_stem}_{copy_index}{candidate_suffix}"
            )
            copy_index += 1

        # Copy the file
        try:
            shutil.copy2(source_path, destination_path)
        except OSError as error:
            messagebox.showerror(
                "Image Copy Failed",
                f"Unable to copy the selected image into the project.\n\nDetails: {error}",
            )
            return None

        return Path("recursos") / "imagenes" / destination_path.name

    def create_transparent_placeholder(self):
        invisible_pixel = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        return ctk.CTkImage(
            light_image=invisible_pixel, dark_image=invisible_pixel, size=(1, 1)
        )
