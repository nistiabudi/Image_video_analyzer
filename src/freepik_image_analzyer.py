import os
import time
import io
from PIL import Image
import pandas as pd
import google.generativeai as genai
from google.generativeai import GenerativeModel
from PyQt6.QtCore import QThread, pyqtSignal
from tenacity import retry, stop_after_attempt, wait_exponential


class FreepikImageAnalyzer(QThread):
    progress_updated = pyqtSignal(int, str)
    analysis_complete = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, input_folder, output_folder, model_source, api_key=None, settings=None):
        super().__init__()
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.model_source = model_source
        self.api_key = api_key or ""
        self.settings = settings or {
            'batch_size': 5,
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

    def process_image(self, image_path):
        try:
            # Open and process image
            img = Image.open(image_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large
            max_size = 1024
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple([int(x * ratio) for x in img.size])
                img = img.resize(new_size, Image.LANCZOS)
            
            return img

        except Exception as e:
            self.error_occurred.emit(f"Error processing image: {str(e)}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def analyze_image(self, image):
        try:
            # Add delay between requests
            time.sleep(self.settings.get('request_delay', 2))

            prompt = """Analyze this image and provide details in the exact format below:
            Filename: [original filename]
            Title: [give the descriptive title max 100 characters, Titles must be coherent and relevant.]
            Keywords: [coherent and relevant keywords, minimum 35 keywords and max 45 keywords, separated by commas. Do not repeat the same keywords over and over.]
            Prompt: [describe the image in a few sentences, be as detailed as possible and optimized when used in another generative AI. 500 characters max Enter the details and specs used to create the AI-generated image]
            """

            response = self.model.generate_content([prompt, image])
            response.resolve()
            return response.text

        except Exception as e:
            if "429" in str(e):
                self.error_occurred.emit("API quota exceeded, waiting before retry...")
                time.sleep(60)  # Wait for 1 minute
                raise  # Retry
            else:
                self.error_occurred.emit(f"Error analyzing image: {str(e)}")
                return None

    def parse_analysis(self, filename, analysis_text):
        try:
            lines = [line.strip() for line in analysis_text.split('\n') if line.strip()]
            result = {
                'Filename': filename,
                'Title': '',
                'Keywords': '',
                'Prompt': '',
                'Model': self.model_source
            }

            for line in lines:
                if line.startswith('Title:'):
                    result['Title'] = line.replace('Title:', '').strip()[:200]
                elif line.startswith('Keywords:'):
                    result['Keywords'] = line.replace('Keywords:', '').strip()
                elif line.startswith('Prompt:'):
                    result['Prompt'] = line.replace('Prompt:', '').strip()
                
            return result

        except Exception as e:
            self.error_occurred.emit(f"Error parsing analysis: {str(e)}")
            return None

    def run(self):
        try:
            data = []
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
            image_files = [f for f in os.listdir(self.input_folder) 
                         if f.lower().endswith(image_extensions)]
            
            total_files = len(image_files)
            if total_files == 0:
                self.error_occurred.emit("No image files found in the input folder")
                return

            # Create output folder if it doesn't exist
            os.makedirs(self.output_folder, exist_ok=True)

            # Progress tracking
            processed_count = 0
            batch = []
            batch_size = self.settings.get('batch_size', 5)

            for filename in image_files:
                if self.stop_requested:
                    self.progress_updated.emit(
                        int(processed_count / total_files * 100),
                        "Analysis stopped by user."
                    )
                    break

                try:
                    image_path = os.path.join(self.input_folder, filename)
                    self.progress_updated.emit(
                        int(processed_count / total_files * 100),
                        f"Processing {filename}..."
                    )

                    # Process image
                    image = self.process_image(image_path)
                    if image:
                        batch.append((filename, image))

                        # Process batch when full or last item
                        if len(batch) >= batch_size or filename == image_files[-1]:
                            for batch_filename, batch_image in batch:
                                if self.stop_requested:
                                    break

                                analysis = self.analyze_image(batch_image)
                                if analysis:
                                    result = self.parse_analysis(batch_filename, analysis)
                                    if result:
                                        data.append(result)
                                        processed_count += 1
                                        self.progress_updated.emit(
                                            int(processed_count / total_files * 100),
                                            f"Successfully analyzed {batch_filename}"
                                        )

                            # Clear batch and wait before next batch
                            batch = []
                            if not self.stop_requested and filename != image_files[-1]:
                                time.sleep(self.settings.get('request_delay', 2))

                except Exception as e:
                    self.error_occurred.emit(f"Error processing {filename}: {str(e)}")
                    continue

            # Save results
            if data:
                df = pd.DataFrame(data)
                csv_path = os.path.join(self.output_folder, 'Freepik_Image_analysis.csv')
                df.to_csv(csv_path, index=False, sep=';')
                
                # Save progress file
                progress_path = os.path.join(self.output_folder, 'analysis_progress.json')
                with open(progress_path, 'w') as f:
                    import json
                    json.dump({
                        'completed': [d['Filename'] for d in data],
                        'total': total_files,
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    }, f)

                self.analysis_complete.emit(df)
            else:
                self.error_occurred.emit("No data was processed successfully")

        except Exception as e:
            self.error_occurred.emit(f"An error occurred: {str(e)}")

    def validate_api_key(self):
        if not self.api_key:
            return False
        # Add additional validation if needed
        return True

    def get_supported_formats(self):
        return ('.jpg', '.jpeg', '.png', '.gif', '.bmp')

    def estimate_processing_time(self, file_count):
        # Rough estimation based on settings
        time_per_image = self.settings.get('request_delay', 2) + 5  # 5 seconds for processing
        batch_size = self.settings.get('batch_size', 5)
        total_batches = file_count // batch_size + (1 if file_count % batch_size else 0)
        
        return total_batches * (time_per_image * batch_size + 10)  # 10 seconds between batches

    def check_output_path(self):
        try:
            os.makedirs(self.output_folder, exist_ok=True)
            test_file = os.path.join(self.output_folder, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True
        except Exception:
            return False
        
    def get_supported_formats(self):
        """Return supported image formats"""
        return ('.jpg', '.jpeg', '.png', '.gif', '.bmp')

    def validate_file(self, file_path):
        """Validate if file is supported"""
        return file_path.lower().endswith(self.get_supported_formats())
    
    
    
