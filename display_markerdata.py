import numpy as np
import matplotlib.pyplot as plt
import mplcursors
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
import yaml

class MarkerVisualizer:
    def __init__(self, config_loc, skip_rows=1):
        """Initialize the MarkerVisualizer with a CSV file."""
        self.skip_rows = skip_rows
        self.df = None
        self.fig_3d = None
        self.ax_3d = None
        self.scatter_3d = None

        # Load the configuration file
        with open(config_loc, "r") as file:
            config = yaml.safe_load(file)

        self.marker_name = config["marker_name"]
        self.csv_file = config["csv_file_path"]

    def load_data(self):
        """Load the marker data from the CSV file."""
        self.df = pd.read_csv(self.csv_file, skiprows=self.skip_rows)
        if 'Frame' not in self.df.columns:
            raise ValueError("The CSV file must contain a 'Frame' column.")
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

        # Add interactivity
        cursor = mplcursors.cursor([x_line, y_line, z_line], hover=True)

        @cursor.connect("add")
        def on_add(sel):
            # Determine the index of the hovered point
            index = int(np.argmin(np.abs(time_stamps - sel.target[0])))

            # Update the 3D plot with the selected marker's position
            self.update_3d_plot(index)

            # Determine the corresponding value for the hovered point
            line_label = sel.artist.get_label()
            position_value = marker_positions[index, {'X Position': 0, 'Y Position': 1, 'Z Position': 2}[line_label]]

            sel.annotation.set_text(
                f"{line_label}\nTime: Frame {time_stamps.iloc[index]}\n"
                f"Value: {position_value:.2f}"
            )
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)

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
        self.create_3d_plot()

        # Extract all marker columns
        marker_columns = [col for col in self.df.columns if '<T-' in col]
        all_marker_positions = self.df[marker_columns].values.reshape(-1, len(marker_columns) // 3, 3)
        frame_positions = all_marker_positions[frame_index]

        # Get the position of the selected marker
        marker_columns_selected = [col for col in self.df.columns if self.marker_name in col]
        selected_marker_idx = marker_columns.index(marker_columns_selected[0]) // 3
        selected_marker_position = frame_positions[selected_marker_idx]

        # Clear the previous scatter plot
        if self.scatter_3d:
            self.scatter_3d.remove()

        # Plot all markers in blue
        self.scatter_3d = self.ax_3d.scatter(
            frame_positions[:, 0], frame_positions[:, 1], frame_positions[:, 2],
            c='blue', s=20, label="All Markers"
        )

        # Remove the previous red marker (if any)
        if hasattr(self, 'red_marker_3d') and self.red_marker_3d:
            self.red_marker_3d.remove()

        # Highlight the selected marker in red
        self.red_marker_3d = self.ax_3d.scatter(
            selected_marker_position[0], selected_marker_position[1], selected_marker_position[2],
            c='red', s=100
        )

        # Update the plot without adding duplicate legends
        self.ax_3d.legend(loc='upper right')
        plt.pause(0.01)  # Brief pause to allow the plot to update

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
