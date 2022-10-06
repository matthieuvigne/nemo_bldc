import numpy as np
import sys

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
        # Note: we are not using scipy to reduce dependencies, hence the size of
        # the Windows binary
        x = np.sign(np.sin(self.omega * t + self.phi)) / 2 + 0.5
        return self.offset + self.A * x

class SignalTriangle(AbstractSignal):
    def __init__(self, frequency: float = 0, phase_shift: float = 0, amplitude: float = 0, offset: float = 0):
        super().__init__(frequency, phase_shift, amplitude, offset)
        self.deriv = SignalSquare(frequency, phase_shift, 4 * amplitude, -2 * amplitude)
        self.f = frequency

    def value(self, t: float):
        """
        Return the value of the signal at time t
        """
        # Note: we are not using scipy to reduce dependencies, hence the size of
        # the Windows binary
        x = self.f * t + self.phi / 2 / np.pi
        return self.offset + self.A * 2 * np.abs(x - np.floor(x + 0.5))

    def derivative(self, t: float):
        """
        Return the derivative of the signal at time t
        """
        return self.deriv.value(t)

def create_signal(signal_class_name: str,
                  frequency: float,
                  phase_shift: float,
                  amplitude: float,
                  offset: float):
    '''
    Create a signal from a class name and phase values
    '''
    return getattr(sys.modules[__name__], signal_class_name)(frequency, phase_shift, amplitude, offset)
