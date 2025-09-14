# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
from module.config.config import Config
import time
from collections import defaultdict
from module.logger import logger
from module.server.main_manager import MainManager
from module.server.script_process import ScriptProcess

from tasks.Component.config_base import TimeDelta


script_app = APIRouter()
mm = MainManager()

@script_app.get('/test')
async def script_test():
    return 'success'

@script_app.get('/script_menu')
async def script_menu():
    return mm.config_cache('template').gui_menu_list
# ----------------------------------   配置文件管理   ----------------------------------
@script_app.get('/config_list')
async def config_list():
    return mm.all_script_files()

@script_app.post('/config_copy')
async def config_copy(file: str, template: str = 'template'):
    mm.copy(file, template)
    return mm.all_script_files()

@script_app.get('/config_new_name')
async def config_new_name():
    return mm.generate_script_name()

@script_app.get('/config_all')
async def config_all():
    return mm.all_json_file()


# ---------------------------------   脚本实例管理   ----------------------------------
@script_app.get('/{script_name}/start')
async def script_start(script_name: str):
    logger.info(f'[{script_name}] script process start')
    if script_name not in mm.script_process:
        mm.script_process[script_name] = ScriptProcess(script_name)
    mm.script_process[script_name].start()
    return

@script_app.get('/{script_name}/stop')
async def script_stop(script_name: str):
    logger.info(f'[{script_name}] script process stop')
    if script_name not in mm.script_process:
        logger.warning(f'[{script_name}] script process does not exist')
        return
    mm.script_process[script_name].stop()
    return

@script_app.get('/{script_name}/{task}/args')
async def script_task(script_name: str, task: str):
    return mm.config_cache(script_name).model.script_task(task)

@script_app.put('/{script_name}/{task}/{group}/{argument}/value')
async def script_task(script_name: str, task: str, group: str, argument: str, types: str, value):
    try:
        match types:
            case 'integer':
                value = int(value)
            case 'number':
                value = float(value)
            case 'boolean':
                if isinstance(value, str):
                    logger.warning(f'[{script_name}] script argument {argument} value is string, try to convert to bool')
                    if value.lower() in ['true', '1']:
                        value = True
                    elif value.lower() in ['false', '0']:
                        value = False
                value = bool(value)
            case 'string':
                pass
            case 'date_time':
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            case 'time_delta':
                # strptime 是个好东西，但是不能解析00的天数
                day = int(value[1])
                date_time = datetime.strptime(value[3:], '%H:%M:%S')
                value = TimeDelta(days=day, hours=date_time.hour, minutes=date_time.minute, seconds=date_time.second)
            case 'time':
                value = datetime.strptime(value, '%H:%M:%S').time()
            case _: pass
    except Exception as e:
        # 类型不正确
        raise HTTPException(status_code=400, detail=f'Argument type error: {e}')
    result = mm.config_cache(script_name).model.script_set_arg(task, group, argument, value)
    script_process = mm.script_process[script_name]
    config = mm.config_cache(script_name)
    config.get_next()
    # data = config.get_schedule_data()
    # logger.info(data)
    # script_process.broadcast_state({"schedule": data})
    await script_process.broadcast_state({"schedule": config.get_schedule_data()})
    return result
# --------------------------------------  SSE  --------------------------------------
@script_app.get('/{script_name}/state')
async def script_task_state(script_name: str):
    async def state_generate_events():
        while True:
            # 生成 SSE 事件数据
            event_data = "data: Hello, SSE!\n\n"
            yield event_data

            # 模拟异步操作，可以替换为您的实际处理逻辑
            await asyncio.sleep(1)

    response = StreamingResponse(state_generate_events(), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    return response

@script_app.get('/{script_name}/log')
async def script_task_log(script_name: str):
    async def log_generate_events():
        while True:
            # 生成 SSE 事件数据
            event_data = "data: log\n"
            yield event_data

            # 模拟异步操作，可以替换为您的实际处理逻辑
            await asyncio.sleep(1)

    response = StreamingResponse(log_generate_events(), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    return response

# -------------------------------------- websocket --------------------------------------
# 全局连接时间记录
last_connections = defaultdict(float)
@script_app.websocket("/ws/{script_name}")
async def websocket_endpoint(websocket: WebSocket, script_name: str):

    client_host = websocket.client.host if websocket.client else "unknown"
    client_key = f"{client_host}:{script_name}"

    # 检查连接频率 - 每秒最多一次连接
    current_time = time.time()
    last_connect_time = last_connections[client_key]

    if current_time - last_connect_time < 1.0:
        logger.warning(f'[{script_name}] 连接频率过高，拒绝连接请求 from {client_host}')

        await websocket.close(code=1008, reason="Connection rate limit exceeded (1 per second)")
        return

    # 更新最后连接时间
    last_connections[client_key] = current_time

    if script_name not in mm.script_process:
        mm.script_process[script_name] = ScriptProcess(script_name)
    script_process = mm.script_process[script_name]
    await script_process.connect(websocket)

    try:
        # 连接建立后广播初始状态
        time.sleep(0.1)
        await script_process.broadcast_state({"state": script_process.state})
        config = mm.config_cache(script_name)
        config.get_next()
        await script_process.broadcast_state({"schedule": config.get_schedule_data()})

        while True:
            # 初次进入，广播state schedule
            data = await websocket.receive_text()
            logger.info(f'[{script_name}] websocket receive: {data}')
            if data == 'get_state':
                await script_process.broadcast_state({"state": script_process.state})
            elif data == 'get_schedule':
                config = mm.config_cache(script_name)
                config.get_next()
                await script_process.broadcast_state({"schedule": config.get_schedule_data()})
            elif data == 'start':
                await script_process.start()
            elif data == 'stop':
                await script_process.stop()

    except WebSocketDisconnect:
        logger.warning(f'[{script_name}] websocket disconnect')
    except Exception as e:
        logger.error(f'[{script_name}] websocket error: {e}')
    finally:
        # 确保连接被正确清理
        try:
            script_process.disconnect(websocket)
        except Exception as e:
            logger.error(f'[{script_name}] error disconnecting websocket: {e}')






