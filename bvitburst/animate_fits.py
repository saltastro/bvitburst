
import sys
import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
import matplotlib.animation as animation

hdu = fits.open(sys.argv[1])

fig = plt.figure()

ims = []

def f(x, y):
    return np.sin(x) + np.cos(y)

x = np.linspace(0, 2 * np.pi, 120)
y = np.linspace(0, 2 * np.pi, 100).reshape(-1, 1)

im = plt.imshow(hdu[1].data, cmap=plt.get_cmap('jet'), vmax=50)

def updatefig(*args):
    i = args[0]%(len(hdu)-1)+1
     
    im.set_array(hdu[i].data)
    return im,

plt.xticks([])
plt.yticks([])

ani = animation.FuncAnimation(fig, updatefig, interval=50, blit=False, repeat=False)
ani.save('im.mp4', metadata={'artist':'S. Crawford'})
#plt.show()
