import random
import simpy


RANDOM_SEED = 42
NUM_BLOCKS = 10  # Number of machines in the carwash
MAX_TIME = 10      # Minutes it takes to clean a car
EVENT_INTERVAL = 3       # Create a car every ~7 minutes
SIM_TIME = 2 * NUM_BLOCKS * MAX_TIME     # Simulation time in minutes
READ_PROB = 0.75
DEBUG = False
NUM_INVALID_WRITES = 0.0
NUM_WRITE_EVENTS = 0.0


class Block(object):
    next_id = 0

    def __init__(self, env, max_time):
        self.env = env
        self.max_time = max_time
        self.last_write = 0
        self.last_read = 0
        self.id = Block.next_id
        Block.next_id += 1

    def access(self):
        access_time = random.randint(0, self.max_time)
        yield self.env.timeout(access_time)


def read(env, name, block):
    arrive = env.now
    if DEBUG:
        print('%4.1f %s: Block %d Received' % (arrive, name, block.id))
    yield env.process(block.access())
    finished = env.now
    block.last_read = finished
    if DEBUG:
        print('%4.1f %s: Block %d Finished' % (finished, name, block.id))


def write(env, name, block):
    arrive = env.now
    global NUM_WRITE_EVENTS
    global NUM_INVALID_WRITES
    NUM_WRITE_EVENTS += 1
    if DEBUG:
        print('%4.1f %s: Block %d Received' % (arrive, name, block.id))

    while True:
        write_start = env.now
        yield env.process(block.access())
        if block.last_write < write_start or block.last_read < write_start:
            break
        if DEBUG:
            print('%4.1f %s: Block %d Invalidated (last write = %4.1f)'
                % (write_start, name, block.id, block.last_write))
            NUM_INVALID_WRITES += 1
        env.timeout(1)

    finished = env.now
    block.last_write = finished
    if DEBUG:
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
DEBUG = True

# Create an environment and start the setup process
env = simpy.Environment()
env.process(setup(env, NUM_BLOCKS, MAX_TIME, EVENT_INTERVAL, READ_PROB))

# Execute!
env.run(until=SIM_TIME)

if NUM_WRITE_EVENTS > 0:
	print("Total Number Writes: %d" % NUM_WRITE_EVENTS)
	print("Number Invalid Writes: %d" % NUM_INVALID_WRITES)
	percent = (NUM_INVALID_WRITES / NUM_WRITE_EVENTS) * 100.0
	print("Invalid Writes: %4.2f%%" % percent)
