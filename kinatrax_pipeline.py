# List session folders function only so far

# Extraction and download steps come next:
# Request download links using POST /ktx_s3/download_files_via_links_v1
# Send multiple file paths per call to reduce waiting under the 5-calls/30-seconds limit
# Download files from those links into staging/raw/, preserve folder structure

import argparse
from datetime import datetime
import json
import logging
import os
from pathlib import Path, PurePosixPath

from dotenv import load_dotenv
import requests

from kinatrax_api import ExplorerClient


logger = logging.getLogger(__name__)
PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = "Data/CPS"
SESSION_FORMAT = "%Y_%m_%d_%H_%M_%S"

DATA_EXTENSIONS = {".csv", ".txt", ".xml", ".json"}


def parse_session_name(name: str) -> datetime:
    timestamp = datetime.strptime(name, SESSION_FORMAT)
    if timestamp.strftime(SESSION_FORMAT) != name:
        raise ValueError("Session name must be YYYY_MM_DD_HH_MM_SS.")
    return timestamp


def list_sessions(client: ExplorerClient, season: int) -> list[str]:
    listing = client.list_folder(f"{SOURCE_ROOT}/{season}/")
    sessions = []
    for folder in listing["folders"]:
        try:
            parse_session_name(PurePosixPath(folder).name)
        except ValueError:
            # Skip folders whose names are not valid session timestamps
            continue
        sessions.append(folder)
    return sorted(set(sessions))

# Next def (list_session_files) to to visit each session's Batting/Pitching subfolder


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_mutually_exclusive_group(required=True)

    # List session folder paths under a season year
    # Ex: For Data/CPS/2026/ run 'python3 kinatrax_pipeline.py --season 2026'
    commands.add_argument("--season", type=int)

    # Show one folder's immediate folders, files, and file metadata
    # Ex: run 'python3 kinatrax_pipeline.py --path Data/CPS/2026/'
    # Files will show as empty here, so next would be to implement list_session_files()
    commands.add_argument("--path")

    args = parser.parse_args(argv)
    if args.season is not None and not 1000 <= args.season <= 9999:
        parser.error("--season must be a four-digit source directory year")

    logging.basicConfig()
    
    load_dotenv(PROJECT_DIR / ".env")
    api_key = os.getenv("KINATRAX_API_KEY", "")
    base_url = os.getenv("KINATRAX_BASE_URL", "https://explorer-api.kinatrax.com")

    try:
        with requests.Session() as http:
            client = ExplorerClient(api_key, base_url, http)
            if args.season is not None:
                result = list_sessions(client, args.season)
            else:
                result = client.list_folder(args.path)
            print(json.dumps(result, indent=2))
        return 0
    
    except requests.HTTPError as error:
        logger.error("Explorer request failed (HTTP %s).", error.response.status_code)
    except requests.RequestException:
        logger.error("Explorer request failed: Check connection and API access")
    except (ValueError, TypeError) as error:
        logger.error("%s", error)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
