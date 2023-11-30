#!/usr/bin/env python
"""
# Stepper Driver
Allows for the control of a single stepper motor. step() function 
allows for customization of stepping sequence, direction, duration, and speed 
of motor. Includes a full and half-step sequence as well as single or offset 
stepping options.
"""

import time
from itertools import permutations
from threading import Thread

import RPi.GPIO as GPIO

__author__ = "Ben Kraft"
__copyright__ = "None"
__credits__ = "Ben Kraft"
__license__ = "MIT"
__version__ = "0.2.0"
__maintainer__ = "Ben Kraft"
__email__ = "ben.kraft@rcn.com"
__status__ = "Prototype"

TOTAL_STEPS = 200

MINIMUM_STAGE_DELAY = 0.005

DEFAULT_RPM = 60


# Defines motor spin directions
class Directions:
    """
    Establishes existing motor directions.
    """

    CLOCKWISE = 1
    COUNTER_CLOCKWISE = -1


class Sequence:
    """
    A class for stepper motor sequences. Consist of 4-integer motor "stages".
    """

    def __init__(
        self,
        stages: list[tuple[int, int, int, int]],
        step_size: int = 1,
    ) -> None:
        # Assigns members
        self._stages = stages
        self._step_size = step_size
        self._length = len(stages)

    def get_stages(self) -> list[tuple[int, int, int, int]]:
        """
        Returns sequences stages.
        """
        return self._stages

    def get_length(self) -> int:
        """
        Returns sequences length.
        """
        return self._length

    def get_step_size(self) -> int:
        """
        Returns sequences length.
        """
        return self._step_size

    def _orient(self, direction: int) -> None:
        """
        Orients sequence in direction.
        """
        self._stages = self._stages[::direction]

    def _encompass(self, num_steps: int) -> None:
        """
        Extends/restricts sequence to fit number of steps.
        """
        # Divides number of specified steps by number of steps in sequence
        multiplier, remainder = divmod(num_steps, (self._length // self._step_size))
        # Prints warning if needed
        if remainder:
            print(
                f"WARNING: Number of steps ({num_steps}) not factor of sequence \
                  ({len(self._stages)}). Future steps might mis-align."
            )
        # Creates shorter version of sequence up to the remainder number of stages
        remainder_stages = self._stages[: (remainder * self._step_size)]
        # Builds a long sequence from "multiplier" number of sequences and remainder
        self._stages = self._stages * multiplier + remainder_stages


class Sequences:
    """
    Establishes existing stepper motor sequences.
    """

    FULLSTEP = Sequence(
        stages=[
            (1, 0, 0, 1),
            (1, 1, 0, 0),
            (0, 1, 1, 0),
            (0, 0, 1, 1),
        ]
    )
    HALFSTEP = Sequence(
        stages=[
            (1, 0, 0, 1),
            (1, 0, 0, 0),
            (1, 1, 0, 0),
            (0, 1, 0, 0),
            (0, 1, 1, 0),
            (0, 0, 1, 0),
            (0, 0, 1, 1),
            (0, 0, 0, 1),
        ],
        step_size=2,
    )
    WAVESTEP = Sequence(
        stages=[
            (1, 0, 0, 0),
            (0, 1, 0, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 1),
        ]
    )
    LOCK = Sequence([(1, 0, 0, 1)])
    UNLOCK = Sequence([(0, 0, 0, 0)])


class Motor:
    """
    A class for stepper motors. Consists of four pin numbers.
    """

    def __init__(self, pins: tuple[int, int, int, int]) -> None:
        # Checks number of pins
        if len(pins) != 4:
            raise ValueError("Motor must consist of four integer pins!")
        # Sets all motor pins to output and disengages them
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)  # type: ignore
            GPIO.output(pin, False)  # type: ignore
        # Creates member
        self._pins = pins

    def get_pins(self) -> tuple[int, int, int, int]:
        """
        Returns pin numbers.
        """
        return self._pins


class _MotorThread(Thread):
    """
    Allows for motor objects to be used concurrently in threads. `_MotorThread`
    can be passed any motor object, as well as a number of steps, a direction,
    a sequnce, and a delay. Optional flag to show start/stop of thread.
    """

    def __init__(
        self,
        motor: Motor,
        num_steps: int,
        direction: int = Directions.CLOCKWISE,
        sequence: Sequence = Sequences.HALFSTEP,
        rpm: float = DEFAULT_RPM,
        flag: bool = False,
    ):
        Thread.__init__(self)
        self.motor = motor
        self.num_steps = num_steps
        self.direction = direction
        self.sequence = sequence
        self.rpm = rpm
        self.flag = flag

    def run(self):
        """
        Starts motor thread.
        """
        if self.flag:
            print(f"Starting {self.name}. . .")
        step_motor(
            self.motor,
            self.num_steps,
            self.direction,
            self.sequence,
            self.rpm,
        )
        if self.flag:
            print(f"Stopping {self.name}. . .")


def step_motors(
    motors: list[Motor],
    num_steps: list[int],
    directions: list[int],
    sequence: Sequence = Sequences.HALFSTEP,
    rpm: float = DEFAULT_RPM,
    flag: bool = False,
) -> None:
    """
    Allows for motors to run a specified number of steps to be run in a
    direction using a sequence of custom stage delay.
    """
    # Counts the number of motors being used
    num_motors = len(motors)
    # Checks list lengths to be the same size
    if num_motors != len(directions) or num_motors != len(num_steps):
        raise ValueError(
            "Lists of motors, directions, and steps must all be of equal size!"
        )
    # Initializes threads list
    threads: list[_MotorThread] = []
    # For each motor:
    for i in range(num_motors):
        # Creates a thread for the motor
        thread = _MotorThread(
            motors[i],
            num_steps[i],
            directions[i],
            sequence,
            rpm,
            flag,
        )
        # Adds thread to list
        threads.append(thread)
        # Starts thread
        thread.start()
    # Displays start of threads
    if flag:
        print("All motor threads started.")
    # For each thread:
    for thread in threads:
        # Wait for all threads to finish
        thread.join()
    # Displays end of threads
    if flag:
        print("All motor threads joined.")


def step_motor(
    motor: Motor,
    num_steps: int,
    direction: int,
    sequence: Sequence = Sequences.HALFSTEP,
    rpm: float = DEFAULT_RPM,
) -> None:
    """
    Allows for a specified number of steps to be run in a direction using a
    sequence of custom stage delay.
    """
    if abs(direction) != 1:
        raise ValueError("Direction must be equal to 1 or -1!")
    # Calculates delay from rpm and sequence attributes
    delay = 1 / (rpm * TOTAL_STEPS * sequence.get_step_size())
    # Raises error if delay is too small
    if delay < MINIMUM_STAGE_DELAY:
        raise ValueError(
            f"Too small of delay. Must be equal to or larger than {MINIMUM_STAGE_DELAY}s!"
        )
    # Returns early if there are no steps.
    if not num_steps:
        return
    # Flips direction if number of steps is negative
    elif num_steps < 0:
        num_steps *= -1
        direction *= -1

    # Gets motor pins from motor
    motor_pins = motor.get_pins()
    # Makes a copy of the input sequence to manipulate
    adjusted_sequence = Sequence(sequence.get_stages())
    # Orients sequence
    adjusted_sequence._orient(direction)
    # Fits sequence to number of steps
    adjusted_sequence._encompass(num_steps)
    # For each stage in sequence
    for stage in adjusted_sequence.get_stages():
        # For each pin level in stage
        for index, level in enumerate(stage):
            # Sets motor pin to specified level
            GPIO.output(motor_pins[index], bool(level))  # type: ignore
        # Delays between stages
        time.sleep(delay)


def board_setup(mode: str = "BCM") -> None:
    """
    Sets up board mode and motor pins. Mode is BCM (GPIO pin numbers) or BOARD
    (processor pin numbers).
    """
    # Sets board mode
    if mode == "BCM":
        GPIO.setmode(GPIO.BCM)  # type:ignore
    elif mode == "BOARD":
        GPIO.setmode(GPIO.BOARD)  # type: ignore
    else:
        raise ValueError("Use 'BCM' or 'BOARD' modes.")


def board_cleanup() -> None:
    """
    Turns off any pins left on.
    """
    GPIO.cleanup()  # type: ignore


def test_pins(
    motor: Motor,
    num_steps: int = 0,
    sequence: Sequence = Sequences.HALFSTEP,
    delay: float = MINIMUM_STAGE_DELAY,
    spacing: float = 0.5,
) -> None:
    """
    Runs stepping sequence on all possible permutations of given pin list in
    order to find correct stepper wiring. Normal `step_motor()` arguments,
    `spacing` determines duration beween tests. `num_steps` is set to length
    of sequence if left at 0. Keyboard interupt will print last permutation.
    """
    # Sets number of steps to length of sequence if not specified
    if not num_steps:
        num_steps = sequence.get_length()
    # Creates a list of all possible pin permutations
    pin_permutations = list(permutations(motor.get_pins(), 4))
    # Initializes a current order
    current_order: tuple[int, ...] = ()
    try:
        # For each permutation:
        for pin_order in pin_permutations:
            # Sets current order
            current_order = pin_order
            # Prints pin order
            print(f"Current permutation: {current_order}")
            # Runs motor for runtime
            step_motor(Motor(current_order), num_steps, Directions.CLOCKWISE, sequence, delay)  # type: ignore
            # Waits between permutations
            time.sleep(spacing)
    # Catches keyboard interupt
    except KeyboardInterrupt:
        # Reports last pin order
        print(f"\nLast pin permutation: {current_order}")


# Runs main only from command line call instead of library call
if __name__ == "__main__":
    print("Use me as a library!")
