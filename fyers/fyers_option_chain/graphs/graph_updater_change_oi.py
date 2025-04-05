import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import mplcursors
from datetime import datetime,timedelta
import matplotlib.pyplot as plt
import mplcursors
from matplotlib.animation import FuncAnimation
import matplotlib.ticker as ticker
from data_fetcher import *
import numpy as np

class RealTimeGraph:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.x_data = []  # This will store datetime objects
        self.call_oi_change_data = []
        self.put_oi_change_data = []

        # Line style customization
        self.call_oi_change_line, = self.ax.plot([], [], label="Change in Call OI", linestyle='-', color='blue', lw=2, markersize=8, markerfacecolor='blue')
        self.put_oi_change_line, = self.ax.plot([], [], label="Change in Put OI", linestyle='-', color='red', lw=2, markersize=8, markerfacecolor='red')

        # Cursor for hover functionality
        self.cursor = mplcursors.cursor([self.call_oi_change_line, self.put_oi_change_line], hover=True)
        self.cursor.connect("add", self.on_hover)
        self.cursor.connect("remove", self.on_remove)

        self.tooltip = None

        # Set up the x-axis to display time
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # Format as HH:MM
        self.ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))  # Tick every 5 minutes

    def update_graph(self, data):
        """Update the graph with new data."""
        # Append new timestamp and change in OI data
        current_time = datetime.now()  # Use datetime object
        self.x_data.append(current_time)
        self.call_oi_change_data.append(data['callOiChange'])
        self.put_oi_change_data.append(data['putOiChange'])

        # Limit the data size for better performance
        if len(self.x_data) > 50:
            self.x_data.pop(0)
            self.call_oi_change_data.pop(0)
            self.put_oi_change_data.pop(0)

        # Update the data for each line
        self.call_oi_change_line.set_data(self.x_data, self.call_oi_change_data)
        self.put_oi_change_line.set_data(self.x_data, self.put_oi_change_data)

        # Adjust y-axis limits based on the changes in OI
        max_change = max(max(self.call_oi_change_data), max(self.put_oi_change_data))
        min_change = min(min(self.call_oi_change_data), min(self.put_oi_change_data))

        # Set y-axis limits with some margin
        self.ax.set_ylim(min_change - abs(min_change * 0.1), max_change + abs(max_change * 0.1))

        # Re-draw the figure
        self.ax.relim()  # Recalculate axis limits
        self.ax.autoscale_view()  # Autoscale the view

        self.ax.legend(loc="upper left")
        self.ax.set_xlabel('Time', fontsize=14, fontweight='bold')
        self.ax.set_ylabel('Change in Open Interest (OI)', fontsize=14, fontweight='bold')
        self.ax.set_title('Real-time Change in OI Data', fontsize=16, fontweight='bold')

        # Rotate the x-axis labels for better visibility
        self.fig.autofmt_xdate()  # Automatically format x-axis labels to prevent overlap

        # Set the x-ticks manually to ensure correct alignment with data points
        self.ax.set_xticks(self.x_data[::5])  # Set x-ticks at every 5th point for better visibility

        self.fig.canvas.draw()  # Redraw the figure

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

        call_oi_change_value = self.call_oi_change_data[index]
        put_oi_change_value = self.put_oi_change_data[index]

        tooltip_text = (
            f"CE OI Change: {call_oi_change_value:,.0f}\n"
            f"PE OI Change: {put_oi_change_value:,.0f}\n"
        )

        if self.tooltip is None:
            self.tooltip = sel.annotation

        sel.annotation.set_text(tooltip_text)
        sel.annotation.set_visible(True)  # Make sure the tooltip is visible

    def on_remove(self, sel):
        """Clear the tooltip when the hover is removed."""
        if self.tooltip:
            self.tooltip.set_visible(False)  # Hide the tooltip

    def fetch_and_update(self, data_fetcher):
        """Fetch the data and update the graph immediately."""
        data = data_fetcher.fetch_option_chain_data()

        if data:
            call_oi_change = 0
            put_oi_change = 0
            call_oi = data.get('callOi', 0)
            put_oi = data.get('putOi', 0)
            print(f"response - 'callOi': {call_oi}")
            print(f"response - 'putOi': {put_oi}")
            print("------------")

            for option in data.get('optionsChain', []):
                option_type = option.get('option_type')
                oi_change = option.get('oich', 0)  # Change in open interest for this specific option

                if option_type == 'CE':  # Call option
                    call_oi_change += oi_change
                elif option_type == 'PE':  # Put option
                    put_oi_change += oi_change

            print(f"Processed - 'callOiChange': {call_oi_change}")
            print(f"Processed - 'putOiChange': {put_oi_change}")
            print("---------------------------")
            # Update the graph with new data
            self.update_graph({
                'callOiChange': call_oi_change,
                'putOiChange': put_oi_change
            })

    def start_real_time_update(self, data_fetcher):
        """Start the real-time update, checking for new data and updating the graph."""
        while True:
            self.fetch_and_update(data_fetcher)
            plt.pause(4)  # Small pause to allow the plot to update
