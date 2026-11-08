import json
import re

from core.camera import describe_camera


def split_description(element):
    description = element.get("desc", "").strip()

    if not description:
        return "", []

    pattern = r",\s+(?=(?:finish|material|headlights|pose|framing|camera angle|composition|hairstyle|clothing|expression|accessories|architectural style|facade|architectural materials|architectural features):)"
    parts = re.split(pattern, description, flags=re.IGNORECASE)

    return parts[0].strip(), [part.strip() for part in parts[1:]]


def describe_camera_angle(camera):
    value = camera.strip().lower()

    known = {
        "eye level": "at eye level",
        "low angle": "from a low angle",
        "high angle": "from a high angle",
        "bird's eye view": "from a bird's-eye view",
        "worm's eye view": "from a worm's-eye view",
        "dutch angle": "at a Dutch angle",
        "over the shoulder": "over the shoulder",
        "side view": "from the side",
        "front view": "from the front",
        "rear view": "from the rear",
        "profile view": "in profile",
        "three-quarter front view": "from a three-quarter front angle",
        "three-quarter rear view": "from a three-quarter rear angle",
        "top-down view": "from directly above",
        "ground-level view": "from ground level",
        "pov (first-person)": "from a first-person point of view",
        "overhead shot": "in an overhead shot",
        "extreme low angle": "from an extreme low angle",
        "extreme high angle": "from an extreme high angle",
    }

    return known.get(value, f"from the {value} angle")


def format_attributes(attributes, element_type=""):
    result = []

    character_labels = {
        "hairstyle": lambda value: f"with {value.lower()}",
        "clothing": lambda value: f"dressed in {value.lower()}",
        "expression": lambda value: f"with a {value.lower()}",
        "accessories": lambda value: f"wearing {value.lower()}"
    }

    architecture_labels = {
        "architectural style": lambda value: f"in the {value.lower()} style",
        "facade": lambda value: f"with {(value.lower() if value.lower().endswith('cladding') else (('an ' if value[0].lower() in 'aeiou' else 'a ') + value.lower()))}",
        "architectural materials": lambda value: f"constructed from {value.lower()}",
        "architectural features": lambda value: f"featuring {(value.lower() if value.lower().endswith(('windows', 'columns', 'detailing')) else (('an ' if value[0].lower() in 'aeiou' else 'a ') + value.lower()))}"
    }

    labels = {
        "finish": "a",
        "material": "",
        "headlights": "",
        "pose": "in a",
        "framing": "framed as",
        "camera angle": "from a",
        "composition": "with"
    }

    for attribute in attributes:
        if ":" not in attribute:
            result.append(attribute)
            continue

        key, value = attribute.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if element_type in ("character", "person", "portrait") and key in character_labels:
            result.append(character_labels[key](value))
        elif element_type == "architecture" and key in architecture_labels:
            result.append(architecture_labels[key](value))
        elif key == "finish":
            result.append(f"{value.lower()} finish")
        elif key == "material":
            result.append(f"{value.lower()} details")
        elif key == "headlights":
            result.append(value)
        elif key == "pose":
            result.append(f"{value.lower()} pose")
        elif key == "framing":
            result.append(f"{value.lower()} framing")
        elif key == "camera angle":
            continue
        elif key == "composition":
            result.append(f"{value.lower()} composition")
        else:
            result.append(f"{key}: {value}")

    return result


def describe_main_element(element, mode):
    name, attributes = split_description(element)
    element_type = element.get("type", "").lower()
    details = format_attributes(attributes, element_type)

    if mode == "anime":
        if element_type == "portrait" and name.strip().lower() == "portrait":
            sentence = "An original anime character portrait"
        elif element_type in ("character", "portrait"):
            if name.strip().lower() in ("character", "original anime character"):
                sentence = "An original anime character"
            else:
                sentence = f"An original anime character design of {name}"
        else:
            sentence = f"An anime-style illustration featuring {name}"

    elif element_type in ("car", "vehicle"):
        sentence = f"A photorealistic automotive photograph featuring {name}"

    elif element_type in ("character", "person", "portrait"):
        sentence = f"A photorealistic portrait featuring {name}"

    elif element_type == "architecture":
        sentence = f"A realistic architectural photograph of {name}"

    else:
        sentence = f"A photorealistic scene featuring {name}"

    if details:
        sentence += ", " + ", ".join(details)
        sentence = sentence.rstrip(" ,") + "."

    return sentence


def describe_additional_elements(elements, mode):
    descriptions = []

    for element in elements:
        name, attributes = split_description(element)

        if not name:
            continue

        details = format_attributes(
            attributes,
            element.get("type", "").lower()
        )
        description = name

        if details:
            description += ", " + ", ".join(details)

        descriptions.append(description)

    if not descriptions:
        return ""

    if len(descriptions) == 1:
        return f", accompanied by {descriptions[0]}"

    return ", accompanied by " + ", ".join(descriptions[:-1]) + " and " + descriptions[-1]


def describe_environment(background):
    parts = []

    location = background.get("location")
    time = background.get("time")
    weather = background.get("weather")
    lighting = background.get("lighting")
    atmosphere = background.get("atmosphere")

    if location:
        parts.append(f"set in {location.lower()}")

    if time:
        parts.append(f"during {time.lower()}")

    if weather:
        weather_text = {
            "snow": "snowy conditions",
            "heavy rain": "heavy rainfall",
            "light rain": "light rainfall",
            "drizzle": "light drizzle",
            "clear sky": "clear weather",
            "overcast sky": "overcast skies",
            "fog": "foggy conditions",
            "thunderstorm": "a thunderstorm"
        }.get(weather.lower(), weather.lower())

        parts.append(f"under {weather_text}")

    if lighting:
        parts.append(f"lit by {lighting.lower()}")

    if atmosphere:
        parts.append(f"with {atmosphere.lower()} in the environment")

    if not parts:
        return ""

    return ", " + ", ".join(parts)


def describe_effects(effects, mode):
    if not effects:
        return ""

    effects_text = [effect.lower() for effect in effects]

    if len(effects_text) == 1:
        combined = effects_text[0]
    else:
        combined = ", ".join(effects_text[:-1]) + " and " + effects_text[-1]

    if mode == "anime":
        return f", enhanced with {combined}"

    return f", enhanced with {combined} effects"

def render_prompt(scene_graph):
    if not isinstance(scene_graph, dict):
        raise TypeError("Scene graph must be a dictionary.")

    composition = scene_graph.get("compositional_deconstruction", {})
    raw_elements = composition.get("elements", [])

    elements = [
        describe_json_element({
            **element,
            "mode": "anime" if scene_graph.get(
                "high_level_description", ""
            ).lower().startswith("anime") else "realistic"
        }).rstrip(".")
        for element in raw_elements
    ]

    return compose_prompt(scene_graph, elements)


def compose_prompt(scene_graph, elements):
    original = scene_graph.get("high_level_description", "")
    anime = original.lower().startswith("anime")

    composition = scene_graph.get("compositional_deconstruction", {})
    background = composition.get("background") or {}

    parts = []

    if anime:
        parts.append("Anime-style illustration")
    else:
        first_type = (
            composition.get("elements", [{}])[0].get("type", "").lower()
            if composition.get("elements") else ""
        )
        if first_type in ("car", "vehicle"):
            parts.append("Photorealistic automotive photography")
        elif first_type in ("character", "person", "portrait"):
            parts.append("Photorealistic portrait photography")
        elif first_type == "architecture":
            parts.append("Realistic architectural photography")
        else:
            parts.append("Photorealistic scene")

    if elements:
        first = elements[0].strip().rstrip(".")
        parts.append(first)

        for extra in elements[1:]:
            extra = extra.strip().rstrip(".")
            if extra:
                parts.append(extra)

    angle = scene_graph.get("camera_angle")
    if angle:
        angle_text = angle.lower().replace("-", " ").strip()
        if angle_text not in ("front view", "rear view", "side view"):
            parts.append(angle_text)
        else:
            parts.append(angle_text)

    location = background.get("location")
    if location:
        parts.append(location.lower())

    time = background.get("time")
    if time:
        time_map = {
            "night": "at night",
            "day": "during the day",
            "sunset": "at sunset",
            "sunrise": "at sunrise"
        }
        parts.append(time_map.get(time.lower(), time.lower()))

    weather = background.get("weather")
    if weather:
        weather_map = {
            "overcast sky": "overcast sky",
            "clear sky": "clear sky",
            "heavy rain": "heavy rainfall",
            "light rain": "light rain",
            "drizzle": "light drizzle",
            "snow": "snow",
            "fog": "fog",
            "thunderstorm": "thunderstorm"
        }
        parts.append(weather_map.get(weather.lower(), weather.lower()))

    lighting = background.get("lighting")
    if lighting:
        parts.append(lighting.lower())

    atmosphere = background.get("atmosphere")
    if atmosphere:
        parts.append(atmosphere.lower())

    effects = scene_graph.get("visual_effects") or []
    parts.extend(effect.lower() for effect in effects)

    style = scene_graph.get("visual_style")
    if style:
        style_map = {
            "minimalism": "minimalist aesthetic",
            "surrealism": "surrealist aesthetic",
            "impressionism": "impressionist aesthetic",
            "expressionism": "expressionist aesthetic",
            "realism": "realist aesthetic"
        }
        parts.append(style_map.get(style.lower(), style.lower() + " aesthetic"))

    grading = scene_graph.get("color_grading")
    if grading:
        grading_map = {
            "high contrast monochrome": "high-contrast monochrome",
            "analog film colors": "analog film color palette",
            "pastel color palette": "pastel color palette",
            "deep emerald tones": "deep emerald tones",
            "golden cinematic tones": "golden cinematic tones",
            "muted earth tones": "muted earth tones",
            "teal and orange": "teal and orange color grading"
        }
        parts.append(grading_map.get(grading.lower(), grading.lower()))

    techniques = scene_graph.get("camera_techniques") or []
    for technique in techniques:
        normalized = technique.lower().replace("-", " ").strip()
        if angle and normalized == angle.lower().replace("-", " ").strip():
            continue

        technique_map = {
            "low perspective shot": "low-angle perspective",
            "extreme close up": "extreme close-up",
            "macro photography": "macro photography",
            "long exposure": "long exposure",
            "symmetrical framing": "symmetrical framing",
            "leading lines": "leading lines",
            "foreground framing": "foreground framing",
            "dutch angle": "Dutch angle",
            "anamorphic cinematography": "anamorphic cinematography",
            "tracking shot": "tracking shot",
            "dolly zoom": "dolly zoom",
            "over the shoulder shot": "over-the-shoulder composition"
        }
        parts.append(technique_map.get(normalized, technique.lower()))

    camera = scene_graph.get("camera") or {}

    lens = camera.get("lens")
    if lens:
        parts.append(f"{lens} lens")

    distance = camera.get("shot_distance")
    distance_map = {
        "Close": "close-up framing",
        "Medium": "medium shot",
        "Wide": "wide shot"
    }
    if distance:
        parts.append(distance_map.get(distance, distance.lower()))

    depth = camera.get("depth_of_field")
    depth_map = {
        "Shallow": "shallow depth of field",
        "Moderate": "moderate depth of field",
        "Deep": "deep depth of field"
    }
    if depth:
        parts.append(depth_map.get(depth, depth.lower()))

    focus = camera.get("focus")
    focus_map = {
        "Subject Focus": "sharp focus on the main subject",
        "Environmental Focus": "environmental focus",
        "Balanced Focus": "balanced subject and environmental focus"
    }
    if focus:
        parts.append(focus_map.get(focus, focus.lower()))

    aspect_ratio = scene_graph.get("aspect_ratio")
    if aspect_ratio:
        parts.append(f"{aspect_ratio} aspect ratio")

    return ", ".join(part.strip(" ,.") for part in parts if part).strip() + "."


def describe_json_background(background):
    if not isinstance(background, dict):
        return ""

    parts = []

    for key in ("location", "time", "weather", "lighting", "atmosphere"):
        value = background.get(key)
        if value:
            parts.append(value.lower())

    return ", ".join(parts)


def describe_json_element(element):
    description = element.get("desc", "").strip()
    name, attribute_parts = split_description(element)

    if not name:
        return description

    attributes = {}
    for part in attribute_parts:
        if ":" in part:
            key, value = part.split(":", 1)
            attributes[key.strip().lower()] = value.strip()

    def add_article(value):
        value = value.strip()
        if not value:
            return value
        if value.lower().startswith(("a ", "an ", "the ")):
            return value
        article = "an" if value[0].lower() in "aeiou" else "a"
        return f"{article} {value}"

    def describe_wearing(value):
        value = value.strip()
        if value.lower().endswith(("s", "glasses", "jewelry")):
            return f"wearing {value.lower()}"
        return f"wearing {add_article(value).lower()}"

    element_type = element.get("type", "").lower()

    vehicle_names = (
        "lamborghini", "ferrari", "bugatti", "pagani",
        "mclaren", "koenigsegg", "rolls-royce",
        "porsche", "mercedes-amg", "bmw"
    )

    is_vehicle = (
        element_type in ("vehicle", "car")
        or name.lower().startswith(vehicle_names)
    )

    if is_vehicle:
        sentence = name

        finish = attributes.get("finish")
        material = attributes.get("material")
        headlights = attributes.get("headlights")

        if finish:
            sentence += f" with a {finish.lower()} finish"

        if material:
            material_text = material.lower()
            if material_text.endswith(" details"):
                sentence += f" with {material_text}"
            else:
                sentence += f" and {material_text} details"

        if headlights:
            sentence += f", featuring {headlights.lower().replace('led', 'LED')}"

        return sentence + "."

    is_character = element_type in ("character", "person", "portrait")

    if is_character:
        mode = element.get("mode", "realistic")
        pose = attributes.get("pose")
        framing = attributes.get("framing")
        camera = attributes.get("camera angle")
        composition = attributes.get("composition")

        if mode == "anime":
            if element_type == "portrait":
                sentence = "An original anime character portrait"
            elif name.strip().lower() in ("character", "original anime character"):
                sentence = "An original anime character"
            else:
                sentence = f"An original anime character named {name}"
        else:
            sentence = name

        details = []

        if pose:
            details.append(f"in a {pose.lower()} pose")

        if framing:
            details.append(
                f"framed as a {framing.lower()}"
                if framing.lower().endswith("shot")
                else f"framed as a {framing.lower()} shot"
            )

        if camera:
            details.append(describe_camera_angle(camera))

        if composition:
            details.append(f"using {composition.lower()} composition")

        character_details = {
            "hairstyle": lambda value: f"with {value.lower()}",
            "clothing": lambda value: f"dressed in {value.lower() if value.lower().endswith(('clothing', 'wear', 'streetwear', 'techwear')) else add_article(value).lower()}",
            "expression": lambda value: (
                f"with {value.lower()}"
                if value.lower().endswith("expression")
                else f"with {add_article(value).lower()} expression"
            ),
            "accessories": describe_wearing
        }

        for key, formatter in character_details.items():
            value = attributes.get(key)
            if value:
                details.append(formatter(value))

        if details:
            sentence += ", " + ", ".join(details)

        return sentence + "."

    if element_type == "architecture":
        details = []

        style = attributes.get("architectural style")
        facade = attributes.get("facade")
        materials = attributes.get("architectural materials")
        features = attributes.get("architectural features")

        if style:
            details.append(f"in the {style.lower()} style")

        if facade:
            details.append(f"with {facade.lower() if facade.lower().endswith('cladding') else add_article(facade).lower()}")

        if materials:
            details.append(f"constructed from {materials.lower()}")

        if features:
            details.append(f"featuring {features.lower() if features.lower().endswith(('windows', 'columns', 'detailing')) else add_article(features).lower()}")

        if details:
            return "An architectural design " + ", ".join(details) + "."

    return description


def create_json_description(scene_graph, elements):
    descriptions = [
        element.get("desc", "").strip().rstrip(".")
        for element in elements
        if element.get("desc", "").strip()
    ]
    return compose_prompt(scene_graph, descriptions)


def render_json(scene_graph, indent=None):
    if not isinstance(scene_graph, dict):
        raise TypeError("Scene graph must be a dictionary.")

    composition = scene_graph.get("compositional_deconstruction", {})
    background = describe_json_background(
        composition.get("background")
    )

    elements = []

    for element in composition.get("elements", []):
        bbox = element.get("bbox", [])

        if len(bbox) != 4:
            raise ValueError("Every element must have a four-value bbox.")

        bbox = [
            round(value * 1000) if 0 <= value <= 1 else round(value)
            for value in bbox
        ]

        elements.append({
            "type": element.get("type", "obj"),
            "bbox": bbox,
            "desc": describe_json_element({**element, "mode": "anime" if scene_graph.get("high_level_description", "").lower().startswith("anime") else "realistic"})
        })

    composition = {
        "elements": elements
    }

    if background:
        composition["background"] = background

    result = {
        "aspect_ratio": scene_graph.get("aspect_ratio", "4:3"),
        "high_level_description": create_json_description(
            scene_graph, elements
        ),
        "compositional_deconstruction": composition
    }

    camera = scene_graph.get("camera")
    if isinstance(camera, dict) and camera:
        result["camera"] = dict(camera)

    camera_angle = scene_graph.get("camera_angle")
    if camera_angle:
        result["camera_angle"] = camera_angle

    for key in ("visual_style", "color_grading", "camera_techniques"):
        if scene_graph.get(key):
            result[key] = scene_graph[key]

    return json.dumps(
        result,
        ensure_ascii=False,
        separators=(",", ":")
    )
