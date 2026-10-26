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

DATA_EXTENSIONS = {".csv", ".txt", ".xml"}
EXCLUDED_FILENAMES = {"cameras.xml", "motion_sequence_batting.csv", "generate_subject_model_properties.xml"}


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
            continue
        sessions.append(folder)
    return sorted(set(sessions))

# Find the data files inside each Pitching and Batting capture folder
def list_session_files(client: ExplorerClient, session_path: str) -> list[dict]:
    session = PurePosixPath(session_path)
    captures = []
    logger.info("Listing session: %s", session.name)
    session_listing = client.list_folder(f"{session}/")
    for activity_path in sorted(session_listing["folders"]):
        activity = PurePosixPath(activity_path)
        if activity.name in {"Pitching", "Batting"}:
            logger.info("Listing activity: %s", activity.name)
            activity_listing = client.list_folder(f"{activity}/")
            captures.extend(activity_listing["folders"])

    # Only check files directly inside the capture folder, not its subfolders. The subfolders only have video files
    files = []
    logger.info("Found %s capture folders", len(captures))
    for capture_path in sorted(captures):
        capture = PurePosixPath(capture_path)
        logger.info("Listing capture: %s", capture.name)
        listing = client.list_folder(f"{capture}/")
        metadata_by_path = listing["metadata"]
        for file_path in listing["files"]:
            path = PurePosixPath(file_path)
            if path.suffix.lower() in DATA_EXTENSIONS and path.name not in EXCLUDED_FILENAMES:
                metadata = metadata_by_path.get(file_path, {})
                files.append({
                    "s3_path": file_path,
                    "size": metadata.get("size"),
                    "last_modified": metadata.get("last_modified"),
                })

    logger.info("Found %s matching data files", len(files))
    return sorted(files, key=lambda file: file["s3_path"])





def download_session(client: ExplorerClient, session_name: str, bucket) -> dict:
    pass
    # Download links for their s3_path values using download_files_via_links_v1 endpoint
    # Transfer to bucket



def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_mutually_exclusive_group(required=True)

    # List session folder paths under a season year
    # Ex: For Data/CPS/2026/ run 'python3 kinatrax_pipeline.py --season 2026'
    commands.add_argument("--season", type=int)

    # Show one folder's immediate folders, files, and file metadata
    # Ex: run 'python3 kinatrax_pipeline.py --path Data/CPS/2026/'
    commands.add_argument("--path")

    args = parser.parse_args(argv)
    if args.season is not None and not 1000 <= args.season <= 9999:
        parser.error("--season must be a four-digit source directory year")

    logging.basicConfig(level=logging.INFO)
    
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
