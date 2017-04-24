import random
import simpy
import time
import argparse

parser = argparse.ArgumentParser(description='Tool to simulate invalid dirty writes.')
parser.add_argument('-b', '--blocks', help='Number of data blocks', required=False, default=10)
parser.add_argument('-r', '--runs', help='Number of runs', required=False, default=1)
parser.add_argument('-d', '--debug', help='Enable debug mode', action="store_true", required=False, default=False,)
parser.parse_args()
args = parser.parse_args()

RANDOM_SEED = int(round(time.time()))
NUM_RUNS = int(args.runs)			 	 # Number of times to run the simulation
NUM_BLOCKS = int(args.blocks) 			 # Number of data blocks
MAX_TIME = 10      						 # Max read or write time
EVENT_INTERVAL = 3      				 # Frequency of data block accesses
SIM_TIME = 2 * NUM_BLOCKS * MAX_TIME     # Simulation time in minutes
READ_PROB = 0.75						 # Probability that event ia a read
DEBUG = args.debug							 # Flag to indicate whether to print DEBUG statements
TOTAL_NUM_INVALID_WRITES = 0.0			 # Number of invalid writes during a sim run
TOTAL_NUM_WRITE_EVENTS = 0.0			 # Total number of write events during a sim run
PERCENT_SUM = 0.0						 # Sum of invalid write percents for each run
NUM_INVALID_NUM_WRITES_PER_RUN = 0.0     # Number of invalid writes for an individual run
NUM_WRITES_PER_RUN = 0.0				 # Number of writes for an individual run


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
    global TOTAL_NUM_WRITE_EVENTS
    global TOTAL_NUM_INVALID_WRITES
    global NUM_WRITES_PER_RUN
    global NUM_INVALID_NUM_WRITES_PER_RUN
    TOTAL_NUM_WRITE_EVENTS += 1
    NUM_WRITES_PER_RUN += 1
    if DEBUG:
        print('%4.1f %s: Block %d Received' % (arrive, name, block.id))

    while True:
        write_start = env.now
        yield env.process(block.access())
        if block.last_write < write_start or block.last_read < write_start:
            break
        else:
        	NUM_INVALID_NUM_WRITES_PER_RUN += 1
        	TOTAL_NUM_INVALID_WRITES += 1
	        if DEBUG:
	            print('%4.1f %s: Block %d Invalidated (last write = %4.1f)'
	                % (write_start, name, block.id, block.last_write))
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


# Setup and start the simulations
print('Invalid Dirty Write')
print("Num Runs= %d" % NUM_RUNS)
print("Num Data Blocks= %d" % NUM_BLOCKS)
print("Max Read/Write Time= %d" % MAX_TIME)
print("Event Interval= %d" % EVENT_INTERVAL)
print("Sim Time= %d" % SIM_TIME)
print("Read Probablity= %4.2f" % READ_PROB) 
print("Debug On= %s" % DEBUG) 
for x in range(1, NUM_RUNS+1):
	print("Processing Run %d/%d..." % (x, NUM_RUNS))
	RANDOM_SEED = int(round(time.time())) + x
	print("Random Seed= %d" % RANDOM_SEED)
	random.seed(RANDOM_SEED)  # This helps reproducing the results

	# Create an environment and start the setup process
	env = simpy.Environment()
	env.process(setup(env, NUM_BLOCKS, MAX_TIME, EVENT_INTERVAL, READ_PROB))

	# Execute!
	env.run(until=SIM_TIME)

	# Keep track of the invalid write percent for this run
	if NUM_WRITES_PER_RUN > 0:
		percent = (NUM_INVALID_NUM_WRITES_PER_RUN / NUM_WRITES_PER_RUN) * 100.0
		PERCENT_SUM += percent

	# Reset the per run variables
	NUM_INVALID_NUM_WRITES_PER_RUN = 0.0
	NUM_WRITES_PER_RUN = 0.0

	time.sleep(.001)

print("\nSummary")
print("Number of Runs: %d" % NUM_RUNS)
if TOTAL_NUM_WRITE_EVENTS > 0:
	print("Total Number Writes: %d" % TOTAL_NUM_WRITE_EVENTS)
	percent = (TOTAL_NUM_INVALID_WRITES / TOTAL_NUM_WRITE_EVENTS) * 100.0
	print("Total Number Invalid Writes: %d ( %4.2f%%)" % (TOTAL_NUM_INVALID_WRITES, percent))
print("Average Percent: %4.2f%%" % (PERCENT_SUM / NUM_RUNS))