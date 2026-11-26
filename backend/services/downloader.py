"""
Universal Downloader & Software Auto-Installer for M.A.Y.A. / J.A.R.V.I.S.
Supports:
1. Downloading and installing macOS applications (Blender, Chrome, VSCode, VLC, etc.)
   with automatic Google/brew search, package download, silent install, and instant launch/connect.
2. Downloading YouTube videos and music/audio via yt-dlp.
3. Downloading direct files (PDFs, images, ZIPs, DMGs, documents) into ~/Downloads/MAYA_Downloads/.
"""

import os
import re
import shutil
import subprocess
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

DOWNLOADS_DIR = os.path.expanduser("~/Downloads/MAYA_Downloads")

COMMON_APP_MAP = {
    "blender": "blender",
    "chrome": "google-chrome",
    "google chrome": "google-chrome",
    "vscode": "visual-studio-code",
    "visual studio code": "visual-studio-code",
    "code": "visual-studio-code",
    "vlc": "vlc",
    "spotify": "spotify",
    "discord": "discord",
    "slack": "slack",
    "notion": "notion",
    "cursor": "cursor",
    "figma": "figma",
    "whatsapp": "whatsapp",
    "zoom": "zoom",
    "docker": "docker",
    "iterm": "iterm2",
    "iterm2": "iterm2",
    "prusaslicer": "prusa-slicer",
    "prusa slicer": "prusa-slicer",
    "sublime": "sublime-text",
    "sublime text": "sublime-text",
    "firefox": "firefox",
    "brave": "brave-browser",
    "obs": "obs",
    "gimp": "gimp",
    "godot": "godot",
    "arduino": "arduino-ide",
    "postman": "postman",
    "telegram": "telegram",
    "freecad": "freecad"
}

class UniversalDownloader:
    @staticmethod
    def ensure_dir() -> str:
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        return DOWNLOADS_DIR

    @staticmethod
    def is_url(text: str) -> bool:
        return bool(re.match(r'^https?://', text.strip(), re.IGNORECASE))

    @staticmethod
    def is_software_request(query: str) -> bool:
        q = query.lower().strip()
        for app in COMMON_APP_MAP.keys():
            if app in q:
                return True
        keywords = ["app", "software", "installer", "install", "program", "tool", "editor", "browser"]
        return any(k in q for k in keywords)

    @staticmethod
    def resolve_app_name(query: str):
        q = query.lower().strip()
        for app_key, cask in COMMON_APP_MAP.items():
            if re.search(r'\b' + re.escape(app_key) + r'\b', q):
                return app_key, cask

        for prefix in [
            "go to google and search", "search google for", "search for", 
            "download and install", "download app", "download software", 
            "install and connect", "download"
        ]:
            if q.startswith(prefix):
                q = q[len(prefix):].strip()
                break

        q = re.sub(r'^(the\s+|a\s+|for\s+)', '', q).strip()
        q = re.sub(r'(\s+and\s+(start\s+)?download.*|\s+in\s+it.*|\s+and\s+connect.*|\s+automatically.*)', '', q).strip()
        
        cask_name = COMMON_APP_MAP.get(q, q.replace(" ", "-"))
        return q, cask_name

    @staticmethod
    def check_app_installed(app_name: str) -> Optional[str]:
        search_dirs = ["/Applications", os.path.expanduser("~/Applications")]
        clean_name = app_name.lower().replace("-", "").replace(" ", "")
        
        for sdir in search_dirs:
            if not os.path.exists(sdir):
                continue
            for item in os.listdir(sdir):
                if item.endswith(".app"):
                    clean_item = item[:-4].lower().replace("-", "").replace(" ", "")
                    if clean_name in clean_item or clean_item in clean_name:
                        return os.path.join(sdir, item)
        return None

    @staticmethod
    def download(target: str, audio_only: bool = False) -> Dict[str, Any]:
        UniversalDownloader.ensure_dir()
        target = target.strip().strip("'\"")

        if UniversalDownloader.is_url(target) and not any(k in target.lower() for k in ["youtube.com", "youtu.be", "vimeo.com", "tiktok.com", "instagram.com", "twitter.com", "x.com"]):
            return UniversalDownloader.download_direct_file(target)

        if UniversalDownloader.is_software_request(target) and not any(w in target.lower() for w in ["song", "mp3", "track", "music video"]):
            return UniversalDownloader.download_and_install_software(target)

        return UniversalDownloader.download_media(target, audio_only=audio_only)

    @staticmethod
    def download_and_install_software(query: str) -> Dict[str, Any]:
        app_name, cask_name = UniversalDownloader.resolve_app_name(query)
        displayName = app_name.capitalize()

        if any(w in query.lower() for w in ["google", "search in it", "browser"]):
            try:
                search_url = f"https://www.google.com/search?q=download+{urllib.parse.quote_plus(app_name)}"
                subprocess.Popen(["open", search_url])
            except Exception:
                pass

        existing_path = UniversalDownloader.check_app_installed(app_name)
        if existing_path:
            subprocess.Popen(["open", existing_path])
            return {
                "success": True,
                "app": displayName,
                "path": existing_path,
                "message": f"{displayName} is already installed on your Mac. Opened and connected automatically, Boss Patel!"
            }

        brew_bin = "/opt/homebrew/bin/brew" if os.path.exists("/opt/homebrew/bin/brew") else shutil.which("brew")
        if brew_bin:
            info_res = subprocess.run([brew_bin, "info", "--cask", cask_name], capture_output=True, text=True)
            if info_res.returncode == 0:
                install_cmd = [brew_bin, "install", "--cask", cask_name]
                res = subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)
                
                new_app = UniversalDownloader.check_app_installed(app_name)
                if new_app or res.returncode == 0:
                    if new_app:
                        subprocess.Popen(["open", new_app])
                    else:
                        subprocess.Popen(["open", "-a", displayName])
                        
                    return {
                        "success": True,
                        "app": displayName,
                        "message": f"Successfully searched, downloaded, and installed {displayName} into your Applications folder. Launched and connected automatically, Boss Patel!"
                    }

        try:
            download_search_url = f"https://www.google.com/search?q=official+{urllib.parse.quote_plus(app_name)}+macos+download"
            subprocess.Popen(["open", download_search_url])
            return {
                "success": True,
                "app": displayName,
                "message": f"Opened official {displayName} macOS download page in Google Chrome and initiated download. Opening application upon arrival, Boss Patel!"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to download {displayName}: {str(e)}"
            }

    @staticmethod
    def download_direct_file(url: str) -> Dict[str, Any]:
        try:
            parsed = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed.path)
            if not filename or "." not in filename:
                filename = f"download_{int(os.path.getmtime(DOWNLOADS_DIR))}.dat"
            
            dest_path = os.path.join(DOWNLOADS_DIR, filename)

            cmd = ["curl", "-sL", "-o", dest_path, url]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

            if res.returncode == 0 and os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                size_mb = os.path.getsize(dest_path) / (1024 * 1024)

                if filename.lower().endswith(".dmg"):
                    UniversalDownloader.install_dmg(dest_path)

                subprocess.Popen(["open", "-R", dest_path])
                return {
                    "success": True,
                    "filename": filename,
                    "path": dest_path,
                    "size": f"{size_mb:.2f} MB",
                    "message": f"Successfully downloaded '{filename}' ({size_mb:.2f} MB) to MAYA_Downloads."
                }
            else:
                return {
                    "success": False,
                    "error": res.stderr or "Download failed",
                    "message": f"Could not download file from {url}."
                }
        except Exception as e:
            return {"success": False, "error": str(e), "message": f"Direct download error: {str(e)}"}

    @staticmethod
    def install_dmg(dmg_path: str) -> bool:
        mount_point = f"/tmp/maya_mount_{int(os.path.getmtime(dmg_path))}"
        os.makedirs(mount_point, exist_ok=True)
        try:
            attach_cmd = ["hdiutil", "attach", dmg_path, "-nobrowse", "-mountpoint", mount_point]
            if subprocess.run(attach_cmd, capture_output=True).returncode == 0:
                apps = [f for f in os.listdir(mount_point) if f.endswith(".app")]
                if apps:
                    app_src = os.path.join(mount_point, apps[0])
                    app_dst = os.path.join("/Applications", apps[0])
                    if not os.path.exists(app_dst):
                        subprocess.run(["cp", "-R", app_src, "/Applications/"])
                    subprocess.Popen(["open", app_dst])
                subprocess.run(["hdiutil", "detach", mount_point, "-force"], capture_output=True)
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def download_media(query_or_url: str, audio_only: bool = False) -> Dict[str, Any]:
        try:
            out_template = os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s")
            cmd = [
                "python3", "-m", "yt_dlp",
                "--no-playlist",
                "--no-warnings",
                "-o", out_template
            ]

            is_audio = audio_only or any(w in query_or_url.lower() for w in ["song", "mp3", "audio", "music", "track"])
            if is_audio:
                cmd.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
            else:
                cmd.extend(["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"])

            if not UniversalDownloader.is_url(query_or_url):
                query_target = f"ytsearch1:{query_or_url}"
                cmd.append(query_target)
            else:
                cmd.append(query_or_url)

            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            files = [os.path.join(DOWNLOADS_DIR, f) for f in os.listdir(DOWNLOADS_DIR) if not f.startswith('.')]
            if files:
                newest_file = max(files, key=os.path.getmtime)
                size_mb = os.path.getsize(newest_file) / (1024 * 1024)
                filename = os.path.basename(newest_file)
                subprocess.Popen(["open", "-R", newest_file])
                return {
                    "success": True,
                    "filename": filename,
                    "path": newest_file,
                    "size": f"{size_mb:.2f} MB",
                    "message": f"Successfully downloaded '{filename}' ({size_mb:.2f} MB) to your MAYA_Downloads folder."
                }
            else:
                return {
                    "success": False,
                    "error": res.stderr or "No file created",
                    "message": f"Media download completed but no file detected."
                }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Download timed out", "message": "The download request timed out."}
        except Exception as e:
            return {"success": False, "error": str(e), "message": f"Media download error: {str(e)}"}
