import json

from core.camera import describe_camera


def split_description(element):
    description = element.get("desc", "").strip()
    parts = [part.strip() for part in description.split(",")]

    if not parts:
        return "", []

    return parts[0], parts[1:]


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
    }

    return known.get(value, f"from the {value} angle")


def format_attributes(attributes):
    labels = {
        "finish": "a",
        "material": "",
        "headlights": "",
        "pose": "in a",
        "framing": "framed as",
        "camera angle": "from a",
        "composition": "with"
    }

    result = []

    for attribute in attributes:
        if ":" not in attribute:
            result.append(attribute)
            continue

        key, value = attribute.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if key == "finish":
            result.append(f"{value.lower()} finish")
        elif key == "material":
            result.append(f"{value.lower()} details")
        elif key == "headlights":
            result.append(f"{value.lower()}")
        elif key == "pose":
            result.append(f"{value.lower()} pose")
        elif key == "framing":
            result.append(f"{value.lower()} framing")
        elif key == "camera angle":
            result.append(describe_camera_angle(value))
        elif key == "composition":
            result.append(f"{value.lower()} composition")
        else:
            result.append(f"{key}: {value}")

    return result


def describe_main_element(element, mode):
    name, attributes = split_description(element)
    details = format_attributes(attributes)
    element_type = element.get("type", "").lower()

    if mode == "anime":
        if element_type == "portrait" and name.strip().lower() == "portrait":
            sentence = "An original anime character portrait"
        elif element_type in ("character", "portrait"):
            if name.strip().lower() == "character":
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

    return sentence


def describe_additional_elements(elements, mode):
    descriptions = []

    for element in elements:
        name, attributes = split_description(element)

        if not name:
            continue

        details = format_attributes(attributes)
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

    effects_text = ", ".join(effect.lower() for effect in effects)

    if mode == "anime":
        return f", enhanced with {effects_text}"

    return f", finished with {effects_text}"


def render_prompt(scene_graph):
    if not isinstance(scene_graph, dict):
        raise TypeError("Scene graph must be a dictionary.")

    composition = scene_graph.get("compositional_deconstruction", {})
    elements = composition.get("elements", [])
    background = composition.get("background") or {}

    original_description = scene_graph.get("high_level_description", "")
    mode = "anime" if original_description.lower().startswith("anime") else "realistic"

    main = describe_main_element(elements[0], mode) if elements else ""
    additional = describe_additional_elements(elements[1:], mode) if elements else ""
    environment = describe_environment(background)
    effects = describe_effects(scene_graph.get("visual_effects"), mode)

    if not main and environment:
        main = "A photorealistic scene" if mode == "realistic" else "An anime-style scene"

    prompt = main + additional + environment + effects

    main_element = elements[0] if elements else {}
    main_name, _ = split_description(main_element)

    camera_description = describe_camera(
        scene_graph.get("camera"),
        mode,
        main_element.get("type"),
        main_name
    )
    if camera_description:
        prompt += ", " + camera_description

    aspect_ratio = scene_graph.get("aspect_ratio")

    if aspect_ratio:
        prompt += f", composed in a {aspect_ratio} aspect ratio"

    prompt = prompt.strip(" ,.")
    if not prompt:
        prompt = "A photorealistic scene" if mode == "realistic" else "An anime-style scene"

    return prompt + "."



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
        parts.append(f"The scene takes place in {location.lower()}.")

    conditions = []

    if time:
        conditions.append(f"at {time.lower()}")

    if weather:
        conditions.append(f"under {weather.lower()} conditions")

    if lighting:
        conditions.append(f"illuminated by {lighting.lower()}")

    if atmosphere:
        conditions.append(f"with {atmosphere.lower()}")

    if conditions:
        if not location:
            parts.append("The environment is " + ", ".join(conditions) + ".")
        else:
            parts.append("The environment features " + ", ".join(conditions) + ".")

    return " ".join(parts) or ""


def describe_json_element(element):
    description = element.get("desc", "").strip()
    parts = [part.strip() for part in description.split(",")]

    if not parts or not parts[0]:
        return description

    name = parts[0]
    attributes = {}

    for part in parts[1:]:
        if ":" in part:
            key, value = part.split(":", 1)
            attributes[key.strip().lower()] = value.strip()

    element_type = element.get("type", "").lower()

    vehicle_names = (
        "lamborghini", "ferrari", "bugatti",
        "pagani", "mclaren", "koenigsegg",
        "rolls-royce", "porsche", "mercedes-amg", "bmw"
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
            sentence += f", featuring {headlights.replace('led', 'LED').lower().replace('led', 'LED')}"

        return sentence + "."

    is_character = element_type in (
        "character", "person", "portrait"
    )

    if is_character:
        mode = element.get("mode", "realistic")
        pose = attributes.get("pose")
        framing = attributes.get("framing")
        camera = attributes.get("camera angle")
        composition = attributes.get("composition")

        if mode == "anime":
            if element_type == "portrait":
                sentence = "An original anime character portrait"
            elif name.strip().lower() == "character":
                sentence = "An original anime character"
            else:
                sentence = f"An original anime character named {name}"
        else:
            sentence = f"A photorealistic portrait of {name}"

        details = []

        if pose:
            details.append(f"in a {pose.lower()} pose")

        if framing:
            details.append(f"framed as a {framing.lower()} shot")

        if camera:
            details.append(describe_camera_angle(camera))

        if composition:
            details.append(f"using {composition.lower()} composition")

        if details:
            sentence += ", " + ", ".join(details)

        return sentence + "."

    return description



def create_json_description(scene_graph, elements):
    original = scene_graph.get("high_level_description", "")
    is_anime = original.lower().startswith("anime")

    if elements:
        first = elements[0]["desc"].strip().rstrip(".")

        if is_anime:
            core = first

            if core.lower().startswith("an "):
                core = core[3:]
            elif core.lower().startswith("a "):
                core = core[2:]

            description = (
                "An anime-style scene featuring "
                + core
                + "."
            )
        elif first.lower().startswith("a photorealistic"):
            description = first + "."
        else:
            vehicle_prefixes = (
                "lamborghini", "ferrari", "bugatti", "pagani",
                "mclaren", "koenigsegg", "rolls-royce",
                "porsche", "mercedes-amg", "bmw"
            )

            if first.lower().startswith(vehicle_prefixes):
                subject = first
            else:
                subject = first[0].lower() + first[1:]

            description = (
                "A photorealistic scene featuring "
                + subject
                + "."
            )
    else:
        description = (
            "An anime-style scene."
            if is_anime
            else "A photorealistic scene."
        )

    background = scene_graph.get(
        "compositional_deconstruction", {}
    ).get("background") or {}

    location = background.get("location")
    if location:
        description += f" The scene is set in {location.lower()}."

    time = background.get("time")
    if time:
        description += f" The time of day is {time.lower()}."

    lighting = background.get("lighting")
    if lighting:
        description += f" The scene is illuminated by {lighting.lower()}."

    weather = background.get("weather")
    if weather:
        description += f" The weather is {weather.lower()}."

    atmosphere = background.get("atmosphere")
    if atmosphere:
        description += f" The atmosphere includes {atmosphere.lower()}."

    effects = scene_graph.get("visual_effects") or []
    if effects:
        description += " Visual effects include " + ", ".join(
            effect.lower() for effect in effects
        ) + "."

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
            "type": "obj",
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

    return json.dumps(
        result,
        ensure_ascii=False,
        separators=(",", ":")
    )
