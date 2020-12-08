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
        
        new_positions = []
        particle_mass = 0.00000001
        num_particles = len(position_array)
        logger.info("## Num particles: {}".format(num_particles))
        logger.info("Length of charge_array: {}".format(len(charge_array)))
        logger.info("Length of velocity_array: {}".format(len(velocity_array)))
        logger.info("Length of eps: {}".format(len(eps)))
        logger.info("Length of rmins: {}".format(len(rmins)))
        # calculate Eelec and Evdw
        const = 332.1*4.184
        for i in range(start, end+1):
            logger.info("## Atom {}".format(i))
            eelec = 0
            evdw = 0
            force_array = []
            a = position_array[i]
            for j in range(num_particles):
                if i != j:
                    #calculate distance
                    b = position_array[j]
                    #logger.info("## Atom {} (looking at atom {} now)".format(i, j))
                    dist = np.linalg.norm(a-b)
                    # logger.info("Distance is {}".format(dist))
                    
                    # Calculating magnitude of force
                    #logger.info("Calculating derivative of eelec using charges and distance")
                    delec = -1*const*charge_array[i]*charge_array[j]/(dist**2)
                    #logger.info("Calculating derivative of evdw using distance and parameters")
                    eij = math.sqrt(eps[i]*eps[j])*4.184
                    #logger.info("Determined eij")
                    rij = rmins[i] + rmins[j]
                    #logger.info("Determined rij")
                    #evdw = eij*( (rij/dist)**12 - 2 * (rij/dist)**6)
                    dvdw = eij * (-12*((rij/dist)**12)/dist + 6*((rij/dist)**6)/dist)
                    #logger.info("## Distance: {}, Eelec: {}, Evdw: {}".format(dist, eelec, evdw))
    
                    # Calculating the direction of the force produced by both elec and vdw
                    unit_vector = (a-b)/dist
                    force_vector = unit_vector*(delec+dvdw)
                    #logger.info("## Force vector is {}".format(force_vector))
                    force_array.append(force_vector)

            #look at force array to determine ultimate force on particle (and thus acceleration and new velocity)
            #logger.info("Determine acceleration from {}".format(force_array))
            pre_mass_acceleration = [sum(x) for x in zip(*force_array)] #/particle_mass
            acceleration_w_time = [m/particle_mass*timestep  for m in pre_mass_acceleration]
            #logger.info("## Acceleration for particle {} is {}".format(i, acceleration_w_time))

            velocity = [sum(x) for x in zip(velocity_array[i-start], acceleration_w_time)]
            #logger.info("## Velocity for particle {} is {}".format(i, velocity))
            velocity_array[i-start] = velocity

            velocity_w_time = [m*timestep for m in velocity]
            position = [sum(x) for x in zip(a, velocity_w_time)]
            # to get wrapping to other side of box if particle leaves the box
            for d in range(len(position)):
                if position[d] > bounds:
                    position[d]  = position[d]%bounds
                elif position[d] < 0:
                    position[d] = bounds + -position[d]%bounds
            logger.info("## Particle {} went from {} to {}".format(i, a, position))
            new_positions.append(position)
            
        logger.info("## Length of position array: {}, Contents: {}".format(len(position_array), position_array))
        
        return {
            'statusCode': 200,
            'start_index': start,
            'end_index': end,
            'positions': new_positions,
            'velocities': velocity_array.tolist()
        }
    except Exception as e:
        logger.error("## {}".format(e))
        return {
            'status': 500,
            'error': str(e)
        }