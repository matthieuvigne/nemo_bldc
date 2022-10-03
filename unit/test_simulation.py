import pytest
import numpy as np
from bisect import bisect
from nemo_bldc.ressources import DEFAULT_LIBRARY
from nemo_bldc.simulation.simulate import simulate
from nemo_bldc.simulation import simulate, ControlType, PIController, SignalConstant, SignalSinus

def test_simulation_current():
    # Test current mode simulation
    motor = DEFAULT_LIBRARY["MyActuator RMD-X6 V3"]

    # Parameters
    duration = 0.5
    frequency = 20000

    signal = SignalConstant(0, 0, 0, 1.0)
    current_controller = PIController(2.0, 500.0, 30.0)
    tau = motor.kt_q_art * signal.value(0)

    for I in [0.1, 0.5]:
        for nu in [0.2, 1.0]:
            result = simulate(motor, ControlType.CURRENT, signal, duration, I, nu, current_controller, control_loop_frequency=frequency)

            # Give time for convergence
            idx = bisect(result.time, 0.1)
            # Check current tracking
            assert np.allclose(result.idq[:, idx:], result.idq_target[:, idx:], atol=0.01)

            # Check mechanical behavior
            dtheta = tau / nu * (1 - np.exp(- nu / I * result.time))
            assert np.allclose(result.dtheta[idx:], dtheta[idx:], atol=0.02)
            assert np.allclose(np.diff(result.theta) * frequency, result.dtheta[1:], atol=0.001)

            # Test power conversation
            p_elec = np.array([i.T @ u for i, u in zip(result.iphase.T, result.Vphase.T)])
            p_meca = motor.kt_q_art * result.dtheta * result.idq[1]
            p_th = 3 / 2 * motor.R * (result.idq[0]**2 + result.idq[1]**2)
            assert np.allclose((p_meca + p_th)[idx:], p_elec[idx:], rtol=1e-3)

    # Test velocity limit
    I = 0.001
    nu = 0.0
    result = simulate(motor, ControlType.CURRENT, signal, duration, I, nu, current_controller, control_loop_frequency=frequency)

    assert np.allclose(result.idq[:, -1000:], np.zeros((2, 1000)), atol=0.0001)
    assert np.allclose(result.dtheta[-1000:], motor.w_max_no_load, atol=0.0001)

def test_simulation_velocity():
    # Test velocity mode simulation
    motor = DEFAULT_LIBRARY["MyActuator RMD-X6 V3"]

    # Parameters
    duration = 0.4
    frequency = 20000

    signal = SignalSinus(2.0, 0.0, 1.0, 0.0)
    current_controller = PIController(2.0, 500.0, 30.0)
    velocity_controller = PIController(30.0, 5.0, 10.0)

    I = 0.1
    nu = 1.0

    result = simulate(motor, ControlType.VELOCITY, signal, duration, I, nu, current_controller, velocity_controller, control_loop_frequency=frequency)

    assert np.allclose(result.vel_target, signal.value(result.time))

    # Give time for convergence
    idx = bisect(result.time, 0.1)
    assert np.allclose(result.dtheta[idx:], signal.value(result.time)[idx:], atol=0.05)

    # Check limit torque
    signal = SignalConstant(0, 0, 0, 2.0)
    result = simulate(motor, ControlType.VELOCITY, signal, duration, I, nu, current_controller, velocity_controller, control_loop_frequency=frequency)

    idx = bisect(result.time, 0.1)
    assert np.allclose(result.dtheta[idx:], signal.value(result.time)[idx:], atol=0.05)
    assert np.allclose(motor.kt_q_art * result.idq[1, idx:], nu * signal.value(result.time)[idx:], atol=0.05)


def test_simulation_position():
    # Test velocity mode simulation
    motor = DEFAULT_LIBRARY["MyActuator RMD-X6 V3"]

    # Parameters
    duration = 0.4
    frequency = 20000

    signal = SignalSinus(0.2, 0.0, 1.0, 0.0)
    current_controller = PIController(2.0, 500.0, 30.0)
    velocity_controller = PIController(100.0, 0.0, 10.0)
    position_controller = PIController(10.0, 2.0, 10.0)


    I = 0.1
    nu = 1.0

    result = simulate(motor, ControlType.POSITION, signal, duration, I, nu, current_controller, velocity_controller, position_controller, control_loop_frequency=frequency)

    assert np.allclose(result.pos_target, signal.value(result.time))
    assert np.allclose(result.vel_target, signal.derivative(result.time))


    # Give time for convergence
    idx = bisect(result.time, 0.2)
    assert np.allclose(result.theta[idx:], signal.value(result.time)[idx:], rtol=1e-2)
