from oocana import Context
import requests
import time
import os

#region generated meta
import typing
class Inputs(typing.TypedDict):
    audio_url: str
class Outputs(typing.TypedDict):
    text: str
#endregion

def get_audio_format(audio_url: str) -> str:
    """Extract audio format from audio URL"""
    from urllib.parse import urlparse
    path = urlparse(audio_url).path
    _, ext = os.path.splitext(path)
    extension = ext.lower().lstrip('.')
    # Map common audio extensions
    format_map = {
        'mp3': 'mp3',
        'wav': 'wav',
        'flac': 'flac',
        'm4a': 'm4a',
        'aac': 'aac',
        'ogg': 'ogg',
        'wma': 'wma'
    }

    return format_map.get(extension, 'mp3')  # Default to mp3 if format not found

def main(params: Inputs, context: Context) -> Outputs:
    """
    Main function: Handles audio to text transcription task
    """
    base_url = (context.oomol_llm_env.get("base_url") or "").rstrip("/")
    api_key = context.oomol_llm_env.get("api_key")
    audio_url = params["audio_url"]
    if not base_url or not api_key:
        raise ValueError("Missing base_url or api_key in context.oomol_llm_env")
    print(f"Processing audio URL: {audio_url}")

    audio_format = get_audio_format(audio_url)
    print(f"Detected audio format: {audio_format}")

    submit_url = f"{base_url}/api/tasks/v1/stt/submit"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    submit_data = {
        "audio_url": audio_url,
        "format": audio_format
    }

    print(f"Submitting STT task to {submit_url}")
    submit_response = requests.post(submit_url, headers=headers, json=submit_data)
    submit_result = submit_response.json()

    if not submit_result.get("success"):
        raise Exception(f"Submit STT task failed: {submit_result}")
    if "data" not in submit_result or "task_id" not in submit_result["data"]:
        raise Exception(f"Submit STT task response missing data or task_id: {submit_result}")

    task_id = submit_result["data"]["task_id"]
    print(f"STT task submitted, task_id: {task_id}")

    
    query_url = f"{base_url}/api/tasks/v1/stt/query"

    while True:
        query_params = {"task_id": task_id}
        query_response = requests.get(query_url, headers=headers, params=query_params)
        query_result = query_response.json()

        print(
            f"Query status: success={query_result.get('success')} "
            f"task_status={query_result.get('data', {}).get('task_status')}"
        )
        # Check if success field is False and handle error
        # Skip validation if message contains "Start Processing" due to backend bug
        if query_result.get("success") is False:
            error_msg = query_result.get("message", "Unknown error")
            if "Start Processing" in error_msg:
                print(f"Backend processing started, skipping success validation: {error_msg}")
            else:
                print(f"Error: {error_msg}")
                raise Exception(f"STT query failed: {error_msg}")

        if query_response.status_code == 200 and query_result.get("success"):
            data = query_result.get("data", {})
            task_status = data.get("task_status")

            # task_status: 1=pending, 2=completed, 3=failed
            if task_status == 2:
                text = data.get("text")
                if text:
                    print(f"STT task completed successfully")
                    return {"text": text}
                else:
                    raise Exception("No text in completed task result")

            elif task_status == 3:
                error_msg = query_result.get("message", "Unknown error")
                raise Exception(f"STT task failed: {error_msg}")

            elif task_status == 1:
                print("Task pending, waiting...")
                time.sleep(2)
                continue

        else:
            time.sleep(2)
