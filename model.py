# MODEL.py

import os
import re
import json
import msgpack
import pymupdf
from collections import Counter, defaultdict
from math import log
from abc import ABC, abstractmethod

# ==============================================================================
# 1. SERIALIZATION STRATEGY PATTERN
# ==============================================================================
class SerializationStrategy(ABC):
    @abstractmethod
    def save(self, filename, data): pass
    @abstractmethod
    def load(self, filename, default_value=None): pass
    @property
    @abstractmethod
    def extension(self): pass

class JsonStrategy(SerializationStrategy):
    @property
    def extension(self): return ".json"
    def save(self, filename, data):
        with open(filename, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)
    def load(self, filename, default_value=None):
        if default_value is None: default_value = {}
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f: return json.load(f)
            except json.JSONDecodeError: return default_value
        return default_value

class MsgpackStrategy(SerializationStrategy):
    @property
    def extension(self): return ".msgpack"
    def save(self, filename, data):
        with open(filename, "wb") as f: f.write(msgpack.packb(data, use_bin_type=True))
    def load(self, filename, default_value=None):
        if default_value is None: default_value = {}
        if os.path.exists(filename):
            try:
                with open(filename, "rb") as f: return msgpack.unpackb(f.read(), raw=False)
            except msgpack.exceptions.UnpackException: return default_value
        return default_value

# ==============================================================================
# 2. FILE MANAGER (CONTEXT)
# ==============================================================================
class FileManager:
    def __init__(self, view):
        self.view = view
        self._strategy: SerializationStrategy = JsonStrategy() # Default strategy
        self.strategies = {'json': JsonStrategy(), 'msgpack': MsgpackStrategy()}

    def set_strategy(self, strategy: SerializationStrategy):
        self._strategy = strategy
    
    def set_strategy_by_format(self, format_name: str):
        if format_name in self.strategies:
            self._strategy = self.strategies[format_name]
        else:
            raise ValueError(f"Unknown format: {format_name}")

    def save(self, filename, data):
        self._strategy.save(filename, data)

    def load(self, filename, default_value=None):
        return self._strategy.load(filename, default_value)
    
    @property
    def extension(self):
        return self._strategy.extension

# ==============================================================================
# 3. TEXT & DOCUMENT PROCESSORS (Unchanged)
# ==============================================================================
class TextProcessor:
    @staticmethod
    def normalize_and_tokenize(text):
        return (m.group() for m in re.finditer(r'\b\w+\b', text.lower()))
    @staticmethod
    def sanitize_filename(name):
        return re.sub(r'[<>:"/\\|?*]', "_", name)

class DocumentConverter:
    def __init__(self, view, file_manager, books_txt_dir, books_msgpack_dir):
        self.view = view
        self.file_manager = file_manager
        self.books_txt_dir = books_txt_dir
        self.books_msgpack_dir = books_msgpack_dir

    def _extract_text_from_document(self, file_path):
        try:
            with pymupdf.open(file_path) as doc:
                return "".join(page.get_text() for page in doc)
        except Exception as e:
            self.view.display_error(f"Cannot read {os.path.basename(file_path)}: {e}")
            return None

    def convert_pdfs_to_txt(self, folder_path):
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.pdf', '.epub'))]
        if not files:
            self.view.display_error(f"No PDF or EPUB files found in {folder_path}")
            return
        for i, filename in enumerate(files, 1):
            path = os.path.join(folder_path, filename)
            base = TextProcessor.sanitize_filename(os.path.splitext(filename)[0])
            txt_name = f"{base}.txt"
            txt_path = os.path.join(self.books_txt_dir, txt_name)
            if not os.path.exists(txt_path):
                text = self._extract_text_from_document(path)
                if text:
                    with open(txt_path, "w", encoding="utf-8") as f: f.write(text)
                self.view.display_progress(i, len(files), f"Converted: {txt_name}")
            else:
                self.view.display_progress(i, len(files), f"Already exists: {txt_name}")

    def convert_txt_to_msgpack(self):
        txt_files = [f for f in os.listdir(self.books_txt_dir) if f.endswith(".txt")]
        if not txt_files:
            self.view.display_error(f"No .txt files found in {os.path.basename(self.books_txt_dir)}. Please run option 3 first.")
            return
        
        self.file_manager.set_strategy(MsgpackStrategy())
        for i, filename in enumerate(txt_files, 1):
            txt_path = os.path.join(self.books_txt_dir, filename)
            base_name = os.path.splitext(filename)[0]
            msgpack_path = os.path.join(self.books_msgpack_dir, f"{base_name}.msgpack")
            if os.path.exists(msgpack_path):
                self.view.display_progress(i, len(txt_files), f"Skipping (exists): {os.path.basename(msgpack_path)}")
                continue
            with open(txt_path, "r", encoding="utf-8") as f: text = f.read()
            self.file_manager.save(msgpack_path, {"text": text})
            self.view.display_progress(i, len(txt_files), f"Packed to msgpack: {os.path.basename(msgpack_path)}")

# ==============================================================================
# 5. METRICS CALCULATOR (Slightly modified to use new FileManager method)
# ==============================================================================
class MetricsCalculator:
    def __init__(self, view, file_manager, paths):
        self.view = view
        self.file_manager = file_manager
        self.paths = paths
        self.idf = {}
        self.cf = defaultdict(int)
        self.df = defaultdict(int)
        self.balanced_scores = {}

    def run(self, export_format):
        self.file_manager.set_strategy_by_format(export_format)
        tf_dir = self.paths[f'tf_{export_format}']
        tfidf_dir = self.paths[f'tfidf_{export_format}']
        results_dir = self.paths[f'results_{export_format}']
        
        self._calculate_tf(tf_dir)
        tf_files = [f for f in os.listdir(tf_dir) if f.endswith(self.file_manager.extension)]
        total_docs = len(tf_files)
        if total_docs == 0:
            self.view.display_error(f"No TF files were generated in {os.path.basename(tf_dir)} to proceed.")
            return

        self._calculate_cf(tf_files, tf_dir)
        self._calculate_df(tf_files, tf_dir)
        self._calculate_idf(total_docs)
        self._calculate_and_save_tfidf(tf_files, tf_dir, tfidf_dir)
        self._calculate_balanced_score()
        self._export_consolidated_metrics(results_dir)

    def _calculate_tf(self, tf_dir):
        self.view.display_message(f"\n--- Phase 1: Calculating TF -> {os.path.basename(tf_dir)} ---")
        msgpack_files = [f for f in os.listdir(self.paths['books_msgpack']) if f.endswith(".msgpack")]
        txt_files = [f for f in os.listdir(self.paths['books_txt']) if f.endswith(".txt")]
        
        source_dir, source_files, use_msgpack = (None, [], False)
        if msgpack_files:
            self.view.display_message(f"Found {len(msgpack_files)} .msgpack files for efficiency.")
            source_dir, source_files, use_msgpack = (self.paths['books_msgpack'], msgpack_files, True)
        elif txt_files:
            self.view.display_message(f"Using {len(txt_files)} .txt files as source.")
            source_dir, source_files = (self.paths['books_txt'], txt_files)
        else:
            self.view.display_error("No source files found. Please run option 3 or 4 first.")
            return

        temp_loader = MsgpackStrategy()
        for i, filename in enumerate(source_files, 1):
            base_name = os.path.splitext(filename)[0]
            target_path = os.path.join(tf_dir, base_name + self.file_manager.extension)
            if os.path.exists(target_path):
                self.view.display_progress(i, len(source_files), f"Skipping TF (exists): {os.path.basename(target_path)}")
                continue

            source_path = os.path.join(source_dir, filename)
            text = ""
            if use_msgpack:
                text = temp_loader.load(source_path, {}).get("text", "")
            else:
                with open(source_path, "r", encoding="utf-8") as f: text = f.read()
            
            if text:
                words = list(TextProcessor.normalize_and_tokenize(text))
                self.file_manager.save(target_path, dict(Counter(words)))
                self.view.display_progress(i, len(source_files), f"TF calculated for: {os.path.basename(target_path)}")
    
    def _calculate_cf(self, tf_files, tf_dir):
        # ... (implementation is correct, no changes needed)
        self.view.display_message("\n--- Phase 2: Calculating Collection Frequency (CF) ---")
        self.cf.clear()
        for i, filename in enumerate(tf_files, 1):
            tf_data = self.file_manager.load(os.path.join(tf_dir, filename), {})
            for word, count in tf_data.items(): self.cf[word] += count
            self.view.display_progress(i, len(tf_files), f"Aggregating CF from: {filename}")

    def _calculate_df(self, tf_files, tf_dir):
        # ... (implementation is correct, no changes needed)
        self.view.display_message("\n--- Phase 3: Calculating Document Frequency (DF) ---")
        self.df.clear()
        for i, filename in enumerate(tf_files, 1):
            tf_data = self.file_manager.load(os.path.join(tf_dir, filename), {})
            for word in tf_data.keys(): self.df[word] += 1
            self.view.display_progress(i, len(tf_files), f"Aggregating DF from: {filename}")

    def _calculate_idf(self, total_docs):
        # ... (implementation is correct, no changes needed)
        self.view.display_message("\n--- Phase 4: Calculating Inverse Document Frequency (IDF) ---")
        self.idf = {word: round(log(total_docs / df_count), 4) for word, df_count in self.df.items() if df_count > 0}
        self.view.display_message(f"IDF calculated for {len(self.idf)} unique words.")

    def _calculate_and_save_tfidf(self, tf_files, tf_dir, tfidf_dir):
        # ... (implementation is correct, no changes needed)
        self.view.display_message(f"\n--- Phase 5: Calculating and Saving TF-IDF to {os.path.basename(tfidf_dir)} ---")
        for i, filename in enumerate(tf_files, 1):
            tf_data = self.file_manager.load(os.path.join(tf_dir, filename), {})
            doc_name = os.path.splitext(filename)[0]
            doc_tfidf = {word: round(count * self.idf.get(word, 0), 4) for word, count in tf_data.items()}
            self.file_manager.save(os.path.join(tfidf_dir, f"{doc_name}{self.file_manager.extension}"), doc_tfidf)
            self.view.display_progress(i, len(tf_files), f"Saved TF-IDF for: {doc_name}{self.file_manager.extension}")

    def _calculate_balanced_score(self):
        # ... (implementation is correct, no changes needed)
        self.view.display_message("\n--- Phase 6: Calculating Balanced Score ---")
        self.balanced_scores = {word: round(log(self.cf[word] + 1) * (self.df[word] ** 2), 4) for word in self.cf}
        self.view.display_message("Balanced Score calculated for the entire vocabulary.")

    def _export_consolidated_metrics(self, results_dir):
        self.view.display_message(f"\n--- Phase 7: Exporting consolidated results to {os.path.basename(results_dir)} ---")
        ext = self.file_manager.extension
        self.file_manager.save(os.path.join(results_dir, f"CF_RESULTS{ext}"), dict(self.cf))
        self.file_manager.save(os.path.join(results_dir, f"DF_RESULTS{ext}"), dict(self.df))
        self.file_manager.save(os.path.join(results_dir, f"IDF_RESULTS{ext}"), self.idf)
        self.file_manager.save(os.path.join(results_dir, f"BALANCED_SCORE{ext}"), self.balanced_scores)
        self.view.display_message(f"Consolidated metrics saved to {results_dir}")
        self.view.display_message("\n>>> All metrics successfully calculated and exported! <<<")

# ==============================================================================
# 6. BOOK CLUSTERER (New Component)
# ==============================================================================
class BookClusterer:
    """Identifies book categories based on TF-IDF scores of predefined keywords."""
    def __init__(self, view, file_manager, paths):
        self.view = view
        self.file_manager = file_manager
        self.paths = paths
        # Simple keyword lists. These can be expanded for better accuracy.
        self.categories = {
            'mathematics': ['math', 'calculus', 'algebra', 'geometry', 'equation', 'theorem', 'integral', 'derivative'],
            'physics': ['physics', 'force', 'energy', 'mass', 'velocity', 'gravity', 'quantum', 'relativity', 'thermodynamics'],
            'chemistry': ['chemistry', 'element', 'compound', 'reaction', 'molecule', 'acid', 'base', 'organic', 'inorganic'],
            'programming': ['python', 'java', 'code', 'algorithm', 'function', 'class', 'variable', 'pointer', 'software', 'database']
        }

    def categorize_books(self, export_format):
        """
        Calculates a score for each category for each book and assigns the book
        to the category with the highest score.
        """
        self.file_manager.set_strategy_by_format(export_format)
        tfidf_dir = self.paths[f'tfidf_{export_format}']
        ext = self.file_manager.extension

        if not os.path.exists(tfidf_dir) or not any(f.endswith(ext) for f in os.listdir(tfidf_dir)):
            # This is now handled by the presenter, but good to keep as a safeguard
            return {}

        clusters = defaultdict(list)
        tfidf_files = [f for f in os.listdir(tfidf_dir) if f.endswith(ext)]

        for i, filename in enumerate(tfidf_files, 1):
            doc_name = os.path.splitext(filename)[0]
            tfidf_data = self.file_manager.load(os.path.join(tfidf_dir, filename))
            
            category_scores = defaultdict(float)
            for category, keywords in self.categories.items():
                score = sum(tfidf_data.get(word, 0) for word in keywords)
                category_scores[category] = score

            if any(s > 0 for s in category_scores.values()):
                best_category = max(category_scores, key=category_scores.get)
                clusters[best_category].append(doc_name)
        
        return clusters

# ==============================================================================
# 7. FACADE (MODEL)
# ==============================================================================
class TextAnalysisModel:
    def __init__(self, view):
        self.view = view
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(script_dir, "DATA")
        
        self.paths = {
            'books_txt': os.path.join(self.data_dir, "FILES_TXT"),
            'books_msgpack': os.path.join(self.data_dir, "FILES_MSGPACK"),
            'tf_json': os.path.join(self.data_dir, "TF_RESULTS_JSON"),
            'tf_msgpack': os.path.join(self.data_dir, "TF_RESULTS_MSGPACK"),
            'tfidf_json': os.path.join(self.data_dir, "TFIDF_RESULTS_JSON"),
            'tfidf_msgpack': os.path.join(self.data_dir, "TFIDF_RESULTS_MSGPACK"),
            'results_json': os.path.join(self.data_dir, "RESULTS_JSON"),
            'results_msgpack': os.path.join(self.data_dir, "RESULTS_MSGPACK")
        }
        for path in self.paths.values(): os.makedirs(path, exist_ok=True)

        # --- Instantiate Components ---
        self.file_manager = FileManager(self.view)
        self.converter = DocumentConverter(self.view, self.file_manager, self.paths['books_txt'], self.paths['books_msgpack'])
        self.calculator = MetricsCalculator(self.view, self.file_manager, self.paths)
        self.clusterer = BookClusterer(self.view, self.file_manager, self.paths)

    def convert_pdfs_to_txt(self, folder_path):
        self.converter.convert_pdfs_to_txt(folder_path)

    def convert_txt_to_msgpack(self):
        self.converter.convert_txt_to_msgpack()

    def compute_and_export_metrics(self, export_format):
        if export_format not in ['json', 'msgpack']:
            self.view.display_error("Invalid export format specified. Use 'json' or 'msgpack'.")
            return
        self.view.display_message(f"\n>>> Starting process for '{export_format.upper()}' format <<<")
        self.calculator.run(export_format)

    def get_book_categories(self, export_format):
        # The presenter will call this method directly. No need for console messages here.
        return self.clusterer.categorize_books(export_format)
