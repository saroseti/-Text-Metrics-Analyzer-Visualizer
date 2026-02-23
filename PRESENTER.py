# PRESENTER.py

import os
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, Button, TextBox, CheckButtons, Slider

class VisualizationPresenter:
    """
    The 'Presenter' in an MVP pattern for the visualization part.
    It fetches data from the model, formats it for the view, and handles all UI logic.
    """
    def __init__(self, view, model, file_manager, paths):
        self.view = view
        self.model = model # Access to the main model for clustering
        self.file_manager = file_manager
        self.paths = paths
        
        # State
        self.data_cache = {}
        self.current_format = None
        self.current_metric = 'Book Categories' # Default metric
        self.current_plot_type = 'Bar'
        self.selected_tf_file = None
        self.top_n = 25 # Default number of items to show

        # UI Options
        self.plot_options = ['Bar', 'Pie', 'Horizontal Bar']
        self.main_metrics = [] # Will be populated on load

    def run_visualization(self, export_format):
        """Main entry point to start the visualization process."""
        self.current_format = export_format
        self.file_manager.set_strategy_by_format(export_format)

        if not self._load_data():
            return False # Indicate failure to the controller

        # Set an initial metric to display
        self.current_metric = self.main_metrics[0] if self.main_metrics else None
        if self.current_metric:
            self.view.display_interactive_window(self)
        else:
            return False # No data was found to visualize
        return True # Indicate success

    def _load_data(self):
        """Loads all available metric files and prepares metric lists."""
        self.data_cache = {}
        results_dir = self.paths[f'results_{self.current_format}']
        ext = self.file_manager.extension

        # 1. Load consolidated metrics from the results folder
        if os.path.exists(results_dir):
            for filename in os.listdir(results_dir):
                if filename.endswith(ext):
                    metric_name = os.path.splitext(filename)[0].replace("_RESULTS", "")
                    full_path = os.path.join(results_dir, filename)
                    self.data_cache[metric_name] = self.file_manager.load(full_path)
        
        # 2. Add placeholder for Book Categories analysis
        self.data_cache['Book Categories'] = {} # Will be computed on demand

        # 3. Check for TF-IDF files to enable category analysis and TF-IDF sample
        tfidf_dir = self.paths[f'tfidf_{self.current_format}']
        if os.path.exists(tfidf_dir) and any(f.endswith(ext) for f in os.listdir(tfidf_dir)):
            self.data_cache['TF-IDF (Sample)'] = self._load_sample_file(tfidf_dir, ext)
        
        # 4. Check for TF files
        tf_dir = self.paths[f'tf_{self.current_format}']
        if os.path.exists(tf_dir) and any(f.endswith(ext) for f in os.listdir(tf_dir)):
            self.data_cache['Term Frequency (Per File)'] = self._get_tf_file_list(tf_dir, ext)
        
        self.main_metrics = list(self.data_cache.keys())
        return bool(self.data_cache)

    def _load_sample_file(self, directory, ext):
        """Loads the first file from a directory as a sample."""
        sample_file = next((f for f in os.listdir(directory) if f.endswith(ext)), None)
        if sample_file:
            return self.file_manager.load(os.path.join(directory, sample_file))
        return {}

    def _get_tf_file_list(self, directory, ext):
        """Returns a list of file names from the TF directory."""
        return [os.path.splitext(f)[0] for f in os.listdir(directory) if f.endswith(ext)]

    def get_plot_data(self):
        """Prepares the data for plotting based on the current selections."""
        metric = self.current_metric
        
        if metric == 'Book Categories':
            clusters = self.model.get_book_categories(self.current_format)
            if not clusters: return [], []
            labels = list(clusters.keys())
            values = [len(books) for books in clusters.values()]
            return labels, values

        if metric == 'Term Frequency (Per File)':
            if not self.selected_tf_file: return [], [] # Nothing selected yet
            tf_dir = self.paths[f'tf_{self.current_format}']
            ext = self.file_manager.extension
            file_path = os.path.join(tf_dir, f"{self.selected_tf_file}{ext}")
            raw_data = self.file_manager.load(file_path)
        else:
            raw_data = self.data_cache.get(metric, {})

        if not isinstance(raw_data, dict) or not raw_data:
            return [], []

        sorted_items = sorted(raw_data.items(), key=lambda item: item[1], reverse=True)
        display_data = sorted_items[:self.top_n]
        
        if not display_data: return [], []
        labels, values = zip(*display_data)
        return labels, values

    # --- UI Event Handlers ---

    def on_metric_changed(self, label):
        """Callback for when the user selects a different metric."""
        self.current_metric = label
        self.selected_tf_file = None # Reset TF file selection
        self.view.update_plot()

    def on_tf_file_selected(self, label):
        """Callback for when a specific TF file is chosen."""
        self.selected_tf_file = label
        self.view.update_plot()

    def on_plot_type_changed(self, label):
        """Callback for when the user selects a different plot type."""
        self.current_plot_type = label
        self.view.update_plot()

    def on_top_n_changed(self, text):
        """Callback for when the user submits a new value for Top N."""
        try:
            self.top_n = int(text)
            if self.top_n < 1: self.top_n = 1
            self.view.update_plot()
        except (ValueError, TypeError):
            print(f"Invalid input for Top N: '{text}'. Please enter a number.")
