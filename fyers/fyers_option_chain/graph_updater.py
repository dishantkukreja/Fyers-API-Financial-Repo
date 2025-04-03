import matplotlib.pyplot as plt
import mplcursors
from matplotlib.animation import FuncAnimation
import matplotlib.ticker as ticker
from data_fetcher import *
import numpy as np

class RealTimeGraph:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.x_data = []
        self.call_oi_data = []
        self.put_oi_data = []
        self.call_oi_change_data = []
        self.put_oi_change_data = []

        # Create lines for plotting
        self.call_oi_line, = self.ax.plot([], [], label="Call OI", linestyle='-', marker='o', color='blue', lw=2)
        self.put_oi_line, = self.ax.plot([], [], label="Put OI", linestyle='-', marker='x', color='red', lw=2)
        self.call_oi_change_line, = self.ax.plot([], [], label="Change in Call OI", linestyle='--', color='green', lw=2)
        self.put_oi_change_line, = self.ax.plot([], [], label="Change in Put OI", linestyle='--', color='orange', lw=2)

        # Cursor for hover functionality
        self.cursor = mplcursors.cursor([self.call_oi_line, self.put_oi_line, self.call_oi_change_line, self.put_oi_change_line], hover=True)
        self.cursor.connect("add", self.on_hover)
        self.cursor.connect("remove", self.on_remove)

    def update_graph(self, data):
        # Append new data
        self.x_data.append(len(self.x_data) + 1)
        self.call_oi_data.append(data['callOi'])
        self.put_oi_data.append(data['putOi'])
        self.call_oi_change_data.append(data['callOiChange'])
        self.put_oi_change_data.append(data['putOiChange'])

        # Limit the data size for better performance
        if len(self.x_data) > 50:
            self.x_data.pop(0)
            self.call_oi_data.pop(0)
            self.put_oi_data.pop(0)
            self.call_oi_change_data.pop(0)
            self.put_oi_change_data.pop(0)

        # Update the data for each line
        self.call_oi_line.set_data(self.x_data, self.call_oi_data)
        self.put_oi_line.set_data(self.x_data, self.put_oi_data)
        self.call_oi_change_line.set_data(self.x_data, self.call_oi_change_data)
        self.put_oi_change_line.set_data(self.x_data, self.put_oi_change_data)

        # Format Y-axis labels to avoid scientific notation
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

        # Set axis limits based on the max value in the data
        self.ax.set_ylim(1e5, max(max(self.call_oi_data), max(self.put_oi_data)) * 1.1)

        # Re-draw the figure
        self.ax.relim()  # Recalculate axis limits
        self.ax.autoscale_view()  # Autoscale the view

        self.ax.legend(loc="upper left")
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Open Interest (OI)')
        self.ax.set_title('Real-time OI Data')

    def find_closest_index(self, value):
        """Find the index of the closest value in self.x_data."""
        closest_index = (np.abs(np.array(self.x_data) - value)).argmin()
        return closest_index

    def on_hover(self, sel):
        """Display the data when hovering over a point on the graph."""
        label = sel.artist.get_label()  # Get the label of the line
        x_value = sel.target[0]  # This is the x-coordinate of the hovered point

        # Find the closest index to the hovered x_value
        index = self.find_closest_index(x_value)

        # Handle the hover based on the label and index
        if label == 'Call OI':
            oi_value = self.call_oi_data[index]
        elif label == 'Put OI':
            oi_value = self.put_oi_data[index]
        elif label == 'Change in Call OI':
            oi_value = self.call_oi_change_data[index]
        elif label == 'Change in Put OI':
            oi_value = self.put_oi_change_data[index]

        # Display the actual data in the tooltip
        sel.annotation.set_text(f'{label}: {oi_value:,.0f}')  # Formatted for better readability

    def on_remove(self, sel):
        """Clear the tooltip when the hover is removed."""
        sel.annotation.set_visible(False)  # Explicitly hide the tooltip when unhovering

    def animate(self, data_fetcher):
        def update(frame):
            # Fetch data using the correct method from FyersAPI
            data = data_fetcher.fetch_option_chain_data()
            if data:
                call_oi = 0
                put_oi = 0
                call_oi_change = 0
                put_oi_change = 0
                
                # Safely access 'oi' and 'prev_oi' for call and put options
                for option in data.get('optionsChain', []):
                    option_type = option.get('option_type')
                    oi = option.get('oi', 0)
                    prev_oi = option.get('prev_oi', 0)

                    if option_type == 'CE':  # Call option
                        call_oi += oi
                        call_oi_change += (oi - prev_oi)
                    elif option_type == 'PE':  # Put option
                        put_oi += oi
                        put_oi_change += (oi - prev_oi)

                # Update graph data
                self.update_graph({
                    'callOi': call_oi,
                    'putOi': put_oi,
                    'callOiChange': call_oi_change,
                    'putOiChange': put_oi_change
                })
                self.fig.canvas.draw()  # Redraw the figure

        ani = FuncAnimation(self.fig, update, interval=5000, cache_frame_data=False)  # Update every 5 seconds
        plt.show()
