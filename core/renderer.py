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
        "architectural style": lambda value: f"in the {value} architectural style",
        "facade": lambda value: f"featuring {value.lower()}",
        "architectural materials": lambda value: f"constructed from {value.lower()}",
        "architectural features": lambda value: f"with {value.lower()}"
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
    elements = composition.get("elements", [])
    background = composition.get("background") or {}

    original_description = scene_graph.get("high_level_description", "")
    mode = "anime" if original_description.lower().startswith("anime") else "realistic"

    main_element = elements[0] if elements else {}
    main = describe_main_element(main_element, mode) if elements else ""

    if not main:
        main = "A photorealistic scene" if mode == "realistic" else "An anime-style scene"

    paragraphs = [main.rstrip(" .") + "."]

    camera_angle = scene_graph.get("camera_angle")
    if camera_angle:
        angle = describe_camera_angle(camera_angle)
        paragraphs.append(f"The shot is captured {angle}.")

    additional = describe_additional_elements(elements[1:], mode) if len(elements) > 1 else ""
    if additional:
        paragraphs.append(f"The scene also includes {additional.lstrip(', ')}.")

    environment_parts = []

    location = background.get("location")
    time = background.get("time")
    weather = background.get("weather")
    lighting = background.get("lighting")
    atmosphere = background.get("atmosphere")

    if location:
        environment_parts.append(f"at {location.lower()}")

    if time:
        environment_parts.append(f"during {time.lower()}")

    weather_descriptions = {
        "snow": "snowy conditions",
        "heavy rain": "heavy rainfall",
        "light rain": "light rainfall",
        "drizzle": "light drizzle",
        "clear sky": "clear skies",
        "overcast sky": "overcast skies",
        "fog": "foggy conditions",
        "thunderstorm": "a thunderstorm"
    }

    if weather:
        environment_parts.append(
            f"under {weather_descriptions.get(weather.lower(), weather.lower())}"
        )

    if environment_parts:
        paragraphs.append("The scene takes place " + ", ".join(environment_parts) + ".")

    if lighting or atmosphere:
        if lighting:
            paragraphs.append(f"The scene is illuminated by {lighting.lower()}.")

        if atmosphere:
            paragraphs.append(f"The atmosphere features {atmosphere.lower()}.")

    effects = [
        "cinematic effects" if item.lower() == "cinematic" else item.lower()
        for item in scene_graph.get("visual_effects", [])
    ]
    if effects:
        if len(effects) == 1:
            effect_text = effects[0]
        else:
            effect_text = ", ".join(effects[:-1]) + " and " + effects[-1]

        paragraphs.append(f"The image is enhanced with {effect_text}.")

    visual_style = scene_graph.get("visual_style")
    if visual_style:
        style_names = {
            "surrealism": "surrealist",
            "impressionism": "impressionist",
            "expressionism": "expressionist",
            "minimalism": "minimalist",
            "realism": "realist"
        }

        if main_element.get("type", "").lower() == "architecture":
            paragraphs.append(
                f"The architecture follows a {visual_style} architectural style."
            )
        else:
            style = style_names.get(visual_style.lower(), visual_style.lower())
            paragraphs.append(f"The image features a {style} visual style.")

    color_grading = scene_graph.get("color_grading")
    if color_grading:
        grading_names = {
            "analog film colors": "an analog film color palette",
            "pastel color palette": "a pastel color palette",
            "deep emerald tones": "deep emerald tones",
            "golden cinematic tones": "golden cinematic tones",
            "muted earth tones": "muted earth tones",
            "teal and orange": "teal and orange tones"
        }
        grading = grading_names.get(color_grading.lower(), color_grading.lower())
        paragraphs.append(f"The image uses {grading}.")

    techniques = scene_graph.get("camera_techniques") or []

    technique_descriptions = {
        "anamorphic cinematography": "Anamorphic framing creates a cinematic widescreen look with distinctive lens characteristics",
        "dutch angle": "A tilted camera angle adds visual tension and a sense of unease",
        "over-the-shoulder shot": "An over-the-shoulder composition adds depth and establishes spatial relationships",
        "tracking shot": "Tracking camera movement creates a sense of motion and follows the subject",
        "dolly zoom": "A dolly zoom creates a dramatic perspective shift while maintaining the subject's visual prominence",
        "macro photography": "Macro photography reveals intricate textures and fine details",
        "long exposure": "Long exposure captures motion as flowing light trails and dynamic movement",
        "low perspective shot": "A low perspective emphasizes the subject's scale and presence",
        "extreme close-up": "Extreme close-up framing highlights minute details and textures",
        "symmetrical framing": "Symmetrical framing creates visual balance and geometric harmony",
        "leading lines": "Leading lines guide the viewer's attention toward the main subject",
        "foreground framing": "Foreground elements add depth and naturally frame the main subject"
    }

    if techniques:
        for technique in techniques:
            description = technique_descriptions.get(
                technique.lower(),
                f"The composition incorporates {technique.lower()}"
            )
            paragraphs.append(description.rstrip(".") + ".")

    main_name, _ = split_description(main_element)

    camera_description = describe_camera(
        scene_graph.get("camera"),
        mode,
        main_element.get("type"),
        main_name
    )

    if camera_description:
        paragraphs.append(camera_description)

    aspect_ratio = scene_graph.get("aspect_ratio")
    if aspect_ratio:
        paragraphs.append(f"The composition uses a {aspect_ratio} aspect ratio.")

    return " ".join(" ".join(paragraphs).split())

def describe_json_background(background):
    if not isinstance(background, dict):
        return ""

    parts = []

    location = background.get("location")
    time = background.get("time")
    weather = background.get("weather")
    lighting = background.get("lighting")
    atmosphere = background.get("atmosphere")

    if location:
        place = location.lower()
        countable_places = (
            "city", "town", "village", "kingdom", "district",
            "forest", "street", "desert", "mansion", "castle",
            "garden", "island", "building", "village"
        )

        last_word = place.split()[-1]
        if last_word in countable_places:
            article = "an" if place[0] in "aeiou" else "a"
            place = f"{article} {place}"

        parts.append(f"The scene takes place in {place}.")

    conditions = []

    if time:
        if time.lower() == "night":
            conditions.append("at night")
        elif time.lower() == "day":
            conditions.append("during the day")
        elif time.lower() == "sunset":
            conditions.append("at sunset")
        elif time.lower() == "sunrise":
            conditions.append("at sunrise")
        else:
            conditions.append(f"during the {time.lower()}")

    if weather:
        conditions.append(f"with {weather.lower()}")

    if lighting:
        conditions.append(f"illuminated by {lighting.lower()}")

    if atmosphere:
        conditions.append(f"surrounded by {atmosphere.lower()}")

    if conditions:
        parts.append("The environment is " + ", ".join(conditions) + ".")

    return " ".join(parts)


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
        if value.lower().endswith(("s", "glasses")):
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
            sentence += f" and {material.lower()} details"

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
            sentence = f"A photorealistic portrait of {name}"

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
            "clothing": lambda value: f"dressed in {add_article(value).lower()}",
            "expression": lambda value: (
                f"with {value.lower()} expression"
                if value.lower().endswith("expression")
                else f"with a {value.lower()} expression"
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
            details.append(f"in a {style.lower()} architectural style")

        if facade:
            details.append(f"with {add_article(facade).lower()}")

        if materials:
            details.append(f"constructed from {materials.lower()}")

        if features:
            details.append(f"featuring {features.lower()}")

        if details:
            return "An architectural design " + ", ".join(details) + "."

    return description


def create_json_description(scene_graph, elements):
    original = scene_graph.get("high_level_description", "")
    is_anime = original.lower().startswith("anime")

    original_elements = scene_graph.get(
        "compositional_deconstruction", {}
    ).get("elements", [])

    first_type = (
        original_elements[0].get("type", "").lower()
        if original_elements else ""
    )

    if elements:
        first = elements[0]["desc"].strip().rstrip(".")

        if is_anime:
            if first.lower().startswith("an original anime character"):
                description = first + "."
            else:
                core = first
                if core.lower().startswith("an "):
                    core = core[3:]
                elif core.lower().startswith("a "):
                    core = core[2:]
                description = "An anime-style scene featuring " + core + "."

        elif first.lower().startswith(("a photorealistic", "an architectural")):
            description = first + "."

        elif first_type == "architecture":
            description = "A realistic architectural photograph of " + first + "."

        elif first_type in ("vehicle", "car"):
            description = "A photorealistic automotive photograph featuring " + first + "."

        else:
            description = "A photorealistic scene featuring " + first + "."

        for element in elements[1:]:
            extra = element["desc"].strip().rstrip(".")
            if extra:
                if extra.lower().startswith(("a ", "an ", "the ")):
                    phrase = extra[0].lower() + extra[1:]
                elif element.get("type", "").lower() == "architecture":
                    phrase = "a " + extra.lower()
                else:
                    phrase = "a " + extra[0].lower() + extra[1:]
                description += " The scene also includes " + phrase + "."

    else:
        description = (
            "An anime-style scene."
            if is_anime
            else "A photorealistic scene."
        )

    camera_angle = scene_graph.get("camera_angle")
    if camera_angle:
        normalized_angle = camera_angle.lower().replace("-", " ").strip()
        if normalized_angle in ("extreme close up", "close up"):
            article = "an" if normalized_angle.startswith("extreme") else "a"
            display_angle = normalized_angle.replace(" ", "-")
            description += f" The shot uses {article} {display_angle} framing."
        else:
            angle = describe_camera_angle(camera_angle)
            description += f" The shot is captured {angle}."

    background = scene_graph.get(
        "compositional_deconstruction", {}
    ).get("background") or {}

    background_description = describe_json_background(background)
    if background_description:
        description += " " + background_description

    effects = scene_graph.get("visual_effects") or []
    if effects:
        effect_names = {
            "cinematic": "cinematic effects",
            "motion blur": "motion blur to emphasize movement",
            "lens flare": "lens flare for enhanced light interaction",
            "depth of field": "depth-of-field effects to separate the subject from its surroundings",
            "film grain": "subtle film grain for a textured photographic appearance"
        }

        effect_descriptions = [
            effect_names.get(effect.lower(), effect.lower())
            for effect in effects
        ]
        description += " The image incorporates " + ", ".join(effect_descriptions) + "."

    visual_style = scene_graph.get("visual_style")
    if visual_style:
        style_names = {
            "surrealism": "surrealist",
            "impressionism": "impressionist",
            "expressionism": "expressionist",
            "minimalism": "minimalist",
            "realism": "realist",
            "gothic": "gothic",
            "anime": "anime"
        }

        architecture = first_type == "architecture"

        style = style_names.get(visual_style.lower(), visual_style.lower())

        if architecture:
            existing_descriptions = " ".join(
                element.get("desc", "").lower() for element in elements
            )
            if f"{style} architectural style" not in existing_descriptions:
                description += f" The architecture follows a {style} architectural style."
        else:
            article = "an" if style[0].lower() in "aeiou" else "a"
            description += f" The image features {article} {style} visual style."

    color_grading = scene_graph.get("color_grading")
    if color_grading:
        grading_names = {
            "analog film colors": "an analog film color palette",
            "pastel color palette": "a pastel color palette",
            "deep emerald tones": "deep emerald tones",
            "golden cinematic tones": "golden cinematic tones",
            "muted earth tones": "muted earth tones",
            "teal and orange": "teal and orange tones"
        }

        grading = grading_names.get(
            color_grading.lower(), color_grading.lower()
        )
        description += f" The image uses {grading}."

    technique_descriptions = {
        "anamorphic cinematography": "Anamorphic framing creates a cinematic widescreen look with distinctive lens characteristics.",
        "dutch angle": "A tilted camera angle adds visual tension and a sense of unease.",
        "over-the-shoulder shot": "An over-the-shoulder composition adds depth and establishes spatial relationships.",
        "tracking shot": "Tracking camera movement creates a sense of motion and follows the subject.",
        "dolly zoom": "A dolly zoom creates a dramatic perspective shift while maintaining the subject's visual prominence.",
        "macro photography": "Macro photography reveals intricate textures and fine details.",
        "long exposure": "Long exposure captures motion as flowing light trails and dynamic movement.",
        "low perspective shot": "A low perspective emphasizes the subject's scale and presence.",
        "extreme close-up": "Extreme close-up framing highlights minute details and textures.",
        "symmetrical framing": "Symmetrical framing creates visual balance and geometric harmony.",
        "leading lines": "Leading lines guide the viewer's attention toward the main subject.",
        "foreground framing": "Foreground elements add depth and naturally frame the main subject."
    }

    techniques = scene_graph.get("camera_techniques") or []
    angle_normalized = (camera_angle or "").lower().replace("-", " ").strip()

    for technique in techniques:
        normalized = technique.lower().replace("-", " ").strip()

        if normalized == angle_normalized:
            continue

        explanation = technique_descriptions.get(
            technique.lower(),
            f"The composition incorporates {technique.lower()}."
        )
        description += " " + explanation

    description += (
        f" The composition uses a "
        f"{scene_graph.get('aspect_ratio', '4:3')} aspect ratio."
    )

    return description


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
