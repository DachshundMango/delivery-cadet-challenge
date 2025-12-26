from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import uuid
import json
from datetime import datetime
from graph import app as graph_app

app = FastAPI(title="Delivery Cadet Agent")

# CORS 허용 (UI 접속용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 간단한 인메모리 스레드 저장소
threads_store: Dict[str, Dict] = {}

class ThreadCreate(BaseModel):
    metadata: Optional[Dict[str, Any]] = None

class StreamInput(BaseModel):
    input: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None
    stream_mode: Optional[List[str]] = ["values"]

# 서버 정보 엔드포인트
@app.get("/info")
async def get_info():
    return {
        "version": "1.0.0",
        "type": "langgraph-server"
    }

# 어시스턴트별 스레드 목록 조회
@app.get("/assistants/{assistant_id}/threads")
async def list_assistant_threads(assistant_id: str, limit: int = 10, offset: int = 0):
    thread_list = list(threads_store.values())
    return {
        "threads": thread_list[offset:offset+limit],
        "total": len(thread_list)
    }

# 스레드 목록 조회
@app.get("/threads")
async def list_threads(limit: int = 10, offset: int = 0):
    thread_list = list(threads_store.values())
    return {
        "threads": thread_list[offset:offset+limit],
        "total": len(thread_list)
    }

# 어시스턴트별 스레드 생성
@app.post("/assistants/{assistant_id}/threads")
async def create_assistant_thread(assistant_id: str, thread_data: Optional[ThreadCreate] = None):
    return await create_thread(thread_data)

# 스레드 생성
@app.post("/threads")
async def create_thread(thread_data: Optional[ThreadCreate] = None):
    thread_id = str(uuid.uuid4())
    thread = {
        "thread_id": thread_id,
        "created_at": datetime.utcnow().isoformat(),
        "metadata": thread_data.metadata if thread_data else {},
        "status": "idle"
    }
    threads_store[thread_id] = thread
    return thread

# 어시스턴트별 스레드 조회
@app.get("/assistants/{assistant_id}/threads/{thread_id}")
async def get_assistant_thread(assistant_id: str, thread_id: str):
    return await get_thread(thread_id)

# 스레드 조회
@app.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    if thread_id not in threads_store:
        raise HTTPException(status_code=404, detail="Thread not found")
    return threads_store[thread_id]

# 스레드 히스토리 조회
@app.post("/threads/{thread_id}/history")
async def get_thread_history(thread_id: str):
    # 스레드가 없거나 히스토리가 없으면 빈 배열 반환
    if thread_id not in threads_store:
        return []

    # 스레드에 저장된 히스토리 반환 (배열 형식)
    thread = threads_store[thread_id]
    history = thread.get("history", [])
    return history

# 어시스턴트별 스레드 히스토리 조회
@app.post("/assistants/{assistant_id}/threads/{thread_id}/history")
async def get_assistant_thread_history(assistant_id: str, thread_id: str):
    return await get_thread_history(thread_id)

# 어시스턴트별 스트리밍 실행 (LangGraph SDK 호환)
@app.post("/assistants/{assistant_id}/threads/{thread_id}/runs/stream")
async def stream_run_with_assistant(assistant_id: str, thread_id: str, stream_input: StreamInput):
    return await stream_run(thread_id, stream_input)

# 스트리밍 실행
@app.post("/threads/{thread_id}/runs/stream")
async def stream_run(thread_id: str, stream_input: StreamInput):
    # 스레드가 없으면 생성
    if thread_id not in threads_store:
        threads_store[thread_id] = {
            "thread_id": thread_id,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {},
            "status": "running"
        }

    async def event_generator():
        try:
            # 입력 데이터 추출
            user_question = stream_input.input.get("messages", [])
            if user_question:
                if isinstance(user_question, list):
                    question_text = user_question[-1].get("content", "") if isinstance(user_question[-1], dict) else str(user_question[-1])
                else:
                    question_text = str(user_question)
            else:
                question_text = stream_input.input.get("user_question", "")

            inputs = {"user_question": question_text}

            # 메시지 누적을 위한 변수
            all_messages = []

            # LangGraph 스트리밍
            for chunk in graph_app.stream(inputs):
                for node_name, node_output in chunk.items():
                    # 메시지 변환 및 누적
                    if "messages" in node_output:
                        for msg in node_output["messages"]:
                            content = msg.content if hasattr(msg, 'content') else str(msg)
                            msg_type = "human" if hasattr(msg, 'type') and msg.type == "human" else "ai"
                            # ID가 None이 아닌 경우에만 사용, 아니면 UUID 생성
                            msg_id = getattr(msg, 'id', None) or str(uuid.uuid4())

                            # 중복 방지: 같은 content를 가진 메시지가 이미 있는지 확인
                            is_duplicate = any(m.get("content") == content for m in all_messages)

                            if not is_duplicate:
                                msg_obj = {
                                    "type": msg_type,
                                    "id": msg_id,
                                    "content": content,
                                    "additional_kwargs": {},
                                    "response_metadata": {}
                                }
                                all_messages.append(msg_obj)

                    # 값 이벤트 - LangGraph SDK 호환 형식 (누적된 메시지 전송)
                    values_data = {
                        "messages": all_messages,
                        "user_question": node_output.get("user_question", question_text)
                    }

                    # 다른 필드들도 추가
                    for key in ["intent", "query", "query_result"]:
                        if key in node_output:
                            values_data[key] = node_output[key]

                    event_data = [
                        "values",
                        values_data
                    ]

                    # SSE 형식으로 전송 (배열 형식)
                    yield f"data: {json.dumps(event_data)}\n\n"

            # 완료 이벤트
            end_event = ["end", None]
            yield f"data: {json.dumps(end_event)}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_event = ["error", {"message": str(e)}]
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
