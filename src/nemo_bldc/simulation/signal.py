import numpy as np
import sys
import scipy.signal

class AbstractSignal:
    """
    Abstract class representing a signal
    """
    def __init__(self, frequency: float = 0, phase_shift: float = 0, amplitude: float = 0, offset: float = 0):
        self.A = amplitude
        self.offset = offset
        self.omega = 2 * np.pi * frequency
        self.phi = phase_shift

    def value(self, t: float):
        """
        Return the value of the signal at time t
        """
        return 0.0

    def derivative(self, t: float):
        """
        Return the derivative of the signal at time t
        """
        return 0.0

class SignalConstant(AbstractSignal):
    def value(self, t: float):
        return self.offset + 0 * t

class SignalSinus(AbstractSignal):
    def value(self, t: float):
        """
        Return the value of the signal at time t
        """
        return self.offset + self.A * np.sin(self.omega * t + self.phi)

    def derivative(self, t: float):
        """
        Return the derivative of the signal at time t
        """
        return self.A * self.omega * np.cos(self.omega * t + self.phi)

class SignalSquare(AbstractSignal):
    def value(self, t: float):
        """
        Return the value of the signal at time t
        """
        return self.offset + self.A * (scipy.signal.square(self.omega * t + self.phi) + 1) / 2

class SignalTriangle(AbstractSignal):
    def value(self, t: float):
        """
        Return the value of the signal at time t
        """
        return self.offset + self.A * (scipy.signal.sawtooth(self.omega * t + self.phi, width=0.5) + 1) / 2

    def derivative(self, t: float):
        """
        Return the derivative of the signal at time t
        """
        return 2 * self.A * scipy.signal.square(self.omega * t + self.phi)

def create_signal(signal_class_name: str,
                  frequency: float,
                  phase_shift: float,
                  amplitude: float,
                  offset: float):
    '''
    Create a signal from a class name and phase values
    '''
    return getattr(sys.modules[__name__], signal_class_name)(frequency, phase_shift, amplitude, offset)