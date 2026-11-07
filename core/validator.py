from core.camera import CAMERA_OPTIONS


def validate_camera(camera):
    if not isinstance(camera, dict) or not camera:
        return False

    for key, value in camera.items():
        if key not in CAMERA_OPTIONS:
            return False
        if value not in CAMERA_OPTIONS[key]:
            return False

    return True


def validate_bbox(bbox):
    if not isinstance(bbox, list) or len(bbox) != 4:
        return False

    if not all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in bbox
    ):
        return False

    x_min, y_min, x_max, y_max = bbox

    if not all(0 <= value <= 1 for value in bbox):
        return False

    if x_min >= x_max or y_min >= y_max:
        return False

    return True


def validate_scene_graph(scene):
    errors = []

    if not isinstance(scene, dict):
        return False, ["Scene graph must be a dictionary."]

    if not scene.get("aspect_ratio"):
        errors.append("Missing aspect_ratio.")

    if "camera" in scene and not validate_camera(scene["camera"]):
        errors.append("Invalid camera settings.")

    if not isinstance(scene.get("high_level_description"), str):
        errors.append("high_level_description must be a string.")

    composition = scene.get("compositional_deconstruction")

    if not isinstance(composition, dict):
        errors.append("Missing compositional_deconstruction.")
        return False, errors

    if "background" not in composition:
        errors.append("Missing background field.")

    elements = composition.get("elements")

    if not isinstance(elements, list):
        errors.append("elements must be a list.")
        return False, errors

    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            errors.append(f"Element {index} must be a dictionary.")
            continue

        if not element.get("type"):
            errors.append(f"Element {index} is missing type.")

        if not isinstance(element.get("desc"), str):
            errors.append(f"Element {index} has an invalid desc.")

        if "bbox" in element and not validate_bbox(element["bbox"]):
            errors.append(f"Element {index} has an invalid bbox.")

    return len(errors) == 0, errors
