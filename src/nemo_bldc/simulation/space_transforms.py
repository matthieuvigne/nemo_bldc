import numpy as np

def clarke_park_inv(theta: float, Vdq: np.array):
    '''
    Clarke-Park inverse transform

    @param theta Electrical angle
    @param Vdq [Vd Vq] array
    @return [Va Vb Vc] array
    '''
    C = 3 / 2 * np.array([[2 / 3, 0], [- 1 / 3, np.sqrt(3) / 3], [- 1 / 3, - np.sqrt(3) / 3]])
    P = np.array([[np.cos(theta), - np.sin(theta)],[ np.sin(theta), np.cos(theta)]])
    return C @ P @ Vdq

def clarke_park(theta, Vphase):
    '''
    Clarke-Park direct transform

    @param theta Electrical angle
    @param Vphase [Va Vb Vc] array
    @return [Vd Vq] array
    '''
    C = 2 / 3 * np.array([[1, - 1/2, - 1/2], [0, np.sqrt(3) / 2, - np.sqrt(3) / 2]])
    P = np.array([[np.cos(theta), np.sin(theta)],[ -np.sin(theta), np.cos(theta)]])
    return P @ C @ Vphase


def svpwm(theta_el: float, Vdq: np.array, Vdc: float):
    """
    Space-vector PWM to compute phase voltage from direct/quadrature vectors.

    This code is derived from the version presented in the SimpleFOC library,
    https://docs.simplefoc.com/foc_theory
    """

    # Compute amplitude and angle - clamping as needed
    Uout = np.linalg.norm(Vdq) / Vdc * np.sqrt(3)
    Uout = min(Uout, 1)

    angle = (theta_el + np.arctan2(Vdq[1], Vdq[0])) % (2 * np.pi)

    # Find the sector
    sector = np.floor(angle / (np.pi / 3.0)) + 1

    # Calculate duty cycles
    T1 = np.sqrt(3) * np.sin(sector * np.pi / 3 - angle) * Uout
    T2 = np.sqrt(3) * np.sin(angle - (sector - 1) * np.pi / 3) * Uout
    T0 = 1 - T1 - T2

    if sector == 1:
        Ta = T1 + T2 + T0/2
        Tb = T2 + T0/2
        Tc = T0/2
    elif sector == 2:
          Ta = T1 +  T0/2
          Tb = T1 + T2 + T0/2
          Tc = T0/2
    elif sector == 3:
          Ta = T0/2
          Tb = T1 + T2 + T0/2
          Tc = T2 + T0/2
    elif sector == 4:
          Ta = T0/2
          Tb = T1+ T0/2
          Tc = T1 + T2 + T0/2
    elif sector == 5:
          Ta = T2 + T0/2
          Tb = T0/2
          Tc = T1 + T2 + T0/2
    else:
          Ta = T1 + T2 + T0/2
          Tb = T0/2
          Tc = T1 + T0/2

    # Calculate the phase voltages, recentering them
    average = (Ta + Tb + Tc) / 3.0
    Ua = (Ta - average) * Vdc / np.sqrt(3)
    Ub = (Tb - average) * Vdc / np.sqrt(3)
    Uc = (Tc - average) * Vdc / np.sqrt(3)
    return np.array([Ua, Ub, Uc])