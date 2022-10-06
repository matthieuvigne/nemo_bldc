import typing as tp
import numpy as np
from enum import Enum

from .signal import AbstractSignal, SignalConstant
from .pi_controller import PIController
from .space_transforms import clarke_park, clarke_park_inv, svpwm
from ..physics.motor import Motor

class ControlType(Enum):
    POSITION = 1
    VELOCITY = 2
    CURRENT = 3

class SimulationResult:
    def __init__(self, time: np.array, motor: Motor, control_type: ControlType):
        self.time = time
        self.motor = motor
        self.control_type = control_type
        l = len(time)
        self.theta = np.zeros(l)
        self.dtheta = np.zeros(l)
        self.idq = np.zeros((2, l))
        self.iphase = np.zeros((3, l))
        self.Vdq = np.zeros((2, l))
        self.Vphase = np.zeros((3, l))
        self.pos_target = np.zeros(l)
        self.vel_target = np.zeros(l)
        self.idq_target = np.zeros((2, l))
        self.Vdq_target = np.zeros((2, l))
        self.load_torque = np.zeros(l)


def bemf(theta):
    '''
    Generate BEMF vector
    '''
    return np.array([np.sin(theta), np.sin(theta - 2 * np.pi / 3), np.sin(theta + 2 * np.pi / 3)])

class MotorSimulator:
    def __init__(self,
                 motor: Motor,
                 inertia: float,
                 friction: float,
                 dt: float,
                 load_torque_signal: AbstractSignal):
        '''
        A class to simulate the motion of a brushless motor using a discrete controller

        @param motor Motor to simulate
        @param inertia Mechanical inertia
        @param friction Viscuous friction
        @param dt Step size
        @param AbstractSignal Resistive torque applied to the motor
        '''
        self.motor = motor
        self.state = np.zeros(5) # Current state: theta, dtheta, iphase
        self.I = inertia
        self.nu = friction
        self.dt = dt
        self.load = load_torque_signal
        self.t = 0

    def _dynamics(self, t, x, Vphase):
        '''
        System dynamics.

        @param x System state
        @param Vphase Phase voltage
        '''
        theta = x[0]
        dtheta = x[1]
        iphase = x[2:]
        idq = clarke_park(self.motor.np * self.motor.rho * theta, iphase)
        tau = self.motor.kt_q_art * idq[1] - self.load.value(t)
        ddtheta = (- self.nu * dtheta + tau) / self.I
        dx = np.zeros(5)
        dx[0] = dtheta
        dx[1] = ddtheta
        dx[2:] = (-self.motor.R * iphase + self.motor.ke * self.motor.rho * dtheta * bemf(self.motor.np * self.motor.rho * theta) + Vphase) / self.motor.L

        return dx

    def step(self, Vdq_target: np.array):
        '''
        Integrate system state over a timestep dt, updating the system's internal state.

        @param dt Integration length
        @param Vdq_target Direct and quadrature voltage target
        '''
        Vphase = svpwm(self.motor.np * self.motor.rho * self.state[0], Vdq_target, self.motor.U)
        self.Vphase = Vphase

        self.state += self.dt * self._dynamics(self.t, self.state, Vphase)
        self.t += self.dt


def simulate(motor: Motor,
             control_type: ControlType,
             target_signal: AbstractSignal,
             duration: float,
             system_inertia: float,
             system_friction: float,
             current_controller: PIController,
             velocity_controller: PIController = PIController(0, 0, 0),
             position_controller: PIController = PIController(0, 0, 0),
             control_loop_frequency: float = 1000,
             commutation_frequency: float = 10000,
             current_direct_target: AbstractSignal = SignalConstant(),
             load_torque_signal: AbstractSignal = SignalConstant()
             ):
    """
    Simulate the motor tracking a reference trajectory using a classical
    cascade PI controller.

    The mechanical equation is a simple load + viscuous friction:
     - I ddtheta = tau - nu dtheta

    The target signal is either a position, velocity or current target.
    The control is perform in cascade as a position PI feeding a velocity PI
    feeding a current PI, which ultimately outputs a voltage target sent to the
    motor through three PWM signal (ideal mosfets)

    Parameters:
     - motor: the motor to simulate
     - TODO

    Return: simulation result
    """
    current_controller.reset_integral(0)
    velocity_controller.reset_integral(0)
    position_controller.reset_integral(0)

    dt = 1 / control_loop_frequency
    time = np.arange(0, duration + dt, dt)
    result = SimulationResult(time, motor, control_type)

    t = 0
    if control_type == ControlType.POSITION:
        result.pos_target[0] = target_signal.value(t)
        result.vel_target[0] = target_signal.derivative(t)
    elif control_type == ControlType.VELOCITY:
        result.vel_target[0] = target_signal.value(t)
    else:
        result.idq_target[0, 1] = target_signal.value(t)
    result.idq_target[0, 0] = current_direct_target.value(t)
    result.load_torque[0] = load_torque_signal.value(t)


    simulator = MotorSimulator(motor, system_inertia, system_friction, dt, load_torque_signal)

    for i in range(1, len(time)):
        t = result.time[i]
        # Position and velocity loops, if enabled.
        target_position = 0
        target_velocity = 0
        idq_target = np.array([current_direct_target.value(t), 0.0])
        if control_type == ControlType.POSITION:
            target_position = target_signal.value(t)
            target_velocity = target_signal.derivative(t)
            vel_input = position_controller.compute(result.theta[i-1] - target_position, dt)
            idq_target[1] = velocity_controller.compute(result.dtheta[i-1] - vel_input - target_velocity, dt)
        elif control_type == ControlType.VELOCITY:
            target_velocity = target_signal.value(t)
            idq_target[1] = velocity_controller.compute(result.dtheta[i-1] - target_velocity, dt)
        else:
            idq_target[1] = target_signal.value(t)

        # Saturate current target, giving priority to the quadrature current.
        idq_target[1] = min(motor.iq_max, max(-motor.iq_max, idq_target[1]))
        id_max = np.sqrt(motor.iq_max**2 - idq_target[1]**2)
        idq_target[0] = min(id_max, max(-id_max, idq_target[0]))

        Vdq_target = current_controller.compute(result.idq[:, i - 1] - idq_target, dt)

        # Integrate
        simulator.step(Vdq_target)

        # Store results
        result.theta[i] = simulator.state[0]
        result.dtheta[i] = simulator.state[1]
        result.idq[:, i] = clarke_park(motor.np * motor.rho * result.theta[i], simulator.state[2:])
        result.iphase[:, i] = simulator.state[2:]
        result.Vdq[:, i] = clarke_park(motor.np * motor.rho * result.theta[i], simulator.Vphase)
        result.Vphase[:, i] =  simulator.Vphase
        result.pos_target[i] = target_position
        result.vel_target[i] = target_velocity
        result.idq_target[:, i] = idq_target
        result.Vdq_target[:, i] = Vdq_target
        result.load_torque[i] = simulator.load.value(t)

        if np.max(np.abs(simulator.state[2:])) > 10 * motor.iq_max:
            # Simulation is unstable
            raise ArithmeticError("Excessive current detected, simulation is likely numerically unstable.\n" +\
                            "Please check controller gains or increase control frequency.")
    return result
