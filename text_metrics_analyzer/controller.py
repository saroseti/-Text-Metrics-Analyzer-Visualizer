# controller.py

from MODEL import TextAnalysisModel
from VIEW import AnalysisView, VisualizationView
from PRESENTER import VisualizationPresenter
import os
import time

class AnalysisController:
    """
    Coordinates user interaction and model computation.
    Delegates visualization tasks to the VisualizationPresenter.
    """
    def __init__(self):
        # Views
        self.analysis_view = AnalysisView()
        self.visualization_view = VisualizationView()
        
        # Model
        self.model = TextAnalysisModel(self.analysis_view)
        
        # Presenter
        self.visualization_presenter = VisualizationPresenter(
            self.visualization_view,
            self.model, 
            self.model.file_manager, 
            self.model.paths
        )
        
        # State
        self.current_folder_path = None
        self.done_flags = {key: False for key in ["3", "4", "5", "6"]}

    def run(self):
        """Main application loop that handles user input."""
        self.analysis_view.display_message("--- Text Metrics Analyzer ---")
        while True:
            option = self.analysis_view.menu(self.done_flags)
            
            start_time = time.time() # Start timer for operations

            if option == "1":
                path = self.analysis_view.get_folder_path()
                if os.path.isdir(path):
                    self.current_folder_path = path
                    self.analysis_view.display_message(f"Path set to: {self.current_folder_path}")
                else:
                    self.analysis_view.display_error("The provided path is not a valid directory.")
            
            elif option == "2":
                if self.current_folder_path:
                    self.analysis_view.display_message(f"Keeping current path: {self.current_folder_path}")
                else:
                    self.analysis_view.display_error("No path has been set yet. Please use option 1 first.")

            elif option == "3":
                if not self.current_folder_path:
                    self.analysis_view.display_error("Please set a folder path first using option 1.")
                else:
                    self.model.convert_pdfs_to_txt(self.current_folder_path)
                    self.done_flags["3"] = True

            elif option == "4":
                self.model.convert_txt_to_msgpack()
                self.done_flags["4"] = True

            elif option == "5":
                self.model.compute_and_export_metrics('json')
                self.done_flags["5"] = True
                self._display_time(start_time)

            elif option == "6":
                self.model.compute_and_export_metrics('msgpack')
                self.done_flags["6"] = True
                self._display_time(start_time)

            elif option == "7":
                self.analysis_view.display_message("Launching visualization for .json data...")
                # Check if visualization can run
                if not self.visualization_presenter.run_visualization('json'):
                    self.analysis_view.display_error(
                        "No .json data found. Please run option 5 to generate data first."
                    )

            elif option == "8":
                self.analysis_view.display_message("Launching visualization for .msgpack data...")
                # Check if visualization can run
                if not self.visualization_presenter.run_visualization('msgpack'):
                    self.analysis_view.display_error(
                        "No .msgpack data found. Please run option 6 to generate data first."
                    )

            elif option == "9":
                self.analysis_view.display_message("Exiting...")
                break
            
            else:
                self.analysis_view.display_error("Invalid option. Please try again.")
            
            # Pause to allow user to see the output before clearing
            if option not in ['7', '8']: # Don't pause after launching GUI
                input("\nPress Enter to continue...")

    def _display_time(self, start_time):
        """Calculates and displays the elapsed time for an operation."""
        elapsed_time = time.time() - start_time
        self.analysis_view.display_message(f"\n[SUCCESS] Total operation time: {elapsed_time:.2f} seconds.")

