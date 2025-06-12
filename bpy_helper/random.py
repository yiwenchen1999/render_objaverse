import math
import random

import numpy as np


def gen_random_pts_around_origin(seed, N, min_dist_to_origin, max_dist_to_origin, min_theta_in_degree,
                                 max_theta_in_degree, z_up=True) -> list:
    """
    Generate random points around the origin

    :param seed: random seed
    :param N: number of points
    :param min_dist_to_origin: minimum distance to the origin
    :param max_dist_to_origin: maximum distance to the origin
    :param min_theta_in_degree: minimum theta in degree
    :param max_theta_in_degree: maximum theta in degree
    :param z_up: if True, z is up, otherwise y is up
    :return: list of point positions
    """

    if seed is not None:
        random.seed(seed)
    ret = []
    for i in range(N):
        phi = 2 * math.pi * random.random()
        theta = math.acos(2.0 * random.random() - 1.0)
        while theta < min_theta_in_degree * np.pi / 180.0 or theta > max_theta_in_degree * math.pi / 180.0:
            theta = math.acos(2.0 * random.random() - 1.0)
        dist = min_dist_to_origin + random.random() * (max_dist_to_origin - min_dist_to_origin)
        pt = [dist * math.sin(theta) * math.cos(phi), dist * math.sin(theta) * math.sin(phi),
              dist * math.cos(theta)]
        if not z_up:
            pt = [pt[0], pt[2], pt[1]]
        ret.append(pt)
    return ret

def gen_clustered_pts_around_origin(seed, N, 
                                    min_dist_to_origin, 
                                    max_dist_to_origin,
                                    min_theta_in_degree, 
                                    max_theta_in_degree,
                                    z_up=True,
                                    dist_range = 0.1,
                                    theta_range_deg = 45,
                                    phi_range_deg = 45,
                                    ) -> list:
    """
    Generate a cluster of random points around a randomly chosen center near the origin.

    :param seed: random seed
    :param N: number of points
    :param min_dist_to_origin: minimum distance to the origin
    :param max_dist_to_origin: maximum distance to the origin
    :param min_theta_in_degree: minimum theta in degree
    :param max_theta_in_degree: maximum theta in degree
    :param cluster_radius: max distance of any point from the cluster center
    :param z_up: if True, z is up, otherwise y is up
    :return: list of point positions
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # Step 1: Choose a random central point in the spherical shell
    phi_center = 2 * math.pi * random.random()
    theta_center = math.acos(2.0 * random.random() - 1.0)
    while theta_center < min_theta_in_degree * np.pi / 180.0 or theta_center > max_theta_in_degree * math.pi / 180.0:
        theta_center = math.acos(2.0 * random.random() - 1.0)
    dist_center = min_dist_to_origin + random.random() * (max_dist_to_origin - min_dist_to_origin)
    cx = dist_center * math.sin(theta_center) * math.cos(phi_center)
    cy = dist_center * math.sin(theta_center) * math.sin(phi_center)
    cz = dist_center * math.cos(theta_center)
    center = np.array([cx, cy, cz])

    # Step 2: Generate points around the center within cluster_radius
    ret = []
    for _ in range(N):
        dist = dist_center + random.uniform(-dist_range, dist_range)
        theta = theta_center + np.radians(random.uniform(-theta_range_deg, theta_range_deg))
        phi = phi_center + np.radians(random.uniform(-phi_range_deg, phi_range_deg))
        while theta < min_theta_in_degree * np.pi / 180.0 or theta > 85 * math.pi / 180.0:
            theta = theta_center + np.radians(random.uniform(-theta_range_deg, theta_range_deg))
        
        pt = [dist * math.sin(theta) * math.cos(phi), dist * math.sin(theta) * math.sin(phi),
              dist * math.cos(theta)]
        if not z_up:
            pt = [pt[0], pt[2], pt[1]]
        ret.append(pt)

    return ret
