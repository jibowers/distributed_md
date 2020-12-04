import json
import numpy as np

""" Events will come in format: 
{"start": start_index, "end": end_index, "positions": position_array, 
"charges":charge_array, "velocities": velocity_array[start_index:end_index, :], "timestep": timestep, "eps": eps, "rmins": rmins}

From this, calculates Eelec and Evdw from the distances (and constants), 
return new positions and velocities for the particles that this lambda is responsible for
"""

def lambda_handler(event, context):
    # TODO implement
    try:
        start = event.get("start")
        end = event.get("end")
        position_array = event.get("positions")
        charge_array = event.get("charges")
        velocity_array = event.get("velocities")
        timestep = event.get("timestep")
        eps = event.get("eps")
        rmins = event.get("rmins")

        new_positions = []
        particle_mass = 0.00000001
        # calculate Eelec and Evdw
        const = 332.1*4.184
        for i in range(start, stop):
            eelec = 0
            evdw = 0
            force_array = []
            a = position_array[i]
            for j in range (i+1, stop):
                #calculate distance
                b = position_array[j]
                dist = np.linalg.norm(a-b)
                eelec = eelec + const*charge_array[i]*charge_array[j]/dist
                eij = sqrt(eps[i]*eps[j])*4.184
                rij = rmins[i] + rmins[j]
                evdw = evdw + eij*( (rij/dist)^12 - 2 * (rij/dist)^6)
                
                unit_vector = a-b/dist
                force_vector = unit_vector*(eelec+evdw)
                force_array.append(force_vector)

            #look at force array to determine ultimate force on particle (and thus acceleration and new velocity)
            acceleration = [sum(x) for x in zip(*force_array)]/particle_mass
            velocity = velocity_array[i-start] + acceleration*timestep
            velocity_array[i-start] = velocity

            position = a + velocity*timestep
            new_positions.append(position)




        return {
            'statusCode': 200,
            'positions': json.dump(new_positions),
            'velocities': json.dump(velocity_array)
        }
    except Exception as e:
        return {
            'status': 500
            'error': str(e)
        }
