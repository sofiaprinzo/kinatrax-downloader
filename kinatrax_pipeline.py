import argparse
from datetime import date, datetime, timezone
import json
import logging
import os
import mimetypes

from pathlib import Path, PurePosixPath

from dotenv import load_dotenv
import requests

from kinatrax_api import ExplorerClient
from supabase import create_client


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
def list_session_files(client: ExplorerClient, session_path: str, discovery_state: dict, save_discovery) -> list[dict]:
    session = PurePosixPath(session_path)

    if discovery_state["remaining_captures"] is None:
        captures = []
        logger.info("Listing session: %s", session.name)
        session_listing = client.list_folder(f"{session}/")
        # Stop if the listing has additional pages
        if session_listing["has_more"]:
            raise ValueError("Session listing has more pages")
        for activity_path in sorted(session_listing["folders"]):
            activity = PurePosixPath(activity_path)
            if activity.name in {"Pitching", "Batting"}:
                logger.info("Listing activity: %s", activity.name)
                activity_listing = client.list_folder(f"{activity}/")
                # Stop if the listing has additional pages
                if activity_listing["has_more"]:
                    raise ValueError("Activity listing has more pages")
                captures.extend(activity_listing["folders"])

        discovery_state["remaining_captures"] = sorted(captures)
        # Save the folders we still need to list
        save_discovery()
        logger.info("Found %s capture folders", len(captures))
    elif discovery_state["remaining_captures"]:
        logger.info("Resuming discovery for session %s: %s capture folders remaining", session.name, len(discovery_state["remaining_captures"]))

    total_captures = len(discovery_state["remaining_captures"])
    while discovery_state["remaining_captures"]:
        capture = PurePosixPath(discovery_state["remaining_captures"][0])
        capture_number = total_captures - len(discovery_state["remaining_captures"]) + 1
        logger.info("Listing capture %s/%s: %s", capture_number, total_captures, capture.name)
        listing = client.list_folder(f"{capture}/")
        # Stop if the listing has additional pages
        if listing["has_more"]:
            raise ValueError("Capture listing has more pages")
        metadata_by_path = listing["metadata"]
        capture_files = []

        # Only check files directly inside the capture folder, not its subfolders. The subfolders only have video files
        for file_path in listing["files"]:
            file = PurePosixPath(file_path)
            if file.suffix.lower() in DATA_EXTENSIONS and file.name not in EXCLUDED_FILENAMES:
                metadata = metadata_by_path.get(file_path, {})
                capture_files.append({
                    "s3_path": file_path,
                    "size": metadata.get("size"),
                    "last_modified": metadata.get("last_modified"),
                })

        # After listing this capture, update its state: add its files and remove it from the remaining captures
        discovery_state["files"].extend(capture_files)
        discovery_state["remaining_captures"].pop(0)
        # Save completed capture progress
        save_discovery()

    files = discovery_state["files"]
    logger.info("Found %s matching data files", len(files))
    return sorted(files, key=lambda file: file["s3_path"])


def download_session(
    client: ExplorerClient, session_name: str, bucket, files: list[dict], transfer_state: list[str], save_transfer, batch_size: int = 10
) -> dict:
    if not files:
        raise ValueError("No matching files found for this session")

    result = {
        "session": session_name,
        "files_found": len(files),
        "uploaded": 0,
        "skipped": 0,
        "failed": 0,
        "bytes_uploaded": 0,
    }

    # Use saved transfer state to skip files already uploaded
    uploaded_paths = set(transfer_state)
    pending = []
    for file in files:
        if file["s3_path"] in uploaded_paths:
            logger.info("Skipping existing file: %s", file["s3_path"])
            result["skipped"] += 1
            continue
        pending.append(file)

    logger.info("Preparing to download %s files", len(pending))

    with requests.Session() as download_http:
        for start in range(0, len(pending), batch_size):
            batch = pending[start : start + batch_size]
            paths = [file["s3_path"] for file in batch]

            links = client.download_files_via_links(paths)

            # Download each file from requested batch and upload it to Supabase bucket
            for file in batch:
                s3_path = file["s3_path"]
                url = links.get(s3_path)

                if not url:
                    logger.error("No download URL for %s", s3_path)
                    result["failed"] += 1
                    continue

                try:
                    logger.info("Transferring %s", s3_path)

                    with download_http.get(url, timeout=(15, 120), allow_redirects=False) as response:
                        response.raise_for_status()
                        content = response.content

                    # Check the complete download before uploading it
                    if len(content) != file["size"]:
                        raise ValueError(f"Downloaded size differs from source listing: {s3_path}")

                    relative = PurePosixPath(s3_path).relative_to(SOURCE_ROOT)
                    destination = f"staging/raw/{relative.as_posix()}"
                    content_type = mimetypes.guess_type(destination)[0] or "application/octet-stream"

                    bucket.upload(
                        file=content,
                        path=destination,
                        file_options={
                            "content-type": content_type,
                            "upsert": "true",
                            "metadata": {
                                "source_last_modified": file["last_modified"],
                            },
                        },
                    )

                    transfer_state.append(s3_path)

                    # Save the file as uploaded
                    save_transfer()

                    result["uploaded"] += 1
                    result["bytes_uploaded"] += len(content)

                except Exception as error:
                    logger.error("Failed to transfer %s: %s", s3_path, error)
                    result["failed"] += 1

    logger.info(
        "Session complete: %s uploaded, %s skipped, %s failed",
        result["uploaded"],
        result["skipped"],
        result["failed"],
    )

    return result


def ingest_session(client: ExplorerClient, session_name: str, bucket, supabase) -> dict:
    timestamp = parse_session_name(session_name)
    s3_path = f"{SOURCE_ROOT}/{timestamp.year}/{session_name}/"
    table = supabase.table("kinatrax_ingest_log")

    existing = (
        table.select("status, discovery_state, transfer_state")
        .eq("session_name", session_name)
        .maybe_single()
        .execute()
    )

    # Get the saved session data if it exists
    existing_data = existing_data if existing is not None else None

    if existing_data is not None and existing_data["status"] == "downloaded":
        logger.info("Session already downloaded. Skipping: %s", session_name)
        return {
            "session": session_name,
            "status": "downloaded",
            "skipped_session": True,
        }

    # Load saved discovery state or start fresh
    discovery_state = existing_data["discovery_state"] if existing_data is not None else None

    if discovery_state is None:
        discovery_state = {
            "remaining_captures": None,
            "files": [],
        }

    # Load saved transfer state or start fresh
    transfer_state = existing_data["transfer_state"] if existing_data is not None else None
    if transfer_state is None:
        transfer_state = []

    record = {
        "session_name": session_name,
        "s3_path": s3_path,
        "file_count": len(discovery_state["files"]) if discovery_state["remaining_captures"] == [] else None,
        "downloaded_at": None,
        "status": "failed",
        "discovery_state": discovery_state,
        "transfer_state": transfer_state,
    }

    # Create the record before starting
    table.upsert(record, on_conflict="session_name").execute()

    def save_discovery():
        # Save the current folder listing progress
        table.update({"discovery_state": discovery_state}).eq("session_name", session_name).execute()

    def save_transfer():
        # Save the files already uploaded
        table.update({"transfer_state": transfer_state}).eq("session_name", session_name).execute()

    # Discover files
    try:
        if discovery_state["remaining_captures"] == []:
            logger.info("Discovery already complete for session %s. Reusing saved file paths.", session_name)

        files = list_session_files(client, s3_path, discovery_state, save_discovery)

        if not files:
            record["discovery_state"] = None
            raise ValueError("No matching files found for this session")

        # Save the complete file list before transfers
        record["file_count"] = len(files)
        table.upsert(record, on_conflict = "session_name").execute()

        # Transfer files to storage
        result = download_session(client, session_name, bucket, files, transfer_state, save_transfer)

    except Exception as error:
        logger.error("Session failed: %s: %s", session_name, error)
        result = {
            "session": session_name,
            "status": "failed",
        }
    else:
        result["status"] = "failed" if result["failed"] > 0 else "downloaded"

    record["status"] = result["status"]

    if result["status"] == "downloaded":
        record["downloaded_at"] = datetime.now(timezone.utc).isoformat()
        record["discovery_state"] = None
        record["transfer_state"] = None

    table.upsert(record, on_conflict = "session_name").execute()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_mutually_exclusive_group(required=True)

    # Ex: run 'python3 kinatrax_pipeline.py --backfill 2026-09-18 2026-12-31'
    commands.add_argument("--backfill", nargs=2, type=date.fromisoformat)

    # Show one folder's immediate folders, files, and file metadata
    # Ex: run 'python3 kinatrax_pipeline.py --path Data/CPS/2026/'
    commands.add_argument("--path")

    args = parser.parse_args()
    if args.backfill is not None:
        start_date, end_date = args.backfill
        if start_date > end_date:
            parser.error("start_date must be on or before end_date")

    logging.basicConfig(level=logging.INFO)

    load_dotenv(PROJECT_DIR / ".env")
    api_key = os.getenv("KINATRAX_API_KEY", "")
    base_url = os.getenv("KINATRAX_BASE_URL", "https://explorer-api.kinatrax.com")

    try:
        with requests.Session() as http:
            client = ExplorerClient(api_key, base_url, http)
            if args.backfill is not None:
                supabase = create_client(
                    os.environ["SUPABASE_URL"],
                    os.environ["SUPABASE_SECRET_KEY"],
                )
                bucket = supabase.storage.from_(os.environ["SUPABASE_BUCKET"])
                results = []
                for season in range(start_date.year, end_date.year + 1):
                    for session_path in list_sessions(client, season):
                        session_name = PurePosixPath(session_path).name
                        session_date = parse_session_name(session_name).date()
                        if start_date <= session_date <= end_date:
                            result = ingest_session(client, session_name, bucket, supabase)
                            results.append(result)
                result = results
            else:
                result = client.list_folder(args.path)
            print(json.dumps(result, indent=2))

        if args.backfill is not None and any(session["status"] == "failed" for session in result):
            return 1
        return 0

    except requests.HTTPError as error:
        logger.error("Explorer request failed (HTTP %s).", error)
    except requests.RequestException as error:
        logger.error("Explorer request failed: %s", error)
    except (ValueError, TypeError) as error:
        logger.error("%s", error)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
