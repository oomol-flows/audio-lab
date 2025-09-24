from oocana import Context
from openai import OpenAI

#region generated meta
import typing
class Inputs(typing.TypedDict):
    audio: str
class Outputs(typing.TypedDict):
    text: str
#endregion

def main(params: Inputs, context: Context) -> Outputs:
    """
    Main function: Handles audio to text transcription task
    """
    client = OpenAI(
        api_key=context.oomol_llm_env.get("api_key"),
        base_url=context.oomol_llm_env.get("base_url_v1")
    )
    
    with open(params["audio"], "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="FunAudioLLM/SenseVoiceSmall",
            file=audio_file
        )
    
    return {"text": transcription.text}
