import random
import simpy


RANDOM_SEED = 42
NUM_BLOCKS = 10  # Number of machines in the carwash
MAX_TIME = 10      # Minutes it takes to clean a car
EVENT_INTERVAL = 3       # Create a car every ~7 minutes
SIM_TIME = 2 * NUM_BLOCKS * MAX_TIME     # Simulation time in minutes
READ_PROB = 0.75


class Block(object):
    next_id = 0

    def __init__(self, env, max_time):
        self.env = env
        self.max_time = max_time
        self.last_accessed = 0
        self.id = Block.next_id
        Block.next_id += 1

    def access(self):
        access_time = random.randint(0, self.max_time)
        yield self.env.timeout(access_time)


def read(env, name, block):
    arrive = env.now
    print('%4.1f %s: Block %d Received' % (arrive, name, block.id))
    yield env.process(block.access())
    block.last_accessed = env.now
    print('%4.1f %s: Block %d Finished' % (block.last_accessed, name, block.id))


def write(env, name, block):
    arrive = env.now
    print('%4.1f %s: Block %d (Last accessed: %4.1f) Received' % (arrive, name, block.id, block.last_accessed))

    while True:
        write_start = env.now
        if write_start > block.last_accessed:
            break
        print('%4.1f %s: Block %d Invalidated' % (write_start, name, block.id))
        env.timeout(1)

    print('%4.1f %s: Block %d Start' % (write_start, name, block.id))
 
    yield env.process(block.access())
    finished = env.now
    block.last_accessed = finished
    print('%4.1f %s: Block %d Finished' % (finished, name, block.id))


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
print('Invalid Dirty Write')
random.seed(RANDOM_SEED)  # This helps reproducing the results

# Create an environment and start the setup process
env = simpy.Environment()
env.process(setup(env, NUM_BLOCKS, MAX_TIME, EVENT_INTERVAL, READ_PROB))

# Execute!
env.run(until=SIM_TIME)
