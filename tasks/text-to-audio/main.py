from oocana import Context
import requests
import time

def make_http_request(method: str, url: str, headers: dict, json_data: dict = None, params: dict = None, timeout: int = 30):
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
    content: str
    file_path: str
    timbre: typing.Literal["zh_male_lengkugege_emo_v2_mars_bigtts", "zh_female_tianxinxiaomei_emo_v2_mars_bigtts", "zh_female_gaolengyujie_emo_v2_mars_bigtts", "zh_male_jingqiangkanye_emo_mars_bigtts", "ICL_zh_female_wenrounvshen_239eff5e8ffa_tob"]
    name: str | None
class Outputs(typing.TypedDict):
    audio_address: str
#endregion

# voice 音色文档地址: https://www.volcengine.com/docs/6561/1257544

def main(params: Inputs, context: Context) -> Outputs:

    my_content = params.get("content")
    api_key= context.oomol_llm_env.get("api_key")
    file_path = params.get("file_path")
    timbre = params.get("timbre")
    name = params.get("name")
    if name is None:
        name = str(int(time.time()))

    if file_path is None:
        file_path = context.session_dir

    speech_file_path = f"{file_path}/{name}.mp3"
    base_url=context.oomol_llm_env.get("base_url")

    # Submit TTS task
    submit_url: str = f"{base_url}/api/tasks/v1/tts/submit"
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    submit_data: dict[str, str] = {
        "text": my_content,
        "voice": timbre
    }

    print(f"Submitting TTS task to {submit_url}")
    submit_response = make_http_request("POST", submit_url, headers=headers, json_data=submit_data)
    submit_result = submit_response.json()

    if not submit_result.get("success"):
        raise Exception(f"Submit TTS task failed: {submit_result}")
    if "data" not in submit_result or "task_id" not in submit_result["data"]:
        raise Exception(f"Submit TTS task response missing data or task_id: {submit_result}")

    task_id = submit_result["data"]["task_id"]
    print(f"TTS task submitted, task_id: {task_id}")

    query_url = f"{base_url}/api/tasks/v1/tts/query"

    while True:
        query_params = {"task_id": task_id}
        query_response = make_http_request("GET", query_url, headers=headers, params=query_params)
        query_result = query_response.json()

        print(f"Query result: {query_result}")

        if query_response.status_code == 200 and query_result.get("success"):
            data = query_result.get("data", {})
            task_status = data.get("task_status")

            # task_status: 1=pending, 2=completed, 3=failed
            if task_status == 2:
                audio_url = data.get("audio_url")
                if audio_url:
                    print(f"Downloading audio from {audio_url}")
                    with requests.get(
                        audio_url, stream=True, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
                    ) as audio_response:
                        audio_response.raise_for_status()
                        with open(speech_file_path, 'wb') as f:
                            for chunk in audio_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                    print(f"Audio saved to {speech_file_path}")
                    return {"audio_address": speech_file_path}
                else:
                    raise Exception("No audio_url in completed task result")

            elif task_status == 3:
                error_msg = query_result.get("message", "Unknown error")
                raise Exception(f"TTS task failed: {error_msg}")

            elif task_status == 1:
                print("Task pending, waiting...")
                time.sleep(2)
                continue

        else:
            print(f"Query failed with status {query_response.status_code}: {query_result}")
            time.sleep(2)