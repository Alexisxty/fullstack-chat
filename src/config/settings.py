from pathlib import Path

# 基础配置
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# API配置
ASR_API_URL = "http://localhost:50000/api/v1/asr"
TTS_API_URL = "http://localhost:49999/tts"

# 模型配置
MODEL_CONFIG = {
    "default_model": "qwen",  # 默认使用的模型
    
    "openai": {
        "api_key": "your-openai-api-key",
        "api_base": "https://api.openai.com/v1",
        "model": "gpt-4-vision-preview",
        "max_tokens": 4096,
        "temperature": 0.7
    },
    
    "qwen": {
        "checkpoint_path": "/mnt/82_store/LLM-weights/Qwen2-VL-7B-Instruct-GPTQ-Int8",
        "device": "cuda",
        "max_seq_len": 64000,
        "temperature": 0.7,
        "top_p": 0.8,
        "use_flash_attention": True,  
        "torch_dtype": "bfloat16",    
    },
    
    "local_vllm": {
        "model_path": "/path/to/local/model",
        "api_url": "http://localhost:8000/v1"
    }
}
# 音频配置
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "chunk_size": 1024 * 16,
    "channels": 1
}

# 视频配置
VIDEO_CONFIG = {
    "frame_width": 640,
    "frame_height": 480,
    "fps": 30
}

# 会话配置
SESSION_CONFIG = {
    "max_history": 100,
    "timeout": 3600  # 1小时
}

# 系统提示词
SYSTEM_PROMPTS = {
    "default": """
    你是一个智能助手，必须严格按照以下规则回复：
    规则1: 当检测到以下情况时，仅输出 [C.LISTEN]
    - 用户正在讲故事（例如："从前..."，"接下来..."）
    - 用户表示要继续说（例如："我要讲..."，"让我说..."）
    - 用户句子明显未完成
    
    规则2: 当检测到以下情况时，仅输出 [S.LISTEN]
    - 用户说"听我说"
    - 用户说"等一下"
    - 用户要求保持安静
    
    规则3: 当需要正常回应时，以 [S.SPEAK] 开头
    """,
    
    "openai": """You are a helpful assistant. Follow these rules strictly:
    1. Output only [C.LISTEN] when:
    - User is telling a story
    - User indicates they want to continue
    - User's sentence is clearly incomplete
    
    2. Output only [S.LISTEN] when:
    - User says "listen to me"
    - User says "wait"
    - User requests silence
    
    3. Start with [S.SPEAK] for normal responses
    """
}