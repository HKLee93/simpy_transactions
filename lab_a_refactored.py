import random
import simpy
import time

RANDOM_SEED = int(round(time.time()))
NUM_BLOCKS = 2 # Number of data blocks
MAX_TIME = 100 # Max read or write time
EVENT_INTERVAL = 7 # Frequency of data block accesses
SIM_TIME = 2 * NUM_BLOCKS * MAX_TIME # Simulation time
READ_PROB = 0.75 # Probability that event ia a read
MAX_WRITE_WAIT = 50 # The longest a write event can wait, so no starvation
POLL_INTERVAL = 1 # Frequency of polling while waiting for lock


class Block(object):
    next_id = 0

    def __init__(self, env, max_time):
        self.env = env
        self.read_lock = simpy.Resource(env, float('inf'))
        self.write_lock = simpy.Resource(env, 1)
        self.max_time = max_time
        self.last_write_time = 0
        self.write_waiting = False
        self.id = Block.next_id
        Block.next_id += 1

    def access(self):
        access_time = random.randint(0, self.max_time)
        yield self.env.timeout(access_time)


def event(env, name, block, read=True):
    arrive = env.now
    print('%4.1f %s (Block %d): Received' % (arrive, name, block.id))

    if read:
        # Don't proceed if time from this block's last write is too long
        while env.now - block.last_write_time >= MAX_WRITE_WAIT and block.write_waiting == True:
            yield env.timeout(POLL_INTERVAL)

        while block.write_lock.count is not 0:
            yield env.timeout(POLL_INTERVAL)

        lock = block.read_lock
    else:
        while block.read_lock.count is not 0:
            block.write_waiting = True
            print("%4.1f %s waiting on block %d (%d readers)" % (env.now, name, block.id, block.read_lock.count))
            yield env.timeout(POLL_INTERVAL)

        lock = block.write_lock

    with lock.request() as request:
        start_wait_for_turn = env.now
        yield request

        wait = env.now - arrive
        if wait is not 0:
            print('%4.1f %s (Block %d): Waited %4.1f' % (env.now, name, block.id, wait))
        start_time = env.now

        yield env.process(block.access())

        finished_time = env.now
        if not read:
            block.last_write_time = finished_time
            block_write_waiting = False
        runtime = finished_time - start_time
        print('%4.1f %s (Block %d): Finished in %4.1f' % (finished_time, name, block.id, runtime))


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
            env.process(event(
                env,
                'Read%d' % i,
                database[rand_block]
            ))
        else:
            env.process(event(
                env, 'Write%d' % i,
                database[rand_block],
                read=False
            ))
        i += 1
        yield env.timeout(random.randint(event_interval - 2, event_interval + 2))


# Setup and start the simulation
print('Typical Reader and Writer')
print("Random Seed= %d" % RANDOM_SEED)
print("Num Data Blocks= %d" % NUM_BLOCKS)
print("Max Read/Write Time= %d" % MAX_TIME)
print("Event Interval= %d" % EVENT_INTERVAL)
print("Sim Time= %d" % SIM_TIME)
print("Read Probablity= %4.2f" % READ_PROB)
print("Max Write Wait Time= %d" % MAX_WRITE_WAIT)
print("Poll Interval= %d" % POLL_INTERVAL)
random.seed(RANDOM_SEED)  # This helps reproducing the results

# Create an environment and start the setup process
env = simpy.Environment()
env.process(setup(env, NUM_BLOCKS, MAX_TIME, EVENT_INTERVAL, READ_PROB))

# Execute!
env.run(until=SIM_TIME)
