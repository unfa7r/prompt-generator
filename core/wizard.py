import json
from pathlib import Path

from .camera import CAMERA_OPTIONS, create_camera_settings

ROOT = Path(__file__).resolve().parent.parent
CATEGORY_FILE = ROOT / "config" / "categories.json"


def load_categories():
    with CATEGORY_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def custom_text(prompt):
    while True:
        value = input(prompt).strip()

        if not value or value == "0":
            return None

        if value.isdigit():
            print("Enter text, not a selection number.")
            continue

        return value


def choose(title, options, custom=True):
    print(f"\n{title.upper()}")
    print("=" * 30)

    for index, option in enumerate(options, 1):
        print(f"{index}. {option}")

    if custom:
        print(f"{len(options) + 1}. Custom")

    print("\n0. Skip")

    while True:
        choice = input("\nSelect: ").strip()

        if choice == "0":
            return None

        if choice.isdigit():
            number = int(choice)

            if 1 <= number <= len(options):
                return options[number - 1]

            if custom and number == len(options) + 1:
                return custom_text("Enter custom text (0 to skip): ")

        print("Invalid selection. Try again.")


def select_camera_settings():
    print("\nCAMERA SETTINGS")
    print("=" * 30)

    lens = choose(
        "Lens",
        CAMERA_OPTIONS["lens"],
        custom=False
    )

    shot_distance = choose(
        "Shot Distance",
        CAMERA_OPTIONS["shot_distance"],
        custom=False
    )

    depth_of_field = choose(
        "Depth of Field",
        CAMERA_OPTIONS["depth_of_field"],
        custom=False
    )

    focus = choose(
        "Focus",
        CAMERA_OPTIONS["focus"],
        custom=False
    )

    return create_camera_settings(
        lens=lens,
        shot_distance=shot_distance,
        depth_of_field=depth_of_field,
        focus=focus
    )


def select_subject(mode):
    subjects = {
        "realistic": [
            "Car",
            "Person",
            "Architecture",
            "Lifestyle",
            "Environment",
            "Custom"
        ],
        "anime": [
            "Character",
            "Portrait",
            "Environment",
            "Vehicle",
            "Custom"
        ]
    }

    selected = choose(
        f"{mode} mode",
        subjects[mode],
        custom=False
    )

    if selected is None:
        return None

    if selected == "Custom":
        subject = custom_text("Enter your subject (0 to skip): ")

        if subject is None:
            return None
    else:
        subject = selected

    result = {
        "mode": mode,
        "subject": subject,
        "brand": None,
        "model": None,
        "color": None,
        "material": None,
        "headlights": None,
        "framing": None,
        "camera_angle": None,
        "composition": None,
        "pose": None,
        "environment_category": None,
        "environment": None,
        "time_of_day": None,
        "lighting": None,
        "weather": None,
        "atmosphere": None,
        "visual_effects": None,
        "camera": None
    }

    if subject == "Architecture":
        result["kind"] = "architecture"
        categories = load_categories()

        structure = choose(
            "Architecture Structure",
            categories["architecture"]["structures"]
        )

        result["subject"] = structure

    if subject in ("Car", "Vehicle"):
        select_vehicle(result)

    if subject in ("Person", "Character", "Portrait"):
        result["framing"] = choose("Framing", [
            "Portrait", "Upper Body", "Full Body", "Close-up",
            "Side Profile", "Three-Quarter View", "Silhouette"
        ])

        result["camera_angle"] = choose("Camera Angle", [
            "Eye Level", "Low Angle", "High Angle",
            "Bird's Eye View", "Worm's Eye View",
            "Dutch Angle", "Over the Shoulder", "Side View"
        ])

        result["composition"] = choose("Composition", [
            "Center", "Left Third", "Right Third",
            "Upper Third", "Lower Third", "Foreground",
            "Background", "Rule of Thirds"
        ])

        result["pose"] = choose("Pose", [
            "Standing", "Sitting", "Walking", "Leaning",
            "Looking Over Shoulder", "Hands in Pockets",
            "Arms Crossed", "Dynamic Action",
            "Kneeling", "Running"
        ])

    select_scene_settings(result)
    result['camera'] = select_camera_settings() or None

    result["additional_elements"] = select_additional_elements(mode)
    result["visual_effects"] = select_visual_effects()

    return result


def select_vehicle(result):
    categories = load_categories()
    vehicles = categories["vehicles"]

    brands = [
        key for key, value in vehicles.items()
        if isinstance(value, list)
        and key not in ("colors", "materials", "headlights")
    ]

    brand_labels = {
        "rolls_royce": "Rolls-Royce",
        "porsche": "Porsche",
        "mercedes_amg": "Mercedes-AMG",
        "bmw": "BMW"
    }

    brand = choose(
        "Vehicle Brand",
        [brand_labels.get(b, b.capitalize()) for b in brands],
        False
    )

    if brand is None:
        return

    brand_key = next(
        b for b in brands
        if brand_labels.get(b, b.capitalize()).lower() == brand.lower()
    )

    result["brand"] = brand_key

    result["model"] = choose(
        f"{brand} Models",
        vehicles[brand_key],
        False
    )

    result["color"] = choose(
        "Vehicle Color",
        vehicles["colors"]
    )

    result["material"] = choose(
        "Vehicle Material",
        vehicles["materials"]
    )

    result["headlights"] = choose(
        "Headlights",
        vehicles["headlights"]
    )


def select_scene_settings(result):
    categories = load_categories()
    locations = categories["scene_locations"]

    group = choose(
        "Environment Type",
        list(locations.keys())
    )

    if group is not None:
        result["environment_category"] = group

        result["environment"] = choose(
            f"{group} Locations",
            locations[group]
        )

    settings = categories["scene_settings"]

    result["time_of_day"] = choose(
        "Time of Day",
        settings["time_of_day"]
    )

    result["lighting"] = choose(
        "Lighting",
        settings["lighting"]
    )

    result["weather"] = choose(
        "Weather",
        settings["weather"]
    )

    result["atmosphere"] = choose(
        "Atmosphere",
        settings["atmosphere"]
    )


def select_visual_effects():
    categories = load_categories()
    groups = categories["visual_effects"]
    options = []

    print("\nVISUAL EFFECTS")
    print("=" * 30)

    for group, effects in groups.items():
        print(f"\n{group.upper()}")

        for effect in effects:
            options.append(effect)
            print(f"{len(options)}. {effect}")

    selected = []

    print("\n0. Finish / Skip")

    while True:
        choice = input("\nSelect effect: ").strip()

        if choice == "0":
            return selected or None

        if choice.isdigit() and 1 <= int(choice) <= len(options):
            effect = options[int(choice) - 1]

            if effect not in selected:
                selected.append(effect)
                print(f"Added: {effect}")
            else:
                print("Already selected.")

            print("Selected:", ", ".join(selected))
        else:
            print("Invalid selection. Try again.")


def select_additional_elements(mode):
    categories = load_categories()
    selected = []

    element_types = [
        "Character",
        "Vehicle",
        "Architecture",
        "Lifestyle",
        "Environment",
        "Custom"
    ]

    print("\nADDITIONAL SCENE ELEMENTS")
    print("=" * 30)
    print("Add optional objects or subjects to your scene.")

    while True:
        element_type = choose(
            "Element Type - 0 to Finish",
            element_types,
            custom=False
        )

        if element_type is None:
            break

        item = {
            "subject": element_type,
            "kind": element_type.lower()
        }

        if element_type == "Character":
            options = categories["characters"].get(mode, [])
            value = choose("Character", options)

            if value is None:
                continue

            item["subject"] = value

        elif element_type == "Vehicle":
            select_vehicle(item)

            if item.get("brand") is None and item.get("model") is None:
                continue

        elif element_type == "Architecture":
            options = categories["architecture"].get("structures", [])
            value = choose("Architecture", options)

            if value is None:
                continue

            item["subject"] = value

        elif element_type == "Lifestyle":
            options = (
                categories["lifestyle"].get("locations", [])
                + categories["lifestyle"].get("accessories", [])
            )

            value = choose("Lifestyle Element", options)

            if value is None:
                continue

            item["subject"] = value

        elif element_type == "Environment":
            options = (
                categories["environments"].get("urban", [])
                + categories["environments"].get("nature", [])
            )

            value = choose("Environment Element", options)

            if value is None:
                continue

            item["subject"] = value

        elif element_type == "Custom":
            value = custom_text(
                "Describe the additional element (0 to skip): "
            )

            if value is None:
                continue

            item["subject"] = value

        selected.append(item)
        print(f"Added: {item['subject']}")

    return selected or None
