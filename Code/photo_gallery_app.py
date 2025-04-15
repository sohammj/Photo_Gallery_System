import sys
import os
import subprocess
import json
from datetime import datetime
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from PIL.ExifTags import TAGS, GPSTAGS
import exifread
import shutil
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QPushButton, QFileDialog, QListWidget, QTabWidget,
                              QLineEdit, QTextEdit, QComboBox, QGridLayout, QScrollArea,
                              QMessageBox, QListWidgetItem, QSplitter, QSlider, QToolBar,
                              QDialog, QCheckBox, QGroupBox, QRadioButton, QProgressBar,
                              QMenu, QStatusBar, QDateEdit)
from PySide6.QtGui import QPixmap, QImage, QIcon, QAction, QKeySequence, QColor, QPainter, QPen
from PySide6.QtCore import Qt, QSize, QThread, Signal, QDate, QRect, QBuffer, QByteArray, QPoint

# Path to your C++ executable
CPP_EXECUTABLE = "./photo_gallery"

class MetadataExtractor:
    @staticmethod
    def extract_from_image(image_path):
        """Extract metadata from image file"""
        try:
            # Basic file info
            file_info = {
                "filename": os.path.basename(image_path),
                "fileSize": os.path.getsize(image_path) // 1024,  # KB
            }
            
            # Extract EXIF using PIL
            image = Image.open(image_path)
            if hasattr(image, '_getexif') and image._getexif():
                exif = image._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'DateTimeOriginal':
                        try:
                            dt = datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                            file_info['dateTime'] = dt.strftime("%Y-%m-%d")
                        except:
                            pass
                    
                    # Handle GPS
                    if tag == 'GPSInfo':
                        gps_data = {}
                        for gps_tag_id, gps_value in value.items():
                            gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                            gps_data[gps_tag] = gps_value
                        
                        # Convert GPS coordinates to a readable format
                        if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
                            try:
                                lat = MetadataExtractor._convert_to_degrees(gps_data['GPSLatitude'])
                                lon = MetadataExtractor._convert_to_degrees(gps_data['GPSLongitude'])
                                file_info['location'] = f"{lat:.6f}, {lon:.6f}"
                            except:
                                pass
            
            # Use exifread for additional metadata
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f)
                
                # Try to detect source application
                if 'Image Software' in tags:
                    file_info['source'] = str(tags['Image Software'])
                elif 'Image Make' in tags:
                    make = str(tags['Image Make'])
                    model = str(tags.get('Image Model', ''))
                    file_info['source'] = f"{make} {model}".strip()
                    
            # Set defaults for missing fields
            if 'dateTime' not in file_info:
                file_info['dateTime'] = datetime.now().strftime("%Y-%m-%d")
            if 'location' not in file_info:
                file_info['location'] = "Unknown"
            if 'source' not in file_info:
                file_info['source'] = "Unknown"
                
            return file_info
            
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {
                "filename": os.path.basename(image_path),
                "fileSize": os.path.getsize(image_path) // 1024,
                "dateTime": datetime.now().strftime("%Y-%m-%d"),
                "location": "Unknown",
                "source": "Unknown"
            }
    
    @staticmethod
    def _convert_to_degrees(value):
        """Helper to convert GPS coordinates to decimal degrees"""
        d = float(value[0].numerator) / float(value[0].denominator)
        m = float(value[1].numerator) / float(value[1].denominator)
        s = float(value[2].numerator) / float(value[2].denominator)
        return d + (m / 60.0) + (s / 3600.0)

class CppBridge:
    """Bridge to the C++ executable"""
    @staticmethod
    def add_photo(filename, location, date_str, description, tags_str, file_size):
        """Add a photo using the C++ program"""
        try:
            cmd = [
                CPP_EXECUTABLE, "add_photo",
                filename, location, date_str, description, tags_str, str(file_size)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0, result.stdout
        except Exception as e:
            print(f"Error calling C++ program: {e}")
            return False, str(e)
    
    @staticmethod
    def get_all_photos():
        """Get all photos from the C++ program"""
        try:
            cmd = [CPP_EXECUTABLE, "get_all_photos"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except Exception as e:
            print(f"Error calling C++ program: {e}")
            return []

    @staticmethod
    def view_photo(photo_id):
        """Increment view count for a photo"""
        try:
            cmd = [CPP_EXECUTABLE, "view_photo", str(photo_id)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error calling C++ program: {e}")
            return False
    
    @staticmethod
    def delete_photo(photo_id):
        """Delete a photo"""
        try:
            cmd = [CPP_EXECUTABLE, "delete_photo", str(photo_id)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error calling C++ program: {e}")
            return False
    
    @staticmethod
    def search_photos(search_type, search_term):
        """Search photos"""
        try:
            cmd = [CPP_EXECUTABLE, "search", search_type, search_term]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except Exception as e:
            print(f"Error calling C++ program: {e}")
            return []
            
    @staticmethod
    def add_tag(photo_id, tag):
        """Add a tag to a photo"""
        try:
            cmd = [CPP_EXECUTABLE, "add_tag", str(photo_id), tag]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error calling C++ program: {e}")
            return False
            
    @staticmethod
    def sort_photos(sort_type, ascending=True):
        """Sort photos"""
        try:
            cmd = [CPP_EXECUTABLE, "sort", sort_type, "true" if ascending else "false"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except Exception as e:
            print(f"Error calling C++ program: {e}")
            return []
            
    @staticmethod
    def update_photo(photo_id, location, description, tags):
        """Update photo metadata"""
        try:
            cmd = [CPP_EXECUTABLE, "update_photo", str(photo_id), location, description, tags]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Error calling C++ program: {e}")
            return False

class ImageProcessingThread(QThread):
    processed = Signal(QImage)
    
    def __init__(self, image_path, operation, params=None):
        super().__init__()
        self.image_path = image_path
        self.operation = operation
        self.params = params or {}
    
    def run(self):
        try:
            # Open the image with PIL
            img = Image.open(self.image_path)
            
            # Apply the requested operation
            if self.operation == "rotate":
                angle = self.params.get("angle", 90)
                img = img.rotate(angle, expand=True)
            
            elif self.operation == "crop":
                left = self.params.get("left", 0)
                top = self.params.get("top", 0)
                right = self.params.get("right", img.width)
                bottom = self.params.get("bottom", img.height)
                img = img.crop((left, top, right, bottom))
            
            elif self.operation == "resize":
                width = self.params.get("width", img.width)
                height = self.params.get("height", img.height)
                img = img.resize((width, height))
            
            elif self.operation == "brightness":
                factor = self.params.get("factor", 1.0)
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(factor)
                
            elif self.operation == "contrast":
                factor = self.params.get("factor", 1.0)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(factor)
                
            elif self.operation == "blur":
                radius = self.params.get("radius", 2)
                img = img.filter(ImageFilter.GaussianBlur(radius))
                
            elif self.operation == "sharpen":
                img = img.filter(ImageFilter.SHARPEN)
                
            elif self.operation == "grayscale":
                img = img.convert('L')
                img = img.convert('RGB')  # Convert back to RGB for Qt compatibility
                
            elif self.operation == "sepia":
                # Create sepia effect
                img = img.convert('L')
                img = ImageOps.colorize(img, "#704214", "#C0A080")
                
            elif self.operation == "invert":
                img = ImageOps.invert(img.convert('RGB'))
                
            # Convert PIL image to QImage
            data = img.tobytes("raw", "RGB")
            qimage = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
            
            self.processed.emit(qimage)
            
        except Exception as e:
            print(f"Error processing image: {e}")

class ImageLoaderThread(QThread):
    image_loaded = Signal(int, QImage)
    
    def __init__(self, photo_id, image_path):
        super().__init__()
        self.photo_id = photo_id
        self.image_path = image_path
    
    def run(self):
        try:
            image = QImage(self.image_path)
            self.image_loaded.emit(self.photo_id, image)
        except Exception as e:
            print(f"Error loading image {self.image_path}: {e}")

class PhotoThumbnail(QWidget):
    clicked = Signal(dict, str)
    
    def __init__(self, photo_data, image_folder, parent=None):
        super().__init__(parent)
        self.photo_data = photo_data
        self.image_path = os.path.join(image_folder, photo_data['filename'])
        
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 200)
        self.image_label.setScaledContents(True)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        # Load a placeholder initially
        placeholder = QPixmap(200, 200)
        placeholder.fill(Qt.lightGray)
        self.image_label.setPixmap(placeholder)
        
        # Start loading the actual image in a thread
        self.loader_thread = ImageLoaderThread(photo_data['id'], self.image_path)
        self.loader_thread.image_loaded.connect(self.on_image_loaded)
        self.loader_thread.start()
        
        # Info label
        filename = photo_data['filename']
        if len(filename) > 20:
            filename = filename[:17] + "..."
            
        info_text = f"{filename}\n{photo_data['dateTime']}"
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.image_label)
        layout.addWidget(info_label)
        
        self.setFixedSize(220, 270)
    
    def on_image_loaded(self, photo_id, qimage):
        if photo_id == self.photo_data['id']:
            pixmap = QPixmap.fromImage(qimage)
            self.image_label.setPixmap(pixmap.scaled(
                200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.photo_data, self.image_path)
        super().mousePressEvent(event)

class ImageEditorDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.original_image = QImage(image_path)
        self.current_image = self.original_image.copy()
        self.crop_rect = None
        self.is_cropping = False
        self.crop_start_point = None
        
        self.setWindowTitle("Image Editor")
        self.setGeometry(100, 100, 800, 600)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QToolBar()
        
        # Create actions
        undo_action = QAction(QIcon(), "Undo", self)
        undo_action.triggered.connect(self.undo_edit)
        toolbar.addAction(undo_action)
        
        toolbar.addSeparator()
        
        rotate_left_action = QAction(QIcon(), "Rotate Left", self)
        rotate_left_action.triggered.connect(lambda: self.rotate_image(-90))
        toolbar.addAction(rotate_left_action)
        
        rotate_right_action = QAction(QIcon(), "Rotate Right", self)
        rotate_right_action.triggered.connect(lambda: self.rotate_image(90))
        toolbar.addAction(rotate_right_action)
        
        crop_action = QAction(QIcon(), "Crop", self)
        crop_action.triggered.connect(self.start_crop)
        toolbar.addAction(crop_action)
        
        toolbar.addSeparator()
        
        brightness_label = QLabel("Brightness:")
        toolbar.addWidget(brightness_label)
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(50, 150)
        self.brightness_slider.setValue(100)
        self.brightness_slider.setFixedWidth(100)
        self.brightness_slider.valueChanged.connect(self.adjust_brightness)
        toolbar.addWidget(self.brightness_slider)
        
        contrast_label = QLabel("Contrast:")
        toolbar.addWidget(contrast_label)
        
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(50, 150)
        self.contrast_slider.setValue(100)
        self.contrast_slider.setFixedWidth(100)
        self.contrast_slider.valueChanged.connect(self.adjust_contrast)
        toolbar.addWidget(self.contrast_slider)
        
        toolbar.addSeparator()
        
        effect_menu = QMenu("Effects", self)
        
        blur_action = QAction("Blur", self)
        blur_action.triggered.connect(lambda: self.apply_effect("blur"))
        effect_menu.addAction(blur_action)
        
        sharpen_action = QAction("Sharpen", self)
        sharpen_action.triggered.connect(lambda: self.apply_effect("sharpen"))
        effect_menu.addAction(sharpen_action)
        
        grayscale_action = QAction("Grayscale", self)
        grayscale_action.triggered.connect(lambda: self.apply_effect("grayscale"))
        effect_menu.addAction(grayscale_action)
        
        sepia_action = QAction("Sepia", self)
        sepia_action.triggered.connect(lambda: self.apply_effect("sepia"))
        effect_menu.addAction(sepia_action)
        
        invert_action = QAction("Invert", self)
        invert_action.triggered.connect(lambda: self.apply_effect("invert"))
        effect_menu.addAction(invert_action)
        
        effect_button = QPushButton("Effects")
        effect_button.setMenu(effect_menu)
        toolbar.addWidget(effect_button)
        
        main_layout.addWidget(toolbar)
        
        # Image display
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.update_image_display()
        
        self.scroll_area.setWidget(self.image_label)
        main_layout.addWidget(self.scroll_area)
        
        # Status bar
        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        main_layout.addLayout(button_layout)
        
        # Processing thread
        self.processing_thread = None
    
    def update_image_display(self):
        pixmap = QPixmap.fromImage(self.current_image)
        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()
        
        # Update status bar with image dimensions
        self.status_bar.showMessage(f"Dimensions: {self.current_image.width()} x {self.current_image.height()} pixels")
    
    def undo_edit(self):
        self.current_image = self.original_image.copy()
        self.update_image_display()
        self.brightness_slider.setValue(100)
        self.contrast_slider.setValue(100)
    
    def rotate_image(self, angle):
        self.processing_thread = ImageProcessingThread(self.image_path, "rotate", {"angle": angle})
        self.processing_thread.processed.connect(self.on_image_processed)
        self.processing_thread.start()
    
    def adjust_brightness(self, value):
        factor = value / 100.0
        self.processing_thread = ImageProcessingThread(self.image_path, "brightness", {"factor": factor})
        self.processing_thread.processed.connect(self.on_image_processed)
        self.processing_thread.start()
    
    def adjust_contrast(self, value):
        factor = value / 100.0
        self.processing_thread = ImageProcessingThread(self.image_path, "contrast", {"factor": factor})
        self.processing_thread.processed.connect(self.on_image_processed)
        self.processing_thread.start()
    
    def apply_effect(self, effect):
        self.processing_thread = ImageProcessingThread(self.image_path, effect)
        self.processing_thread.processed.connect(self.on_image_processed)
        self.processing_thread.start()
    
    def on_image_processed(self, qimage):
        self.current_image = qimage
        self.update_image_display()
    
    def start_crop(self):
        self.is_cropping = True
        self.crop_start_point = None
        self.crop_rect = None
        self.status_bar.showMessage("Click and drag to select crop area, then press Enter to crop or Esc to cancel")
    
    def mousePressEvent(self, event):
        if self.is_cropping:
            self.crop_start_point = self.scroll_area.mapToGlobal(event.pos())
            self.crop_rect = QRect(self.crop_start_point, QSize(0, 0))
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_cropping and self.crop_start_point:
            current_point = self.scroll_area.mapToGlobal(event.pos())
            self.crop_rect = QRect(self.crop_start_point, current_point).normalized()
            self.update()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self.is_cropping:
            # Finalize the crop rectangle
            current_point = self.scroll_area.mapToGlobal(event.pos())
            self.crop_rect = QRect(self.crop_start_point, current_point).normalized()
            
            # Convert global coordinates to image coordinates
            img_pos = self.image_label.mapFromGlobal(self.crop_start_point)
            crop_params = {
                "left": img_pos.x(),
                "top": img_pos.y(),
                "right": img_pos.x() + self.crop_rect.width(),
                "bottom": img_pos.y() + self.crop_rect.height()
            }
            
            # Apply the crop
            self.processing_thread = ImageProcessingThread(self.image_path, "crop", crop_params)
            self.processing_thread.processed.connect(self.on_image_processed)
            self.processing_thread.start()
            
            # Reset cropping state
            self.is_cropping = False
            self.crop_start_point = None
            self.crop_rect = None
        super().mouseReleaseEvent(event)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.is_cropping and self.crop_rect:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.drawRect(self.crop_rect)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.is_cropping:
            self.is_cropping = False
            self.crop_start_point = None
            self.crop_rect = None
            self.update()
        super().keyPressEvent(event)
    
    def get_edited_image(self):
        return self.current_image

class AddPhotoDialog(QDialog):
    def __init__(self, metadata, parent=None, is_edit=False):
        super().__init__(parent)
        self.metadata = metadata
        self.is_edit = is_edit
        
        # Set up dialog
        self.setWindowTitle("Add Photo" if not is_edit else "Edit Photo")
        self.setGeometry(300, 300, 500, 400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Form layout for metadata
        form = QGridLayout()
        
        # Filename (read-only)
        form.addWidget(QLabel("Filename:"), 0, 0)
        self.filename_field = QLineEdit(metadata.get("filename", ""))
        self.filename_field.setReadOnly(True)
        form.addWidget(self.filename_field, 0, 1)
        
        # Location
        form.addWidget(QLabel("Location:"), 1, 0)
        self.location_field = QLineEdit(metadata.get("location", ""))
        form.addWidget(self.location_field, 1, 1)
        
        # Date
        form.addWidget(QLabel("Date:"), 2, 0)
        self.date_field = QDateEdit()
        try:
            date_str = metadata.get("dateTime", datetime.now().strftime("%Y-%m-%d"))
            date_obj = QDate.fromString(date_str, "yyyy-MM-dd")
            self.date_field.setDate(date_obj)
        except:
            self.date_field.setDate(QDate.currentDate())
        form.addWidget(self.date_field, 2, 1)
        
        # Tags
        form.addWidget(QLabel("Tags:"), 3, 0)
        self.tags_field = QLineEdit(metadata.get("tags", ""))
        form.addWidget(self.tags_field, 3, 1)
        
        # Description
        form.addWidget(QLabel("Description:"), 4, 0)
        self.description_field = QTextEdit()
        self.description_field.setText(metadata.get("description", ""))
        form.addWidget(self.description_field, 4, 1)
        
        # Add form to main layout
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def get_metadata(self):
        # Update metadata with edited values
        self.metadata["location"] = self.location_field.text()
        self.metadata["dateTime"] = self.date_field.date().toString("yyyy-MM-dd")
        self.metadata["tags"] = self.tags_field.text()
        self.metadata["description"] = self.description_field.toPlainText()
        return self.metadata

class SlideshowDialog(QDialog):
    def __init__(self, photos, image_folder, parent=None):
        super().__init__(parent)
        self.photos = photos
        self.image_folder = image_folder
        self.current_index = 0
        
        self.setWindowTitle("Slideshow")
        self.setGeometry(100, 100, 800, 600)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        
        # Controls
        controls = QHBoxLayout()
        
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.show_previous)
        controls.addWidget(self.prev_button)
        
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_button)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.show_next)
        controls.addWidget(self.next_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        controls.addWidget(self.close_button)
        
        layout.addLayout(controls)
        
        # Load the first image
        self.show_current_image()
    
    def show_current_image(self):
        if self.photos and 0 <= self.current_index < len(self.photos):
            photo = self.photos[self.current_index]
            image_path = os.path.join(self.image_folder, photo['filename'])
            
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    self.image_label.width(), 
                    self.image_label.height(),
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(pixmap)
                self.setWindowTitle(f"Slideshow - {photo['filename']}")
    
    def show_previous(self):
        if self.photos:
            self.current_index = (self.current_index - 1) % len(self.photos)
            self.show_current_image()
    
    def show_next(self):
        if self.photos:
            self.current_index = (self.current_index + 1) % len(self.photos)
            self.show_current_image()
    
    def toggle_play(self):
        # Implement automatic slideshow here
        pass

class BatchProcessingDialog(QDialog):
    def __init__(self, photos, image_folder, parent=None):
        super().__init__(parent)
        self.photos = photos
        self.image_folder = image_folder
        
        self.setWindowTitle("Batch Processing")
        self.setGeometry(300, 300, 500, 400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Photo selection
        selection_group = QGroupBox("Select Photos")
        selection_layout = QVBoxLayout()
        
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.toggled.connect(self.toggle_all_photos)
        selection_layout.addWidget(self.select_all_checkbox)
        
        self.photo_list = QListWidget()
        for photo in self.photos:
            item = QListWidgetItem(photo['filename'])
            item.setData(Qt.UserRole, photo)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.photo_list.addItem(item)
        
        selection_layout.addWidget(self.photo_list)
        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)
        
        # Operations
        operations_group = QGroupBox("Select Operations")
        operations_layout = QVBoxLayout()
        
        self.resize_checkbox = QCheckBox("Resize")
        operations_layout.addWidget(self.resize_checkbox)
        
        resize_options = QHBoxLayout()
        resize_options.addWidget(QLabel("Width:"))
        self.width_field = QLineEdit("800")
        resize_options.addWidget(self.width_field)
        
        resize_options.addWidget(QLabel("Height:"))
        self.height_field = QLineEdit("600")
        resize_options.addWidget(self.height_field)
        
        operations_layout.addLayout(resize_options)
        
        self.grayscale_checkbox = QCheckBox("Convert to Grayscale")
        operations_layout.addWidget(self.grayscale_checkbox)
        
        self.add_tag_checkbox = QCheckBox("Add Tag to All")
        operations_layout.addWidget(self.add_tag_checkbox)
        
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("Tag:"))
        self.tag_field = QLineEdit()
        tag_layout.addWidget(self.tag_field)
        
        operations_layout.addLayout(tag_layout)
        
        operations_group.setLayout(operations_layout)
        layout.addWidget(operations_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        buttons = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_button)
        
        self.process_button = QPushButton("Process")
        self.process_button.clicked.connect(self.process_photos)
        buttons.addWidget(self.process_button)
        
        layout.addLayout(buttons)
    
    def toggle_all_photos(self, checked):
        for i in range(self.photo_list.count()):
            item = self.photo_list.item(i)
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
    
    def process_photos(self):
        # Get selected photos
        selected_photos = []
        for i in range(self.photo_list.count()):
            item = self.photo_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_photos.append(item.data(Qt.UserRole))
        
        if not selected_photos:
            QMessageBox.warning(self, "No Selection", "Please select at least one photo to process.")
            return
        
        # Get selected operations
        operations = []
        
        if self.resize_checkbox.isChecked():
            try:
                width = int(self.width_field.text())
                height = int(self.height_field.text())
                operations.append(("resize", {"width": width, "height": height}))
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for width and height.")
                return
        
        if self.grayscale_checkbox.isChecked():
            operations.append(("grayscale", {}))
        
        if self.add_tag_checkbox.isChecked():
            tag = self.tag_field.text().strip()
            if tag:
                operations.append(("add_tag", {"tag": tag}))
            else:
                QMessageBox.warning(self, "Missing Tag", "Please enter a tag to add.")
                return
        
        if not operations:
            QMessageBox.warning(self, "No Operations", "Please select at least one operation to perform.")
            return
        
        # Process the photos
        self.progress_bar.setValue(0)
        total_steps = len(selected_photos) * len(operations)
        current_step = 0
        
        for photo in selected_photos:
            for operation, params in operations:
                current_step += 1
                progress = int((current_step / total_steps) * 100)
                self.progress_bar.setValue(progress)
                
                if operation == "resize" or operation == "grayscale":
                    # Image processing operations
                    image_path = os.path.join(self.image_folder, photo['filename'])
                    
                    if operation == "resize":
                        # Resize the image
                        img = Image.open(image_path)
                        img = img.resize((params["width"], params["height"]))
                        img.save(image_path)
                    
                    elif operation == "grayscale":
                        # Convert to grayscale
                        img = Image.open(image_path)
                        img = img.convert('L')
                        img.save(image_path)
                
                elif operation == "add_tag":
                    # Database operation
                    CppBridge.add_tag(photo['id'], params["tag"])
        
        QMessageBox.information(self, "Processing Complete", "Batch processing has been completed successfully.")
        self.accept()

class PhotoGalleryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Photo Gallery System")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set up the image folder
        self.image_folder = "images"
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
        
        # Set up the main UI
        self.setup_ui()
        
        # Load photos
        self.load_photos()
    
    def setup_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Menu bar
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        add_action = QAction("Add Photos", self)
        add_action.setShortcut(QKeySequence("Ctrl+A"))
        add_action.triggered.connect(self.on_add_photos)
        file_menu.addAction(add_action)
        
        export_action = QAction("Export Selected", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.on_export_photos)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        
        slideshow_action = QAction("Slideshow", self)
        slideshow_action.triggered.connect(self.on_slideshow)
        edit_menu.addAction(slideshow_action)
        
        batch_action = QAction("Batch Processing", self)
        batch_action.triggered.connect(self.on_batch_processing)
        edit_menu.addAction(batch_action)
        
        # View menu
        view_menu = menu_bar.addMenu("View")
        
        sort_date_action = QAction("Sort by Date", self)
        sort_date_action.triggered.connect(lambda: self.on_sort("date"))
        view_menu.addAction(sort_date_action)
        
        sort_name_action = QAction("Sort by Name", self)
        sort_name_action.triggered.connect(lambda: self.on_sort("name"))
        view_menu.addAction(sort_name_action)
        
        sort_size_action = QAction("Sort by Size", self)
        sort_size_action.triggered.connect(lambda: self.on_sort("size"))
        view_menu.addAction(sort_size_action)
        
        sort_view_action = QAction("Sort by Views", self)
        sort_view_action.triggered.connect(lambda: self.on_sort("popularity"))
        view_menu.addAction(sort_view_action)
        
        # Toolbar at the top
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Add photo button
        add_button = QAction(QIcon(), "Add Photos", self)
        add_button.triggered.connect(self.on_add_photos)
        toolbar.addAction(add_button)
        
        toolbar.addSeparator()
        
        # Search controls
        toolbar.addWidget(QLabel("Search by:"))
        
        self.search_type = QComboBox()
        self.search_type.addItems(["Location", "Tag", "Date Range", "Description"])
        toolbar.addWidget(self.search_type)
        
        self.search_term = QLineEdit()
        self.search_term.setPlaceholderText("Search term...")
        self.search_term.setMinimumWidth(200)
        self.search_term.returnPressed.connect(self.on_search)
        toolbar.addWidget(self.search_term)
        
        search_button = QAction(QIcon(), "Search", self)
        search_button.triggered.connect(self.on_search)
        toolbar.addAction(search_button)
        
        reset_button = QAction(QIcon(), "Reset", self)
        reset_button.triggered.connect(self.load_photos)
        toolbar.addAction(reset_button)
        
        # Split view: gallery on left, details on right
        splitter = QSplitter(Qt.Horizontal)
        
        # Gallery area (scrollable grid of thumbnails)
        gallery_widget = QWidget()
        self.gallery_layout = QGridLayout(gallery_widget)
        
        gallery_scroll = QScrollArea()
        gallery_scroll.setWidgetResizable(True)
        gallery_scroll.setWidget(gallery_widget)
        
        splitter.addWidget(gallery_scroll)
        
        # Detail view
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        
        # Image view
        self.detail_image = QLabel()
        self.detail_image.setAlignment(Qt.AlignCenter)
        self.detail_image.setMinimumSize(400, 300)
        
        # Metadata fields
        metadata_grid = QGridLayout()
        
        row = 0
        labels = ["Filename:", "Location:", "Date:", "Source:", "Tags:", "File Size:", "View Count:"]
        self.metadata_fields = {}
        
        for label_text in labels:
            label = QLabel(label_text)
            field = QLabel()
            self.metadata_fields[label_text.replace(":", "")] = field
            metadata_grid.addWidget(label, row, 0)
            metadata_grid.addWidget(field, row, 1)
            row += 1
        
        # Description field
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.description_field = QTextEdit()
        self.description_field.setReadOnly(True)
        desc_layout.addWidget(self.description_field)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.edit_metadata_button = QPushButton("Edit Metadata")
        self.edit_metadata_button.clicked.connect(self.on_edit_metadata)
        button_layout.addWidget(self.edit_metadata_button)
        
        self.edit_image_button = QPushButton("Edit Image")
        self.edit_image_button.clicked.connect(self.on_edit_image)
        button_layout.addWidget(self.edit_image_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.on_delete_photo)
        button_layout.addWidget(self.delete_button)
        
        # Add layouts to detail view
        detail_layout.addWidget(self.detail_image)
        detail_layout.addLayout(metadata_grid)
        detail_layout.addLayout(desc_layout)
        detail_layout.addLayout(button_layout)
        
        splitter.addWidget(detail_widget)
        
        # Set initial splitter sizes
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
        
        self.setCentralWidget(main_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Initially hide the detail view elements
        self.detail_image.hide()
        for field in self.metadata_fields.values():
            field.hide()
        self.description_field.hide()
        self.edit_metadata_button.hide()
        self.edit_image_button.hide()
        self.delete_button.hide()
    
    def load_photos(self):
        # Clear existing thumbnails
        while self.gallery_layout.count():
            item = self.gallery_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get photos from C++ backend
        photos = CppBridge.get_all_photos()
        self.photos = photos
        
        if not photos:
            self.status_bar.showMessage("No photos found.")
            return
        
        # Create thumbnails
        row, col = 0, 0
        max_cols = 4
        
        for photo in photos:
            thumbnail = PhotoThumbnail(photo, self.image_folder, self)
            thumbnail.clicked.connect(self.on_thumbnail_clicked)
            self.gallery_layout.addWidget(thumbnail, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        self.status_bar.showMessage(f"Loaded {len(photos)} photos")
    
    def on_thumbnail_clicked(self, photo_data, image_path):
        # Show the selected photo in the detail view
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.detail_image.setPixmap(scaled_pixmap)
            self.detail_image.show()
        
        # Update metadata fields
        self.metadata_fields["Filename"].setText(photo_data['filename'])
        self.metadata_fields["Location"].setText(photo_data['location'])
        self.metadata_fields["Date"].setText(photo_data['dateTime'])
        self.metadata_fields["Tags"].setText(photo_data['tags'])
        self.metadata_fields["File Size"].setText(f"{photo_data['fileSize']} KB")
        self.metadata_fields["View Count"].setText(str(photo_data['viewCount']))
        
        # Set source if available
        if 'source' in photo_data:
            self.metadata_fields["Source"].setText(photo_data['source'])
        else:
            self.metadata_fields["Source"].setText("Unknown")
        
        # Update description
        self.description_field.setText(photo_data['description'])
        
        # Show all fields
        for field in self.metadata_fields.values():
            field.show()
        self.description_field.show()
        self.edit_metadata_button.show()
        self.edit_image_button.show()
        self.delete_button.show()
        
        # Store current photo data
        self.current_photo = photo_data
        self.current_image_path = image_path
        
        # Increment view count (using C++ logic)
        CppBridge.view_photo(photo_data['id'])
    
    def on_add_photos(self):
        # Open file dialog to select images
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            
            for file_path in selected_files:
                # Extract metadata from image
                metadata = MetadataExtractor.extract_from_image(file_path)
                
                # Create destination path in images folder
                dest_path = os.path.join(self.image_folder, metadata["filename"])
                
                # Copy file to images folder
                if not os.path.exists(dest_path):
                    try:
                        with open(file_path, 'rb') as src_file:
                            with open(dest_path, 'wb') as dest_file:
                                dest_file.write(src_file.read())
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Could not copy file: {e}")
                        continue
                
                # Show dialog to edit/confirm metadata
                dialog = AddPhotoDialog(metadata, self)
                if dialog.exec():
                    # Get edited metadata
                    metadata = dialog.get_metadata()
                    
                    # Add to database via C++ bridge
                    success, _ = CppBridge.add_photo(
                        metadata["filename"],
                        metadata["location"],
                        metadata["dateTime"],
                        metadata["description"],
                        metadata["tags"],
                        metadata["fileSize"]
                    )
                    
                    if not success:
                        QMessageBox.warning(self, "Error", "Failed to add photo to database")
            
            # Reload photos
            self.load_photos()
    
    def on_search(self):
        search_type = self.search_type.currentText().lower()
        search_term = self.search_term.text()
        
        if not search_term:
            self.load_photos()
            return
        
        # Map UI search types to C++ search types
        cpp_search_type_map = {
        "location": "location",
        "tag": "tag",  # Changed from "tag" to "prefix"
        "date range": "date_range",
        "description": "description"
        }
        
        cpp_search_type = cpp_search_type_map.get(search_type, "location")
        
        # Use C++ bridge to search
        results = CppBridge.search_photos(cpp_search_type, search_term)
        
        if not results:
            self.status_bar.showMessage(f"No photos found matching '{search_term}'")
            # Clear gallery but don't clear detail view
            while self.gallery_layout.count():
                item = self.gallery_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            return
        
        # Clear existing thumbnails
        while self.gallery_layout.count():
            item = self.gallery_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Display results
        row, col = 0, 0
        max_cols = 4
        
        for photo in results:
            thumbnail = PhotoThumbnail(photo, self.image_folder, self)
            thumbnail.clicked.connect(self.on_thumbnail_clicked)
            self.gallery_layout.addWidget(thumbnail, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        self.status_bar.showMessage(f"Found {len(results)} photos matching '{search_term}'")
    
    def on_edit_metadata(self):
        if not hasattr(self, 'current_photo'):
            return
        
        # Show dialog to edit metadata
        dialog = AddPhotoDialog(self.current_photo, self, is_edit=True)
        if dialog.exec():
            # Get edited metadata
            metadata = dialog.get_metadata()
            
            # Update in database using C++ bridge
            success = CppBridge.update_photo(
                self.current_photo['id'],
                metadata['location'],
                metadata['description'],
                metadata['tags']
            )
            
            if success:
                self.status_bar.showMessage("Photo metadata updated successfully")
                
                # Update current displayed metadata
                self.metadata_fields["Location"].setText(metadata['location'])
                self.metadata_fields["Date"].setText(metadata['dateTime'])
                self.metadata_fields["Tags"].setText(metadata['tags'])
                self.description_field.setText(metadata['description'])
                
                # Update current_photo
                self.current_photo.update(metadata)
                
                # Reload photos to reflect changes in gallery
                self.load_photos()
            else:
                QMessageBox.warning(self, "Error", "Failed to update photo metadata")
    
    def on_edit_image(self):
        if not hasattr(self, 'current_photo') or not hasattr(self, 'current_image_path'):
            return
        
        # Open image editor dialog
        editor = ImageEditorDialog(self.current_image_path, self)
        if editor.exec():
            # Get edited image
            edited_image = editor.get_edited_image()
            
            # Save edited image
            edited_image.save(self.current_image_path)
            
            # Update display
            pixmap = QPixmap.fromImage(edited_image)
            self.detail_image.setPixmap(pixmap.scaled(
                400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
            
            # Refresh the gallery thumbnails
            self.load_photos()
            
            self.status_bar.showMessage("Image edited successfully")
    
    def on_delete_photo(self):
        if not hasattr(self, 'current_photo'):
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {self.current_photo['filename']}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete from database using C++ bridge
            success = CppBridge.delete_photo(self.current_photo['id'])
            
            if success:
                # Try to delete the file
                try:
                    os.remove(self.current_image_path)
                except Exception as e:
                    print(f"Could not delete file: {e}")
                
                # Reload photos
                self.load_photos()
                
                # Hide detail view
                self.detail_image.hide()
                for field in self.metadata_fields.values():
                    field.hide()
                self.description_field.hide()
                self.edit_metadata_button.hide()
                self.edit_image_button.hide()
                self.delete_button.hide()
                
                self.status_bar.showMessage(f"Deleted photo: {self.current_photo['filename']}")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete photo")
    
    def on_sort(self, sort_type):
        # Sort photos using C++ backend
        sorted_photos = CppBridge.sort_photos(sort_type)
        
        if sorted_photos:
            self.photos = sorted_photos
            
            # Clear existing thumbnails
            while self.gallery_layout.count():
                item = self.gallery_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Display sorted photos
            row, col = 0, 0
            max_cols = 4
            
            for photo in sorted_photos:
                thumbnail = PhotoThumbnail(photo, self.image_folder, self)
                thumbnail.clicked.connect(self.on_thumbnail_clicked)
                self.gallery_layout.addWidget(thumbnail, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            self.status_bar.showMessage(f"Photos sorted by {sort_type}")
    
    def on_slideshow(self):
        if not hasattr(self, 'photos') or not self.photos:
            QMessageBox.information(self, "No Photos", "There are no photos to display in a slideshow.")
            return
        
        slideshow = SlideshowDialog(self.photos, self.image_folder, self)
        slideshow.exec()
    
    def on_batch_processing(self):
        if not hasattr(self, 'photos') or not self.photos:
            QMessageBox.information(self, "No Photos", "There are no photos to process.")
            return
        
        batch_dialog = BatchProcessingDialog(self.photos, self.image_folder, self)
        if batch_dialog.exec():
            # Reload photos to reflect changes
            self.load_photos()
    
    def on_export_photos(self):
        if not hasattr(self, 'current_photo'):
            QMessageBox.information(self, "No Selection", "Please select a photo to export.")
            return
        
        # Ask user for destination
        directory = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if not directory:
            return
        
        # Copy the file to destination
        source_path = self.current_image_path
        filename = self.current_photo['filename']
        dest_path = os.path.join(directory, filename)
        
        try:
            shutil.copy2(source_path, dest_path)
            self.status_bar.showMessage(f"Exported {filename} to {directory}")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export file: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PhotoGalleryApp()
    window.show()
    sys.exit(app.exec())