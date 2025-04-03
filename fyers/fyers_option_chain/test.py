import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

# Simulating the time and data
time_stamps = ['09:15', '09:42', '10:00', '10:27', '10:54', '11:21', '11:48', '12:15', '12:42', '13:09', '13:27']
ce_oi_change = [5, 20, 30, 50, 60, 70, 80, 95, 110, 125, 140]  # Call OI Change in crores
pe_oi_change = [2, 15, 25, 40, 55, 65, 75, 90, 100, 115, 130]  # Put OI Change in crores
price = [23310, 23320, 23330, 23340, 23350, 23360, 23370, 23380, 23390, 23400, 23410]  # Nifty price in points

# Convert time to a format matplotlib understands (HH:MM format to datetime)
time_stamps = [f'2025-04-03 {t}' for t in time_stamps]
time_stamps = [np.datetime64(t) for t in time_stamps]

# Set up the figure and axis
fig, ax1 = plt.subplots(figsize=(14, 8))

# Bar Chart for OI Change for CE and PE
ax1.bar(time_stamps, ce_oi_change, width=0.03, label="CE OI Change", color='green', alpha=0.7)
ax1.bar(time_stamps, pe_oi_change, width=0.03, label="PE OI Change", color='red', alpha=0.7, bottom=ce_oi_change)

# Adding a second y-axis for price
ax2 = ax1.twinx()

# Plotting the lines (Red and Blue dotted lines)
ax2.plot(time_stamps, ce_oi_change, 'r-', label="CE OI Change", linewidth=2)
ax2.plot(time_stamps, pe_oi_change, 'b:', label="PE OI Change", linewidth=2)
ax2.plot(time_stamps, price, 'b-.', label="Price", linewidth=2)

# Formatting the axes
ax1.set_xlabel('Time')
ax1.set_ylabel('OI Change (Crores)', color='black')
ax2.set_ylabel('Price (NIFTY)', color='blue')

# Formatting the time axis to show hour:minute
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))

# Title and legends
ax1.set_title("OI Change Chart NIFTY", fontsize=16, weight='bold')
ax1.legend(loc="upper left", fontsize=12)
ax2.legend(loc="upper right", fontsize=12)

# Display CE OI Change and PE OI Change values
ax2.text(0.8, 0.95, f"CE OI Change: ₹7.74 Cr", transform=ax2.transAxes, fontsize=12, color="green")
ax2.text(0.8, 0.90, f"PE OI Change: ₹10.61 Cr", transform=ax2.transAxes, fontsize=12, color="red")

# Rotate time labels for better readability
plt.xticks(rotation=45)

# Show the plot
plt.tight_layout()
plt.show()
