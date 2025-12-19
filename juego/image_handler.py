import shutil
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image, ImageTk
from tksvg import SvgImage as TkSvgImage


class ImageHandler:

    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
    MAX_DISPLAY_NAME_LENGTH = 60

    def __init__(self, images_dir):
        self.images_dir = images_dir

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            return ImageTk.getimage(
                TkSvgImage(file=str(svg_path), scale=scale)
            ).convert("RGBA")
        except (FileNotFoundError, OSError, ValueError, RuntimeError):
            return None

    def get_svg_base_size(self, svg_path):
        """Get the base size of an SVG by loading at scale 1.0"""
        try:
            img = ImageTk.getimage(TkSvgImage(file=str(svg_path), scale=1.0))
            return img.size
        except (FileNotFoundError, OSError, ValueError, RuntimeError):
            return (24, 24)  # fallback

    def crop_to_alpha_bounds(self, pil_image):
        try:
            bbox = pil_image.getchannel("A").getbbox()
            return pil_image.crop(bbox) if bbox else pil_image
        except (ValueError, OSError, AttributeError):
            return pil_image

    def resize_image(self, image, target_size):
        if image.size == target_size:
            return image
        resample = getattr(Image.Resampling, "LANCZOS", 1)
        return image.resize(target_size, resample)

    def create_ctk_icon(self, svg_filename, size, scale=None):
        svg_path = self.images_dir / svg_filename
        target_w, target_h = size
        target_max = max(target_w, target_h)

        if scale is None:
            # Calculate the scale needed to rasterize SVG at target resolution
            base_w, base_h = self.get_svg_base_size(svg_path)
            base_max = max(base_w, base_h, 1)
            # Rasterize at 2x target size for crispness, then downscale
            scale = (target_max * 2) / base_max

        pil_image = self.load_svg_image(svg_path, scale)
        if not pil_image:
            return None

        cropped = self.crop_to_alpha_bounds(pil_image)

        # Preserve aspect ratio when resizing
        orig_w, orig_h = cropped.size
        if orig_w > 0 and orig_h > 0:
            ratio = min(target_w / orig_w, target_h / orig_h)
            new_w = max(1, int(orig_w * ratio))
            new_h = max(1, int(orig_h * ratio))
            resized = self.resize_image(cropped, (new_w, new_h))

            # Center on transparent canvas
            final = Image.new("RGBA", size, (0, 0, 0, 0))
            paste_x = (target_w - new_w) // 2
            paste_y = (target_h - new_h) // 2
            final.paste(resized, (paste_x, paste_y))
        else:
            final = cropped

        return ctk.CTkImage(light_image=final, dark_image=final, size=size)

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

        max_width, max_height = max_size
        scale = min(max_width / width, max_height / height, 1)

        new_width = max(1, int(width * scale))
        new_height = max(1, int(height * scale))

        resized_image = self.resize_image(prepared_image, (new_width, new_height))

        final_image = Image.new("RGBA", max_size, (0, 0, 0, 0))
        paste_x = (max_width - new_width) // 2
        paste_y = (max_height - new_height) // 2
        final_image.paste(resized_image, (paste_x, paste_y))

        return ctk.CTkImage(
            light_image=final_image,
            dark_image=final_image,
            size=max_size,
        )

    def truncate_filename(self, name):
        if not name or len(name) <= self.MAX_DISPLAY_NAME_LENGTH:
            return name or ""
        return f"{name[:28]}...{name[-24:]}"

    def validate_image_extension(self, file_path):
        return file_path.suffix.lower() in self.ALLOWED_EXTENSIONS

    def resolve_paths(self, source_path):
        try:
            return self.images_dir.resolve(), source_path.resolve()
        except OSError:
            return self.images_dir, source_path

    def get_unique_destination(self, source_path):
        stem = source_path.stem or "image"
        suffix = source_path.suffix or ".png"

        destination = self.images_dir / source_path.name or "image.png"
        counter = 1
        while destination.exists():
            destination = self.images_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        return destination

    def copy_image_to_project(self, source_path):
        images_dir, source = self.resolve_paths(source_path)

        try:
            sub_path = source.relative_to(images_dir)
            return Path("recursos") / "imagenes" / sub_path
        except ValueError:
            pass

        try:
            self.images_dir.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            messagebox.showerror(
                "Image Folder Error",
                f"Unable to create the images directory.\n\nDetails: {error}",
            )
            return None

        destination = self.get_unique_destination(source_path)
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
