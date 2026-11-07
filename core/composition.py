def clamp(value):
    return round(max(0.0, min(1.0, value)), 3)


def calculate_bbox(data):
    subject = str(data.get("subject") or "").lower()
    framing = data.get("framing")
    position = data.get("composition")

    profiles = {
        "person": (0.42, 0.88),
        "character": (0.42, 0.88),
        "portrait": (0.48, 0.68),
        "car": (0.82, 0.48),
        "vehicle": (0.82, 0.48),
        "architecture": (0.82, 0.78),
        "lifestyle": (0.62, 0.76),
        "environment": (0.90, 0.80)
    }

    width, height = profiles.get(subject, (0.60, 0.75))

    framing_sizes = {
        "Close-up": (0.70, 0.55),
        "Portrait": (0.48, 0.68),
        "Upper Body": (0.58, 0.76),
        "Full Body": (0.42, 0.88),
        "Silhouette": (0.48, 0.88),
        "Side Profile": (0.48, 0.75),
        "Three-Quarter View": (0.55, 0.78)
    }

    if framing in framing_sizes:
        width, height = framing_sizes[framing]

    if subject in ("car", "vehicle"):
        width = max(width, 0.72)

    if subject == "architecture":
        width = max(width, 0.80)

    if position == "Left Third":
        x = 0.08
    elif position == "Right Third":
        x = 0.92 - width
    elif position == "Foreground":
        width = min(width * 1.15, 0.95)
        height = min(height * 1.10, 0.95)
        x = (1 - width) / 2
    elif position == "Background":
        width *= 0.70
        height *= 0.70
        x = (1 - width) / 2
    else:
        x = (1 - width) / 2

    if position == "Upper Third":
        y = 0.08
    elif position == "Lower Third":
        y = 0.92 - height
    elif position == "Foreground":
        y = 0.95 - height
    elif position == "Background":
        y = 0.08
    else:
        y = (1 - height) / 2

    if data.get("camera_angle") in ("Low Angle", "Worm's Eye View"):
        y += 0.04
    elif data.get("camera_angle") in ("High Angle", "Bird's Eye View"):
        y -= 0.04

    x = clamp(x)
    y = clamp(y)

    return [
        x,
        y,
        clamp(x + width),
        clamp(y + height)
    ]


def get_element_kind(data):
    return str(
        data.get("kind") or data.get("subject") or "subject"
    ).lower()


def calculate_scene_layout(data, aspect_ratio="4:3"):
    primary = data

    additional = data.get("additional_elements") or []

    items = [primary] + [
        item for item in additional
        if isinstance(item, dict) and item.get("subject")
    ]

    def kind_of(item):
        return str(
            item.get("kind") or item.get("subject") or "subject"
        ).lower()

    background_kinds = ("architecture", "environment")

    foreground = [
        item for item in items
        if kind_of(item) not in background_kinds
    ]

    try:
        width, height = map(float, aspect_ratio.split(":"))
        ratio = width / height

        if ratio <= 0:
            raise ValueError

    except (ValueError, AttributeError, ZeroDivisionError):
        ratio = 4 / 3

    assigned = {}

    for item in items:
        if kind_of(item) in background_kinds:
            assigned[id(item)] = [0.0, 0.0, 1.0, 1.0]

    count = len(foreground)

    if count == 1:
        item = foreground[0]
        assigned[id(item)] = calculate_bbox(item)

    elif count == 2:
        first, second = foreground
        kinds = [kind_of(first), kind_of(second)]

        characters = ("person", "character", "portrait")
        vehicles = ("car", "vehicle")

        if ratio >= 1.0:
            if kinds[0] in characters and kinds[1] in vehicles:
                boxes = [
                    [0.04, 0.08, 0.44, 0.92],
                    [0.53, 0.22, 0.97, 0.80]
                ]

            elif kinds[1] in characters and kinds[0] in vehicles:
                boxes = [
                    [0.53, 0.22, 0.97, 0.80],
                    [0.04, 0.08, 0.44, 0.92]
                ]

            elif all(kind in characters for kind in kinds):
                boxes = [
                    [0.04, 0.08, 0.46, 0.92],
                    [0.54, 0.08, 0.96, 0.92]
                ]

            elif all(kind in vehicles for kind in kinds):
                boxes = [
                    [0.03, 0.18, 0.48, 0.82],
                    [0.52, 0.18, 0.97, 0.82]
                ]

            elif "lifestyle" in kinds:
                boxes = [
                    [0.04, 0.08, 0.62, 0.92],
                    [0.68, 0.30, 0.96, 0.70]
                ]

            else:
                boxes = [
                    [0.04, 0.08, 0.46, 0.92],
                    [0.54, 0.08, 0.96, 0.92]
                ]

        else:
            if kinds[0] in characters and kinds[1] in vehicles:
                boxes = [
                    [0.08, 0.04, 0.92, 0.44],
                    [0.08, 0.56, 0.92, 0.96]
                ]

            elif kinds[1] in characters and kinds[0] in vehicles:
                boxes = [
                    [0.08, 0.56, 0.92, 0.96],
                    [0.08, 0.04, 0.92, 0.44]
                ]

            elif all(kind in characters for kind in kinds):
                boxes = [
                    [0.08, 0.04, 0.92, 0.46],
                    [0.08, 0.54, 0.92, 0.96]
                ]

            elif all(kind in vehicles for kind in kinds):
                boxes = [
                    [0.08, 0.04, 0.92, 0.46],
                    [0.08, 0.54, 0.92, 0.96]
                ]

            elif "lifestyle" in kinds:
                boxes = [
                    [0.08, 0.04, 0.92, 0.64],
                    [0.25, 0.72, 0.75, 0.96]
                ]

            else:
                boxes = [
                    [0.08, 0.04, 0.92, 0.46],
                    [0.08, 0.54, 0.92, 0.96]
                ]

        for item, bbox in zip(foreground, boxes):
            assigned[id(item)] = bbox

    elif count >= 3:
        columns = min(count, 3) if ratio >= 1.5 else (
            2 if ratio >= 1.0 else 1
        )

        rows = (count + columns - 1) // columns

        margin_x = 0.04
        margin_y = 0.08
        gap_x = 0.04
        gap_y = 0.06

        cell_width = (
            1.0 - 2 * margin_x - (columns - 1) * gap_x
        ) / columns

        cell_height = (
            1.0 - 2 * margin_y - (rows - 1) * gap_y
        ) / rows

        slots = []

        for row in range(rows):
            for column in range(columns):
                if len(slots) >= count:
                    break

                x1 = margin_x + column * (cell_width + gap_x)
                y1 = margin_y + row * (cell_height + gap_y)

                slots.append((
                    x1,
                    y1,
                    x1 + cell_width,
                    y1 + cell_height
                ))

        composition = primary.get("composition")

        preferred_x = (
            0.75 if composition == "Right Third"
            else 0.25 if composition == "Left Third"
            else 0.50
        )

        slots.sort(
            key=lambda slot: (
                abs((slot[0] + slot[2]) / 2 - preferred_x),
                slot[1]
            )
        )

        for item, slot in zip(foreground, slots):
            kind = kind_of(item)

            if kind in ("person", "character", "portrait"):
                width_scale, height_scale = 0.88, 0.94
            elif kind in ("car", "vehicle"):
                width_scale, height_scale = 0.94, 0.76
            elif kind == "lifestyle":
                width_scale, height_scale = 0.58, 0.55
            else:
                width_scale, height_scale = 0.76, 0.76

            x1, y1, x2, y2 = slot

            box_width = (x2 - x1) * width_scale
            box_height = (y2 - y1) * height_scale

            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            assigned[id(item)] = [
                clamp(center_x - box_width / 2),
                clamp(center_y - box_height / 2),
                clamp(center_x + box_width / 2),
                clamp(center_y + box_height / 2)
            ]

    for item in foreground:
        bbox = assigned[id(item)]
        kind = kind_of(item)

        framing = str(item.get("framing") or "").lower()
        camera = str(item.get("camera_angle") or "").lower()

        width_scale = 1.0
        height_scale = 1.0

        if kind in ("person", "character", "portrait"):
            framing_scales = {
                "close-up": (0.96, 0.58),
                "portrait": (0.86, 0.82),
                "upper body": (0.90, 0.78),
                "full body": (0.82, 0.98),
                "silhouette": (0.82, 0.98),
                "side profile": (0.82, 0.88),
                "three-quarter view": (0.88, 0.90)
            }

            width_scale, height_scale = framing_scales.get(
                framing,
                (1.0, 1.0)
            )

        elif kind in ("car", "vehicle"):
            if framing in ("wide angle", "full shot"):
                width_scale, height_scale = (0.98, 0.88)
            elif framing in ("close-up", "detail shot"):
                width_scale, height_scale = (0.78, 0.82)

        x1, y1, x2, y2 = bbox

        box_width = (x2 - x1) * width_scale
        box_height = (y2 - y1) * height_scale

        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        if camera in ("low angle", "worm's eye view"):
            center_y += (y2 - y1) * 0.025
        elif camera in ("high angle", "bird's eye view"):
            center_y -= (y2 - y1) * 0.025

        assigned[id(item)] = [
            clamp(center_x - box_width / 2),
            clamp(center_y - box_height / 2),
            clamp(center_x + box_width / 2),
            clamp(center_y + box_height / 2)
        ]

    return [
        assigned[id(item)]
        for item in items
    ]
