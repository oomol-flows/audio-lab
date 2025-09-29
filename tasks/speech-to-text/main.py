from oocana import Context
from openai import OpenAI, base_url
from typing import Any
import requests
import time
import os

#region generated meta
import typing
class Inputs(typing.TypedDict):
    audio_url: str
class Outputs(typing.TypedDict):
    text: typing.NotRequired[str]
#endregion

def get_audio_format(audio_url: str) -> str:
    """Extract audio format from audio URL"""
    parsed_url = os.path.splitext(audio_url)
    extension = parsed_url[1].lower().lstrip('.')

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
    base_url = context.oomol_llm_env.get("base_url")
    api_key = context.oomol_llm_env.get("api_key")
    audio_url = params["audio_url"]

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
    max_attempts = 60
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        query_params = {"task_id": task_id}
        query_response = requests.get(query_url, headers=headers, params=query_params)
        query_result = query_response.json()

        print(f"Query result (attempt {attempt}): {query_result}")

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
            print(f"Query failed with status {query_response.status_code}: {query_result}")
            time.sleep(2)

    raise Exception(f"STT task timed out after {max_attempts} attempts")
