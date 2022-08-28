import typing as tp
import numpy as np

class Motor:
    '''
    A class to represent a PMSM motor, implementing all relevant computations
    '''
    @staticmethod
    def FromDict(data):
        m = Motor(1, 1, 1, 1, 1, 1, 48, 1)
        m.update_constants(n = data['np'],
                           R = data['R'],
                           L = data['L'] / 1000.0,
                           ke = data['ke'],
                           iq_max = data['i_quadrature_max'],
                           iq_nominal = data.get('i_quadrature_nominal', data['i_quadrature_max']),
                           U = data['U'],
                           reduction_ratio = data['reduction_ratio'])
        return m

    def __init__(self, n:int, R:float, L:float, ke:float, iq_max:float, iq_nominal:float, U: float, reduction_ratio:float):
        '''
        Build a PMSM motor from the fundamental parameters.
            - n: number of poles
            - R: resistor, per phase, in Ohm
            - L: phase inductance, in H
            - ke: rotor flux in a phase
            - iq_max: maximum quadrature current (assuming no defluxing) in the motor
            - U: driver voltage
            - reduction_ratio: reduction ratio
        Note:
            - magnetic saturations not modelled
            - salliancy ratio is set to 1
        '''
        self.update_constants(n, R, L, ke, iq_max, iq_nominal, U, reduction_ratio)

    def to_dict(self):
        '''
        Store motore in dictionnary to save to json file.
        '''
        return {"np": 2 * self.np,
                "R": self.R,
                "L": self.L,
                "L": 1000.0 * self.L,
                "ke": self.ke,
                "i_quadrature_max": self.iq_max,
                "i_quadrature_nominal": self.iq_nominal,
                "U": self.U,
                "reduction_ratio": self.rho
                }

    def copy(self, other_motor:"Motor"):
        '''
        Copy the constants of other_motor onto self.
        '''
        self.update_constants(n = 2 * other_motor.np,
                              R = other_motor.R,
                              L = other_motor.L,
                              ke = other_motor.ke,
                              iq_max = other_motor.iq_max,
                              iq_nominal = other_motor.iq_nominal,
                              U = other_motor.U,
                              reduction_ratio = other_motor.rho)

    def update_constants(self,
                         n:int = None,
                         R:float = None,
                         L:float = None,
                         ke:float = None,
                         iq_max:float = None,
                         iq_nominal:float = None,
                         U: float = None,
                         reduction_ratio: float = None):
        '''
        Update the motor's constants (none to keep previous value).
        Note that updating the parameters should be done through this function
        only, otherwise the derived constants will be wrong !
        The parameters are the same as in the constructor.
        '''
        if n is not None:
            self.np = n / 2
        if R is not None:
            self.R = R
        if L is not None:
            self.L = L
        if ke is not None:
            self.ke = ke
        if iq_max is not None:
            self.iq_max = iq_max
        if iq_nominal is not None:
            self.iq_nominal = iq_nominal
        if U is not None:
            self.U = U
        if reduction_ratio is not None:
            self.rho = reduction_ratio

        self._compute_derived_constants()

    def _compute_derived_constants(self):
        '''
        Compute useful constants, derived from the fundamental parameters
        '''
        # See BrushlessMotorPhysics.pdf for more informations on these constants.
        # Torque-related constants
        self.kt_q_art = 3.0 / 2.0 * self.rho * self.ke
        self.i_rms_max = self.iq_max / np.sqrt(2)
        self.tau_max = self.kt_q_art * self.iq_max

        # Velocity-related constants
        self.ke_phasetophase = np.sqrt(3) * self.ke
        self.w_max_no_load = self.U / self.ke_phasetophase / self.rho
        self.w_max_at_max_torque = self.compute_max_speed_no_deflux(self.tau_max)

        # Power-related constants
        self.K_m_art = np.sqrt(2.0 / 3.0) * self.kt_q_art / np.sqrt(self.R)

        # Miscellaneous.
        self.r_deflux = self.np * self.L * self.iq_max / self.ke
        tau_n = self.kt_q_art * self.iq_nominal
        self.nominal_power = self.compute_max_speed_no_deflux(tau_n) * tau_n


    def __str__(self):
        return f"R: {self.R}Ohm, L: {self.L * 1000.0}mH, Phi: {self.ke}Wb, Iq_max: {self.iq_max}A, Np {self.np}, U {self.U}, reduction {self.rho}"

    def compute_max_speed_no_deflux(self, tau):
        '''
        Return the maximum articular speed, given articular torque, when not defluxing.
         - tau: input articular torque, Nm
        '''
        tau = np.asarray(tau)

        iq = tau / self.kt_q_art

        a = self.rho**2 * ((self.np * self.L * iq)**2 + self.ke**2)
        b = 2 * self.rho * self.R * self.ke * iq
        c = (self.R * iq)**2 - self.U**2 / 3

        return (-b + np.sqrt(b**2 - 4 * a * c)) / 2 / a

    def compute_defluxing_current(self, tau, w):
        '''
        Get defluxing current, in A, given articular torque and velocity.
        '''
        tau = np.asarray(tau)
        w = np.asarray(w)

        i_q = tau / self.kt_q_art

        # Compute the minimum amount of current that is needed to deflux:
        # this corresponds to the amount of current such that U = U_eff.
        a = self.R**2 + (self.rho * w * self.np * self.L)**2
        b = 2 * self.np * self.L * self.ke * (self.rho * w)**2
        c = (self.rho * w * self.np * self.L * i_q)**2 \
            + 2 * self.R * i_q * self.ke * self.rho * w \
            + self.R**2 * i_q**2 + (self.ke * self.rho * w)**2 \
            - self.U**2  / 3

        return np.minimum(0.0, (-b + np.sqrt(b**2 - 4 * a * c)) / 2 / a)

    def compute_max_speed_deflux(self, tau):
        '''
        Returns the maximum articular speed, given articular torque, with defluxing.
         - tau: input articular torque, Nm
        '''
        tau = np.asarray(tau)

        i_q = tau / self.kt_q_art
        i_d = np.maximum(-np.sqrt(np.maximum(0, 2 * self.i_rms_max**2 - i_q**2)),
                         - self.ke / self.np / self.L)

        a = (self.rho * self.np * self.L * i_q)**2  + self.rho**2 * (self.np * self.L * i_d + self.ke)**2
        b = 2 * self.rho * self.R * i_q * self.ke
        c = self.R**2 * (i_d**2 + i_q**2) - self.U**2  / 3
        return np.maximum((-b + np.sqrt(b**2 - 4 * a * c)) / 2 / a, self.compute_max_speed_no_deflux(tau))

    def compute_thermal_power(self, tau, w, force_no_defluxing=False):
        '''
            Compute the thermal power to reach a specific working point.
            The motor will deflux if needed, unless specified.
            Note: this function does not check that the point is feasible for
            the motor: if you ask for infinite torque, you get infinite power !
        '''
        tau = np.asarray(tau)
        w = np.asarray(w)

        i_q = tau / self.kt_q_art
        if force_no_defluxing:
            i_d = np.zeros(w.shape)
        else:
            i_d = self.compute_defluxing_current(tau, w)
        power = 3 / 2 * self.R * (i_d**2 + i_q**2)
        return power

    def get_power(self, w, tau):
        '''
        Return the total power (mecanical + thermal) required by the motor,
        (assuming no defluxing).
        '''
        return w * tau + 1 / self.K_m_art**2 * tau**2