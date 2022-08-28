# Modeling of a battery as voltage source + resistor
import typing as tp
import numpy as np

def get_battery_state(U_bat, R_bat, P):
    '''
    Return battery current and voltage, given a power input.
    The battery is modeled as a constant voltage source U_bat (typ. 48V), with
    a resistor R_bat in serie.
     - U_bat: battery voltage
     - R_bat: battery resistor
     - P: power drawn
    Return: U, I
    '''
    I = (U_bat - np.sqrt(U_bat**2 - 4 * R_bat * P)) / 2 / R_bat
    return U_bat - R_bat * I, I
