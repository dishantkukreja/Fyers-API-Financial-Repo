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

        # Line style customization
        self.call_oi_line, = self.ax.plot([], [], label="Call OI", linestyle='-', marker='o', color='blue', lw=2, markersize=8, markerfacecolor='blue')
        self.put_oi_line, = self.ax.plot([], [], label="Put OI", linestyle='-', marker='x', color='red', lw=2, markersize=8, markerfacecolor='red')
        self.call_oi_change_line, = self.ax.plot([], [], label="Change in Call OI", linestyle='--', color='green', lw=2, markersize=8, markerfacecolor='green')
        self.put_oi_change_line, = self.ax.plot([], [], label="Change in Put OI", linestyle='--', color='orange', lw=2, markersize=8, markerfacecolor='orange')

        # Cursor for hover functionality
        self.cursor = mplcursors.cursor([self.call_oi_line, self.put_oi_line, self.call_oi_change_line, self.put_oi_change_line], hover=True)
        self.cursor.connect("add", self.on_hover)
        self.cursor.connect("remove", self.on_remove)

        self.tooltip = None

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
        self.ax.set_xlabel('Time', fontsize=14, fontweight='bold')
        self.ax.set_ylabel('Open Interest (OI)', fontsize=14, fontweight='bold')
        self.ax.set_title('Real-time OI Data', fontsize=16, fontweight='bold')

    def find_closest_index(self, value):
        """Find the index of the closest value in self.x_data."""
        closest_index = (np.abs(np.array(self.x_data) - value)).argmin()
        return closest_index

    def on_hover(self, sel):
        """Display the data when hovering over a point on the graph."""
        # Merge all relevant data into a single tooltip box
        label = sel.artist.get_label()  # Get the label of the line
        x_value = sel.target[0]  # This is the x-coordinate of the hovered point

        # Find the closest index to the hovered x_value
        index = self.find_closest_index(x_value)

        # Gather all values to display
        call_oi_value = self.call_oi_data[index]
        put_oi_value = self.put_oi_data[index]
        call_oi_change_value = self.call_oi_change_data[index]
        put_oi_change_value = self.put_oi_change_data[index]
        # Example price (replace this with actual price data if available)
        price = 23278.5  # Replace with dynamic price if available

        tooltip_text = (
            f"CE OI Change: {call_oi_change_value:,.0f}\n"
            f"PE OI Change: {put_oi_change_value:,.0f}\n"
            f"CE OI: {call_oi_value:,.2f}\n"
            f"PE OI: {put_oi_value:,.2f}\n"
        )

        if self.tooltip is None:
            self.tooltip = sel.annotation

        # Display all data points in a single box
        sel.annotation.set_text(tooltip_text)
        sel.annotation.set_visible(True)  # Make sure the tooltip is visible

    def on_remove(self, sel):
        """Clear the tooltip when the hover is removed."""
        if self.tooltip:
            self.tooltip.set_visible(False)  # Hide the tooltip
    def animate(self, data_fetcher):
        def update(frame):
            # Fetch data using the correct method from FyersAPI
            data = data_fetcher.fetch_option_chain_data()
            print(f"Response - 'callOi': {data['callOi']}")
            print(f"Response - 'putOi': {data['putOi']}")
            print("-----")

            if data:
                # Get total open interest for call and put options directly from the response
                call_oi = data.get('callOi', 0)
                put_oi = data.get('putOi', 0)

                # Calculate change in open interest (using 'oich' from the response for individual options)
                call_oi_change = 0
                put_oi_change = 0

                # Loop through the options chain and calculate changes in OI for call and put options
                for option in data.get('optionsChain', []):
                    option_type = option.get('option_type')
                    oi_change = option.get('oich', 0)  # Change in open interest for this specific option

                    if option_type == 'CE':  # Call option
                        call_oi_change += oi_change
                    elif option_type == 'PE':  # Put option
                        put_oi_change += oi_change

                print(f"Processed - 'callOi': {call_oi}")
                print(f"Processed - 'putOi': {put_oi}")
                print(f"Processed - 'callOiChange': {call_oi_change}")
                print(f"Processed - 'putOiChange': {put_oi_change}")
                print("--------------------------------")
                
                # Update graph data with the correctly fetched and processed data
                self.update_graph({
                    'callOi': call_oi,
                    'putOi': put_oi,
                    'callOiChange': call_oi_change,
                    'putOiChange': put_oi_change
                })
                self.fig.canvas.draw()  # Redraw the figure

        ani = FuncAnimation(self.fig, update, interval=5000, cache_frame_data=False)  # Update every 5 seconds
        plt.show()

