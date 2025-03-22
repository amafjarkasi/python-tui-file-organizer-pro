#!/usr/bin/env python3
"""
File Sorter TUI - A text-based user interface for sorting files into appropriate folders.
"""

import os
import shutil
import mimetypes
from pathlib import Path
import string
from typing import Dict, List, Optional, Tuple

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DirectoryTree, Footer, Header, Static, Label, ProgressBar, Select
from textual.binding import Binding
from textual.screen import Screen


class FileCategory:
    """Class to define file categories and their associated extensions."""
    
    CATEGORIES = {
        "Documents": [".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", 
                     ".md", ".markdown", ".tex", ".log", ".pages", ".numbers", ".key", ".odp", ".ods", ".epub", 
                     ".djvu", ".mobi", ".azw", ".azw3", ".fb2", ".oxps", ".xps"],
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".tiff", ".webp", ".ico", ".psd", ".ai", 
                  ".eps", ".indd", ".raw", ".cr2", ".nef", ".orf", ".sr2", ".heif", ".heic", ".xcf", ".cdr"],
        "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpg", ".mpeg", ".3gp", 
                  ".3g2", ".ogv", ".vob", ".swf", ".m2ts", ".mts", ".ts", ".divx", ".f4v", ".rm", ".rmvb", ".ogm"],
        "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus", ".aiff", ".alac", ".ape", 
                 ".mid", ".midi", ".amr", ".ac3", ".dts", ".ra", ".voc", ".pcm", ".dsf", ".dff", ".mka", ".au"],
        "Archives": [".zip", ".rar", ".tar", ".gz", ".7z", ".bz2", ".xz", ".iso", ".tgz", ".tbz2", ".txz", 
                    ".cab", ".deb", ".rpm", ".pkg", ".dmg", ".z", ".lzma", ".lz", ".lz4", ".lzo", ".zst", ".arj"],
        "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h", ".php", ".rb", ".go", ".rs", ".ts", 
                ".swift", ".kt", ".kts", ".scala", ".sc", ".dart", ".lua", ".pl", ".pm", ".sh", ".bash", ".ps1", 
                ".bat", ".cmd", ".sql", ".r", ".jsx", ".tsx", ".vue", ".elm", ".clj", ".ex", ".exs", ".erl", ".hrl", 
                ".hs", ".lhs", ".fs", ".fsx", ".ml", ".mli", ".groovy", ".cs", ".vb", ".xaml", ".xml", ".json", 
                ".yaml", ".yml", ".toml", ".ini", ".config", ".cmake", ".make", ".gradle", ".m", ".mm", ".f", 
                ".f90", ".f95", ".f03", ".f08", ".asm", ".s", ".gitignore", ".dockerignore", ".editorconfig"],
        "Executables": [".exe", ".msi", ".app", ".dmg", ".deb", ".rpm", ".apk", ".jar", ".war", ".dll", ".so", 
                       ".dylib", ".bin", ".run", ".bat", ".cmd", ".com", ".gadget", ".vb", ".vbs", ".ps1", ".msc"],
        "Fonts": [".ttf", ".otf", ".woff", ".woff2", ".eot", ".fnt", ".fon", ".bdf", ".pfb", ".pfm", ".afm", ".pfa"],
        "Spreadsheets": [".xlsx", ".xls", ".xlsm", ".xlsb", ".numbers", ".ods", ".csv", ".tsv", ".dif", ".sylk", ".dbf"],
        "Presentations": [".pptx", ".ppt", ".pps", ".ppsx", ".odp", ".key", ".gslides"],
        "Databases": [".db", ".sqlite", ".sqlite3", ".mdb", ".accdb", ".sql", ".bak", ".dbf", ".frm", ".ibd", ".myd", ".myi"],
        "3D_Models": [".obj", ".fbx", ".3ds", ".stl", ".dae", ".blend", ".max", ".ma", ".mb", ".c4d", ".lwo", ".lws"],
        "CAD": [".dwg", ".dxf", ".step", ".stp", ".iges", ".igs", ".x_t", ".x_b", ".sldprt", ".sldasm", ".ipt", ".iam"],
        "Vector": [".svg", ".ai", ".eps", ".pdf", ".cdr", ".afdesign", ".sketch"],
        "Ebooks": [".epub", ".mobi", ".azw", ".azw3", ".fb2", ".ibooks", ".cbr", ".cbz", ".pdf"],
        "Others": []  # Catch-all for other file types
    }
    
    @classmethod
    def get_category(cls, file_path: Path) -> str:
        """Determine the category of a file based on its extension."""
        extension = file_path.suffix.lower()
        
        for category, extensions in cls.CATEGORIES.items():
            if extension in extensions:
                return category
        
        return "Others"


class SortingResults(Screen):
    """Screen to display sorting results."""
    
    def __init__(self, results: Dict[str, List[Path]]):
        super().__init__()
        self.results = results
    
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the sorting results screen."""
        yield Header(show_clock=True)
        
        with Container(id="results-container"):
            yield Label("✓ Sorting Results", id="results-title")
            
            total_files = sum(len(files) for files in self.results.values())
            yield Label(f"Total files sorted: {total_files}", classes="results-summary")
            
            for category, files in self.results.items():
                if files:
                    with Container(classes="category-container"):
                        yield Label(f"{category} ({len(files)})", classes="category-title")
                        for file in files[:5]:  # Show only first 5 files to avoid clutter
                            yield Label(f"  • {file.name}", classes="file-item")
                        if len(files) > 5:
                            yield Label(f"  • ... and {len(files) - 5} more", classes="file-item-more")
            
        with Horizontal(id="button-row"):
            yield Button("Back to Main", id="back-button", variant="primary")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "back-button":
            self.app.pop_screen()


class FileOrganizerPro(App):
    """Main application class for the File Organizer Pro TUI."""
    
    TITLE = "🗂️ File Organizer Pro"
    
    CSS = """
    /* Global styles */
    Screen {
        background: $surface;
    }
    
    Label {
        color: $text;
    }
    
    Button {
        margin: 1 1;
        width: 100%;
        content-align: center middle;
        height: 3;
    }
    
    Button:hover {
        background: $accent-darken-1;
    }
    
    /* Main layout containers */
    #directory-container {
        width: 60%;
        height: 70%;
        border: solid $primary-background;
        border-title-color: $primary;
        background: $surface;
        padding: 0 1;
    }
    
    #controls-container {
        width: 40%;
        height: 70%;
        border: solid $primary-background;
        border-title-color: $primary;
        background: $surface;
        padding: 1 2;
    }
    
    #status-container {
        height: 30%;
        border: solid $primary-background;
        border-title-color: $primary;
        background: $surface;
        padding: 1 2;
    }
    
    /* Directory navigation */
    .section-title {
        margin-bottom: 1;
    }
    
    #drive-label {
        margin-top: 1;
        color: $primary;
        text-style: bold;
    }
    
    #drive-buttons {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    
    .drive-button {
        background: $primary;
        color: $surface;
        text-style: bold;
        margin: 0 1 1 0;
        width: auto;
        min-width: 16;
        height: 3;
        padding: 0 2;
    }
    
    .drive-button:hover {
        background: $primary-darken-1;
    }
    
    DirectoryTree {
        border: none;
        background: $surface;
        color: $text;
    }
    
    DirectoryTree:focus {
        border: none;
    }
    
    /* Control buttons */
    #app-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
        margin-top: 1;
        padding: 1;
    }
    
    #sort-button {
        background: $success-darken-2;
        color: white;
        text-style: bold;
        width: 100%;
        margin-top: 1;
        height: 3;
    }
    
    #sort-button:hover {
        background: $success-darken-3;
    }
    
    #results-button {
        background: $primary-darken-2;
        color: white;
        text-style: bold;
        width: 100%;
        height: 3;
        margin-top: 1;
    }
    
    #results-button:hover {
        background: $primary-darken-3;
    }
    
    #undo-button {
        background: $warning-darken-2;
        color: white;
        text-style: bold;
        width: 100%;
        height: 3;
        margin-top: 1;
    }
    
    #undo-button:hover {
        background: $warning-darken-3;
    }
    
    #sort-progress {
        margin-top: 2;
        height: 1;
    }
    
    /* Status area */
    #status-label {
        text-style: bold;
        color: $primary;
    }
    
    #status-text {
        margin-top: 1;
        height: 3;
        overflow: auto;
    }
    
    /* Results screen */
    #results-container {
        padding: 1 2;
        height: 90%;
        overflow: auto;
    }
    
    #results-title {
        text-style: bold;
        color: $success;
        text-align: center;
        margin-bottom: 1;
    }
    
    .results-summary {
        text-align: center;
        margin-bottom: 1;
        color: $text;
    }
    
    .category-container {
        margin-bottom: 1;
        border: panel $primary-background;
        padding: 0 1;
    }
    
    .category-title {
        color: $primary;
        text-style: bold;
    }
    
    .file-item {
        color: $text;
    }
    
    .file-item-more {
        color: $text-muted;
        text-style: italic;
    }
    
    #button-row {
        height: 3;
        align: center middle;
    }
    
    #back-button {
        width: 30%;
        height: 3;
        background: $primary;
        color: $surface;
        text-style: bold;
    }
    
    #back-button:hover {
        background: $primary-darken-1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "sort", "Sort Files"),
        Binding("r", "refresh", "Refresh"),
    ]
    
    def __init__(self):
        super().__init__()
        self.selected_directory: Optional[Path] = None
        self.last_sort_results: Dict[str, List[Path]] = {}
        self.undo_data: Dict[Path, Path] = {}  # Original path -> New path
        self.current_root: str = "/"  # Start at root directory
        
    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header(show_clock=True, name=self.TITLE)
        
        with Horizontal():
            with Container(id="directory-container"):
                yield Label("📁 Select a directory to sort:", classes="section-title")
                
                # Add a clear label for the drive selector
                yield Label("💾 Available Drives:", id="drive-label")
                
                # Create a horizontal container for drive buttons
                with Horizontal(id="drive-buttons"):
                    # Get available drives and create buttons for each
                    for drive, label in self.get_available_drives():
                        yield Button(label, id=f"drive-{drive[0]}", classes="drive-button")
                
                # Directory tree - provide a default path
                default_path = "C:\\" if os.path.exists("C:\\") else str(Path.home())
                yield DirectoryTree(path=default_path, id="directory-tree")
            
            with Vertical(id="controls-container"):
                yield Button("📊 Sort Files", id="sort-button")
                yield Button("📋 Show Results", id="results-button", disabled=True)
                yield Button("↩ Undo Last Sort", id="undo-button", disabled=True)
                yield ProgressBar(total=100, id="sort-progress")
        
        with Container(id="status-container"):
            yield Label("Status:", id="status-label")
            yield Static("Ready. Select a directory to begin.", id="status-text")
        
        yield Footer()
    
    def get_available_drives(self) -> List[Tuple[str, str]]:
        """Get available drives on Windows for the Select widget."""
        drives = []
        
        # Add Windows drives
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    volumeNameBuffer = ctypes.create_unicode_buffer(1024)
                    fileSystemNameBuffer = ctypes.create_unicode_buffer(1024)
                    
                    rc = kernel32.GetVolumeInformationW(
                        ctypes.c_wchar_p(drive),
                        volumeNameBuffer,
                        ctypes.sizeof(volumeNameBuffer),
                        None,  # serial number
                        None,  # max component length
                        None,  # file system flags
                        fileSystemNameBuffer,
                        ctypes.sizeof(fileSystemNameBuffer)
                    )
                    
                    if rc != 0 and volumeNameBuffer.value:
                        # Format with more space and clear labeling
                        drives.append((drive, f"{letter}: - {volumeNameBuffer.value}"))
                    else:
                        drives.append((drive, f"{letter}:"))
                except Exception as e:
                    # Fall back to simple label if there's an error
                    drives.append((drive, f"{letter}:"))
        
        # Log the drives found for debugging
        print(f"Available drives: {drives}")
        
        return drives
    
    def on_mount(self) -> None:
        """Initialize the application when mounted."""
        # Focus the directory tree
        directory_tree = self.query_one(DirectoryTree)
        directory_tree.focus()
        
        # Hide progress bar initially
        self.query_one("#sort-progress").display = False
    
    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        """Handle directory selection events."""
        self.selected_directory = Path(event.path)
        self.update_status(f"Selected directory: {self.selected_directory}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        # Handle drive selection buttons
        if button_id and button_id.startswith("drive-"):
            drive_letter = button_id.split("-")[1]
            self.update_directory_tree(f"{drive_letter}:\\")
        elif button_id == "sort-button":
            self.action_sort()
        elif button_id == "results-button":
            self.show_results()
        elif button_id == "undo-button":
            self.undo_sort()
    
    def update_directory_tree(self, root_path: str) -> None:
        """Update the directory tree with a new root path."""
        try:
            self.current_root = root_path
            directory_tree = self.query_one(DirectoryTree)
            
            # Use path property instead of root
            directory_tree.path = root_path
            self.update_status(f"Browsing: {root_path}")
        except Exception as e:
            self.update_status(f"Error changing directory: {str(e)}")
    
    def action_sort(self) -> None:
        """Sort files in the selected directory."""
        if not self.selected_directory:
            self.update_status("No directory selected. Please select a directory first.")
            return
        
        self.update_status(f"Sorting files in {self.selected_directory}...")
        progress_bar = self.query_one("#sort-progress")
        progress_bar.display = True
        
        # Get all files in the selected directory (non-recursive)
        files = [f for f in self.selected_directory.iterdir() if f.is_file()]
        
        if not files:
            self.update_status("No files found in the selected directory.")
            progress_bar.display = False
            return
        
        # Reset results and undo data
        self.last_sort_results = {category: [] for category in FileCategory.CATEGORIES.keys()}
        self.undo_data = {}
        
        # First pass: categorize files without moving them
        files_by_category = {}
        for file_path in files:
            category = FileCategory.get_category(file_path)
            if category not in files_by_category:
                files_by_category[category] = []
            files_by_category[category].append(file_path)
        
        # Second pass: create only needed directories and move files
        total_files = len(files)
        processed_files = 0
        
        for category, category_files in files_by_category.items():
            if not category_files:
                continue  # Skip if no files for this category
                
            # Create category directory only if it has files
            category_dir = self.selected_directory / category
            if not category_dir.exists():
                category_dir.mkdir(exist_ok=True)
            
            # Move files for this category
            for file_path in category_files:
                # Skip if file is already in its category directory
                if file_path.parent == category_dir:
                    continue
                
                # Create a new path for the file
                new_path = category_dir / file_path.name
                
                # Handle filename conflicts
                counter = 1
                original_stem = file_path.stem
                while new_path.exists():
                    new_stem = f"{original_stem}_{counter}"
                    new_path = category_dir / f"{new_stem}{file_path.suffix}"
                    counter += 1
                
                # Move the file
                try:
                    shutil.move(str(file_path), str(new_path))
                    self.last_sort_results[category].append(new_path)
                    self.undo_data[new_path] = file_path
                except Exception as e:
                    self.update_status(f"Error moving {file_path.name}: {str(e)}")
                
                # Update progress
                processed_files += 1
                progress = int(processed_files / total_files * 100)
                progress_bar.update(progress=progress)
        
        # Enable results and undo buttons
        self.query_one("#results-button").disabled = False
        self.query_one("#undo-button").disabled = False
        
        # Update status
        total_sorted = sum(len(files) for files in self.last_sort_results.values())
        self.update_status(f"Sorting complete. {total_sorted} files sorted into categories.")
        
        # Refresh the directory tree
        self.action_refresh()
    
    def show_results(self) -> None:
        """Show the results of the last sort operation."""
        if not self.last_sort_results:
            self.update_status("No sorting results to show.")
            return
        
        self.push_screen(SortingResults(self.last_sort_results))
    
    def undo_sort(self) -> None:
        """Undo the last sort operation."""
        if not self.undo_data:
            self.update_status("Nothing to undo.")
            return
        
        self.update_status("Undoing last sort operation...")
        progress_bar = self.query_one("#sort-progress")
        progress_bar.display = True
        
        # Track category directories to check if they're empty after moving files
        category_dirs = set()
        
        total_files = len(self.undo_data)
        for i, (new_path, original_path) in enumerate(self.undo_data.items()):
            try:
                if new_path.exists():
                    # Store the parent directory to check if it's empty later
                    category_dirs.add(new_path.parent)
                    
                    # Move the file back to its original location
                    shutil.move(str(new_path), str(original_path))
            except Exception as e:
                self.update_status(f"Error undoing move for {new_path.name}: {str(e)}")
            
            # Update progress
            progress = int((i + 1) / total_files * 100)
            progress_bar.update(progress=progress)
        
        # Remove empty category directories
        removed_dirs = 0
        for directory in category_dirs:
            try:
                # Check if directory exists and is empty
                if directory.exists() and not any(directory.iterdir()):
                    directory.rmdir()
                    removed_dirs += 1
            except Exception as e:
                self.update_status(f"Error removing directory {directory.name}: {str(e)}")
        
        status_message = "Undo complete. Files restored to their original locations."
        if removed_dirs > 0:
            status_message += f" Removed {removed_dirs} empty directories."
        
        self.update_status(status_message)
        self.undo_data = {}
        self.last_sort_results = {}
        
        # Disable results and undo buttons
        self.query_one("#results-button").disabled = True
        self.query_one("#undo-button").disabled = True
        
        # Refresh the directory tree
        self.action_refresh()
    
    def action_refresh(self) -> None:
        """Refresh the directory tree."""
        directory_tree = self.query_one(DirectoryTree)
        directory_tree.reload()
    
    def update_status(self, message: str) -> None:
        """Update the status message."""
        self.query_one("#status-text").update(message)


if __name__ == "__main__":
    # Initialize mimetypes
    mimetypes.init()
    
    # Run the application
    app = FileOrganizerPro()
    app.run()
