# About the Project

A 3D projekt with Panda3D and Python, ultimate goal is to find a configuration
of digits floating in space which build a number


## Installation

To simplify distribution this project relies on uv, so everything should work
out-of-the box if uv is installed on your system. This how the interactive viewer
is started:

```bash
uv run [FILE].py [ARGS]
```

This currently shows a random configuration of digits in space (stored in file 
`config.json`).

## Ideas

The first idea was to find a configuration of digits in space which blend into
the shape of different numbers when viewed from different angles.

To find such a configuration a
[gentic algorithm](https://en.wikipedia.org/wiki/Genetic_algorithm) is applied:
`uv run genetics.py`

The fitness function: view the scene from pre-defined angles and compare each
appearance to a desired target image.

The more similarities and the fewer differences, the better.

The overall fitness of a specific configuration is then the average over all
views.

One can view results produced by the genetic algorithm by providing the corresponding
`winner.[..].json` file as argument to `visualization.py`.

Sadly there are open problems:

- Digits build cluster close together, overlapping each other
- The fitness value stagates after time, and solutions found are visually not appealing
- To come up with means to circumvent clustering (so limiting the search space) will
   probably make the best solution even worse

So I came up with another idea (sadly the name of this repository no longer fits): the 
digits a illuminated with light beams so that the illuminated numbers combined reveal
the current time. 

As a light source I will use a beamer. Setting up the "clock" involves the following
steps:

- Hang the digits "randomly" into the beamer space - do not align them in one plane,
  since "image sharpness" does not matter
- Using `uv run calibrate.py` create a calibration by aligning that each digit in real
  space align with the corresponding image in the beamer image
- Then do `uv run clock.py` to start the real-time clock animation


## Ressources

- [Panda3D](https://panda3d.org/)
- [uv](https://docs.astral.sh/uv/)
- [Genetic Algorithm](https://en.wikipedia.org/wiki/Genetic_algorithm)

