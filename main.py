import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

font_dirs = ["./font/Inter"]
font_files = font_manager.findSystemFonts(fontpaths=font_dirs)
for font_file in font_files:
    font_manager.fontManager.addfont(font_file)

mpl.rcParams['font.family'] = "Inter"
mpl.rcParams['figure.facecolor'] = "#F5F5F5"
mpl.rcParams['axes.facecolor'] = "#F5F5F5"
mpl.rcParams['font.size'] = 14.0


def plot():
    x = np.linspace(0, 2, 100)  # Sample data.

    # Note that even in the OO-style, we use `.pyplot.figure` to create the Figure.
    fig, ax = plt.subplots(figsize=(7, 3.8), layout='constrained')
    ax.plot(x, x, label='linear')  # Plot some data on the axes.
    ax.set_xlabel('x label')  # Add an x-label to the axes.
    ax.set_ylabel('y label')  # Add a y-label to the axes.
    ax.set_title("Simple Plot")  # Add a title to the axes.
    ax.legend()  # Add a legend.
    plt.savefig('linear.png')
    plt.show()


if __name__ == '__main__':
    plot()
