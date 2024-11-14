class CameraManager {
    constructor() {
        this.stream = null;
        this.videoElement = null;
        this.canvasElement = null;
        this.isStreaming = false;
        this.frameInterval = 200; // 200ms per frame
    }

    async initialize(videoElementId) {
        this.videoElement = document.getElementById(videoElementId);
        this.canvasElement = document.createElement('canvas');
        this.context = this.canvasElement.getContext('2d');

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                }
            });
            this.videoElement.srcObject = this.stream;
            await this.videoElement.play();
            
            this.canvasElement.width = this.videoElement.videoWidth;
            this.canvasElement.height = this.videoElement.videoHeight;
            
            return true;
        } catch (error) {
            console.error('Camera initialization error:', error);
            return false;
        }
    }

    startStreaming() {
        if (this.isStreaming) return;
        
        this.isStreaming = true;
        this.captureFrame();
    }

    stopStreaming() {
        this.isStreaming = false;
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    captureFrame() {
        if (!this.isStreaming) return;

        if (this.videoElement.readyState === this.videoElement.HAVE_ENOUGH_DATA) {
            this.context.drawImage(this.videoElement, 0, 0);
            const frameData = this.canvasElement.toDataURL('image/jpeg', 0.8);
            
            // 发送帧数据到服务器
            this.sendFrameToServer(frameData);
        }

        setTimeout(() => this.captureFrame(), this.frameInterval);
    }

    async sendFrameToServer(frameData) {
        try {
            const response = await fetch('/process_frame', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ frame: frameData })
            });
            
            if (!response.ok) {
                throw new Error('Frame processing failed');
            }
        } catch (error) {
            console.error('Error sending frame:', error);
        }
    }

    takeSnapshot() {
        if (!this.videoElement || !this.context) return null;
        
        this.context.drawImage(this.videoElement, 0, 0);
        return this.canvasElement.toDataURL('image/jpeg', 0.8);
    }
}