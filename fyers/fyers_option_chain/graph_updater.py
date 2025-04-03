import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.ticker as ticker
from data_fetcher import *

class RealTimeGraph:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.x_data = []
        self.call_oi_data = []
        self.put_oi_data = []
        self.call_oi_change_data = []
        self.put_oi_change_data = []

    def update_graph(self, data):
        self.x_data.append(len(self.x_data) + 1)
        self.call_oi_data.append(data['callOi'])
        self.put_oi_data.append(data['putOi'])
        self.call_oi_change_data.append(data['callOiChange'])
        self.put_oi_change_data.append(data['putOiChange'])

        if len(self.x_data) > 50:  # Limit the data size for better performance
            self.x_data.pop(0)
            self.call_oi_data.pop(0)
            self.put_oi_data.pop(0)
            self.call_oi_change_data.pop(0)
            self.put_oi_change_data.pop(0)

        # Debugging: Print data for Call and Put OI
        print("Call OI Data:", self.call_oi_data[-1])
        print("Put OI Data:", self.put_oi_data[-1])

        # Plot the data
        self.ax.clear()
        self.ax.plot(self.x_data, self.call_oi_data, label="Call OI", linestyle='-', marker='o')
        self.ax.plot(self.x_data, self.put_oi_data, label="Put OI", linestyle='-', marker='x')
        self.ax.plot(self.x_data, self.call_oi_change_data, label="Change in Call OI", linestyle='--')
        self.ax.plot(self.x_data, self.put_oi_change_data, label="Change in Put OI", linestyle='--')

        # Format Y-axis labels to avoid scientific notation
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

        # Set axis limits based on the max value in the data
        self.ax.set_ylim(1e5, max(max(self.call_oi_data), max(self.put_oi_data)) * 1.1)

        self.ax.legend(loc="upper left")
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Open Interest (OI)')
        self.ax.set_title('Real-time OI Data')

    def animate(self, data_fetcher):
        def update(frame):
            # Fetch data using the correct method from FyersAPI
            data = data_fetcher.fetch_option_chain_data()
            if data:
                # Print the structure of optionsChain to debug
                print("optionsChain structure:", data.get('optionsChain'))

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

                # Print the aggregated OI values for debugging
                print("Aggregated Call OI:", call_oi)
                print("Aggregated Put OI:", put_oi)

                # Update graph data
                self.update_graph({
                    'callOi': call_oi,
                    'putOi': put_oi,
                    'callOiChange': call_oi_change,
                    'putOiChange': put_oi_change
                })

        ani = FuncAnimation(self.fig, update, interval=5000, cache_frame_data=False)  # Update every 5 seconds
        plt.show()
