CAMERA_OPTIONS = {
    "lens": [
        "24mm",
        "35mm",
        "50mm",
        "85mm",
        "135mm"
    ],
    "shot_distance": [
        "Close",
        "Medium",
        "Wide"
    ],
    "depth_of_field": [
        "Shallow",
        "Moderate",
        "Deep"
    ],
    "focus": [
        "Subject Focus",
        "Environmental Focus",
        "Balanced Focus"
    ]
}


def create_camera_settings(
    lens=None,
    shot_distance=None,
    depth_of_field=None,
    focus=None
):
    selections = {
        "lens": lens,
        "shot_distance": shot_distance,
        "depth_of_field": depth_of_field,
        "focus": focus
    }

    result = {}

    for key, value in selections.items():
        if value is None:
            continue

        if value not in CAMERA_OPTIONS[key]:
            raise ValueError(f"Invalid {key}: {value}")

        result[key] = value

    return result


def describe_camera(camera, mode="realistic", subject_type=None, subject_name=None):
    if not isinstance(camera, dict) or not camera:
        return ""

    realistic_lenses = {
        "24mm": "a 24mm ultra-wide lens with expansive perspective",
        "35mm": "a 35mm wide-angle lens with natural environmental perspective",
        "50mm": "a 50mm standard lens with natural perspective",
        "85mm": "an 85mm portrait lens with flattering compression",
        "135mm": "a 135mm telephoto lens with compressed perspective"
    }

    anime_lenses = {
        "24mm": "an ultra-wide perspective emphasizing spatial depth",
        "35mm": "a wide cinematic perspective with environmental context",
        "50mm": "a balanced perspective with natural visual proportions",
        "85mm": "a compressed cinematic perspective emphasizing the character",
        "135mm": "a strong telephoto perspective with layered visual depth"
    }

    realistic_distances = {
        "Close": "a close camera distance",
        "Medium": "a medium camera distance",
        "Wide": "a wide camera distance"
    }

    anime_distances = {
        "Close": "close character framing",
        "Medium": "medium character framing",
        "Wide": "wide cinematic framing that reveals more of the environment"
    }

    realistic_depth = {
        "Shallow": "shallow depth of field with a softly blurred background",
        "Moderate": "moderate depth of field with balanced subject separation",
        "Deep": "deep depth of field with the environment clearly visible"
    }

    anime_depth = {
        "Shallow": "shallow cinematic focus with a softly blurred background",
        "Moderate": "balanced depth with clear character separation",
        "Deep": "deep visual focus keeping the character and environment detailed"
    }

    realistic_focus = {
        "Subject Focus": "sharp focus on the main subject",
        "Environmental Focus": "focus emphasizing the surrounding environment",
        "Balanced Focus": "balanced focus between the subject and environment"
    }

    anime_focus = {
        "Subject Focus": "visual emphasis and sharp detail on the main character",
        "Environmental Focus": "visual emphasis on the surrounding world and scenery",
        "Balanced Focus": "balanced visual emphasis between character and environment"
    }

    is_anime = mode == "anime"

    vehicle_names = (
        "lamborghini", "ferrari", "bugatti", "pagani",
        "mclaren", "koenigsegg", "rolls-royce",
        "porsche", "mercedes-amg", "bmw"
    )

    is_vehicle = (
        str(subject_type or "").lower() in ("car", "vehicle")
        or str(subject_name or "").strip().lower().startswith(vehicle_names)
    )

    if is_anime and is_vehicle:
        anime_lenses["85mm"] = "a compressed cinematic perspective emphasizing the vehicle"
        anime_distances["Close"] = "close vehicle framing"
        anime_distances["Medium"] = "medium vehicle framing"
        anime_depth["Moderate"] = "balanced depth with clear vehicle separation"
        anime_depth["Deep"] = "deep visual focus keeping the vehicle and environment detailed"
        anime_focus["Subject Focus"] = "visual emphasis and sharp detail on the main vehicle"
        anime_focus["Balanced Focus"] = "balanced visual emphasis between the vehicle and environment"


    lens_descriptions = anime_lenses if is_anime else realistic_lenses
    distance_descriptions = anime_distances if is_anime else realistic_distances
    depth_descriptions = anime_depth if is_anime else realistic_depth
    focus_descriptions = anime_focus if is_anime else realistic_focus

    descriptions = []

    lens = camera.get("lens")
    distance = camera.get("shot_distance")
    depth = camera.get("depth_of_field")
    focus = camera.get("focus")

    if lens in lens_descriptions:
        descriptions.append(lens_descriptions[lens])

    if distance in distance_descriptions:
        descriptions.append(distance_descriptions[distance])

    if depth in depth_descriptions:
        descriptions.append(depth_descriptions[depth])

    if focus in focus_descriptions:
        descriptions.append(focus_descriptions[focus])

    if not descriptions:
        return ""

    if is_anime:
        return (
            "Cinematic anime camera direction: "
            + ", ".join(descriptions)
        )

    return (
        "Photographic camera setup: "
        + ", ".join(descriptions)
    )
