# Panda3D Project

A 3D projekt with Panda3D and Python, ultimate goal is to find a configuration
of digits floating in space which, when looked at from different angles itself
build numbers.


## Installation

To simplify distribution this project relies on uv, so everything should work
out-of-the box if uv is installed on your system. This how the interactive viewer
is started:

```bash
uv run visualization.py
```

This app currently shows a random configuration of digits in space (stored in file `config.json`).

The genetic algorithm, still not finished, lives in `genetics.py`.

## Todos

Ultimate goal is to find a configuration of digits in space which blend into
the shape of different numbers when viewed from different angles.

To find such a configuration the idea is to apply a
[gentic algorithm](https://en.wikipedia.org/wiki/Genetic_algorithm).

The next step would is to come up with a fitness function: view the scene from
pre-defined angles and compare each appearance to a (differnt) target image.

The more similarities and the fewer differences, the better.

The overall fitness of a specific configuration is then the average over all
views.

## Ressources

- [Panda3D](https://panda3d.org/)
- [uv](https://docs.astral.sh/uv/)
- [Gentic Algorithm](https://en.wikipedia.org/wiki/Genetic_algorithm)

