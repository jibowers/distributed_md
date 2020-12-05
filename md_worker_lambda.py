import json
import numpy as np
import logging
import math
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
        position_array = np.asarray(event.get("positions"))
        charge_array = np.asarray(event.get("charges"))
        velocity_array = np.asarray(event.get("velocities"))
        timestep = event.get("timestep")
        eps = np.asarray(event.get("eps"))
        rmins = np.asarray(event.get("rmins"))
        bounds = event.get("bounds")
        #logger.info("Positions: {}\nCharges: {}\nVelocities: {}\nEpsilons: {}\nRmins: {}".format(position_array, charge_array, velocity_array, eps, rmins))
        logger.info("Epsilons: {}".format(eps))
        logger.info("## Got all the arguments passed to this lambda")
        new_positions = np.empty(3)
        particle_mass = 0.00000001
        # calculate Eelec and Evdw
        const = 332.1*4.184
        for i in range(start, end):
            eelec = 0
            evdw = 0
            force_array = []
            a = position_array[i]
            for j in range (start, end):
                if i != j:
                    #calculate distance
                    b = position_array[j]
                    logger.info("## Calculating energy terms between atom {} (at {}) and atom {} (at {})".format(i, a, j, b))
                    dist = np.linalg.norm(a-b)
                    logger.info("Distance is {}".format(dist))
                    
                    logger.info("Calculating eelec using charges and distance")
                    eelec = const*charge_array[i]*charge_array[j]/dist
                    logger.info("Calculating evds using charges and distance")
                    eij = math.sqrt(eps[i]*eps[j])*4.184
                    logger.info("Determined eij")
                    rij = rmins[i] + rmins[j]
                    logger.info("Determined rij")
                    evdw = eij*( (rij/dist)**12 - 2 * (rij/dist)**6)
                    logger.info("## Distance: {}, Eelec: {}, Evdw: {}".format(dist, eelec, evdw))
    
                    unit_vector = a-b/dist
                    force_vector = unit_vector*(eelec+evdw)
                    logger.info("## Force vector is {}".format(force_vector))
                    force_array.append(force_vector)

            #look at force array to determine ultimate force on particle (and thus acceleration and new velocity)
            logger.info("Determine acceleration from {}".format(force_array))
            pre_mass_acceleration = [sum(x) for x in zip(*force_array)] #/particle_mass
            acceleration_w_time = [m/particle_mass*timestep  for m in pre_mass_acceleration]
            logger.info("## Acceleration for particle {} is {}".format(i, acceleration_w_time))

            velocity = [sum(x) for x in zip(velocity_array[i-start], acceleration_w_time)]
            logger.info("## Velocity for particle {} is {}".format(i, velocity))
            velocity_array[i-start] = velocity

            velocity_w_time = [m*timestep for m in velocity]
            position = [sum(x) for x in zip(a, velocity_w_time)]
            # to get wrapping to other side of box if particle leaves the box
            for d in range(len(position)):
                if position[d] > bounds:
                    position[d]  = position[d] - bounds
                elif position[d] < 0:
                    position[d] = bounds + position[d]
            logger.info("## Particle {} went from {} to {}".format(i, a, position))
            new_positions = np.append(new_positions, position)

        return {
            'statusCode': 200,
            'positions': new_positions.tolist(),
            'velocities': velocity_array.tolist()
        }
    except Exception as e:
        logger.error("## {}".format(e))
        return {
            'status': 500,
            'error': str(e)
        }