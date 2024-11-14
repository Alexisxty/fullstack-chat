import gradio as gr
import asyncio
from src.core.worker import Worker
from src.config.settings import SESSION_CONFIG

class Interface:
    def __init__(self):
        self.worker = Worker()
        
    def create_interface(self):
        with gr.Blocks(css=self.load_css()) as demo:
            session_id = gr.State(lambda: self.worker.session_manager.create_session())
            
            with gr.Row():
                with gr.Column(scale=1):
                    start_button = gr.Button("开始对话", elem_id="start-button")
                    stop_button = gr.Button("结束对话", elem_id="stop-button")
                    
                with gr.Column(scale=2):
                    status = gr.HTML("""
                        <div class="status-container">
                            状态: <span class="status-indicator status-inactive"></span>
                        </div>
                    """)
                    
            with gr.Row():
                with gr.Column(scale=1):
                    camera_feed = gr.Image(
                        label="摄像头预览",
                        sources="webcam",
                        streaming=True,
                        elem_id="video-feed"
                    )
                    with gr.Row():
                        camera_start = gr.Button("开启摄像头", elem_id="camera-start")
                        camera_stop = gr.Button("关闭摄像头", elem_id="camera-stop")
                        
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        height=400,
                        elem_id="chatbot"
                    )
                    
            with gr.Row():
                audio_input = gr.Audio(
                    sources="microphone",
                    streaming=True,
                    elem_id="audio-input"
                )
                audio_output = gr.Audio(
                    label="Assistant's Response",
                    elem_id="audio-output"
                )
                
            # 绑定事件处理
            start_button.click(
                fn=self.start_session,
                inputs=[session_id],
                outputs=[chatbot, status]
            )
            
            stop_button.click(
                fn=self.stop_session,
                inputs=[session_id],
                outputs=[status]
            )
            
            # 处理音频流
            audio_input.stream(
                fn=self.worker.process_input,
                inputs=[session_id, audio_input],
                outputs=[chatbot, audio_output]
            )
            
            # 处理视频流
            camera_feed.stream(
                fn=self.worker.process_input,
                inputs=[session_id, None, camera_feed],
                outputs=[chatbot]
            )
            
        return demo
        
    def load_css(self):
        with open('src/interface/static/css/style.css', 'r') as f:
            return f.read()
            
    async def start_session(self, session_id):
        """开始会话"""
        if not session_id:
            return None, "错误：无效的会话ID"
            
        self.worker.session_manager.update_session_state(
            session_id,
            DialogueState.LISTENING
        )
        return [], """
            <div class="status-container">
                状态: <span class="status-indicator status-active"></span>
            </div>
        """
        
    async def stop_session(self, session_id):
        """结束会话"""
        if session_id:
            await self.worker.handle_interrupt(session_id)
        return """
            <div class="status-container">
                状态: <span class="status-indicator status-inactive"></span>
            </div>
        """