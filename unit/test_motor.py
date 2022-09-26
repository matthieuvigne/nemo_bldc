# Test the physical computation of Nemo, by comparing various values
# with the datasheets.
import pytest
import numpy as np
import copy

from nemo_bldc.physics import Motor
from nemo_bldc.ressources import DEFAULT_LIBRARY


def test_MyActuator():
    # Check the derived parameters against the datasheet, to make sure the
    # computation makes sense.
    m = DEFAULT_LIBRARY["MyActuator RMD-X6 V2"]

    # Check the parameters
    assert 2 * m.R == pytest.approx(0.33)  # phase to phase
    assert 2 * m.L == pytest.approx(0.19 * 1e-3)  # phase to phase
    assert m.U == pytest.approx(24)
    assert m.iq_nominal == pytest.approx(4)
    assert m.np == 14
    assert m.rho == pytest.approx(6)

    # Magnetic parameter was determined using KV
    kv = 1 / m.ke * 60 / 2 / np.pi / np.sqrt(3)
    assert kv == pytest.approx(60.0, rel=0.001)

    # Speed limits
    assert m.w_max_at_max_torque * 30 / np.pi == pytest.approx(190, rel=0.1)
    assert m.w_max_no_load * 30 / np.pi == pytest.approx(240, rel=0.01)
    assert (
        m.compute_max_speed_no_deflux(m.kt_q_art * m.iq_nominal) > m.w_max_at_max_torque
    )
    assert m.compute_max_speed_no_deflux(m.kt_q_art * m.iq_nominal) < m.w_max_no_load


def test_reduction():
    # Make sure that the reduction ratio rho works as intended
    m = DEFAULT_LIBRARY["MyActuator RMD-X6 V2"]
    m.update_constants(reduction_ratio=1.0)
    a = copy.copy(DEFAULT_LIBRARY["MyActuator RMD-X6 V2"])
    rho = 42.2
    a.update_constants(reduction_ratio=rho)

    # Check the parameters
    assert m.R == pytest.approx(a.R)
    assert m.L == pytest.approx(a.L)
    assert m.ke == pytest.approx(a.ke)
    assert m.iq_max == pytest.approx(a.iq_max)
    assert m.np == pytest.approx(a.np)
    assert m.U == pytest.approx(a.U)
    assert m.rho == pytest.approx(1)
    assert a.rho == pytest.approx(rho)

    # Check the derived constants
    assert a.kt_q_art == pytest.approx(rho * m.kt_q_art)
    assert a.K_m_art == pytest.approx(rho * m.K_m_art)
    assert a.w_max_no_load == pytest.approx(m.w_max_no_load / rho)
    assert a.w_max_at_max_torque == pytest.approx(m.w_max_at_max_torque / rho)
    # Maximum speed is not exactly linear in reduction ratio, due to the inductive effect.
    assert a.compute_max_speed_no_deflux(0.1) == pytest.approx(
        m.compute_max_speed_no_deflux(0.1) / rho, 0.05
    )

    # Check conservation of power
    assert m.nominal_power == pytest.approx(a.nominal_power)
