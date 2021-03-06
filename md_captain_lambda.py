from multiprocessing import Process, Pipe
import boto3
import json
import re
import numpy as np
import random

#client = boto3.client('lambda')

def trigger_worker(lname, data, conn):
    ## helper function that triggers the md_worker lambda
    response = client.invoke(
        FunctionName = 'arn:aws:lambda:us-east-1:019215887465:function:md_worker',
        InvocationType = 'RequestResponse',
        Payload = json.dumps(data)
    )
    print(response)
    result = response.get('Payload')
    conn.send(result.read())
    conn.close()

def lambda_handler(event, context):

    ## create our space with particles
    # we'll start with 2D (a square), then we can work up to 3D later

    side_length = 20
    num_particles = 10
    dimensions = 2
    # create positions_array with x and y columns with random positions in our box
    position_array = np.random.rand(num_particles, dimensions)*side_length

    # create charge_array with charges -1 and 1
    charge_array = np.ones(num_particles)
    for p in range(num_particles):
        charge_array[0] = random.choice([-1, 1])

    num_workers = 2
    processes = []
    parent_connections = []

    return position_array
    # create a process per instance
    for i in range(5):            
        # create a pipe for communication
        parent_conn, child_conn = Pipe()
        parent_connections.append(parent_conn)

        # create the process, pass instance and connection
        data = {"num": i}
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

    return json.dumps(answers)


event = {
    "key1"   : "value1"
}
run_response = lambda_handler(event,'')
print(run_response)