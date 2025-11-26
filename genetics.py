from random import random, randint, sample
import os
import json
import sys
from time import time
from math import sqrt, sin, cos, pi
import visualization
from fitness import FitnessFunction
from dotenv import load_dotenv
from random import random, randint

# parameters for the genetic algorithm (genetics.py) 
#
# number of genes per individual (number of placed digits in the configuration)
SIZE_OF_GENOM=220

# number of individuals per generation competing
SIZE_OF_GENERATION=400

# rate of best individuals surviving and being parents for the next generation
SURVIVOR_RATE=0.8

# rate of individuals being mutated per generation (only applies to new offsprings)
MUTATION_RATE=0.7

# maximum number of parents for crossover. must be >= 2
MAX_PARENTS = 3

# maximumnumber of generations
TOURNAMENT_SIZE=5000

# path for fitness images
FITNESS_IMAGE_PATH="img/"

# images to compare against for fitness evaluation
FITNESS_IMAGES="h_1.png,h_2.png,h_3.png,h_4.png,h_5.png,h_6.png,h_7.png,h_8.png,h_9.png,h_10.png,h_11.png,h_12.png"

# camera distance from the center of the sphere
CAMERA_DISTANCE = -60

# level of quantization for position (x,y,z)
QUANTIZATION = 100

# radius of the sphere for placement of digits
RADIUS = 15000

# scale limits for the digits
# in real life this should be at least 40 mm
MIN_SCALE =  600 
MAX_SCALE = 6000

# prefer less visual noise around image
FITNESS_FUNCTION_FACTOR = 1.1

Q = RADIUS // QUANTIZATION # the following condition should hold: Q * QUANTIZATION == RADIUS 

class Individual:

    def __init__(self, genom):
        self.genom = genom
        self.fitness = None


    def _random_point():
        # Blender (and Panda3d) uses a right-angled “Cartesian” coordinate system with the Z axis pointing upwards.
        # X axis - Left / Right
        # Y axis - Front / Back
        # Z axis - Top / Bottom
        while True:
            x = random() * 2 - 1
            y = random() * 2 - 1
            z = random() * 2 - 1
            if x*x + y*y + z*z <= 1:
                return (int(x * Q) * QUANTIZATION, int(y * Q) * QUANTIZATION, int(z * Q) * QUANTIZATION)


    def create_random_gene():
        # [digit, x, y, z, size, heading_degrees]
        x, y, z = Individual._random_point()
        return [randint(0, 9), x, y, z, randint(MIN_SCALE, MAX_SCALE), randint(0, 359)]


    @staticmethod
    def random_individual(size_of_genom):
        genom = [Individual.create_random_gene() for _ in range(size_of_genom)]
        genom.sort(key=lambda gene: (gene[1], gene[2]))  # sort by x, y
        return Individual(genom)
    

    @staticmethod
    def breed(parents):
        # We can do a N-way crossover by taking similar amount of genes from each parent.
        # For example, if we have 100 genes, we can take 33 to 34 genes for N=3 parents.
        # Note that number of genes per genome may not be exactly divisible by N.
        # We should randomly select which genes to take from each parent.
        # Make sure the resulting child has the same number genes as it's parents.
        # We assume all parents have the same number of genes.
        childGenom = []
        genes_per_parent = int(len(parents[0].genom) / len(parents))
        while parents: 
            parent = parents.pop(0)
            number_of_genes = genes_per_parent if parents else len(parent.genom) - len(childGenom)
            childGenom += sample(parent.genom, number_of_genes)
        return Individual(childGenom)


    def getFitness(self, fitness_function=None):
        if self.fitness is None:
            if fitness_function is None:
                raise ValueError("Fitness function must be provided for fitness evaluation.")
            self.fitness = fitness_function(self.genom)
        return self.fitness


    def mutate(self, count=1):
        # We can mutate by replacing one gene with a new random one, 
        # or by mutate an individual gene.
        # A gene has six parameters: [digit, x, y, z, size, heading_degrees].
        # Each parameter should should mutate with equal probability.
        # A mutation should be small, e.g. position +/- 1000, size +/- 100, heading +/- 20 degrees.
        # Make sure to keep parameters within valid ranges
        self.fitness = None  # reset cached fitness
        for _ in range(count):
            index = randint(0, len(self.genom) - 1)
            choice = random()
            if choice < 0.1:
                # Replace a chromosom
                self.genom[index] = Individual.create_random_gene()
            else:
                # Mutate a parameter
                # [0: digit, 1: x, 2: y, 3: z, 4: size, 5: heading_degrees]
                pos = randint(0, 5)
                gene = self.genom[index]
                if pos == 0:
                    gene[0] = randint(0, 9)
                elif pos in [1, 2, 3]:
                    # todo: we could do a better job here to ensure we stay within the target space
                    gene[pos] += randint(-1000, 1000)
                    gene[pos] = max(-RADIUS, min(RADIUS, gene[pos]))
                elif pos == 4:
                    gene[4] += randint(-100, 100)
                    gene[4] = max(MIN_SCALE, min(MAX_SCALE, gene[4]))
                elif pos == 5:
                    gene[5] += randint(-20, 20)
                    gene[5] = gene[5] % 360
        return self
    
    
    def copy(self):
        return Individual(self.genom.copy())


    def __len__(self):
        return len(self.genom)
    

    def __str__(self):
        return f'Individual(fitness={self.fitness}, len={len(self.genom)})'


class Genetics:

    def __init__(self, target_images):
        self.mutation_rate = MUTATION_RATE
        self.target_images = target_images
        self.winner = None


    def run(self, app):
        app.set_camera_distance(CAMERA_DISTANCE)
        fitness_function = FitnessFunction(app, self.target_images, FITNESS_FUNCTION_FACTOR).fitness_function
        population = self.create_random_population(SIZE_OF_GENERATION)
        self.winner = population[0].genom
        print("=============================================================")
        print("starting genetic algorithm...")
        print("=============================================================")
        worst_survivor_fitness = -1000.0
        stagnation_count = 0
        self.generation = -1
        while True:
            self.generation += 1
            start_time = time()
            population.sort(key=lambda x: x.getFitness(fitness_function=fitness_function), reverse=True)
            self.winner = population[0].genom # store the best individuals genom
            num_survivors = int(SIZE_OF_GENERATION * SURVIVOR_RATE)
            survivors = population[:num_survivors]
            self.log_stats(population, start_time, survivors)
            population = []
            if self.generation >= TOURNAMENT_SIZE:
                # final generation, do not breed further
                return
            if worst_survivor_fitness == survivors[-1].getFitness():
                stagnation_count += 1
                self.mutation_rate = self.mutation_rate * 1.05
                if stagnation_count == 1:
                    # alternative breed starts from scratch
                    print(f"Warn: Stagnation ({stagnation_count}) detected, develop new breed to mix in")
                    survivors += self.alternative_breed(
                        fitness_function, survivors[0].getFitness())
                elif stagnation_count <= 3:
                    # seed alternative breed
                    print(f"Warn: Stagnation ({stagnation_count}) detected, develop new breed to mix in")
                    l = len(survivors) - 1
                    survivors += self.alternative_breed(
                        fitness_function, survivors[0].getFitness(), population=sample(survivors[1:], l // 2))
                elif stagnation_count >= 10:
                    print(f"Warn: Termininating after #{stagnation_count} stagnations")
                    return
            else:
                worst_survivor_fitness = survivors[-1].getFitness()
            # Breeding
            while len(population) + len(survivors) < SIZE_OF_GENERATION:
                child = Individual.breed(sample(survivors, MAX_PARENTS))
                population.append(child)
            # Mutation
            for _ in range(int(len(population) * self.mutation_rate)):
                individual = population[randint(0,  len(population) - 1)]
                individual.mutate()
            # Elitism: carry over the best individuals
            population += survivors


    def alternative_breed(self, fitness_function, target_fitness, population=[]):
        # additional breeding to reach target fitness
        population += self.create_random_population(SIZE_OF_GENERATION - len(population))
        last_worst_fitness = -1000.0
        while True:
            self.generation += 1
            start_time = time()
            population.sort(key=lambda x: x.getFitness(fitness_function=fitness_function), reverse=True)
            num_survivors = int(SIZE_OF_GENERATION * SURVIVOR_RATE)
            survivors = population[:num_survivors]
            self.log_stats(population, start_time, survivors)
            winner = survivors[0]
            worst_survivor = survivors[-1]
            population = []  
            if (self.generation >= TOURNAMENT_SIZE) or (winner.getFitness() >= target_fitness) or (last_worst_fitness == worst_survivor.getFitness()):
                # do not breed further
                print("Info: Ending alternative breeding phase.")
                return survivors
            last_worst_fitness = survivors[-1].getFitness()
            # Breeding
            while len(population) + len(survivors) < SIZE_OF_GENERATION:
                child = Individual.breed(sample(survivors, MAX_PARENTS))
                population.append(child)
            # Mutation
            for _ in range(int(len(population) * self.mutation_rate)):
                individual = population[randint(0,  len(population) - 1)]
                individual.mutate()
            # Elitism: carry over the best individuals
            population += survivors


    def log_stats(self, population, start_time, survivors):
        if self.generation % 25 == 0:
            print( "=============================================================")
            print("           best     worst   average   average")
            print("    #  survivor  survivor survivors       all  duration")
            #      ----+----|----+----|----+----|----+----|----+----|----+----|
        print(f"{self.generation:5d}"+
                  f"{survivors[0].getFitness():10.5f}"+
                  f"{survivors[-1].getFitness():10.5f}"+
                  f"{sum(ind.getFitness() for ind in survivors) / len(survivors):10.5f}"+
                  f"{sum(ind.getFitness() for ind in population) / len(population):10.5f}"+
                  f"{time() - start_time:10.3f}")


    def create_random_population(self, count):
        population = []
        for _ in range(count):
            population.append(Individual.random_individual(SIZE_OF_GENOM))
        return population


def _get_from_env(var_name, default, cast_type):
    value = os.getenv(var_name)
    if value is None:
        value = default
    try:
        value = cast_type(value)
        print(f"Info: Using {var_name}={value}{'' if value != default else ' (default)'}")
        return value
    except ValueError:
        print(f"Warning: Could not cast environment variable {var_name}='{value}' to {cast_type}. Using default {default}.")
    return default


def load_settings():
    load_dotenv()
    global SIZE_OF_GENOM, SIZE_OF_GENERATION, SURVIVOR_RATE, MUTATION_RATE
    global TOURNAMENT_SIZE, FITNESS_IMAGE_PATH, FITNESS_IMAGES
    global CAMERA_DISTANCE, QUANTIZATION, RADIUS, MIN_SCALE, MAX_SCALE
    global FITNESS_FUNCTION_FACTOR, Q
    SIZE_OF_GENOM = _get_from_env("SIZE_OF_GENOM", SIZE_OF_GENOM, int)
    SIZE_OF_GENERATION = _get_from_env("SIZE_OF_GENERATION", SIZE_OF_GENERATION, int)
    SURVIVOR_RATE = _get_from_env("SURVIVOR_RATE", SURVIVOR_RATE, float)
    MUTATION_RATE = _get_from_env("MUTATION_RATE", MUTATION_RATE, float)
    TOURNAMENT_SIZE = _get_from_env("TOURNAMENT_SIZE", TOURNAMENT_SIZE, int)
    FITNESS_IMAGE_PATH = _get_from_env("FITNESS_IMAGE_PATH", FITNESS_IMAGE_PATH, str)
    FITNESS_IMAGES = _get_from_env("FITNESS_IMAGES", FITNESS_IMAGES, str)
    CAMERA_DISTANCE = _get_from_env("CAMERA_DISTANCE", CAMERA_DISTANCE, int)
    QUANTIZATION = _get_from_env("QUANTIZATION", QUANTIZATION, int)
    RADIUS = _get_from_env("RADIUS", RADIUS, int)
    MIN_SCALE = _get_from_env("MIN_SCALE", MIN_SCALE, int)
    MAX_SCALE = _get_from_env("MAX_SCALE", MAX_SCALE, int)
    FITNESS_FUNCTION_FACTOR = _get_from_env("FITNESS_FUNCTION_FACTOR", FITNESS_FUNCTION_FACTOR, float)
    Q = RADIUS // QUANTIZATION


if __name__ == "__main__":
    start_time = time()
    print("=============================================================")
    print("Info: Starting genetic algorithm... (cancel with Ctrl-C)")
    print("=============================================================")
    load_settings()
    print("=============================================================")
    assert len(FITNESS_IMAGES) > 0, "Error: No FITNESS_IMAGES specified in .env file."
    target_images = [FITNESS_IMAGE_PATH + img for img in FITNESS_IMAGES.split(",")]
    for img in target_images:
        assert os.path.isfile(img), f"Error: Target image file '{img}' does not exist."
    genetics = Genetics(target_images)
    try:
        visualization.headless_app(callback=genetics.run, prc_file="headless_128x128.prc")
    except KeyboardInterrupt:
        print("Info: Interrupted by user.")
    json_str = json.dumps(genetics.winner, indent=4, check_circular=False)
    filename = "winner.%d.json" % int(time()) if len(sys.argv) < 2 else sys.argv[1]
    with open(filename, "w") as f:
        f.write(json_str)
    print("=============================================================")
    print(f"Info: Total time elapsed   {time() - start_time:.3f} seconds")
    print(f"Info: Winner configuration saved to {filename}")
    print("=============================================================")
