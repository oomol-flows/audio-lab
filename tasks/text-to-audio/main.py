from oocana import Context
from openai import OpenAI
from typing import Any
#region generated meta
import typing
class Inputs(typing.TypedDict):
    content: str
    file_path: str
    timbre: typing.Literal["anna", "alex", "bella"]
    name: str | None
class Outputs(typing.TypedDict):
    audio_address: typing.NotRequired[str]
#endregion

def main(params: Inputs, context: Context) -> Outputs:

    my_content = params.get("content")
    api_key= context.oomol_llm_env.get("api_key")
    file_path = params.get("file_path")
    timbre = params.get("timbre")
    name = params.get("name")
    if name is None:
        import time
        name = str(int(time.time()))
    model = "FunAudioLLM/CosyVoice2-0.5B"
    voice: Any = f"{model}:{timbre}"

    if file_path is None:
        file_path = context.session_dir

    speech_file_path = f"{file_path}/{name}.mp3"
    client = OpenAI(api_key=api_key, base_url=context.oomol_llm_env.get("base_url_v1"))

    with client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=my_content,
        response_format="mp3",
    ) as response:
        response.stream_to_file(speech_file_path)
    return {"audio_address": speech_file_path}