import matplotlib.pyplot as plt
import mplcursors
from matplotlib.animation import FuncAnimation
import matplotlib.ticker as ticker
from data_fetcher import *
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import mplcursors
from datetime import datetime,timedelta


class RealTimeGraph:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.x_data = []  # This will store datetime objects
        self.call_oi_data = []  # Total Call OI
        self.put_oi_data = []  # Total Put OI

        # Line style customization
        self.call_oi_line, = self.ax.plot([], [], label="Call OI", linestyle='-', color='blue', lw=2, markersize=8, markerfacecolor='blue')
        self.put_oi_line, = self.ax.plot([], [], label="Put OI", linestyle='-', color='red', lw=2, markersize=8, markerfacecolor='red')

        # Cursor for hover functionality
        self.cursor = mplcursors.cursor([self.call_oi_line, self.put_oi_line], hover=True)
        self.cursor.connect("add", self.on_hover)
        self.cursor.connect("remove", self.on_remove)

        self.tooltip = None

        # Set up the x-axis to display time
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # Format as HH:MM
        self.ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))  # Tick every 5 minutes

    def update_graph(self, data):
        """Update the graph with new data."""
        # Append new timestamp and OI data
        current_time = datetime.now()  # Use datetime object
        self.x_data.append(current_time)
        self.call_oi_data.append(data['callOi'])
        self.put_oi_data.append(data['putOi'])

        # Limit the data size for better performance
        if len(self.x_data) > 50:
            self.x_data.pop(0)
            self.call_oi_data.pop(0)
            self.put_oi_data.pop(0)

        # Update the data for each line
        self.call_oi_line.set_data(self.x_data, self.call_oi_data)
        self.put_oi_line.set_data(self.x_data, self.put_oi_data)

        # Adjust y-axis limits based on the OI data
        max_oi = max(max(self.call_oi_data), max(self.put_oi_data))
        min_oi = min(min(self.call_oi_data), min(self.put_oi_data))

        # If the data range is too small (e.g., it's in a range of hundreds), expand the y-axis range
        padding = max_oi * 0.05  # 5% padding of the maximum value

        # Set y-axis limits with some margin to ensure the graph is readable
        self.ax.set_ylim(min_oi - padding, max_oi + padding)

        # Re-draw the figure
        self.ax.relim()  # Recalculate axis limits
        self.ax.autoscale_view()  # Autoscale the view

        self.ax.legend(loc="upper left")
        self.ax.set_xlabel('Time', fontsize=14, fontweight='bold')
        self.ax.set_ylabel('Open Interest (OI)', fontsize=14, fontweight='bold')
        self.ax.set_title('Real-time OI Data', fontsize=16, fontweight='bold')

        # Rotate the x-axis labels for better visibility
        self.fig.autofmt_xdate()  # Automatically format x-axis labels to prevent overlap

        # Set the x-ticks manually to ensure correct alignment with data points
        self.ax.set_xticks(self.x_data[::5])  # Set x-ticks at every 5th point for better visibility

        # Manually format the y-ticks for better readability (display full numbers)
        self.ax.tick_params(axis='y', labelsize=10)
        self.ax.set_yticklabels([f'{int(label):,}' for label in self.ax.get_yticks()])  # Format y-ticks with commas

        self.fig.canvas.draw()  # Redraw the figure

    def on_hover(self, sel):
        """Display the data when hovering over a point on the graph."""
        label = sel.artist.get_label()  # Get the label of the line
        x_value = sel.target[0]  # This is the x-coordinate of the hovered point

        # Find the closest index to the hovered x_value
        try:
            index = self.find_closest_index(x_value)
        except Exception as e:
            print(f"Error finding closest index: {e}")
            return

        # Ensure valid index before accessing the data
        if index >= len(self.x_data):
            print(f"Invalid index: {index}")
            return

        call_oi_value = self.call_oi_data[index]
        put_oi_value = self.put_oi_data[index]

        tooltip_text = (
            f"Call OI: {call_oi_value:,.0f}\n"
            f"Put OI: {put_oi_value:,.0f}\n"
        )

        if self.tooltip is None:
            self.tooltip = sel.annotation

        sel.annotation.set_text(tooltip_text)
        sel.annotation.set_visible(True)  # Make sure the tooltip is visible

    def on_remove(self, sel):
        """Clear the tooltip when the hover is removed."""
        if self.tooltip:
            self.tooltip.set_visible(False)  # Hide the tooltip

    def find_closest_index(self, value):
        """Find the index of the closest value in self.x_data."""
        # Get the x-axis limits (which are in float form) and map the hover x-value to datetime
        x_min, x_max = self.ax.get_xlim()  # Get the current x-axis limits (time range)
        x_range = (x_max - x_min)  # Get the total range of x-values in float
        time_range = (self.x_data[-1] - self.x_data[0]).total_seconds()  # Calculate total time range

        # Calculate the scale between datetime and float
        scale = time_range / x_range

        # Convert the float x-value (from hover) back to a datetime object
        time_diff = (value - x_min) * scale  # Convert to time difference in seconds
        target_time = self.x_data[0] + timedelta(seconds=time_diff)  # Add the time difference to the start time

        # Find the closest index
        time_diffs = np.abs(np.array([t - target_time for t in self.x_data], dtype='timedelta64[s]'))
        closest_index = np.argmin(time_diffs)  # Find the index with the smallest time difference
        return closest_index

    def fetch_and_update(self, data_fetcher):
        """Fetch the data and update the graph immediately."""
        data = data_fetcher.fetch_option_chain_data()

        if data:
            call_oi = data.get('callOi', 0)
            put_oi = data.get('putOi', 0)

            # Update the graph with new data
            self.update_graph({
                'callOi': call_oi,
                'putOi': put_oi
            })

    def start_real_time_update(self, data_fetcher):
        """Start the real-time update, checking for new data and updating the graph."""
        while True:
            self.fetch_and_update(data_fetcher)
            plt.pause(0.1)  # Small pause to allow the plot to update





