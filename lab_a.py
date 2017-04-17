import random

import simpy


RANDOM_SEED = 42
NUM_BLOCKS = 2  # Number of machines in the carwash
MAX_TIME = 100      # Minutes it takes to clean a car
EVENT_INTERVAL = 7       # Create a car every ~7 minutes
SIM_TIME = 2 * NUM_BLOCKS * MAX_TIME     # Simulation time in minutes
READ_PROB = 0.75
MAX_WRITE_WAIT = 50


class Block(object):
    def __init__(self, env, max_time):
        self.env = env
        self.read_lock = simpy.Resource(env, float('inf'))
        self.write_lock = simpy.Resource(env, 1)
        self.max_time = max_time
        self.last_write_time = 0

    def access(self):
        access_time = random.randint(0, self.max_time)
        yield self.env.timeout(access_time)


def read(env, name, block):
    arrive = env.now
    print('%7.4f %s: Received' % (arrive, name))

    # Don't proceed if time from this block's last write is too long
    while env.now - block.last_write_time >= MAX_WRITE_WAIT:
        yield env.timeout(0.001)

    while block.write_lock.count is not 0:
        yield env.timeout(0.001)

    with block.read_lock.request() as request:

        yield request

        wait = env.now - arrive
        print('%7.4f %s: Waited %7.4f' % (env.now, name, wait))

        yield env.process(block.access())

        print('%7.4f %s: Finished' % (env.now, name))

def write(env, name, block):
    arrive = env.now
    print('%7.4f %s: Received' % (arrive, name))

    while block.read_lock.count is not 0:
        yield env.timeout(0.001)

    with block.read_lock.request() as request:

        yield request

        wait = env.now - arrive
        print('%7.4f %s: Waited %7.4f' % (env.now, name, wait))

        yield env.process(block.access())
        finished_time = env.now
        block.last_write_time = finished_time

        print('%7.4f %s: Finished' % (finished_time, name))


def setup(env, num_blocks, max_time, event_interval, read_prob):
    # Create the array of data blocks
    database = [ Block(env, max_time) for i in xrange(num_blocks) ]

    i = 0

    # Create more events while the simulation is running
    while True:
        # Randomly decide whether to read or write
        rand_event = random.random()
        rand_block = random.randint(0, num_blocks - 1)

        if (rand_event < read_prob):
          env.process(read(env, 'Read%d' % i, database[rand_block]))
        else:
          env.process(write(env, 'Write%d' % i, database[rand_block]))
        i += 1
        yield env.timeout(random.randint(event_interval - 2, event_interval + 2))


# Setup and start the simulation
print('Typical Reader and Writer')
random.seed(RANDOM_SEED)  # This helps reproducing the results

# Create an environment and start the setup process
env = simpy.Environment()
env.process(setup(env, NUM_BLOCKS, MAX_TIME, EVENT_INTERVAL, READ_PROB))

# Execute!
env.run(until=SIM_TIME)
