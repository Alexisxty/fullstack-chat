class ChatInterface {
    constructor() {
        this.cameraManager = new CameraManager();
        this.sessionId = null;
        this.isActive = false;
        this.audioContext = null;
        this.mediaRecorder = null;
    }

    async initialize() {
        // 初始化会话
        this.sessionId = await this.createSession();
        
        // 初始化摄像头
        const cameraInitialized = await this.cameraManager.initialize('video-feed');
        if (!cameraInitialized) {
            this.showError('摄像头初始化失败');
            return false;
        }

        // 初始化音频
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (error) {
            this.showError('音频初始化失败');
            return false;
        }

        this.bindEvents();
        return true;
    }

    async createSession() {
        try {
            const response = await fetch('/create_session', { method: 'POST' });
            const data = await response.json();
            return data.session_id;
        } catch (error) {
            console.error('Session creation failed:', error);
            return null;
        }
    }

    bindEvents() {
        // 绑定开始/停止按钮事件
        document.getElementById('start-button').addEventListener('click', () => this.startChat());
        document.getElementById('stop-button').addEventListener('click', () => this.stopChat());

        // 绑定摄像头控制按钮事件
        document.getElementById('camera-start').addEventListener('click', () => this.cameraManager.startStreaming());
        document.getElementById('camera-stop').addEventListener('click', () => this.cameraManager.stopStreaming());
    }

    async startChat() {
        if (this.isActive) return;
        
        this.isActive = true;
        this.updateStatus('active');
        
        // 开始音频录制
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.startAudioRecording(stream);
        } catch (error) {
            console.error('Audio recording failed:', error);
            this.showError('音频录制失败');
        }
        
        // 开始视频流
        this.cameraManager.startStreaming();
    }

    stopChat() {
        this.isActive = false;
        this.updateStatus('inactive');
        
        // 停止音频录制
        if (this.mediaRecorder) {
            this.mediaRecorder.stop();
        }
        
        // 停止视频流
        this.cameraManager.stopStreaming();
    }

    startAudioRecording(stream) {
        this.mediaRecorder = new MediaRecorder(stream);
        
        this.mediaRecorder.ondataavailable = async (event) => {
            if (event.data.size > 0) {
                await this.sendAudioChunk(event.data);
            }
        };
        
        this.mediaRecorder.start(1000); // 每秒发送一次数据
    }

    async sendAudioChunk(audioData) {
        try {
            const formData = new FormData();
            formData.append('audio', audioData, 'audio.wav');
            formData.append('session_id', this.sessionId);

            const response = await fetch('/process_audio', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Audio processing failed');
            }

            const data = await response.json();
            this.updateChat(data);
        } catch (error) {
            console.error('Error sending audio:', error);
        }
    }

    updateChat(data) {
        const chatContainer = document.querySelector('.chat-container');
        
        if (data.text) {
            const messageElement = document.createElement('div');
            messageElement.className = `message ${data.role}-message`;
            messageElement.textContent = data.text;
            chatContainer.appendChild(messageElement);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    updateStatus(status) {
        const indicator = document.querySelector('.status-indicator');
        indicator.className = `status-indicator status-${status}`;
    }

    showError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        document.body.appendChild(errorElement);
        
        setTimeout(() => errorElement.remove(), 3000);
    }
}

// 初始化接口
document.addEventListener('DOMContentLoaded', async () => {
    const chatInterface = new ChatInterface();
    await chatInterface.initialize();
});