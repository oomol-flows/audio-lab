from oocana import Context
from openai import OpenAI, base_url
from typing import Any
import requests
import time
import json
#region generated meta
import typing
class Inputs(typing.TypedDict):
    content: str
    file_path: str
    timbre: typing.Literal["zh_male_lengkugege_emo_v2_mars_bigtts", "zh_female_tianxinxiaomei_emo_v2_mars_bigtts", "zh_female_gaolengyujie_emo_v2_mars_bigtts"]
    name: str | None
class Outputs(typing.TypedDict):
    audio_address: typing.NotRequired[str]
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
    submit_response = requests.post(submit_url, headers=headers, json=submit_data)
    submit_result = submit_response.json()

    if not submit_result.get("success"):
        raise Exception(f"Submit TTS task failed: {submit_result}")
    if "data" not in submit_result or "task_id" not in submit_result["data"]:
        raise Exception(f"Submit TTS task response missing data or task_id: {submit_result}")

    task_id = submit_result["data"]["task_id"]
    print(f"TTS task submitted, task_id: {task_id}")

    # Poll for task completion
    query_url = f"{base_url}/api/tasks/v1/tts/query"

    while True:
        query_params = {"task_id": task_id}
        query_response = requests.get(query_url, headers=headers, params=query_params)
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
                    audio_response = requests.get(audio_url)

                    if audio_response.status_code == 200:
                        with open(speech_file_path, 'wb') as f:
                            f.write(audio_response.content)
                        print(f"Audio saved to {speech_file_path}")
                        return {"audio_address": speech_file_path}
                    else:
                        raise Exception(f"Failed to download audio file: {audio_response.status_code}")
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