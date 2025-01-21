import math
import numpy as np
import matplotlib.pyplot as plt
import mplcursors
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
import yaml
import time

import communicateBabylon as cb
babylon_communicator = cb.BabylonCommunicator()

class MarkerVisualizer:
    def __init__(self, config_loc, skip_rows=1):
        """Initialize the MarkerVisualizer with a CSV file."""
        self.skip_rows = skip_rows
        self.df = None
        self.fig_3d = None
        self.ax_3d = None
        self.scatter_3d = None
        self.last_hover_time = 0  # Initialize hover timestamp

        # Load the configuration file
        with open(config_loc, "r") as file:
            config = yaml.safe_load(file)

        self.marker_name = config["marker_name"]
        self.csv_file = config["csv_file_path"]
        self.use_babylon = config["use_babylon"]

    # def load_data(self):
    #     """Load the marker data from the CSV file."""
    #     self.df = pd.read_csv(self.csv_file, skiprows=self.skip_rows)
    #     if 'Frame' not in self.df.columns:
    #         raise ValueError("The CSV file must contain a 'Frame' column.")
    #     print(f"Data loaded successfully with {len(self.df)} frames.")
    def load_data(self):
        """Load the marker data from the CSV file."""
        self.df = pd.read_csv(self.csv_file, skiprows=self.skip_rows)
        if 'Frame' not in self.df.columns:
            raise ValueError("The CSV file must contain a 'Frame' column.")

        # Drop completely empty rows
        self.df = self.df.dropna(how='all')

        # Drop rows missing critical columns
        marker_columns = [col for col in self.df.columns if self.marker_name in col]
        required_columns = ['Frame'] + marker_columns
        self.df = self.df.dropna(subset=required_columns)

        # Optional: Fill missing values if required
        self.df = self.df.fillna(0)  # Replace NaN with 0 or interpolate

        # Ensure no infinite values
        self.df = self.df.replace([np.inf, -np.inf], np.nan).dropna()

        print(f"Data loaded successfully with {len(self.df)} frames.")

    def plot_marker_graph(self):
        """Plot the X, Y, and Z values of a single marker over time."""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        # Extract the selected marker's columns
        marker_columns = [col for col in self.df.columns if self.marker_name in col]
        if len(marker_columns) != 3:
            raise ValueError(f"Marker '{self.marker_name}' must have exactly 3 columns (X, Y, Z).")

        time_stamps = self.df['Frame']
        marker_positions = self.df[marker_columns].values

        # Plot the position of the selected marker over time (X, Y, Z)
        plt.figure(figsize=(10, 6))
        x_line, = plt.plot(time_stamps, marker_positions[:, 0], label='X Position')
        y_line, = plt.plot(time_stamps, marker_positions[:, 1], label='Y Position')
        z_line, = plt.plot(time_stamps, marker_positions[:, 2], label='Z Position')

        plt.title(f"Marker {self.marker_name} Position Over Time")
        plt.xlabel("Time (frames)")
        plt.ylabel("Position (units)")
        plt.legend()
        plt.grid()

        # @cursor.connect("add")
        def on_add(sel):
            current_time = time.time()
            if current_time - self.last_hover_time < 0.1:  # Throttle to 100ms
                return
            self.last_hover_time = current_time

            try:
                sel.annotation.arrow_patch.set_visible(False)  # Disable the arrow
                # sel.annotation.arrow_patch.set_connectionstyle("arc3")  # Simpler connection style

                if sel.artist is None:
                    return  # Skip invalid artists
                
                if not np.isfinite(sel.target[0]) or not np.isfinite(sel.target[1]):
                    print("Invalid cursor target:", sel.target)
                    return  # Skip invalid targets

                # Ensure the cursor interaction is within plot bounds
                if sel.target[0] < min(time_stamps) or sel.target[0] > max(time_stamps):
                    print("Cursor interaction out of bounds.")
                    return

                # Determine the index of the hovered point
                index = int(np.argmin(np.abs(time_stamps - sel.target[0])))
                if index < 0 or index >= len(time_stamps):
                    print("Index out of bounds:", index)
                    return  # Invalid index, skip update

                # Send the frame data to the Babylon server
                if self.use_babylon:
                    babylon_communicator.percentage_frame_sender(time_stamps.iloc[index]/len(time_stamps)*100)

                # Update the 3D plot with the selected marker's position
                self.update_3d_plot(index)

                # Determine the corresponding value for the hovered point
                line_label = sel.artist.get_label()
                position_value = marker_positions[index, {'X Position': 0, 'Y Position': 1, 'Z Position': 2}[line_label]]

                #  Check if position value is finite
                if not np.isfinite(position_value):
                    print("Invalid position value:", position_value)
                    return
                
                if np.nan in marker_positions[index]:
                    print("NaN value detected in marker position.")
                    return

                x_pos = sel.target[0]
                y_pos = sel.target[1]
                sel.annotation.set_text(
                    f"{line_label}\nTime: Frame {time_stamps.iloc[index]}\n"
                    f"Value: {position_value:.2f}"
                )
                sel.annotation.xy = (x_pos, y_pos)
                # sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)
            except Exception as e:
                print(f"Error updating annotation: {e}")

        # Add interactivity
        cursor = mplcursors.cursor([x_line, y_line, z_line], hover=True)
        cursor.connect("add", on_add)

        plt.show()

    def create_3d_plot(self):
        """Create the 3D plot for displaying the marker positions."""
        if self.fig_3d is None:
            self.fig_3d = plt.figure(figsize=(8, 6))
            self.ax_3d = self.fig_3d.add_subplot(111, projection='3d')
            self.ax_3d.set_xlabel("X-axis")
            self.ax_3d.set_ylabel("Y-axis")
            self.ax_3d.set_zlabel("Z-axis")
            self.ax_3d.set_title("Marker Positions at Selected Frame")

    def update_3d_plot(self, frame_index):
        """Update the existing 3D plot with all markers and highlight the selected one."""
        try:
            # Validate frame_index
            if frame_index < 0 or frame_index >= len(self.df):
                print(f"Frame index {frame_index} out of bounds.")
                return

            # Ensure the 3D figure is initialized
            self.create_3d_plot()

            # Extract all marker columns
            marker_columns = [col for col in self.df.columns if '<T-' in col]
            if len(marker_columns) % 3 != 0:
                print("Marker columns are not a multiple of 3, invalid structure.")
                return
            
            # Reshape to (frames, markers, 3)
            all_marker_positions = self.df[marker_columns].values.reshape(-1, len(marker_columns) // 3, 3)

            # Validate marker positions for the frame
            if frame_index >= len(all_marker_positions):
                print(f"Invalid frame index: {frame_index} exceeds available frames.")
                return
            frame_positions = all_marker_positions[frame_index]

            # Handle NaN or infinite values in the frame data
            if not np.isfinite(frame_positions).all():
                print(f"Frame {frame_index} contains invalid marker positions.")
                return
            
            # Define valid bounds for marker positions
            position_min, position_max = -1000, 10000  # Adjust these bounds as needed
            valid_marker_positions = []
            
            # Threshold for extreme values (to avoid floating point errors or outlier positions)
            extreme_threshold_min = -1e5  # Minimum threshold (e.g., -100,000)
            extreme_threshold_max = 1e5   # Maximum threshold (e.g., 100,000)
            
            # Filter out markers outside the bounds and non-finite values
            for i, pos in enumerate(frame_positions):
                # Check if any of the values in the position are NaN or Inf
                if any(math.isnan(val) or math.isinf(val) for val in pos):
                    print(f"Skipping marker at index {i} with position {pos} (NaN or Inf values).")
                    continue  # Skip this marker

                # Ensure position is within bounds and not too extreme
                if np.all((pos >= position_min) & (pos <= position_max)):
                    # Check for extreme values
                    if np.all((pos >= extreme_threshold_min) & (pos <= extreme_threshold_max)):
                        # Marker passes all checks, add it to valid list
                        valid_marker_positions.append(pos)
                    else:
                        print(f"Skipping marker at index {i} with position {pos} (extreme values).")
                else:
                    print(f"Skipping marker at index {i} with position {pos} (out of bounds).")

            # Skip if no valid markers are found
            if not valid_marker_positions:
                print(f"No valid markers found for frame {frame_index}.")
                return

            # Get the position of the selected marker
            marker_columns_selected = [col for col in self.df.columns if self.marker_name in col]
            if len(marker_columns_selected) < 3:
                print(f"Marker '{self.marker_name}' does not have complete X, Y, Z data.")
                return
            selected_marker_idx = marker_columns.index(marker_columns_selected[0]) // 3
            valid_selected_marker = frame_positions[selected_marker_idx]

            # Clear the previous scatter plot
            if self.scatter_3d:
                self.scatter_3d.remove()

            # Plot all valid markers in blue
            valid_marker_positions = np.array(valid_marker_positions)

            # Check if all valid_marker_positions are finite
            if not np.all(np.isfinite(valid_marker_positions)):
                print("There are still non-finite values in valid_marker_positions.")
                return

            self.scatter_3d = self.ax_3d.scatter(
                valid_marker_positions[:, 0], valid_marker_positions[:, 1], valid_marker_positions[:, 2],
                c='blue', s=20, label="All Markers"
            )

            # Remove the previous red marker (if any)
            if hasattr(self, 'red_marker_3d') and self.red_marker_3d:
                self.red_marker_3d.remove()

            # Highlight the selected marker in red
            if np.isfinite(valid_selected_marker).all():  # Check if selected marker is valid
                self.red_marker_3d = self.ax_3d.scatter(
                    valid_selected_marker[0], valid_selected_marker[1], valid_selected_marker[2],
                    c='red', s=100, label="Selected Marker"
                )

            # Dynamically adjust plot limits based on valid marker positions
            x_vals = valid_marker_positions[:, 0]
            y_vals = valid_marker_positions[:, 1]
            z_vals = valid_marker_positions[:, 2]
            
            # Set axis limits to fit the valid marker positions
            self.ax_3d.set_xlim([x_vals.min(), x_vals.max()])
            self.ax_3d.set_ylim([y_vals.min(), y_vals.max()])
            self.ax_3d.set_zlim([z_vals.min(), z_vals.max()])

            # Update the plot without adding duplicate legends
            self.ax_3d.legend(loc='upper right')
            self.ax_3d.figure.canvas.draw_idle()
            self.ax_3d.figure.canvas.flush_events()
            plt.pause(0.01)  # Brief pause to allow the plot to update

        except Exception as e:
            print(f"Error in update_3d_plot: {e}")

    def show_3d_plot(self):
        """Show the 3D plot window."""
        if self.fig_3d is not None:
            plt.show()


# Example usage
if __name__ == "__main__":
    visualizer = MarkerVisualizer("config.yaml")
    visualizer.load_data()

    # Visualize marker's position over time
    visualizer.plot_marker_graph()

    # Keep the 3D plot open
    visualizer.show_3d_plot()

# # Example usage
# if __name__ == "__main__":
#     visualizer = MarkerVisualizer("config.yaml")
#     visualizer.load_data()

#     # Visualize marker's 3D trajectory
#     visualizer.plot_marker_trajectories()

#     # Visualize marker's position over time
#     visualizer.plot_marker_graph()
