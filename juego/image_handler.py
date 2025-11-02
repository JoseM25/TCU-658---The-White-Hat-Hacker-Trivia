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
            return ImageTk.getimage(
                TkSvgImage(file=str(svg_path), scale=scale)
            ).convert("RGBA")
        except (FileNotFoundError, OSError, ValueError, RuntimeError):
            return None

    def _crop_to_alpha_bounds(self, pil_image):
        try:
            bbox = pil_image.getchannel("A").getbbox()
            return pil_image.crop(bbox) if bbox else pil_image
        except (ValueError, OSError, AttributeError):
            return pil_image

    def _resize_image(self, image, target_size):
        if image.size == target_size:
            return image
        resample = getattr(Image.Resampling, "LANCZOS", 1)
        return image.resize(target_size, resample)

    def create_ctk_icon(self, svg_filename, size, scale=None):
        pil_image = self.load_svg_image(
            self.images_dir / svg_filename, scale or self.SVG_RASTER_SCALE
        )
        if not pil_image:
            return None

        cropped = self._crop_to_alpha_bounds(pil_image)
        resized = self._resize_image(cropped, size)

        return ctk.CTkImage(light_image=resized, dark_image=resized, size=size)

    def resolve_image_path(self, image_path):
        if not image_path:
            return None

        candidate = Path(image_path)
        if not candidate.is_absolute():
            candidate = Path(__file__).resolve().parent.parent / candidate

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

        # Scale to fit within max_size
        max_width, max_height = max_size
        scale = min(max_width / width, max_height / height, 1)

        if scale < 1:
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
            prepared_image = self._resize_image(prepared_image, new_size)

        return ctk.CTkImage(
            light_image=prepared_image,
            dark_image=prepared_image,
            size=prepared_image.size,
        )

    def truncate_filename(self, name):
        if not name or len(name) <= self.MAX_DISPLAY_NAME_LENGTH:
            return name or ""
        return f"{name[:28]}...{name[-24:]}"

    def validate_image_extension(self, file_path):
        return file_path.suffix.lower() in self.ALLOWED_EXTENSIONS

    def _resolve_paths(self, source_path):
        try:
            return self.images_dir.resolve(), source_path.resolve()
        except OSError:
            return self.images_dir, source_path

    def _get_unique_destination(self, source_path):
        stem = source_path.stem or "image"
        suffix = source_path.suffix or ".png"

        destination = self.images_dir / source_path.name or "image.png"
        counter = 1
        while destination.exists():
            destination = self.images_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        return destination

    def copy_image_to_project(self, source_path):
        images_dir, source = self._resolve_paths(source_path)

        # Check if already in images directory
        try:
            sub_path = source.relative_to(images_dir)
            return Path("recursos") / "imagenes" / sub_path
        except ValueError:
            pass  # Not in directory, need to copy

        # Ensure images directory exists
        try:
            self.images_dir.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            messagebox.showerror(
                "Image Folder Error",
                f"Unable to create the images directory.\n\nDetails: {error}",
            )
            return None

        # Copy with unique filename
        destination = self._get_unique_destination(source_path)
        try:
            shutil.copy2(source_path, destination)
            return Path("recursos") / "imagenes" / destination.name
        except OSError as error:
            messagebox.showerror(
                "Image Copy Failed",
                f"Unable to copy the selected image into the project.\n\nDetails: {error}",
            )
            return None

    def create_transparent_placeholder(self):
        pixel = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        return ctk.CTkImage(light_image=pixel, dark_image=pixel, size=(1, 1))
