# ui/widgets/plot_widget.py
"""
Custom plot widget using PyQtGraph
"""
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import numpy as np


class PlotWidget(pg.PlotWidget):
    """Enhanced plot widget for DSP visualization"""
    
    def __init__(self, title: str = "", x_label: str = "", y_label: str = ""):
        super().__init__()
        
        # Configure plot
        self.setLabel('left', y_label)
        self.setLabel('bottom', x_label)
        self.setTitle(title)
        
        # Set background color
        self.setBackground('#020617')
        
        # Configure axis text color
        axis_color = '#cbd5e1'
        self.getAxis('left').setPen(axis_color)
        self.getAxis('bottom').setPen(axis_color)
        self.getAxis('left').setTextPen(axis_color)
        self.getAxis('bottom').setTextPen(axis_color)
        
        # Configure grid
        self.showGrid(x=True, y=True, alpha=0.3)
        
        # Enable antialiasing for better quality
        self.setAntialiasing(True)
        
        # Store plot items
        self.plot_items = []
        
        # Enable auto range
        self.enableAutoRange()
        
        # Set default view range
        self.setXRange(0, 1)
        self.setYRange(-1.5, 1.5)
    
    def plot(self, x_data: np.ndarray, y_data: np.ndarray, clear: bool = True, 
             color: str = '#3b82f6', pen_width: float = 2.0, 
             symbol: str = None, symbol_size: int = 5):
        """
        Plot data on the widget
        
        Args:
            x_data: X-axis data
            y_data: Y-axis data
            clear: Clear existing plots
            color: Line color
            pen_width: Line width
            symbol: Symbol type ('o', 's', 't', etc.)
            symbol_size: Symbol size in pixels
        """
        if clear:
            self.clear()
            self.plot_items = []
        
        # Create pen
        pen = pg.mkPen(color=color, width=pen_width)
        
        # Create symbol brush
        symbol_brush = pg.mkBrush(color=color)
        
        # Plot data using plotItem
        if symbol:
            plot = self.plotItem.plot(x_data, y_data, pen=pen, symbol=symbol, 
                           symbolSize=symbol_size, symbolBrush=symbol_brush)
        else:
            plot = self.plotItem.plot(x_data, y_data, pen=pen)
        
        self.plot_items.append(plot)
        
        # Auto-range
        self.autoRange()
    
    def stem_plot(self, x_data: np.ndarray, y_data: np.ndarray, clear: bool = True,
                  color: str = '#60a5fa', stem_width: float = 2.0, 
                  marker_size: int = 8):
        """
        Create a stem plot (discrete frequency component visualization)
        
        Args:
            x_data: X-axis data (frequencies)
            y_data: Y-axis data (magnitudes)
            clear: Clear existing plots
            color: Color for stems and markers
            stem_width: Width of stem lines
            marker_size: Size of marker circles at stem tops
        """
        if clear:
            self.clear()
            self.plot_items = []
        
        # Create stem pen and brush
        stem_pen = pg.mkPen(color=color, width=stem_width)
        marker_brush = pg.mkBrush(color=color)
        
        # Draw vertical lines (stems) from zero to each data point
        for x, y in zip(x_data, y_data):
            if y > 0:  # Only draw positive values
                line = pg.PlotCurveItem(
                    x=[x, x], 
                    y=[0, y],
                    pen=stem_pen
                )
                self.addItem(line)
                self.plot_items.append(line)
        
        # Add circle markers at the top of each stem
        scatter = pg.ScatterPlotItem(
            x=x_data, 
            y=y_data, 
            size=marker_size,
            brush=marker_brush,
            pen=pg.mkPen(None)
        )
        self.addItem(scatter)
        self.plot_items.append(scatter)
        
        # Auto-range
        self.autoRange()
    
    def add_scatter(self, x_data: np.ndarray, y_data: np.ndarray, 
                    color: str = '#ef4444', size: int = 10):
        """Add scatter points to the plot"""
        scatter = pg.ScatterPlotItem(x=x_data, y=y_data, size=size, 
                                     brush=pg.mkBrush(color))
        self.addItem(scatter)
        self.plot_items.append(scatter)
    
    def add_vertical_line(self, x_position: float, color: str = '#f59e0b', 
                          label: str = None):
        """Add a vertical line at specified x position"""
        line = pg.InfiniteLine(pos=x_position, angle=90, pen=pg.mkPen(color=color, width=2))
        if label:
            text = pg.TextItem(text=label, color=color, anchor=(0, 1))
            text.setPos(x_position, self.getAxis('left').range[1])
            self.addItem(text)
        self.addItem(line)
        self.plot_items.append(line)
    
    def add_horizontal_line(self, y_position: float, color: str = '#f59e0b',
                            label: str = None):
        """Add a horizontal line at specified y position"""
        line = pg.InfiniteLine(pos=y_position, angle=0, pen=pg.mkPen(color=color, width=2))
        if label:
            text = pg.TextItem(text=label, color=color, anchor=(1, 0))
            text.setPos(self.getAxis('bottom').range[0], y_position)
            self.addItem(text)
        self.addItem(line)
        self.plot_items.append(line)
    
    def clear(self):
        """Clear all plot items"""
        for item in self.plot_items:
            self.removeItem(item)
        self.plot_items = []
    
    def set_background_color(self, color: str):
        """Set plot background color"""
        self.setBackground(color)
    
    def enable_log_scale(self, x: bool = False, y: bool = True):
        """Enable logarithmic scale for axes"""
        if y:
            self.setLogMode(x, y)
    
    def set_limits(self, x_min: float = None, x_max: float = None,
                   y_min: float = None, y_max: float = None):
        """Set axis limits"""
        if x_min is not None and x_max is not None:
            self.setXRange(x_min, x_max)
        if y_min is not None and y_max is not None:
            self.setYRange(y_min, y_max)
    
    def add_legend(self, labels: list):
        """Add legend to the plot"""
        legend = self.addLegend()
        for plot_item, label in zip(self.plot_items, labels):
            legend.addItem(plot_item, label)