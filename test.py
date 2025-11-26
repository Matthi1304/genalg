import os
import sys
import json
import visualization
import genetics
import fitness


from panda3d.core import PNMImage
from panda3d.core import Texture


def load_settings_test():
    genetics.load_settings()


def flip_image_test():
    image = PNMImage()
    image.read("img/9.png")
    visualization.flip_image_and_exchange_black_with_white(image)
    image.write("tmp/9_flipped.png")


def _invert_image(image):
    black = PNMImage(image.getXSize(), image.getYSize(), 1)
    black.fill(0.0)
    white = PNMImage(image.getXSize(), image.getYSize(), 1)
    white.fill(1.0)
    
    # threshold(source: PNMImage, channel: int, threshold: float, lt: PNMImage, ge: PNMImage)
    # For each source pixel (x, y):
    # c = source.get_channel(x, y, channel). 
    # Set this image’s (x, y) to:
    #  if c <  threshold --> take from lt
    #  if c >= threshold --> take from ge
    inverted_image = PNMImage()
    inverted_image.copyFrom(image)
    inverted_image.threshold(image, 0, 0.9, white, black)
    return inverted_image


def invert_image_test():
    image = PNMImage("img/h_1.png")
    image = _invert_image(image)
    image.write("tmp/h_1_inverted.png")


def configuration_test(app):
    config = genetics.Individual.random_individual(100).genom
    app.set_configuration(config)
    
    json_str = json.dumps(config, indent=4, check_circular=False)
    with open("tmp/config.json", "w") as f:
        f.write(json_str)

    image = app.make_screenshot(0)
    image.write("tmp/screenshot_config_before.png")

    app.set_configuration([])
    image = app.make_screenshot(0)
    image.write("tmp/screenshot_config_cleared.png")

    app.set_configuration(config)
    image = app.make_screenshot(0)
    image.write("tmp/screenshot_config_restored.png")


def screenshot_test(app):
    config = genetics.Individual.random_individual(30).genom
    app.set_configuration(config)

    for hour in range(1):
        texture = app.make_screenshot(hour * 30)
        print("type", type(texture))
        print("component_width", texture.component_width)
        print("num_components", texture.num_components)
        print("num_pages", texture.num_pages)
        print("ram_image_size", texture.ram_image_size)
        image = PNMImage()
        image.read(f"img/h_{hour + 1}.png")
        texture.store(image)
        image.setNumChannels(1)
        image.write(f"tmp/digits_screenshot_{hour + 1}.png")


def fitness_calculation_test():
        positiveMask = fitness.MaskImage("img/h_1.png")
        negativeMask = positiveMask.invert_image()

        print("fitness for best possible match")
        print(f"positive: {positiveMask.get_score(PNMImage("img/h_1.png"))}")
        print(f"negative: {negativeMask.get_score(PNMImage("img/h_1.png"))}")

        print("fitness for worst possible match")
        print(f"positive: {positiveMask.get_score(_invert_image(PNMImage("img/h_1.png")))}")
        print(f"negative: {negativeMask.get_score(_invert_image(PNMImage("img/h_1.png")))}")


def fitness_test(app):
    fitness.DEBUG = True
    try:
        target_images = [f"img/h_{i}.png" for i in range(1, 13)]
        fitness_function = fitness.FitnessFunction(app, target_images)
        with open("winner.1764013618.json", "r") as f:
            config = json.load(f)
        print("Fitness:", fitness_function.fitness_function(config))
    finally:
        fitness.DEBUG = False


if __name__ == "__main__":
    cases = [k[: -5] for k in dir() if k.endswith("_test") and not k.startswith("_")]
    arguments = ", ".join(sorted([k for k in cases])).replace("'", " ")
    if len(sys.argv) == 1:
        print(f"Please provide an argument: {arguments}")
        sys.exit(1)
    if not sys.argv[1] in cases:
        print(f"Unknown argument. Please provide one of: {arguments}")
        sys.exit(1)
    os.makedirs("tmp", exist_ok=True)
    function = globals().get(sys.argv[1] + '_test')
    if function.__code__.co_argcount == 1:
        visualization.headless_app(callback=function)
    else:
        function()
