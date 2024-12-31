import cv2
import os
import time
from PIL import Image
import pandas as pd
import google.generativeai as genai
from google.generativeai import GenerativeModel
from PyQt6.QtCore import QThread, pyqtSignal
from tenacity import retry, stop_after_attempt, wait_exponential

class VideoAnalyzer(QThread):
    progress_updated = pyqtSignal(int, str)
    analysis_complete = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, input_video, output_folder, api_key=None, settings=None):
        super().__init__()
        self.input_video = input_video
        self.output_folder = output_folder
        self.api_key = api_key or ""
        self.settings = settings or {
            'frame_position': 0.5,  # Posisi frame (0.0 - 1.0)
            'request_delay': 2,
            'max_retries': 3
        }
        self.stop_requested = False
        self.model = None
        self.setup_api()

    def setup_api(self):
        try:
            if not self.api_key:
                raise ValueError("API Key tidak ditemukan!")
            
            genai.configure(api_key=self.api_key)
            self.model = GenerativeModel(self.settings.get('selected_model', 'gemini-1.5-flash'))
            self.progress_updated.emit(0, "API initialized successfully")
        except Exception as e:
            self.error_occurred.emit(f"API Setup Error: {str(e)}")

    def extract_frame(self, video_path, position=0.5):
        try:
            # Buka video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Error opening video file")

            # Dapatkan total frame
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Hitung frame yang akan diambil
            frame_number = int(total_frames * position)
            
            # Set posisi video ke frame yang diinginkan
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Baca frame
            ret, frame = cap.read()
            if not ret:
                raise Exception("Error reading frame")

            # Konversi BGR ke RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Konversi ke PIL Image
            image = Image.fromarray(frame_rgb)
            
            # Resize jika terlalu besar
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple([int(x * ratio) for x in image.size])
                image = image.resize(new_size, Image.LANCZOS)

            cap.release()
            return image

        except Exception as e:
            self.error_occurred.emit(f"Error extracting frame: {str(e)}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def analyze_frame(self, image):
        try:
            # Add delay between requests
            time.sleep(self.settings.get('request_delay', 2))

            prompt = """Analyze this video frame and provide details in the exact format below:
            Filename: [original video filename]
            Title: [descriptive title for the video, max 200 characters]
            Keywords: [relevant keywords, minimum 35 keywords and max 50 keywords, separated by commas]
            Category: [numerical category code based on:
            1. Animals
            2. Buildings and Architecture
            3. Business
            4. Drinks
            5. The Environment
            6. States of Mind
            7. Food
            8. Graphic Resources
            9. Hobbies and Leisure
            10. Industry
            11. Landscape
            12. Lifestyle
            13. People
            14. Plants and Flowers
            15. Culture and Religion
            16. Science
            17. Social Issues
            18. Sports
            19. Technology
            20. Transport
            21. Travel]
            Scene Description: [brief description of the scene]
            Releases: [leave empty if no model/property releases needed]
            """

            response = self.model.generate_content([prompt, image])
            response.resolve()
            return response.text

        except Exception as e:
            if "429" in str(e):
                self.error_occurred.emit("API quota exceeded, waiting before retry...")
                time.sleep(60)
                raise
            else:
                self.error_occurred.emit(f"Error analyzing frame: {str(e)}")
                return None

    def parse_analysis(self, filename, analysis_text):
        try:
            lines = [line.strip() for line in analysis_text.split('\n') if line.strip()]
            result = {
                'Filename': filename,
                'Title': '',
                'Keywords': '',
                'Category': '',
                'Scene Description': '',
                'Releases': ''
            }

            for line in lines:
                if line.startswith('Title:'):
                    result['Title'] = line.replace('Title:', '').strip()[:200]
                elif line.startswith('Keywords:'):
                    result['Keywords'] = line.replace('Keywords:', '').strip()
                elif line.startswith('Category:'):
                    result['Category'] = line.replace('Category:', '').strip()
                elif line.startswith('Scene Description:'):
                    result['Scene Description'] = line.replace('Scene Description:', '').strip()
                elif line.startswith('Releases:'):
                    result['Releases'] = line.replace('Releases:', '').strip()

            return result

        except Exception as e:
            self.error_occurred.emit(f"Error parsing analysis: {str(e)}")
            return None

    def run(self):
        try:
            # Create output folder if it doesn't exist
            os.makedirs(self.output_folder, exist_ok=True)

            # Extract filename
            video_filename = os.path.basename(self.input_video)
            
            self.progress_updated.emit(10, "Extracting frame from video...")
            
            # Extract frame
            frame = self.extract_frame(
                self.input_video, 
                position=self.settings.get('frame_position', 0.5)
            )
            
            if not frame:
                self.error_occurred.emit("Failed to extract frame from video")
                return

            self.progress_updated.emit(40, "Analyzing frame...")

            # Analyze frame
            analysis = self.analyze_frame(frame)
            if not analysis:
                self.error_occurred.emit("Failed to analyze frame")
                return

            self.progress_updated.emit(70, "Processing analysis results...")

            # Parse results
            result = self.parse_analysis(video_filename, analysis)
            if not result:
                self.error_occurred.emit("Failed to parse analysis results")
                return

            # Save frame
            frame_path = os.path.join(self.output_folder, f"{video_filename}_frame.jpg")
            frame.save(frame_path)

            # Save results
            df = pd.DataFrame([result])
            csv_path = os.path.join(self.output_folder, f"{video_filename}_analysis.csv")
            df.to_csv(csv_path, index=False)

            self.progress_updated.emit(100, "Analysis completed successfully!")
            self.analysis_complete.emit(df)

        except Exception as e:
            self.error_occurred.emit(f"An error occurred: {str(e)}")

    def get_supported_formats(self):
        return ('.mp4', '.avi', '.mov', '.mkv')

    def validate_video(self, video_path):
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False
            cap.release()
            return True
        except:
            return False

class VideoBatchAnalyzer(QThread):
    overall_progress_updated = pyqtSignal(int)
    current_progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    analysis_complete = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, video_files, output_folder, api_key=None, settings=None):
        super().__init__()
        self.video_files = video_files
        self.output_folder = output_folder
        self.api_key = api_key
        self.settings = settings or {}
        self.stop_requested = False
        self.results = []

    def run(self):
        try:
            total_videos = len(self.video_files)
            
            for index, video_file in enumerate(self.video_files, 1):
                if self.stop_requested:
                    self.status_updated.emit("Analysis stopped by user")
                    break

                self.status_updated.emit(f"\nProcessing video {index}/{total_videos}: {os.path.basename(video_file)}")
                
                # Create analyzer for current video
                analyzer = VideoAnalyzer(
                    input_video=video_file,
                    output_folder=self.output_folder,
                    api_key=self.api_key,
                    settings=self.settings
                )

                # Connect signals for current video progress
                analyzer.progress_updated.connect(
                    lambda value, msg: self.current_progress_updated.emit(value)
                )
                analyzer.error_occurred.connect(self.error_occurred.emit)

                # Process video
                try:
                    frame = analyzer.extract_frame(video_file, self.settings.get('frame_position', 0.5))
                    if frame:
                        analysis = analyzer.analyze_frame(frame)
                        if analysis:
                            result = analyzer.parse_analysis(os.path.basename(video_file), analysis)
                            if result:
                                self.results.append(result)
                                
                                # Save frame
                                frame_path = os.path.join(
                                    self.output_folder, 
                                    f"{os.path.basename(video_file)}_frame.jpg"
                                )
                                frame.save(frame_path)

                except Exception as e:
                    self.error_occurred.emit(f"Error processing {os.path.basename(video_file)}: {str(e)}")
                    continue

                # Update overall progress
                overall_progress = int((index / total_videos) * 100)
                self.overall_progress_updated.emit(overall_progress)

            # Save final results
            if self.results:
                df = pd.DataFrame(self.results)
                csv_path = os.path.join(self.output_folder, 'batch_video_analysis.csv')
                df.to_csv(csv_path, index=False)

            self.analysis_complete.emit(self.results)

        except Exception as e:
            self.error_occurred.emit(f"An error occurred during batch processing: {str(e)}")