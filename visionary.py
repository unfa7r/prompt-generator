from core.engine import load_settings, validate_settings
from core.wizard import select_subject, choose
from core.scene_graph import build_scene_graph
from core.renderer import render_prompt, render_json
from core.validator import validate_scene_graph


ASPECT_RATIOS = [
    "1:1",
    "4:3",
    "3:2",
    "16:9",
    "9:16",
    "4:5"
]


def show_menu():
    print("\n")
    print("=" * 36)
    print("          V I S I O N A R Y")
    print("=" * 36)
    print()
    print("  1. Realistic")
    print("  2. Anime")
    print()
    print("  0. Exit")
    print()
    print("=" * 36)


def show_output_menu():
    print("\nOUTPUT FORMAT")
    print("=" * 36)
    print("1. Text Prompt")
    print("2. JSON")
    print("3. Both")
    print("0. Cancel")


def select_aspect_ratio(default):
    print("\nASPECT RATIO")
    print("=" * 36)

    for index, ratio in enumerate(ASPECT_RATIOS, 1):
        print(f"{index}. {ratio}")

    print(f"\n0. Default ({default})")

    while True:
        choice = input("\nSelect aspect ratio: ").strip()

        if choice == "0":
            return default

        if choice.isdigit():
            number = int(choice)

            if 1 <= number <= len(ASPECT_RATIOS):
                return ASPECT_RATIOS[number - 1]

        print("Invalid selection. Try again.")


def display_output(scene):
    choice = None

    while choice not in ("0", "1", "2", "3"):
        show_output_menu()
        choice = input("\nSelect format: ").strip()

        if choice not in ("0", "1", "2", "3"):
            print("Invalid selection. Try again.")

    if choice == "0":
        return

    if choice in ("1", "3"):
        print("\n")
        print("=" * 50)
        print("              GENERATED PROMPT")
        print("=" * 50)
        print()
        print(render_prompt(scene))
        print("\n" + "=" * 50)

    if choice in ("2", "3"):
        print("\n")
        print("=" * 50)
        print("              GENERATED JSON")
        print("=" * 50)
        print()
        print(render_json(scene))
        print("\n" + "=" * 50)


def generate_scene(mode, settings):
    selection = select_subject(mode)

    if selection is None:
        print("\nScene creation cancelled.")
        return

    aspect_ratio = select_aspect_ratio(settings["aspect_ratio"])

    scene = build_scene_graph(
        selection,
        aspect_ratio=aspect_ratio
    )

    valid, errors = validate_scene_graph(scene)

    if not valid:
        print("\nSCENE VALIDATION FAILED")

        for error in errors:
            print(f"- {error}")

        return

    display_output(scene)


def show_settings(settings):
    print("\nSETTINGS")
    print("=" * 36)

    for key, value in settings.items():
        print(f"{key}: {value}")


def main():
    settings = validate_settings(load_settings())

    while True:
        show_menu()
        choice = input("Select an option: ").strip()

        if choice == "1":
            generate_scene("realistic", settings)
        elif choice == "2":
            generate_scene("anime", settings)
        elif choice == "0":
            print("\nVISIONARY closed.")
            break
        else:
            print("\\nInvalid selection. Try again.")


if __name__ == "__main__":
    main()
