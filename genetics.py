from random import random, randint, sample
import os
import json
import sys
from time import time
import visualization
from fitness import FitnessFunction
from dotenv import load_dotenv
from random import random, randint

RADIUS = 15000.0

MAX_SCALE = 6000
MIN_SCALE =  500

DEFAULT_NUM_CHROMOSOMS = 100
DEFAULT_SIZE_OF_GENERATION = 50
DEFAULT_SURVIVOR_RATE = 0.3
DEFAULT_MUTATION_RATE = 0.1
DEFAULT_TOURNAMENT_SIZE = 100


class Individual:

    def __init__(self, genom):
        self.genom = genom
        self.fitness = None
    

    def getFitness(self, fitness_function=None):
        if self.fitness is None:
            if fitness_function is None:
                raise ValueError("Fitness function must be provided for first fitness evaluation.")
            self.fitness = fitness_function(self.genom)
        return self.fitness


    def mutate(self):
        # We can mutate by replacing one gene with a new random one, 
        # or by mutate an individual gene.
        # A gene has six parameters: [digit, x, y, z, size, heading_degrees].
        # Each parameter should should mutate with equal probability.
        # A mutation should be small, e.g. position +/- 1000, size +/- 100, heading +/- 10 degrees.
        # Make sure to keep parameters within valid ranges
        index = randint(0, len(self.genom) - 1)
        choice = random()
        if choice < 0.2:
            # Replace a chromosom
            self.genom[index] = create_random_gene()
        else:
            # Mutate a parameter
            # [digit, x, y, z, size, heading_degrees]
            pos = randint(0, 5)
            gene = self.genom[index]
            if pos == 0:
                gene[0] = randint(0, 9)
            elif pos in [1, 2, 3]:
                # todo: we could do a better job here to ensure we stay within the sphere
                gene[pos] += randint(-1000, 1000)
                gene[pos] = max(-RADIUS, min(RADIUS, gene[pos]))
            elif pos == 4:
                gene[4] += randint(-100, 100)
                gene[4] = max(MIN_SCALE, min(MAX_SCALE, gene[4]))
            elif pos == 5:
                gene[5] += randint(-10, 10)
                gene[5] = gene[5] % 360


class Genetics:

    def __init__(self, 
                 size_of_genom=DEFAULT_NUM_CHROMOSOMS, 
                 size_of_generation=DEFAULT_SIZE_OF_GENERATION,
                 survivor_rate=DEFAULT_SURVIVOR_RATE, 
                 mutation_rate=DEFAULT_MUTATION_RATE,
                 tournament_size=DEFAULT_TOURNAMENT_SIZE):
        self.size_of_genom = size_of_genom
        self.size_of_generation = size_of_generation
        self.survivor_rate = survivor_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.winner = None


    def run(self, app):
        fitness_function = FitnessFunction(app).fitness_function
        population = self.create_random_population(self.size_of_generation)
        print("=============================================================")
        print("starting genetic algorithm...")
        print("=============================================================")
        worst_survivor_fitness = 0.0
        stagnation_count = 0
        for generation in range(self.tournament_size + 1):
            start_time = time()
            population.sort(key=lambda x: x.getFitness(fitness_function=fitness_function), reverse=True)
            num_survivors = int(self.size_of_generation * self.survivor_rate)
            survivors = population[:num_survivors]
            self.winner = survivors[0].genom # store the best individuals genom
            if generation % 25 == 0:
                print( "=============================================================")
                print("                best     worst   average   average")
                print("         #  survivor  survivor survivors       all  duration")
                #      ----+----|----+----|----+----|----+----|----+----|----+----|
            print(f"{generation:10d}"+
                  f"{survivors[0].getFitness():10.5f}"+
                  f"{survivors[-1].getFitness():10.5f}"+
                  f"{sum(ind.getFitness() for ind in survivors) / len(survivors):10.5f}"+
                  f"{sum(ind.getFitness() for ind in population) / len(population):10.5f}"+
                  f"{time() - start_time:10.3f}")
            if generation == self.tournament_size:
                # final generation, do not breed further
                return
            new_breed = []  
            if worst_survivor_fitness == survivors[-1].getFitness():
                stagnation_count += 1
                if stagnation_count >= 4:
                    print("Warn: Stagnation detected, killing half of the survivors, adding new geenoms to the pool.")
                    survivors = survivors[:len(survivors)//2]
                    new_breed = self.create_random_population(num_survivors - len(survivors))
            else:
                worst_survivor_fitness = survivors[-1].getFitness()
                stagnation_count = 0
            # Breeding
            while len(new_breed) + num_survivors < self.size_of_generation:
                child = self.crossover(sample(survivors, 3))
                new_breed.append(child)
            # Mutation
            for m in range(int(len(new_breed) * self.mutation_rate)):
                individual = new_breed[randint(0,  len(new_breed) - 1)]
                individual.mutate()
            # Elitism: carry over the best individuals
            population = survivors + new_breed


    def crossover(self, parents):
        # We can do a N-way crossover by taking similar amount of genes from each parent.
        # For example, if we have 100 genes, we can take 33 to 34 genes for N=3 parents.
        # Note that number of genes per genome may not be exactly divisible by N.
        # We should randomly select which genes to take from each parent.
        # Make sure the resulting child has the same number genes as it's parents.
        # We assume all parents have the same number of genes.
        childGenom = []
        count = int(len(parents[0].genom) / len(parents))
        while parents: 
            parent = parents.pop(0)
            number_of_genes = count if parents else len(parent.genom) - len(childGenom)
            childGenom += sample(parent.genom, number_of_genes)
        return Individual(childGenom)


    def create_random_population(self, count):
        population = []
        for _ in range(count):
            genome = self.generate_random_genome()
            population.append(Individual(genome))
        return population


    def generate_random_genome(self):
        genome = []
        for _ in range(self.size_of_genom):
            gene = create_random_gene()
            genome.append(gene)
        return genome


def create_random_gene():
    # [digit, x, y, z, size, heading_degrees]
    return [randint(0, 9)] + _random_point_in_sphere(RADIUS) + [randint(MIN_SCALE, MAX_SCALE), randint(0, 359)]


def _random_point_in_sphere(radius):
    while True:
        x = random() * 2 - 1
        y = random() * 2 - 1
        z = random() * 2 - 1
        if x*x + y*y + z*z <= 1:
            return [int(x * radius), int(y * radius), int(z * radius)]


def _get_from_env(var_name, default, cast_type):
    value = os.getenv(var_name)
    if value is None:
        print(f"Info: Using {var_name}={default} (default)")
    else:
        try:
            value = cast_type(value)
            print(f"Info: Using {var_name}={value} (.env / environment)")
            return value
        except ValueError:
            print(f"Warning: Could not cast environment variable {var_name}='{value}' to {cast_type}. Using default {default}.")
    return default




if __name__ == "__main__":
    start_time = time()
    print("=============================================================")
    print("Info: Starting genetic algorithm... (cancel with Ctrl-C)")
    print("=============================================================")
    load_dotenv()
    SIZE_OF_GENOM = _get_from_env("SIZE_OF_GENOM", 100, int)
    SIZE_OF_GENERATION = _get_from_env("SIZE_OF_GENERATION", 50, int)
    SURVIVOR_RATE = _get_from_env("SURVIVOR_RATE", 0.3, float)
    MUTATION_RATE = _get_from_env("MUTATION_RATE", 0.1, float)
    TOURNAMENT_SIZE = _get_from_env("TOURNAMENT_SIZE", 100, int)
    print("=============================================================")
    genetics = Genetics(
        size_of_genom=SIZE_OF_GENOM,
        size_of_generation=SIZE_OF_GENERATION,
        survivor_rate=SURVIVOR_RATE,
        mutation_rate=MUTATION_RATE,
        tournament_size=TOURNAMENT_SIZE
    )
    try:
        visualization.headless_app(callback=genetics.run, prc_file="headless_128x128.prc")
    except KeyboardInterrupt:
        print("Info: Interrupted by user.")
    json_str = json.dumps(genetics.winner, indent=4, check_circular=False)
    filename = "winner.%d.json" % int(time())
    with open(filename, "w") as f:
        f.write(json_str)
    print("=============================================================")
    print(f"Info: SIZE_OF_GENOM        {SIZE_OF_GENOM}")
    print(f"Info: SIZE_OF_GENERATION   {SIZE_OF_GENERATION}")
    print(f"Info: SURVIVOR_RATE        {SURVIVOR_RATE}")
    print(f"Info: MUTATION_RATE        {MUTATION_RATE}")
    print(f"Info: TOURNAMENT_SIZE      {TOURNAMENT_SIZE}")
    print("=============================================================")
    print(f"Info: Total time elapsed   {time() - start_time:.3f} seconds")
    print(f"Info: Winner configuration saved to {filename}")
    print("=============================================================")
