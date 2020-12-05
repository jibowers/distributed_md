from multiprocessing import Process, Pipe
import boto3
import json
import re
import numpy as np
import random
import math

client = boto3.client('lambda', region_name='us-east-1')

def trigger_worker(lname, data, conn):
    ## helper function that triggers the md_worker lambda
    response = client.invoke(
        FunctionName = 'arn:aws:lambda:us-east-1:019215887465:function:md_worker',
        InvocationType = 'RequestResponse',
        Payload = json.dumps(data)
    )
    #print(response)
    result = response.get('Payload')
    conn.send(result.read())
    conn.close()


## create our space with particles
# we'll start with 2D (a square), then we can work up to 3D later

side_length = 20
num_particles = 100
dimensions = 3
timestep = 1 * 10**-12
total_time = 0.01 * 10**-9
num_steps = math.floor(total_time/timestep)
print("This will take {} steps of {} seconds each".format(num_steps, timestep))

# create positions_array with x and y columns with random positions in our box
position_array = np.random.rand(num_particles, dimensions)*side_length

# create charge_array with point charges between -1 and 1
charge_array = np.random.rand(num_particles)*2-1 

# create velocity_array with randoom velocities between 0 and max initial velocity
max_vi = 10
velocity_array = np.random.rand(num_particles, dimensions) * max_vi

#TODO find more accurate eps and rmins for the system
eps = np.ones(num_particles) * -0.1
rmins = np.random.rand(num_particles, 1) + 0.5

print("Positions:")
print(position_array)
print("Charges:")
print(charge_array)
print("Velocities:")
print(velocity_array)

num_workers = 4
processes = []
parent_connections = []
particles_per_split = math.floor(num_particles/num_workers)

f = open("md_sim.txt", "a")
f.write("Now the file has more content!")


for n in range(1):

    # create a process per worker
    for i in range(num_workers):            
        # create a pipe for communication
        parent_conn, child_conn = Pipe()
        parent_connections.append(parent_conn)

        # create the process, pass instance and connection
        start_index = i*particles_per_split
        if i == num_workers-1: #last worker
            end_index = num_particles - 1
        else:
            end_index = (i+1)*particles_per_split-1
        print("Worker {} start index: {}, end index: {}".format(i, start_index, end_index))
        data = {"start": start_index, "end": end_index, "positions": position_array.tolist(), "charges":charge_array.tolist(), "velocities": velocity_array[start_index:end_index].tolist(), "timestep": timestep, "eps": eps.tolist(), "rmins": rmins.tolist(), "bounds": side_length}
        process = Process(target=trigger_worker, args=("md_worker", data, child_conn,))
        processes.append(process)

    for process in processes:
        process.start()

    for process in processes:
        process.join()

    raw_answers = []
    received_positions = {}
    received_velocities = {}
    for parent_connection in parent_connections:
        message = parent_connection.recv().decode()
        raw_answers.append(message)
        dict_message = json.loads(message)
        received_positions[dict_message.get("start_index")] = dict_message.get("positions")
        received_velocities[dict_message.get("start_index")] = dict_message.get("velocities")

    #for answer in answers:
        #answer =  re.sub(r"\\",r" ",answer)

    print("## Putting the returned answers together in order")
    new_positions = np.empty(3)
    for i in sorted (received_positions) : 
        new_positions.append(received_positions.get(i))
    position_array = new_positions

    new_velocities= np.empty(3)
    for i in sorted (received_velocities) : 
        new_velocities.append(received_velocities.get(i))
    velocity_array = new_velocities

    print("{} iteration\nPositions: {}\nVelocities: {}".format(n, position_array, velocity_array))

f.close()