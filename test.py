import sys
import json
import visualization
import genetics


def configuration_test(app):
    config = genetics.Genetics().create_random_individual()
    app.set_configuration(config)
    
    json_str = json.dumps(config, indent=4, check_circular=False)
    with open("tmp/config.json", "w") as f:
        f.write(json_str)

    image = app.make_screenshot(hour=0)
    image.write("tmp/screenshot_config_before.png")

    app.set_configuration([])
    image = app.make_screenshot(hour=0)
    image.write("tmp/screenshot_config_cleared.png")

    app.set_configuration(config)
    image = app.make_screenshot(hour=0)
    image.write("tmp/screenshot_config_restored.png")

    print(f"configuration same? {app.get_configuration() == config}")


def screenshot_test(app):
    config = genetics.Genetics().create_random_individual()
    app.set_configuration(config)

    for hour in range(1):
        image = app.make_screenshot(hour=hour)
        print("type", type(image))
        print("component_width", image.component_width)
        print("num_components", image.num_components)
        print("num_pages", image.num_pages)
        print("ram_image_size", image.ram_image_size)
        image.write(f"tmp/digits_screenshot_{hour}.png")

def fitness_test(app):
    g = genetics.Genetics(num_chromosoms=3, size_of_generation=10, tournament_size=2)
    g.create_random_individual() # todo: test something more meaningful
    a = [genetics.create_random_chromosom() for _ in range(3)]
    b = [genetics.create_random_chromosom() for _ in range(3)]
    c = [genetics.create_random_chromosom() for _ in range(3)]
    child = g.crossover([a, b, c])
    print(f"Parent A: {a}")
    print(f"Parent B: {b}")
    print(f"Parent C: {c}")
    print(f"Child:    {child}")
    g.mutate(child)
    print(f"Mutated:  {child}")
    child = g.crossover([a, b])
    print(f"Child 2:  {child}")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Please provide an argument: 'screenshot' or 'configuration'")
        sys.exit(1)
    if sys.argv[1] == "screenshot":
        visualization.headless_app(callback=screenshot_test)
    elif sys.argv[1] == "configuration":
        visualization.headless_app(callback=configuration_test)
    elif sys.argv[1] == "fitness":
        visualization.headless_app(callback=fitness_test)
    else:
        print("Unknown argument. Please use 'screenshot' or 'configuration'")
        sys.exit(1)