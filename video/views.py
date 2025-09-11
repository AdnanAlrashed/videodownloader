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
    # More permissive pattern that allows any URL (yt-dlp will handle validation)
    url_pattern = re.compile(
        r'^(https?://)?'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        raise ValidationError("الرابط المدخل غير صالح. الرجاء إدخال رابط صالح.")

def sanitize_filename(filename):
    """Sanitize the filename to ensure it's filesystem-friendly."""
    # قائمة بالأحرف غير المسموحة في أسماء الملفات
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    
    # إزالة أي أحرف تحكم غير مرغوب فيها
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # تقصير الاسم إذا كان طويلاً جداً
    if len(filename) > 150:
        name, ext = os.path.splitext(filename)
        filename = name[:150 - len(ext)] + ext
    
    return filename

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
                'no_warnings': True,
                'restrictfilenames': True,
                'format': 'bestaudio/best',
                # Add these options to handle bot detection
                'cookiefile': 'cookies.txt',  # Optional: use cookies if you have them
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'referer': 'https://www.google.com/',
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
                # إضافة هذه الخيارات لمنع مشاكل الدمج
                'merge_output_format': 'mp4',  # إجبار الدمج إلى mp4
                'windowsfilenames': True,      # أسماء ملفات متوافقة مع Windows
                'restrictfilenames': True,     # تقييد أسماء الملفات
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
                ext = info_dict.get('ext', 'mp4') if download_type == 'video' else audio_format
                filename = f"{title}.{ext}"
                final_file_path = os.path.join(settings.MEDIA_ROOT, 'downloads', filename)
                
                # البحث عن الملف المنتهي بدلاً من الاعتماد على المسار المتوقع
                actual_file = None
                for file in os.listdir(temp_dir):
                    if download_type == 'audio' and file.endswith(('.mp3', '.aac', '.m4a', '.wav')):
                        actual_file = os.path.join(temp_dir, file)
                        break
                    elif download_type == 'video' and file.endswith(('.mp4', '.webm', '.mkv', '.avi', '.mov')):
                        actual_file = os.path.join(temp_dir, file)
                        break
                
                if actual_file and os.path.exists(actual_file):
                    # Ensure final directory exists
                    os.makedirs(os.path.dirname(final_file_path), exist_ok=True)
                    
                    # نقل الملف إلى الوجهة النهائية
                    shutil.move(actual_file, final_file_path)
                    
                    if os.path.exists(final_file_path):
                        logger.info(f"File exists at final destination: {final_file_path}")
                        return JsonResponse({
                            'finished': 'تم تنزيل الصوت بنجاح!' if download_type == 'audio' else 'تم تنزيل الفيديو بنجاح!', 
                            'file_path': os.path.join(settings.MEDIA_URL, 'downloads', filename),
                            'filename': filename
                        })
                    else:
                        logger.error(f"Final file does not exist. Expected path: {final_file_path}")
                        return JsonResponse({'error': 'حدث خطأ في تنزيل الملف. الرجاء المحاولة مرة أخرى.'}, status=500)
                else:
                    # محاولة بديلة: البحث عن أي ملف وسائط في المجلد المؤقت
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if download_type == 'audio' and file.endswith(('.mp3', '.aac', '.m4a', '.wav')):
                                actual_file = os.path.join(root, file)
                                break
                            elif download_type == 'video' and file.endswith(('.mp4', '.webm', '.mkv', '.avi', '.mov')):
                                actual_file = os.path.join(root, file)
                                break
                    
                    if actual_file and os.path.exists(actual_file):
                        os.makedirs(os.path.dirname(final_file_path), exist_ok=True)
                        shutil.move(actual_file, final_file_path)
                        
                        if os.path.exists(final_file_path):
                            logger.info(f"File found and moved to: {final_file_path}")
                            return JsonResponse({
                                'finished': 'تم تنزيل الصوت بنجاح!' if download_type == 'audio' else 'تم تنزيل الفيديو بنجاح!', 
                                'file_path': os.path.join(settings.MEDIA_URL, 'downloads', filename),
                                'filename': filename
                            })
                    
                    logger.error(f"No downloaded files found in temporary directory: {temp_dir}")
                    return JsonResponse({'error': 'حدث خطأ في تنزيل الملف المؤقت. الرجاء المحاولة مرة أخرى.'}, status=500)
                
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            return JsonResponse({'error': 'حدث خطأ غير متوقع: ' + str(e)}, status=500)
        finally:
            # تنظيف الملفات المؤقتة
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Error cleaning up temporary directory: {str(e)}")

    return JsonResponse({'error': 'Invalid request method'}, status=405)