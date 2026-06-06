import pyqtgraph as pg
import numpy as np

app = pg.mkQApp()

n = 1_000_000

x = np.random.rand(n)
y = np.random.rand(n)

w = pg.PlotWidget()
w.show()

scatter = pg.ScatterPlotItem(
    x=x,
    y=y,
    size=2,
    pen=None,
    brush='w'
)

w.addItem(scatter)

app.exec()