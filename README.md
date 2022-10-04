
<div align="center">
  <a href="#"><img width="400px" height="auto" src="https://raw.githubusercontent.com/matthieuvigne/nemo_bldc/main/src/nemo_bldc/ressources/logo_readme.svg"></a>
</div>

____

In drones or in robotics, brushless motors are becoming more and more common. However, choosing the right motor for the right application can be quite difficult. Indeed, understanding datasheets can be quite complexe: is a motor with a no-load speed of 5000rpm more powerful that one with the same torque, but specified for 3000rpm at max torque? How do you compare a motor with a KV of 500 rpm/V with one with a Kt of 0.5Nm/Arms? And what do these value even mean? Sometimes you might feel like nobody can answer - well now, **Nemo** can!

**Nemo** is a *Nifty Evaluator for MOtors* - more practically, it is a tool to compare brushless motors (PMSM). While the choice of the "best" motor ultimately depends on the application, **Nemo** will help you in making a fair comparison between motors from various manufacturers, to truly understand their limit. It also offers a simulation of a basic Field Oriented Control (FOC) controller, which can be used to easily configure the gains of the various feedback loops.

Let's take an example: [My Actuator](https://www.myactuator.com/)'s pancake motors. How does the old [RMD-L-7025](https://www.myactuator.com/product-page/rmd-l-7025), equipped with a 1:6 gearbox, compare to the newer [RMD-X6 1:6](https://www.myactuator.com/product-page/rmd-x6). Well, here are the motor's characteristics (torque-speed curve) and specs for a direct comparison:

<img src="https://raw.githubusercontent.com/matthieuvigne/nemo_bldc/main/src/nemo_bldc/doc/Figures/overview.png" width="100.0%"/>

**Nemo** can be used to:

  - compare motors from different manufacturers and choose the best for a given application
  - obtain detailed information about a motor, like output power, efficiency, required battery current... that may not be available on the datasheet
  - simulate motor motion with a typical FOC driver - which can come in handy when tuning the feedback gains
  - more generally, learn about brushless motors, as the [full mathematical model is detailed here](https://raw.githubusercontent.com/matthieuvigne/nemo_bldc/main/src/nemo_bldc/doc/BrushlessMotorPhysics.pdf)

Please see the [User Manual](https://raw.githubusercontent.com/matthieuvigne/nemo_bldc/main/src/nemo_bldc/doc/user_manual.pdf) for more information on the software.

<u>*Important note*</u>: **Nemo** works by using the classical linear model of non-sallient PMSM. While this model is known to be fairly accurate (being the base of Field-Oriented Control), in practice non-linear phenomenons can alter motor performance (magnetic saturation, cogging, friction...). Also, motor parameters usually vary between one unit and another (manufacturers typically guarantee them by 10%). Thus, values from the manufacturer's datasheet may differ from those given by **Nemo**: when in doubt, don't hesitate to ask the manufacturer about their datasheet. As always in engineering, remain cautious and plan system dimensioning with a reasonable margin of error.


## Installing Nemo

### Dependency: PyGObject

**Nemo** depends on PyGObject, python bindings for the GTK library. Refer to [the PyGObject documentation](https://pygobject.readthedocs.io/en/latest/getting_started.html) for instruction on how
to install it on your system.

### Python install

**Nemo** is distributed though [PyPi](https://pypi.org/project/nemo-bldc/) and can just be installed using `pip`:

```
pip install nemo_bldc
```

You can also install it from source by downloading this repo and running:

```
pip install .
```

### Windows binary

For Windows, you can simply use [this binary](https://github.com/matthieuvigne/nemo_bldc/raw/main/Nemo.exe) ; you can of course also install it in a python environment by following the above instructions.