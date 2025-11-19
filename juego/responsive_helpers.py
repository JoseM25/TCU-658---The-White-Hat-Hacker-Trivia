class ResponsiveScaler:

    def __init__(self, base_dimensions, scale_limits, global_scale_factor):
        self.base_dimensions = base_dimensions
        self.min_scale, self.max_scale = scale_limits
        self.global_scale_factor = global_scale_factor

    def calculate_scale(self, width, height, low_res_profile=None):
        base_w, base_h = self.base_dimensions
        raw_scale = min(width / base_w, height / base_h)

        scaled = raw_scale * self.global_scale_factor

        # Apply resolution penalties
        if width <= 900:
            scaled *= 0.88
        if height <= 550:
            scaled *= 0.92

        # Extra low resolution penalty
        if low_res_profile:
            min_dimension = min(width, height)
            penalty = self.interpolate_profile(min_dimension, low_res_profile)
            scaled *= penalty

        return max(self.min_scale, min(self.max_scale, scaled))

    def scale_value(self, base, scale, min_value=None, max_value=None):
        value = base * scale
        if min_value is not None:
            value = max(min_value, value)
        if max_value is not None:
            value = min(max_value, value)
        return int(round(value))

    def interpolate_profile(self, value, profile):
        if not profile or value is None:
            return value if value is not None else (profile[-1][0] if profile else 1.0)

        sample_value = profile[0][1]
        cast_func = (
            float if isinstance(sample_value, float) else lambda x: int(round(x))
        )

        lower_bound, lower_value = profile[0]
        if value <= lower_bound:
            return cast_func(lower_value)

        for upper_bound, upper_value in profile[1:]:
            if value <= upper_bound:
                span = upper_bound - lower_bound or 1
                ratio = (value - lower_bound) / span
                interpolated = lower_value + ratio * (upper_value - lower_value)
                return cast_func(interpolated)
            lower_bound, lower_value = upper_bound, upper_value

        return cast_func(profile[-1][1])

    def clamp_value(self, value, min_value=None, max_value=None):
        if min_value is not None:
            value = max(min_value, value)
        if max_value is not None:
            value = min(max_value, value)
        return value


class SizeStateCalculator:

    def __init__(self, scaler, base_sizes, profiles):
        self.scaler = scaler
        self.base_sizes = base_sizes
        self.profiles = profiles

    def calculate_sizes(self, scale, window_width):
        s = self.scaler.scale_value

        sizes = {
            "question_btn_height": s(50, scale, 26, 86),
            "question_margin": s(8, scale, 3, 18),
            "question_padding": s(4, scale, 2, 14),
            "question_corner_radius": s(12, scale, 5, 20),
            "max_questions": max(4, min(12, int(round(8 * scale)))),
            "list_frame_padding": s(8, scale, 4, 24),
            "list_frame_corner_radius": s(24, scale, 12, 40),
            "scrollbar_offset": s(22, scale, 12, 36),
        }

        # Detail panel sizes
        detail_image_size = (s(220, scale, 110, 420), s(220, scale, 110, 420))
        sizes["detail_image"] = detail_image_size
        sizes["detail_panel_height"] = s(520, scale, 320, 880)
        sizes["detail_scroll_height"] = max(
            200, sizes["detail_panel_height"] - s(150, scale, 90, 260)
        )

        # Calculate sidebar/detail widths
        sidebar_share = self._get_sidebar_share(window_width)
        gutter = s(60, scale, 32, 110)

        sidebar_minsize = s(280, scale, 220, 560)
        estimated_sidebar = max(
            sidebar_minsize, int(round(window_width * sidebar_share))
        )

        available_width = max(220, window_width - estimated_sidebar - gutter)
        detail_minsize = s(820, scale, 320, 1400)
        detail_width = max(min(detail_minsize, available_width), available_width)

        sizes["sidebar_minsize"] = sidebar_minsize
        sizes["detail_minsize"] = min(detail_minsize, available_width)
        sizes["detail_width_estimate"] = detail_width
        sizes["sidebar_width_estimate"] = estimated_sidebar
        sizes["window_width"] = window_width

        return sizes

    def get_sidebar_share(self, window_width):
        return self._get_sidebar_share(window_width)

    def _get_sidebar_share(self, window_width):
        if not window_width or window_width <= 0:
            window_width = 1280

        profile = self.profiles.get("sidebar_width", [])
        if not profile:
            return 0.28

        share = self.scaler.interpolate_profile(window_width, profile)
        return self.scaler.clamp_value(share, 0.24, 0.32)


class LayoutCalculator:

    def __init__(self, scaler, profiles):
        self.scaler = scaler
        self.profiles = profiles

    def compute_definition_padding(self, width, scale):
        profile = self.profiles.get("definition_padding", [])
        pad = self.scaler.interpolate_profile(width, profile)

        min_pad = self.scaler.scale_value(8, scale, 6, 16)
        max_pad = self.scaler.scale_value(36, scale, 24, 60)

        if width <= 640:
            pad *= 0.7
            pad = max(6, pad)

        return self.scaler.clamp_value(pad, min_pad, max_pad)

    def should_stack_layout(self, container_width, scale, stack_breakpoint=520):
        threshold = self.scaler.scale_value(stack_breakpoint, scale, 220, 640)
        return container_width <= threshold

    def calculate_wrap_ratio(self, width):
        profile = self.profiles.get("wrap_fill", [])
        ratio = self.scaler.interpolate_profile(width or 1000, profile)
        return self.scaler.clamp_value(ratio, 0.78, 0.985)
