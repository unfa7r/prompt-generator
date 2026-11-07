from core.composition import calculate_scene_layout


def get_subject_name(data):
    subject = data.get("subject")

    if isinstance(subject, dict):
        subject = subject.get("subject")

    return str(subject) if subject else None


def describe_item(data):
    subject = get_subject_name(data)
    model = data.get("model")
    brand = data.get("brand")

    parts = []

    if model:
        parts.append(str(model))
    elif brand:
        parts.append(str(brand).title())
    elif subject:
        parts.append(subject)

    fields = {
        "color": "finish",
        "material": "material",
        "headlights": "headlights",
        "pose": "pose",
        "framing": "framing",
        "composition": "composition"
    }

    for key, label in fields.items():
        value = data.get(key)

        if value is not None:
            parts.append(f"{label}: {value}")

    detail_labels = {
        "hairstyles": "hairstyle",
        "clothing": "clothing",
        "expressions": "expression",
        "accessories": "accessories",
        "styles": "architectural style",
        "facades": "facade",
        "materials": "architectural materials",
        "features": "architectural features"
    }

    for key, label in detail_labels.items():
        details = data.get("character_details") or {}
        architecture = data.get("architecture_details") or {}
        value = details.get(key) or architecture.get(key)

        if value:
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            parts.append(f"{label}: {value}")

    return ", ".join(parts)


def describe_scene(data):
    mode = data.get("mode")
    subject = get_subject_name(data)

    parts = []

    if mode == "anime":
        parts.append("Anime-style scene")
    elif mode == "realistic":
        parts.append("Photorealistic scene")

    if subject:
        parts.append(f"featuring {describe_item(data)}")

    if data.get("visual_style"):
        parts.append(f"visual style: {data['visual_style']}")

    if data.get("color_grading"):
        parts.append(f"color grading: {data['color_grading']}")

    techniques = data.get("camera_techniques")
    if techniques:
        parts.append("camera techniques: " + ", ".join(techniques))

    additional = []

    for item in data.get("additional_elements") or []:
        if isinstance(item, dict):
            description = describe_item(item)

            if description:
                additional.append(description)

    if additional:
        parts.append("with " + ", ".join(additional))

    fields = {
        "environment": "located in",
        "time_of_day": "during",
        "weather": "under",
        "lighting": "illuminated by",
        "atmosphere": "with"
    }

    for key, label in fields.items():
        value = data.get(key)

        if value is not None:
            parts.append(f"{label} {str(value).lower()}")

    effects = data.get("visual_effects")

    if effects:
        parts.append("with visual effects: " + ", ".join(effects))

    return " ".join(parts).strip()


def create_background(data):
    background = {}

    fields = {
        "environment": "location",
        "time_of_day": "time",
        "lighting": "lighting",
        "weather": "weather",
        "atmosphere": "atmosphere"
    }

    for source, target in fields.items():
        value = data.get(source)

        if value is not None:
            background[target] = value

    return background or None


def create_element(data, bbox):
    subject = get_subject_name(data)

    element_type = data.get(
        "kind",
        str(subject or "subject").lower()
    )

    return {
        "type": element_type,
        "bbox": bbox,
        "desc": describe_item(data)
    }


def build_scene_graph(data, aspect_ratio="4:3"):
    if not isinstance(data, dict):
        raise TypeError("Scene data must be a dictionary.")

    layout_data = dict(data)

    primary_subject = get_subject_name(data)
    is_environment = (
        primary_subject is not None
        and primary_subject.strip().lower() == "environment"
    )

    if is_environment:
        layout_data["subject"] = None

    layout = calculate_scene_layout(layout_data, aspect_ratio)

    items = []

    if layout_data.get("subject"):
        items.append(layout_data)

    for item in layout_data.get("additional_elements") or []:
        if isinstance(item, dict) and item.get("subject"):
            items.append(item)

    elements = [
        create_element(item, bbox)
        for item, bbox in zip(items, layout)
    ]

    scene = {
        "aspect_ratio": aspect_ratio,
        "high_level_description": describe_scene(data),
        "compositional_deconstruction": {
            "background": create_background(data),
            "elements": elements
        }
    }

    camera = data.get("camera")
    if isinstance(camera, dict) and camera:
        scene["camera"] = dict(camera)

    if data.get("camera_angle"):
        scene["camera_angle"] = data["camera_angle"]

    if data.get("visual_effects"):
        scene["visual_effects"] = data["visual_effects"]

    for key in ("visual_style", "color_grading", "camera_techniques"):
        if data.get(key):
            scene[key] = data[key]

    return scene

