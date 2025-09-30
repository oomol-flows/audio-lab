from oocana import Context
import requests
import time
import os

def make_http_request(method: str, url: str, headers: dict, json_data: dict | None = None, params: dict | None = None, timeout: int = 30):
    """
    Make HTTP request with simple retry logic for timeouts and 50x errors
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if method.upper() == "POST":
                response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            else:
                response = requests.get(url, headers=headers, params=params, timeout=timeout)

            # Check for 50x server errors (retryable)
            if 500 <= response.status_code < 600:
                print(f"Server error {response.status_code}, attempt {attempt + 1}/{max_retries}")
                # Special handling for "Start Processing" error in 500 responses
                try:
                    result = response.json()
                    error_msg = result.get("message", "")
                    if "Start Processing" in error_msg:
                        print(f"Backend processing started, treating as success: {error_msg}")
                        return response
                except:
                    pass  # If JSON parsing fails, continue with normal retry logic

                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    response.raise_for_status()

            return response

        except requests.exceptions.Timeout:
            print(f"Request timeout, attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                raise
        except requests.exceptions.ConnectionError:
            print(f"Connection error, attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                raise

    raise Exception("Max retries exceeded")

#region generated meta
import typing
class Inputs(typing.TypedDict):
    audio_url: str
class Outputs(typing.TypedDict):
    text: typing.NotRequired[str]
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
    submit_response = make_http_request("POST", submit_url, headers=headers, json_data=submit_data)
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
        query_response = make_http_request("GET", query_url, headers=headers, params=query_params)
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
                    print("STT task completed successfully")
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
