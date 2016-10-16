"""
Constructs a planner that is good for getting out of sticky situations!

"""
from __future__ import division
import numpy as np
import numpy.linalg as npl

from params import *
import lqrrt

################################################# DYNAMICS

def dynamics(x, u, dt):
	"""
	Returns next state given last state x, wrench u, and timestep dt.

	"""
	# Rotation matrix (orientation, converts body to world)
	R = np.array([
				  [np.cos(x[2]), -np.sin(x[2]), 0],
				  [np.sin(x[2]),  np.cos(x[2]), 0],
				  [           0,             0, 1]
				])

	# Construct drag coefficients based on our motion signs
	D = np.copy(D_neg)
	for i, v in enumerate(x[3:]):
		if v >= 0:
			D[i] = D_pos[i]

	# Actuator saturation
	u = B.dot(np.clip(invB.dot(u), -thrust_max, thrust_max))

	# M*vdot + D*v = u  and  pdot = R*v
	xdot = np.concatenate((R.dot(x[3:]), invM*(u - D*x[3:])))

	# First-order integrate
	xnext = x + xdot*dt

	return xnext

################################################# POLICY

kp = np.diag([150, 150, 1000])
kd = np.diag([150, 150, 1])
S = np.diag([1, 1, 1, 1, 1, 1])

def lqr(x, u):
	"""
	Returns cost-to-go matrix S and policy matrix K given local state x and effort u.

	"""
	R = np.array([
				  [np.cos(x[2]), -np.sin(x[2]), 0],
				  [np.sin(x[2]),  np.cos(x[2]), 0],
				  [           0,             0, 1]
				])
	K = np.hstack((kp.dot(R.T), kd))
	return (S, K)

################################################# HEURISTICS

goal_buffer = [free_radius, free_radius, np.inf, np.inf, np.inf, np.inf]
error_tol = np.copy(goal_buffer)

sf = 3

def gen_ss(seed, goal):
	"""
	Returns a sample space given a seed state and goal state.

	"""
	return [(seed[0] - sf*ss_buff, seed[0] + sf*ss_buff),
			(seed[1] - sf*ss_buff, seed[1] + sf*ss_buff),
			(-np.pi, np.pi),
			(-abs(velmax_neg_plan[0]), velmax_pos_plan[0]),
			(-abs(velmax_neg_plan[1]), velmax_pos_plan[1]),
			(-abs(velmax_neg_plan[2]), velmax_pos_plan[2])]

################################################# MAIN ATTRIBUTES

constraints = lqrrt.Constraints(nstates=nstates, ncontrols=ncontrols,
								goal_buffer=goal_buffer, is_feasible=unset)

planner = lqrrt.Planner(dynamics, lqr, constraints,
						horizon=horizon, dt=dt, FPR=FPR,
						error_tol=error_tol, erf=unset,
						min_time=0, max_time=5, max_nodes=max_nodes,
						sys_time=unset, printing=False)
