import typing as tp
import numpy as np

class PIController:
    def __init__(self, Kp: float, Ki: float, integral_max: float):
        """
        A PI controller, with anti-windup
        The output of the controller is given by:
        u = - Kp * ((e) + sat(Ki * int(e)))
        where e = x - x_target is the error ; int is a time integral
        and sat a saturation at integral_max
        Parameters:
         - Kp: proportional gain
         - Ki: integral gain
         - integral_max: anti-windup: maximum value of Ki * integral
        """
        self.Kp = Kp
        self.Ki = Ki
        self.integral_max = integral_max
        self.integral = 0

    def reset_integral(self, value: float = 0):
        """
        Reset the integral to a specific value
        """
        self.integral = value

    def compute(self, e: float, dt: float):
        """
        Compute next PI output
        Parameters:
         - e: current error (x - x_target)
         - dt: time (in s) since last call
        Returns: PI output
        """
        # Anti-windup
        if self.Ki > 1e-10:
            self.integral = np.maximum(-self.integral_max / self.Ki, np.minimum(self.integral_max / self.Ki, self.integral + dt * e))

        return - self.Kp * (e + self.Ki * self.integral)
