import shutil
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image, ImageTk
from tksvg import SvgImage as TkSvgImage


class ImageHandler:

    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
    MAX_DISPLAY_NAME_LENGTH = 60

    def __init__(
        self,
        images_dir,
        user_images_dir=None,
        data_root=None,
        resource_root=None,
    ):
        self.images_dir = Path(images_dir)
        self.user_images_dir = (
            Path(user_images_dir) if user_images_dir is not None else None
        )
        self.data_root = Path(data_root) if data_root is not None else None
        self.resource_root = Path(resource_root) if resource_root is not None else None
        if self.user_images_dir is None and self.data_root is not None:
            self.user_images_dir = self.data_root / "recursos" / "imagenes"
        self.iconcache = {}
        self.detailcache = {}
        self.cachemax = 128

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            return ImageTk.getimage(
                TkSvgImage(file=str(svg_path), scale=scale)
            ).convert("RGBA")
        except (FileNotFoundError, OSError, ValueError, RuntimeError):
            return None

    def get_svg_base_size(self, svg_path):
        try:
            img = ImageTk.getimage(TkSvgImage(file=str(svg_path), scale=1.0))
            return img.size
        except (FileNotFoundError, OSError, ValueError, RuntimeError):
            return (24, 24)  # respaldo

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
            # Calcular la escala necesaria para rasterizar SVG a resolución objetivo
            base_w, base_h = self.get_svg_base_size(svg_path)
            base_max = max(base_w, base_h, 1)
            # Rasterizar a 2x el tamaño objetivo para nitidez, luego reducir
            scale = (target_max * 2) / base_max

        key = (str(svg_path), size, round(scale, 4))
        cached = self.iconcache.get(key)
        if cached is not None:
            return cached

        pil_image = self.load_svg_image(svg_path, scale)
        if not pil_image:
            return None

        cropped = self.crop_to_alpha_bounds(pil_image)

        # Preservar proporción de aspecto al redimensionar
        orig_w, orig_h = cropped.size
        if orig_w > 0 and orig_h > 0:
            ratio = min(target_w / orig_w, target_h / orig_h)
            new_w = max(1, int(orig_w * ratio))
            new_h = max(1, int(orig_h * ratio))
            resized = self.resize_image(cropped, (new_w, new_h))

            # Centrar en lienzo transparente
            final = Image.new("RGBA", size, (0, 0, 0, 0))
            paste_x = (target_w - new_w) // 2
            paste_y = (target_h - new_h) // 2
            final.paste(resized, (paste_x, paste_y))
        else:
            final = cropped

        icon = ctk.CTkImage(light_image=final, dark_image=final, size=size)
        self.iconcache[key] = icon
        if len(self.iconcache) > self.cachemax:
            viejo = next(iter(self.iconcache))
            self.iconcache.pop(viejo, None)
        return icon

    def resolve_image_path(self, image_path):
        if not image_path:
            return None

        candidate = Path(image_path)
        if not candidate.is_absolute():
            for base in (
                self.data_root,
                self.resource_root,
                self.user_images_dir,
                self.images_dir,
            ):
                if base is None:
                    continue
                resolved = base / candidate
                if resolved.exists():
                    return resolved
            candidate = Path(__file__).resolve().parent.parent / candidate

        return candidate if candidate.exists() else None

    def create_detail_image(self, image_path, max_size):
        resolved_path = self.resolve_image_path(image_path)
        if not resolved_path:
            return None

        key = (str(resolved_path), max_size)
        cached = self.detailcache.get(key)
        if cached is not None:
            return cached

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

        image = ctk.CTkImage(
            light_image=final_image,
            dark_image=final_image,
            size=max_size,
        )
        self.detailcache[key] = image
        if len(self.detailcache) > self.cachemax:
            viejo = next(iter(self.detailcache))
            self.detailcache.pop(viejo, None)
        return image

    def truncate_filename(self, name):
        if not name or len(name) <= self.MAX_DISPLAY_NAME_LENGTH:
            return name or ""
        return f"{name[:28]}...{name[-24:]}"

    def validate_image_extension(self, file_path):
        return file_path.suffix.lower() in self.ALLOWED_EXTENSIONS

    def resolve_paths(self, source_path):
        target_dir = self.user_images_dir or self.images_dir
        try:
            return target_dir.resolve(), source_path.resolve()
        except OSError:
            return target_dir, source_path

    def get_unique_destination(self, source_path):
        stem = source_path.stem or "image"
        suffix = source_path.suffix or ".png"

        target_dir = self.user_images_dir or self.images_dir
        destination = target_dir / source_path.name or "image.png"
        counter = 1
        while destination.exists():
            destination = target_dir / f"{stem}_{counter}{suffix}"
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
            images_dir.mkdir(parents=True, exist_ok=True)
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
