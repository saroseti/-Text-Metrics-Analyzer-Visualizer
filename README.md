# Text Metrics Analyzer & Visualizer

An advanced, high-performance tool for text corpus analysis, Natural Language Processing (NLP) metrics calculation, and interactive data visualization. It extracts text from books (PDF/EPUB), processes word frequencies, and enables deep visual exploration through an interactive graphical interface.

## Key Features

* **Robust Text Extraction:** Converts PDF and EPUB files to plain text using PyMuPDF.
* **Storage Efficiency:** Data serialization in `.msgpack` format for high-speed processing, alongside `.json` for human readability.
* **NLP Calculation Engine:** Automatically computes essential text analysis metrics for entire document collections.
* **Interactive Visualization (GUI):** Graphical interface built with matplotlib featuring smart scrollbars, interactive metric selection, and dynamic charts (Vertical Bar, Pie, Horizontal Bar).
* **Automatic Book Classifier:** Groups documents into categories (Mathematics, Physics, Chemistry, Programming) by analyzing the TF-IDF scores of specific keywords.
* **Clean Software Architecture:** Implemented using a hybrid MVC (Model-View-Controller) architecture for the console flow and MVP (Model-View-Presenter) for the graphical visualization.

## Calculated Metrics

The system processes and exports the following metrics for each text corpus:

* **TF (Term Frequency):** Frequency of terms per individual document.
* **CF (Collection Frequency):** Total frequency of a term across the entire book collection.
* **DF (Document Frequency):** Number of documents in which a specific term appears.
* **IDF (Inverse Document Frequency):** A measure of how much information a word provides, calculated as $\log(N / DF)$.
* **TF-IDF:** The relevance of a word in a specific document relative to the entire collection.
* **Balanced Score:** A custom mathematical metric defined as $\log(CF + 1) \cdot DF^2$, ideal for finding highly recurrent and evenly distributed keywords.

## Architecture & Design Patterns

The code is structured to be highly scalable and maintainable, applying SOLID principles:

* **MVC & MVP:** The CLI flow uses Model-View-Controller, while the complex visualization window delegates its interface to a Model-View-Presenter to isolate UI state logic (`presenter.py`).
* **Strategy Pattern:** Used in data serialization (`JsonStrategy`, `MsgpackStrategy`), allowing the swap of save/load algorithms at runtime.
* **Facade Pattern:** `TextAnalysisModel` acts as a facade that hides the complexity of mathematical calculations and file conversions from the Controller.

## Installation and Dependencies

**1. Clone the repository**
```bash
git clone [https://github.com/saroseti/Text-Metrics-Analyzer-Visualizer.git](https://github.com/saroseti/Text-Metrics-Analyzer-Visualizer.git)
cd Text-Metrics-Analyzer-Visualizer
```

**2. Install Dependencies**

This project requires Python 3.8 or higher. The core dependencies are:

* `pymupdf` (for PDF/EPUB text extraction)
* `msgpack` (for high-speed binary serialization)
* `matplotlib` (for generating the interactive GUI and charts)

You can install all required packages at once using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

**3. Run the application**

```bash
python main.py
```

## Interactive Menu Guide

Upon running the program, you will be greeted by a terminal menu:

* **[1/2] Path Management:** Define the folder containing your PDF/EPUB books.
* **[3/4] Conversion:** Convert books to `.txt` and subsequently to `.msgpack` to optimize read speeds.
* **[5/6] Compute Metrics:** Calculate all mathematical formulas and export them to your desired format (JSON for debugging, Msgpack for performance).
* **[7/8] Visualization Interface:** Open the interactive Graphical User Interface (GUI).

## Graphical Interface (GUI)

Options 7 and 8 will open an interactive window where you can:

* Select the metric to visualize (CF, DF, IDF, Balanced Score, or Book Categories).
* Analyze the individual TF of each book by selecting it from an interactive radio-button menu.
* Switch between Bar, Pie, and Horizontal Bar charts.
* Define the number of variables to display using the "Show Top:" text box (e.g., Top 300 words).
* Navigate through massive datasets using the smart bottom Scrollbar (automatically activates when the bar chart gets too large).

## Project Structure

```text
📁 text-metrics-analyzer/
│
├── main.py              # Application entry point
├── controller.py        # Routing and program flow control (MVC)
├── model.py             # Business logic, math, read/write ops (Facade)
├── view.py              # Console interface and Matplotlib UI setup
├── presenter.py         # Logical orchestrator for the GUI (MVP)
├── requirements.txt     # Project dependencies
│
└── 📁 DATA/             # (Automatically generated folder)
    ├── FILES_TXT/       # Extracted plain texts
    ├── FILES_MSGPACK/   # Serialized texts
    ├── TF_RESULTS...    # Individual frequencies
    └── RESULTS...       # Exported global metrics
```

## Roadmap (Next Steps)

- [ ] Multithreading/Multiprocessing support for massive book collections.
- [ ] Advanced, customizable Stop-Words filter.
- [ ] Export interactive charts to PNG/PDF formats.

---
*Developed with ❤️ combining the power of traditional NLP and pure software architecture design.*
