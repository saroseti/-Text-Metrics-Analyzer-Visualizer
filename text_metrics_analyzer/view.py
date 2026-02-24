# view.py
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons, RadioButtons, TextBox, Slider

class AnalysisView:
    """Handles all user-facing console output."""
    def get_folder_path(self):
        return input("-> Please enter the path to the folder containing the PDF/EPUB books: ")

    def display_message(self, message):
        print(message)

    def display_progress(self, current, total, message):
        print(f"[{current}/{total}] {message}")

    def display_error(self, error_message):
        print(f"X ERROR: {error_message}")

    def clear_console(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def menu(self, done_flags):
        """Displays the main menu."""
        self.clear_console()
        print("\n----------------------------- PATH -----------------------------")
        print("    1] [ Enter a new path for PDF/EPUB files ]")
        print("    2] [ Keep current PDF/EPUB folder path ]\n")
        print("---------- CONVERT [ PDF/EPUB --> .txt --> .msgpack ] ----------")
        print(f"    3] Convert PDF/EPUB to .txt    {'[#DONE √]' if done_flags.get('3') else ''}")
        print(f"    4] Convert .txt to .msgpack    {'[#DONE √]' if done_flags.get('4') else ''}\n")
        print("-------------------- COMPUTE & VISUALIZE ---------------------")
        print(f"    5] Compute & Export to .json    {'[#DONE √]' if done_flags.get('5') else ''}")
        print(f"    6] Compute & Export to .msgpack {'[#DONE √]' if done_flags.get('6') else ''}")
        print("    7] Visualize metrics from .json files")
        print("    8] Visualize metrics from .msgpack files\n")
        print("------------------------------------------------------------------")
        print("    9] Exit")
        return input("Option: ").strip()

class VisualizationView:
    """
    The 'View' in an MVP pattern. A passive view for rendering the plot window.
    """
    def __init__(self):
        self.presenter = None
        self.fig = None
        self.ax_main = None
        self.widgets = {} # Store widgets to keep them alive and accessible
        self.initial_display_count = 30 # How many bars to show at once

    def display_interactive_window(self, presenter):
        """Creates and shows the main plot window."""
        self.presenter = presenter
        
        self.fig = plt.figure(figsize=(15, 8))
        # Define axes layout manually for more control
        self.ax_main = self.fig.add_axes([0.3, 0.1, 0.65, 0.8])
        self.ax_metrics = self.fig.add_axes([0.03, 0.5, 0.2, 0.45])
        self.ax_plot_type = self.fig.add_axes([0.03, 0.35, 0.2, 0.12])
        self.ax_top_n = self.fig.add_axes([0.03, 0.25, 0.2, 0.05])
        self.ax_slider = self.fig.add_axes([0.3, 0.02, 0.65, 0.03])
        self.ax_tf_selector = self.fig.add_axes([0.3, 0.1, 0.65, 0.8]) # Overlaps main
        
        self._setup_widgets()
        self.update_plot()
        plt.show()

    def _setup_widgets(self):
        """Creates the interactive widgets."""
        # Main metric selection
        self.widgets['metrics'] = CheckButtons(
            self.ax_metrics, self.presenter.main_metrics, actives=[True] * len(self.presenter.main_metrics)
        )
        self.widgets['metrics'].on_clicked(self._on_metric_selected)
        
        # Plot type selection
        self.widgets['plot_type'] = RadioButtons(
            self.ax_plot_type, self.presenter.plot_options, active=0
        )
        self.widgets['plot_type'].on_clicked(self.presenter.on_plot_type_changed)
        
        # Top N text box
        self.widgets['top_n'] = TextBox(
            self.ax_top_n, 'Show Top:', initial=str(self.presenter.top_n)
        )
        self.widgets['top_n'].on_submit(self.presenter.on_top_n_changed)

        # Scrollbar slider
        self.widgets['slider'] = Slider(
            self.ax_slider, 'Scroll', 0, 1, valinit=0
        )
        self.widgets['slider'].on_changed(self._on_scroll)
        self.ax_slider.set_visible(False)
        
        # TF file selector (initially hidden)
        self.ax_tf_selector.set_visible(False)

    def _on_metric_selected(self, label):
        """Ensures only one metric is active at a time, like radio buttons."""
        # Deactivate all others
        for i, l in enumerate(self.widgets['metrics'].labels):
            if l.get_text() != label:
                self.widgets['metrics'].set_active(i)
        self.presenter.on_metric_changed(label)

    def update_plot(self):
        """Clears and redraws the plot based on the presenter's state."""
        self.ax_main.clear()
        self.ax_tf_selector.clear()
        self.ax_tf_selector.set_visible(False)
        self.ax_main.set_visible(True)

        # Special case for TF: show file selector instead of plot
        if self.presenter.current_metric == 'Term Frequency (Per File)' and not self.presenter.selected_tf_file:
            self._show_tf_selection_ui()
            return

        labels, values = self.presenter.get_plot_data()

        if not labels:
            self.ax_main.text(0.5, 0.5, "No data to display.", ha='center', va='center')
            self.ax_slider.set_visible(False)
            self.fig.canvas.draw_idle()
            return
        
        self._draw_chart(labels, values)
        self.fig.canvas.draw_idle()

    def _show_tf_selection_ui(self):
        """Displays the UI for selecting a specific TF file."""
        self.ax_main.set_visible(False)
        self.ax_slider.set_visible(False)
        self.ax_tf_selector.set_visible(True)
        
        tf_files = self.presenter.data_cache.get('Term Frequency (Per File)', [])
        if not tf_files:
            self.ax_tf_selector.text(0.5, 0.5, "No TF files found.", ha='center')
            return

        self.ax_tf_selector.set_title("Select a Term Frequency File to Visualize")
        self.widgets['tf_selector'] = RadioButtons(self.ax_tf_selector, tf_files)
        self.widgets['tf_selector'].on_clicked(self.presenter.on_tf_file_selected)

    def _draw_chart(self, labels, values):
        """Handles the actual drawing of the selected chart type."""
        plot_type = self.presenter.current_plot_type
        title = f"{self.presenter.current_metric}"
        if self.presenter.selected_tf_file:
            title = f"TF: {self.presenter.selected_tf_file}"
        
        self.ax_main.set_title(title)
        
        # Logic for enabling/disabling scrollbar
        is_scrollable = plot_type in ['Bar', 'Horizontal Bar'] and len(labels) > self.initial_display_count
        self.ax_slider.set_visible(is_scrollable)

        if plot_type == 'Bar':
            self.ax_main.bar(labels, values, color='darkcyan')
            self.ax_main.tick_params(axis='x', rotation=90)
            if is_scrollable:
                self._setup_scrollbar(len(labels))
        elif plot_type == 'Pie':
            self.ax_main.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8})
            self.ax_main.axis('equal')
        elif plot_type == 'Horizontal Bar':
            self.ax_main.barh(labels, values, color='coral')
            self.ax_main.invert_yaxis()
            if is_scrollable:
                self._setup_scrollbar(len(labels), is_horizontal=True)

    def _setup_scrollbar(self, num_items, is_horizontal=False):
        """Configures the slider to act as a scrollbar."""
        slider = self.widgets['slider']
        slider.valmax = num_items - self.initial_display_count
        slider.ax.set_xlim(0, slider.valmax)
        slider.set_val(0)
        
        if is_horizontal:
            self.ax_main.set_ylim(self.initial_display_count - 0.5, -0.5)
        else:
            self.ax_main.set_xlim(-0.5, self.initial_display_count - 0.5)

    def _on_scroll(self, val):
        """Callback for when the slider value changes."""
        start_index = int(val)
        end_index = start_index + self.initial_display_count
        
        if self.presenter.current_plot_type == 'Horizontal Bar':
            self.ax_main.set_ylim(end_index - 0.5, start_index - 0.5)
        else: # Vertical Bar
            self.ax_main.set_xlim(start_index - 0.5, end_index - 0.5)
        
        self.fig.canvas.draw_idle()

