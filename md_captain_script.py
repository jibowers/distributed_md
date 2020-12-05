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
timestep = 0.00000001
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

answers = []
for parent_connection in parent_connections:
    message = parent_connection.recv().decode()
    answers.append(message)

for answer in answers:
    answer =  re.sub(r"\\",r" ",answer)

print(json.dumps(answers))
