import time

import camera
import gpio_driver
from dual_motor_threading import weighted_move

# Defines proportional constant

MIN_STEPS = 4

BASE_MOVE_COUNT = 2
K_P = 0.01


def main() -> None:

    gpio_driver.board_setup("BCM")

    while True:

        try:

            x_error, y_error = camera.find_line(True)

            print(f"X: {x_error}\nY: {y_error}\n")

            x_error_scaled = int(x_error * K_P)

            num_steps = (
                (BASE_MOVE_COUNT + x_error_scaled) * MIN_STEPS,
                (BASE_MOVE_COUNT - x_error_scaled) * MIN_STEPS,
            )

            print(f"Number of Steps: {num_steps}")

            time.sleep(0.1)
            #             # Moves
            weighted_move(num_steps, delay=0.01)

        except KeyboardInterrupt:

            gpio_driver.board_cleanup()
            break

    # gpio_driver.board_cleanup()


# def main():

#     gpio_driver.board_setup("BCM")
#     sensor = APDS()

#     ON_COLOR = RED

#     RIGHT_TURN_WEIGHT = 1
#     LEFT_TURN_WEIGHT = 4

#     BASE_STEP_COUNT = 4

#     # Defines correctional limits
#     LOW_CORRECT_LIMIT = int(BASE_STEP_COUNT * 0.7)
#     HIGH_CORRECT_LIMIT = int(BASE_STEP_COUNT * 1.3)

#     try:

#         step_weights = BASE_STEP_COUNT

#         while True:
#             # Acquires color data from sensor
#             color = sensor.get_color()
#             print(f"Adjusted color: {color}")
#             # Finds error from correct color
#             color_error = find_error(color, ON_COLOR) * K_P
#             print(f"Color Error: {color_error}")
#             # RIDES LEFT SIDE OF LINE
#             # Guides right if error is high
#             if color_error > 30:
#                 step_weights -= RIGHT_TURN_WEIGHT
#             # Guides left if color error is low
#             elif color_error < 15:
#                 step_weights += LEFT_TURN_WEIGHT

#             # Corrects out-of-range values
#             if step_weights < LOW_CORRECT_LIMIT:
#                 step_weights = LOW_CORRECT_LIMIT
#             elif step_weights > HIGH_CORRECT_LIMIT:
#                 step_weights = HIGH_CORRECT_LIMIT
#             print(f"Step Weights: {step_weights}")
#             # Converts weights into discrete step values
#             step_nums = (step_weights, 2 * BASE_STEP_COUNT - step_weights)
#             print(f"Step nums: {step_nums}")

#             time.sleep(0.1)
#             # Moves
#             weighted_move(step_nums, delay=0.01)

#     except KeyboardInterrupt:

#         gpio_driver.board_cleanup()


# def find_error(color: tuple[int, ...], base: tuple[int, ...]) -> float:
#     """
#     Finds an error value between the base and provided color.
#     """
#     # Finds number of channels
#     num_channels = range(len(base))
#     # Finds the differences between channels
#     differences = (abs(base[i] - color[i]) for i in num_channels)
#     # Sums the differences and rounds
#     return round(sum(differences), 3)


if __name__ == "__main__":
    main()
