#!/usr/bin/env python3
"""
YouTube Multi-Video Downloader
A Python tool to download multiple YouTube videos with various options.
"""

import sys
from typing import List, Dict, Optional
from pathlib import Path
import argparse

try:
    import yt_dlp
except ImportError:
    print("yt-dlp not found. Please install it with: pip install yt-dlp")
    sys.exit(1)


class YouTubeDownloader:
    def __init__(self, download_path: str = "./downloads", audio_only: bool = False,
                 quality: str = "best", format_selector: str = None):
        """
        Initialize the YouTube downloader.

        Args:
            download_path: Directory to save downloads
            audio_only: Download audio only (MP3)
            quality: Video quality preference ('best', 'worst', '720p', etc.)
            format_selector: Custom format selector for yt-dlp
        """
        self.download_path = Path(download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)

        # configure yt-dlp options
        self.ydl_opts = {
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
            'ignoreerrors': True,  # continue on error
            'no_warnings': False, # warnings are for nerds
            'extractaudio': audio_only,
            'audioformat': 'mp3' if audio_only else None,
        }

        # set format/quality
        if format_selector:
            self.ydl_opts['format'] = format_selector
        elif audio_only:
            self.ydl_opts['format'] = 'bestaudio/best'
        else:
            if quality == 'best':
                self.ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            elif quality == 'worst':
                self.ydl_opts['format'] = 'worst[ext=mp4]/worst'
            else:
                self.ydl_opts['format'] = f'best[height<={quality.rstrip("p")}][ext=mp4]/best[height<={quality.rstrip("p")}]'


    def download_single_video(self, url: str) -> Dict[str, any]:
        """Download a single video and return result info."""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # extract info first, so we know what we're getting into
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)

                print(f"Downloading: {title}")
                if duration:
                    print(f"Duration: {duration // 60}:{duration % 60:02d}")

                # download the video, this is the fun part!
                ydl.download([url])

                return {
                    'url': url,
                    'title': title,
                    'status': 'success',
                    'duration': duration,
                    'error': None
                }
        except Exception as e:
            error_msg = str(e)
            print(f"Error downloading {url}: {error_msg}")
            # oh no, it broke :c
            return {
                'url': url,
                'title': 'Unknown',
                'status': 'error',
                'duration': 0,
                'error': error_msg
            }

    def download_multiple_videos(self, urls: List[str]) -> List[Dict[str, any]]:
        """Download multiple videos and return results."""
        results = []
        total = len(urls)

        print(f"Starting download of {total} videos...")
        print(f"Download directory: {self.download_path.absolute()}")
        print("-" * 50)

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{total}] Processing: {url}")
            result = self.download_single_video(url)
            results.append(result)

        return results

    def download_from_file(self, file_path: str) -> List[Dict[str, any]]:
        """Download videos from a text file containing URLs (one per line)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # read all the URLs from the file, but skip empty lines and comments
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            return self.download_multiple_videos(urls)
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
            return []
        except Exception as e:
            print(f"Error reading file '{file_path}': {e}")
            return []

    def print_summary(self, results: List[Dict[str, any]]):
        """Print download summary."""
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'error']

        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY :3")
        print("=" * 60)
        print(f"Total videos processed: {len(results)}")
        print(f"Successfully downloaded: {len(successful)}")
        print(f"Failed downloads: {len(failed)}")

        if successful:
            total_duration = sum(r['duration'] for r in successful)
            print(f"Total duration: {total_duration // 3600}h {(total_duration % 3600) // 60}m {total_duration % 60}s")

        if failed:
            print("\nFailed downloads:")
            for result in failed:
                print(f"  - {result['url']}: {result['error']}")


def main():
    parser = argparse.ArgumentParser(description='Download multiple YouTube videos')
    parser.add_argument('urls', nargs='*', help='YouTube URLs to download')
    parser.add_argument('-f', '--file', help='Text file containing URLs (one per line)')
    parser.add_argument('-o', '--output', default='./downloads', help='Output directory')
    parser.add_argument('-a', '--audio-only', action='store_true', help='Download audio only (MP3)')
    parser.add_argument('-q', '--quality', default='best',
                        help='Video quality (best, worst, 720p, 1080p, etc.)')
    parser.add_argument('--format', help='Custom format selector for yt-dlp')

    args = parser.parse_args()

    # create downloader instance
    downloader = YouTubeDownloader(
        download_path=args.output,
        audio_only=args.audio_only,
        quality=args.quality,
        format_selector=args.format
    )

    results = []

    # download from file if provided
    if args.file:
        results.extend(downloader.download_from_file(args.file))

    # download from command line URLs
    if args.urls:
        results.extend(downloader.download_multiple_videos(args.urls))

    # if no URLs provided, show help
    if not args.file and not args.urls:
        print("No URLs provided. Use --help for usage information.")
        print("\nExample usage:")
        print("  python youtube_downloader.py 'https://youtube.com/watch?v=...' 'https://youtube.com/watch?v=...'")
        print("  python youtube_downloader.py -f urls.txt")
        print("  python youtube_downloader.py -a -q 720p 'https://youtube.com/watch?v=...'")
        return

    # print summary
    downloader.print_summary(results)


# example usage as a module
if __name__ == "__main__":
    # check if running as script or being imported
    if len(sys.argv) > 1:
        main()
    else:
        # interactive example for when u import it :3
        print("YouTube Multi-Video Downloader")
        print("=" * 40)

        # save this for future use and knowing which videos are we using
        example_urls = [
            "https://youtu.be/9uxvKLSKpPA?si=g_RfxgG-LGlEVhE7",
            "https://youtu.be/NCPIBPGJTFk?si=N-KiG-EeUVIGYbYS",
            "https://youtu.be/gsUPN9h9Kd4?si=dU59r4Wqy2SExVvc",
            "https://youtu.be/Z8XSbud_OEo?si=zATy_tqmLVtVMs7N"
            "https://youtu.be/9oE0ByeTF58?si=WNjQfgmco2YKnNyn", # <- this is one lap
            "https://youtu.be/uoor0Gvhn-s?si=8UBYad5eqkknltaE",
            "https://youtu.be/dT9xRd86h18?si=CdAzn8-5hbdqCFdr",
            "https://youtu.be/rVo3Z9MddAA?si=9Mz_PzXl1eLpWEyu",
            "https://youtu.be/O6z2jAs6wLc?si=93KWaMC1wrbuLkVy",
            "https://youtu.be/B0EIkD3yIbI?si=F7p2ZxTNXZ20O9Jk",
            "https://youtu.be/MqSAneZZG3c?si=G-emgMn2xYXKbaKa"
        ]
        #
       # print("Example usage:")
        #print("downloader = YouTubeDownloader(download_path='./my_videos', audio_only=False)")
        #print("results = downloader.download_multiple_videos(urls_list)")
        #print("downloader.print_summary(results)")

        downloader = YouTubeDownloader()
        results = downloader.download_multiple_videos(example_urls)
        downloader.print_summary(results)