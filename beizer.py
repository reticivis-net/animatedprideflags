import bezier
import numpy as np
import seaborn
import matplotlib.pyplot as plt

nodes1 = np.asfortranarray([
    [0, .5, .5, 1],
    [0, 0, 1, 1],
])
curve1 = bezier.Curve.from_nodes(nodes1)
# intersections = curve1.intersect(curve2)
# s_vals = np.asfortranarray(intersections[0, :])
# points = curve1.evaluate_multi(s_vals)

seaborn.set()

ax = curve1.plot(num_pts=256)
# lines = ax.plot(
#     points[0, :], points[1, :],
#     marker="o", linestyle="None", color="black")
_ = ax.axis("scaled")

plt.show()
