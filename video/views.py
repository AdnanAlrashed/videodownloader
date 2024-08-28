import os
import re
import logging
import yt_dlp
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.conf import settings
import tempfile
import shutil

# Configure logger
logger = logging.getLogger(__name__)

# Define a global variable to store the status of the download
download_status = {"status": "", "filename": ""}

def index(request):
    """
    Render the main page where users can input video URLs.
    """
    return render(request, 'video/index.html')

def validate_video_url(url):
    """
    Function to validate if the provided URL is a valid video URL.
    """
    video_url_pattern = re.compile(r'^(https?://)?(www\.)?(youtube|facebook|instagram|twitter)\.com/.+$')
    if not video_url_pattern.match(url):
        raise ValidationError("الرابط المدخل غير صالح. الرجاء إدخال رابط صالح.")

def sanitize_filename(filename):
    """Sanitize the filename to ensure it's filesystem-friendly."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def progress_hook(d):
    global download_status
    
    if d['status'] == 'downloading':
        # Calculate percentage completed
        total_bytes = int(d.get('total_bytes', 0))
        downloaded_bytes = int(d.get('downloaded_bytes', 0))
        percentage = min((downloaded_bytes / total_bytes) * 100, 100)
        
        # Update the global status with the current percentage
        download_status["status"] = f"{percentage:.2f}%"
    
    elif d['status'] == 'finished':
        # Update the global status to finished
        download_status["status"] = "finished"
        download_status["filename"] = d['filename']
        logger.info(f"Done downloading: {d['filename']}")

@csrf_exempt
def get_video_info(request):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        
        try:
            validate_video_url(video_url)
            ydl_opts = {
                'quiet': True,
                'format': 'bestaudio/best',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=False)
                return JsonResponse({
                    'title': info_dict.get('title', 'Unknown'),
                    'uploader': info_dict.get('uploader', 'Unknown'),
                    'duration': info_dict.get('duration', 0),
                    'thumbnail': info_dict.get('thumbnail', ''),
                    'video_url': info_dict.get('url', '')  # Add this if available
                })
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'حدث خطأ أثناء جلب معلومات الفيديو: ' + str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def download_video(request):
    global download_status  # Reference the global variable

    logger.info(f"Starting download process for URL: {request.POST.get('video_url')}")

    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        download_type = request.POST.get('download_type')
        quality = request.POST.get('quality', '720')  # Default to 720p if not provided
        audio_format = request.POST.get('audio_format', 'mp3')  # Default to mp3 if not provided
        
        try:
            validate_video_url(video_url)
            
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, '%(title)s.%(ext)s')
            
            ydl_opts = {
                'format': f'bestvideo[height<={quality}]+bestaudio/best' if download_type == 'video' else 'bestaudio/best',
                'outtmpl': temp_file_path,
                'noplaylist': True,
                'progress_hooks': [progress_hook],
            }
            
            if download_type == 'audio':
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                    'preferredquality': '192',
                }]
                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=True)
                title = sanitize_filename(info_dict.get('title', 'Unknown'))
                ext = info_dict.get('ext', 'mp4')  # Default to mp4 if not available
                filename = f"{title}.{ext}"
                final_file_path = os.path.join(settings.MEDIA_ROOT, 'downloads', filename)
                
                if download_status["status"] == "finished":
                    # Ensure final directory exists
                    os.makedirs(os.path.dirname(final_file_path), exist_ok=True)
                    
                    # Construct the full temporary file path
                    temp_file_full_path = temp_file_path % {'title': title, 'ext': ext}
                    
                    # Check if the temporary file exists
                    if os.path.exists(temp_file_full_path):
                        # Move the file to the final destination
                        shutil.move(temp_file_full_path, final_file_path)
                        
                        if os.path.exists(final_file_path):
                            logger.info(f"File exists at final destination: {final_file_path}")
                            return JsonResponse({'finished': 'تم تنزيل الصوت بنجاح!' if download_type == 'audio' else 'تم تنزيل الفيديو بنجاح!', 'file_path': os.path.join(settings.MEDIA_URL, 'downloads', filename)})
                        else:
                            logger.error(f"Final file does not exist. Expected path: {final_file_path}")
                            return JsonResponse({'error': 'حدث خطأ في تنزيل الملف. الرجاء المحاولة مرة أخرى.'}, status=500)
                    else:
                        logger.error(f"Temporary file does not exist. Expected path: {temp_file_full_path}")
                        return JsonResponse({'error': 'حدث خطأ في تنزيل الملف المؤقت. الرجاء المحاولة مرة أخرى.'}, status=500)
                
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            return JsonResponse({'error': 'حدث خطأ غير متوقع: ' + str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
