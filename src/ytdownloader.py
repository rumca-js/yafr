import sys
from pathlib import Path
import yt_dlp

def progress_hook(d):
    if d['status'] == 'finished':
        print("\nDownload complete! Starting audio conversion to MP3...")


class YtDownloader(object):
    def __init__(self, cwd, url):
        self.home_dir = cwd
        self.video_url = url
        self.errors = []

    def get_audio_download_options(self):
        home_dir = self.home_dir

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'{home_dir}/%(title)s.%(ext)s',
            #'progress_hooks': [progress_hook],
            #'js_runtimes': {'deno' : {"path" : "path"}},
        }
        return ydl_opts


    def get_video_download_options(self):
        home_dir = self.home_dir

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            #'merge_output_format' : 'mp4',
            'merge_output_format' : 'mkv',
            'outtmpl': f'{home_dir}/%(title)s.%(ext)s',
            #'js_runtimes': {'deno' : {'path': ':/home/rumcajs/.deno/bin/deno'}, "node" : {"path" : "/usr/bin/nodejs"}},
            #'progress_hooks': [progress_hook],
            #'js_runtimes': {'deno' : {"path" : "path"}},
            #'postprocessors': [{
            #  'key': 'FFmpegMerger',
            #}]
            "postprocessor_args" : { "ffmpeg" : ["-c:a", "libmp3lame", "-q:a","2"]},
        }
        return ydl_opts

    def download_with_options(self, ydl_opts, suffix=".mp3"):
        video_url = self.video_url

        try:
            print(f"Extracting information for: {video_url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 1. Extract metadata without downloading first to get the info dict
                info_dict = ydl.extract_info(video_url, download=False)
                
                # 2. Predict the final filename based on the template options
                predicted_filename = ydl.prepare_filename(info_dict)
                
                # 3. Adjust extension for the return value since the postprocessor forces it to .mp3
                final_file_path = str(Path(predicted_filename).with_suffix(suffix))

                if not Path(final_file_path).exists():
                    # 4. Perform the actual download
                    ydl.download([video_url])
                
                return final_file_path
                
        except Exception as e:
            self.errors.append(str(e))
            return None

    def download_audio(self):
        ydl_opts = self.get_audio_download_options()
        file_name = self.download_with_options(ydl_opts, ".mp3")
        return file_name

    def download_video(self):
        ydl_opts = self.get_video_download_options()
        file_name = self.download_with_options(ydl_opts, ".mp4")
        return file_name


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_audio.py <YOUTUBE_URL>")
        sys.exit(1)
        
    url = sys.argv[1]
    home_dir = str(Path.home())

    downloader = YtDownloader(home_dir, url)
    saved_path = downloader.download_audio()
    print(f"Saved {saved_path}")
    saved_path = downloader.download_video()
    print(f"Saved {saved_path}")
    
    if saved_path:
        print(f"\nReturned to Main: File successfully saved at -> {saved_path}")
