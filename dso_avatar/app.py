import os
import time
import cv2
import glob
import pickle
import copy
import queue
from queue import Queue
from threading import Thread, Event
import torch.multiprocessing as mp
import asyncio
import aiohttp_cors
from aiohttp import web
import aiohttp
import importlib
import argparse

from utils.logger import logger
from server.session_manager import session_manager
from server.rtc_manager import rtc_manager
from server.routes import setup_routes

# 全局变量
global_avatars = {}
opt = None
model = None

def build_avatar_session(sessionid, params):
    # This is the factory function for SessionManager
    # It constructs a NEW avatar instance for the requested session
    from avatars.wav2lip_avatar import LipReal
    global global_avatars, opt, model
    
    avatar = LipReal(opt, model, global_avatars[opt.avatar_id])
    return avatar

async def offer(request):
    return await rtc_manager.handle_offer(request)

async def on_shutdown(app):
    await rtc_manager.shutdown()

def llm_response(text):
    # Placeholder for LLM logic if needed
    pass

def main():
    global opt, model
    parser = argparse.ArgumentParser()
    parser.add_argument('--fps', type=int, default=25)
    parser.add_argument('-l', type=int, default=10)
    parser.add_argument('-m', type=int, default=8)
    parser.add_argument('-r', type=int, default=3)
    parser.add_argument('--model', type=str, default='wav2lip')
    parser.add_argument('--avatar_id', type=str, default='sarah_static')
    parser.add_argument('--batch_size', type=int, default=4)
    parser.add_argument('--modelres', type=int, default=256)
    parser.add_argument('--listenport', type=int, default=8010)
    parser.add_argument('--transport', type=str, default='webrtc')
    parser.add_argument('--push_url', type=str, default='http://localhost:1985/rtc/v1/whip/?app=live&stream=livestream')
    parser.add_argument('--max_session', type=int, default=1)
    parser.add_argument('--tts', type=str, default='edgetts')
    parser.add_argument('--REF_FILE', type=str, default='zh-CN-YunxiaNeural')
    parser.add_argument('--REF_TEXT', type=str, default=None)
    parser.add_argument('--TTS_SERVER', type=str, default='http://127.0.0.1:9880')

    opt, unknown = parser.parse_known_args()
    
    # Load Engine
    _avatar_modules = {
        'wav2lip': 'avatars.wav2lip_avatar'
    }
    avatar_mod = importlib.import_module(_avatar_modules[opt.model])
    load_model = avatar_mod.load_model
    load_avatar = avatar_mod.load_avatar
    warm_up = avatar_mod.warm_up
    
    logger.info("Initializing Engine...")
    model = load_model("./models/wav2lip.pth")
    global_avatars[opt.avatar_id] = load_avatar(opt.avatar_id)
    warm_up(opt.batch_size, model, opt.modelres)

    # Init Session Manager
    session_manager.init_builder(build_avatar_session)
    
    # Pre-load Session 0
    logger.info("Pre-loading default session '0'...")
    session_manager.add_session('0', build_avatar_session('0', {}))

    # Setup Server
    appasync = web.Application(client_max_size=1024**2*100)
    appasync.on_shutdown.append(on_shutdown)
    
    # Routes
    appasync.router.add_post("/offer", offer)
    setup_routes(appasync)

    # CORS
    cors = aiohttp_cors.setup(appasync, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*",
        )
    })
    for route in list(appasync.router.routes()):
        try: cors.add(route)
        except: pass

    logger.info(f"Server starting on port {opt.listenport}")
    
    def run_server(runner):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(runner.setup())
        site = web.TCPSite(runner, '0.0.0.0', opt.listenport)
        loop.run_until_complete(site.start())
        loop.run_forever()

    run_server(web.AppRunner(appasync))

if __name__ == '__main__':
    mp.set_start_method('spawn')
    main()
