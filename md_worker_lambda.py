import json
import numpy as np
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

""" Events will come in format: 
{"start": start_index, "end": end_index, "positions": position_array, 
"charges":charge_array, "velocities": velocity_array[start_index:end_index, :], 
"timestep": timestep, "eps": eps, "rmins": rmins, "bounds": 20}

From this, calculates Eelec and Evdw from the distances (and constants), 
return new positions and velocities for the particles that this lambda is responsible for
"""

def lambda_handler(event, context):
    # TODO implement
    logger.info("## Event: {}".format(event))
    try:
        start = event.get("start")
        end = event.get("end")
        position_array = event.get("positions")
        charge_array = event.get("charges")
        velocity_array = event.get("velocities")
        timestep = event.get("timestep")
        eps = event.get("eps")
        rmins = event.get("rmins")
        bounds = event.get("bounds")

        logging.info("## Got all the arguments passed to this lambda")
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
                logger.info("## Calculating energy terms between atom {} (at {}) and atom {} (at {})".format(i, a, j, b))
                dist = np.linalg.norm(a-b)
                
                eelec = eelec + const*charge_array[i]*charge_array[j]/dist
                eij = sqrt(eps[i]*eps[j])*4.184
                rij = rmins[i] + rmins[j]
                evdw = evdw + eij*( (rij/dist)^12 - 2 * (rij/dist)^6)
                logger.info("## Distance: {}, Eelec: {}, Evdw: {}".format(dist, eelec, evdw))

                unit_vector = a-b/dist
                force_vector = unit_vector*(eelec+evdw)
                logger.info("## Force vector is {}")
                force_array.append(force_vector)

            #look at force array to determine ultimate force on particle (and thus acceleration and new velocity)
            acceleration = [sum(x) for x in zip(*force_array)]/particle_mass
            logger.info("## Acceleration for particle {} is {}".format(i, acceleration))

            velocity = velocity_array[i-start] + acceleration*timestep
            logger.info("## Velocity for particle {} is {}".format(i, velocity))
            velocity_array[i-start] = velocity

            new_position = a + velocity*timestep
            # to get wrapping to other side of box if particle leaves the box
            for d in len(new_position):
                if new_position[d] > bounds:
                    new_position[d]  = new_position[d] - bounds
                elif new_position[d] < 0:
                    new_position[d] = bounds + new_position[d]
            logger.info("## Particle {} went from {} to {}".format(i, a, new_position))
            new_positions.append(new_position)




        return {
            'statusCode': 200,
            'positions': new_positions,
            'velocities': velocity_array
        }
    except Exception as e:
        return {
            'status': 500
            'error': str(e)
        }
