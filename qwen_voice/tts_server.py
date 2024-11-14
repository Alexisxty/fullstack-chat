from fastapi import FastAPI
from pydantic import BaseModel
from cosyvoice.cli.cosyvoice import CosyVoice
import torchaudio
import torch
from fastapi.responses import StreamingResponse
import io

app = FastAPI()

# 初始化 CosyVoice 模型，只需在启动时加载一次
cosyvoice = CosyVoice(
    '/mnt/82_store/LLM-weights/voice/CosyVoice-300M-SFT',
    load_jit=True,
    load_onnx=False,
    fp16=True
)

# 定义请求体的数据模型
class TTSRequest(BaseModel):
    text: str
    speaker: str = '中文女'  
    stream: bool = True     # 是否流式合成

@app.post("/tts")
async def tts(request: TTSRequest):
    text = request.text
    speaker = request.speaker
    stream = request.stream

    # 生成语音
    speech_list = []
    for i, output in enumerate(cosyvoice.inference_sft(text, speaker, stream=stream)):
        tts_speech = output['tts_speech']
        speech_list.append(tts_speech)

    # 合并多个语音片段
    if len(speech_list) > 1:
        speech = torch.cat(speech_list, dim=-1)
    else:
        speech = speech_list[0]

    # 将语音保存到内存缓冲区
    buffer = io.BytesIO()
    torchaudio.save(buffer, speech.cpu(), 22050, format='wav')
    buffer.seek(0)

    # 返回语音数据作为响应
    return StreamingResponse(buffer, media_type="audio/wav")

# 可选：提供一个接口来列出可用的说话人
@app.get("/speakers")
async def list_speakers():
    speakers = cosyvoice.list_avaliable_spks()
    return {"speakers": speakers}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=49999)