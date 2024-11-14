import asyncio
import argparse
from src.interface.app import Interface

def parse_args():
    parser = argparse.ArgumentParser(description='启动全双工对话系统')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='服务器主机地址')
    parser.add_argument('--port', type=int, default=7860,
                        help='服务器端口')
    parser.add_argument('--share', action='store_true',
                        help='是否创建公共链接')
    return parser.parse_args()

def main():
    args = parse_args()
    
    interface = Interface()
    demo = interface.create_interface()
    
    demo.queue()
    demo.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share
    )

if __name__ == "__main__":
    main()