import matplotlib.colors as mc
import colorsys
import numpy as np
import functools
import json

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, GdkPixbuf

from ..physics.motor import Motor

DISPLAYED_CTES = [('Km, articular', 'Nm/\u221AW', lambda m: f"{m.K_m_art:.3f}"),
                  ('', 'W /Nm\u00B2', lambda m: f"{1 / m.K_m_art**2:.3f}"),
                  ('Power (non defluxing)', 'W', lambda m: f"{m.w_max_at_max_torque * m.iq_max * m.kt_q_art:.1f}"),
                  ('Ke phase-phase', 'V/rad.s', lambda m: f"{m.ke_phasetophase:.3f}"),
                  ('', 'V/krpm', lambda m: f"{m.ke_phasetophase * 1000 * np.pi / 30:.3f}"),
                  ('KV', 'rpm/V', lambda m: f"{1 / (m.ke_phasetophase * np.pi / 30):.0f}"),
                  ('Ktq, articular', 'Nm/A', lambda m: f"{m.kt_q_art:.3f}"),
                  ('Max RMS current', 'A', lambda m: f"{m.i_rms_max:.1f}"),
                  ('Max torque, articular', 'Nm', lambda m: f"{m.tau_max:.1f}"),
                  ('No load speed, articular', 'rad/s', lambda m: f"{m.w_max_no_load:.1f}"),
                  ('', 'rpm', lambda m: f"{30 / np.pi * m.w_max_no_load:.0f}"),
                  ('Max speed @ max torque', 'rad/s', lambda m: f"{m.w_max_at_max_torque:.1f}"),
                  ('', 'rpm', lambda m: f"{30 / np.pi * m.w_max_at_max_torque:.0f}")]

def gdk_rgba_to_tuple(color: Gdk.RGBA):
    return (color.red, color.green, color.blue, color.alpha)

def mpl_to_gdk_rgba(color):
    return Gdk.RGBA(*mc.to_rgba(color))

def color_to_pixbuf(color: Gdk.RGBA):
    pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 50, 25)
    fillr = int(color.red * 255) << 24
    fillg = int(color.green * 255) << 16
    fillb = int(color.blue * 255) << 8
    fillcolor = fillr | fillg | fillb | 255
    pixbuf.fill(fillcolor)
    return pixbuf

def lighten_color(color, amount=0.5):
    """
    Lightens the given color by multiplying (1-luminosity) by the given amount.
    Input can be matplotlib color string, hex string, or RGB tuple.

    Examples:
    >> lighten_color('g', 0.3)
    >> lighten_color('#F034A3', 0.6)
    >> lighten_color((.3,.55,.1), 0.5)
    """
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])

def plot_motor_caracteristic(ax: "matplotlib.axis", motor, color, four_quadrants=False, linewidth=2, linestyle='-'):
    tau = np.arange(0, motor.tau_max, 0.01)
    w_no_deflux = np.array([motor.compute_max_speed_no_deflux(t) for t in tau] + [motor.w_max_at_max_torque, 0])
    ax.plot(w_no_deflux, list(tau) + [motor.tau_max, motor.tau_max], color=color, linewidth=linewidth, linestyle=linestyle)
    # Defluxing
    w_deflux = np.array([motor.compute_max_speed_deflux(t) for t in tau] + [motor.w_max_at_max_torque])
    ax.plot(w_deflux, list(tau) + [motor.tau_max], color=lighten_color(color), linewidth=linewidth, linestyle=linestyle)
    # 4 quandrants.
    if four_quadrants:
        ax.plot(-w_deflux, tau, color=lighten_color(color), linewidth=linewidth, linestyle=linestyle)
        ax.plot(w_deflux, -tau, color=lighten_color(color), linewidth=linewidth, linestyle=linestyle)
        ax.plot(-w_deflux, -tau, color=lighten_color(color), linewidth=linewidth, linestyle=linestyle)

        ax.plot(w_no_deflux, list(-tau) + [-motor.tau_max, -motor.tau_max], color=color, linewidth=linewidth, linestyle=linestyle)
        ax.plot(-w_no_deflux, list(tau) + [motor.tau_max, motor.tau_max], color=color, linewidth=linewidth, linestyle=linestyle)
        ax.plot(-w_no_deflux, list(-tau) + [-motor.tau_max, -motor.tau_max], color=color, linewidth=linewidth, linestyle=linestyle)


def plot_caracteristics(ax,
                        motors,
                        colors,
                        margin=0,
                        four_quadrants=False,
                        plot_nominal=True,
                        secondary_y_axes=True):
        ax.clear()

        for m, c in zip(motors, colors):
            plot_motor_caracteristic(ax, m, c, four_quadrants)
            if plot_nominal:
                m_nom = Motor(1, 1, 1, 1, 1, 1, 48, 1)
                m_nom.copy(m)
                m_nom.update_constants(iq_max = m_nom.iq_nominal)
                plot_motor_caracteristic(ax, m_nom, c, four_quadrants, 2, 'dotted')

        # Adjust range
        if len(motors) > 0:
            i_m = max([m.tau_max for m in motors])
            w_m = max([m.w_max_no_load for m in motors])
            if four_quadrants:
                ax.set_xlim([-2 * w_m, 2 * w_m])
            else:
                ax.set_xlim([-margin * w_m, 2 * w_m])
            ax.set_xlabel("Articular speed (top rad/s, bottom rpm)")
            ax.secondary_xaxis(-0.07, functions=(lambda x: x * 30 / np.pi, lambda x: x * np.pi / 30))

            if four_quadrants:
                ax.set_ylim([-1.1 * i_m, 1.1 * i_m])
            else:
                ax.set_ylim([-margin * i_m, 1.1 * i_m])
            ax.set_ylabel("Torque (Nm)")
            # Create axes
            if secondary_y_axes:
                if len(motors) == 1:
                    ax.text(-0.1, 0.4, 'Quadrature current (A)', transform=ax.transAxes, rotation=90)
                else:
                    ax.text(-0.15, -0.03, 'Quadrature current (A)', transform=ax.transAxes)
                for i, m in enumerate(motors):
                    def direct(x, m):
                        return x / m.kt_q_art
                    def inv(x, m):
                        return x * m.kt_q_art
                    sa = ax.secondary_yaxis(-0.06 -0.04 * i , functions=(functools.partial(direct, m=m), functools.partial(inv, m=m)), color=colors[i])
            ax.grid(True)

