import os
import sys
import json
import visualization
import genetics
import fitness


from panda3d.core import PNMImage
from panda3d.core import Texture


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

def image_test():
    print("black = 0.0")
    print("white = 1.0")
    image_1 = PNMImage()
    image_1.read("img/h_1.png")
    image_1.setNumChannels(1)
    target = 1 - image_1.getAverageGray() 

    image_1i = PNMImage()
    image_1i.read("img/h_1i.png")
    image_1i.setNumChannels(1)
    inverted_target = 1 - image_1i.getAverageGray()

    image_bw = PNMImage()
    image_bw.read("tmp/bw.png")
    image_bw.setNumChannels(1)

    image_bw.threshold(image_bw, 0, 0.9, image_1, image_bw)
    # image_bw.write("tmp/a_good_pixels.png")
    match = 1 - image_bw.getAverageGray()

    image_bw.read("tmp/bw.png")
    image_bw.setNumChannels(1)

    image_bw.threshold(image_bw, 0, 0.9, image_1i, image_bw)
    # image_bw.write("tmp/b_bad_pixels.png")
    mismatch = 1 - image_bw.getAverageGray()

    matchPercent = 1 - (target - match) / target

    print(f"target level:     {target:.3f}")
    print(f"match level:      {match:.3f}")
    print(f"matchPercent:     {matchPercent:.3f}")
   
    mismatchPercent = (inverted_target - mismatch) / inverted_target

    print()
    print(f"inverted level:   {inverted_target:.3f}")
    print(f"mismatch level:   {mismatch:.3f}")
    print(f"mismatchPercent:  {mismatchPercent:.3f}")

    score = matchPercent - mismatchPercent
    print()
    print(f"score:            {score:.3f}")


def configuration_test(app):
    config = genetics.Genetics().random_individual(100).genom
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

    print(f"configuration same? {app.get_configuration() == config}")


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
    target_images = [f"img/h_{i}.png" for i in range(1, 13)]
    g = genetics.Genetics(
        size_of_genom=1000,
        size_of_generation=1,
        tournament_size=1,
        survivor_rate=1.0,
        target_images=target_images)
    g.run(app)


if __name__ == "__main__":
    cases = {
        "invert-image": [invert_image_test, False],
        "flip-image": [flip_image_test, False],
        "image": [image_test, False], 
        "screenshot": [screenshot_test, True], 
        "configuration": [configuration_test, True], 
        "fitness": [fitness_test, True],
        "fitness-calculation": [fitness_calculation_test, False]
    }
    arguments = ", ".join(sorted([k for k in cases.keys()])).replace("'", " ")
    if len(sys.argv) == 1:
        print(f"Please provide an argument: {arguments}")
        sys.exit(1)
    if not sys.argv[1] in cases:
        print(f"Unknown argument. Please provide one of: {arguments}")
        sys.exit(1)
    os.makedirs("tmp", exist_ok=True)
    c = cases.get(sys.argv[1])
    if c[1]:
        visualization.headless_app(callback=c[0])
    else:
        c[0]()
