"""Loopback-only reviewer metadata API and static desk; no action endpoints."""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from importlib.resources import files
from typing import Any
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response
from pydantic import ValidationError

from sentinel.review.brief import json_brief, text_brief
from sentinel.review.evidence import LegacyEvidence, bundle, source_status
from sentinel.review.models import CHAIN_ID, GUARDIAN, UNIT, VAULT, Decision
from sentinel.review.observer import ObserveConfig, Observer, ReadRpc
from sentinel.review.rules import ReviewPolicy, process_pending
from sentinel.review.store import ReviewConflictError, ReviewStore


def create_app(
    store: ReviewStore,
    policy: ReviewPolicy,
    legacy: LegacyEvidence | None = None,
    *,
    origin: str = "http://127.0.0.1:8089",
    observe: ObserveConfig | None = None,
) -> FastAPI:
    parsed = urlsplit(origin)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port:
        raise ValueError("Review API origin must be an explicit loopback HTTP port")
    legacy = legacy or LegacyEvidence()
    if legacy.path == store.path:
        raise ValueError("Legacy and review state must be separate")

    async def observe_loop(observer: Observer) -> None:
        while True:
            try:
                await asyncio.to_thread(observer.poll)
                await asyncio.to_thread(process_pending, store, policy)
            except Exception as exc:
                # Observer persists degraded health; keep the desk available for evidence review.
                health = store.metadata("health") or {}
                if health.get("status") != "degraded":
                    store.health(
                        {
                            **health,
                            "status": "evaluation_error",
                            "error_type": type(exc).__name__,
                            "gap": "Review evaluation failed; inspect policy/source state.",
                        }
                    )
            await asyncio.sleep(15)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        with httpx.Client() as client:
            task = None
            if observe:
                observer = Observer(observe, store, ReadRpc(observe.rpc_url, client), client)
                task = asyncio.create_task(observe_loop(observer))
            try:
                yield
            finally:
                if task:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task

    app = FastAPI(
        title="NexGuard Incident Review Desk",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    assets = files("sentinel.review").joinpath("static")

    @app.middleware("http")
    async def local_guard(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.headers.get("host") != parsed.netloc:
            return PlainTextResponse("Unsupported Host", status_code=400)
        if request.method not in ("GET", "HEAD"):
            if (
                request.headers.get("origin") != origin
                or request.headers.get("x-nexguard-review") != "1"
                or request.headers.get("sec-fetch-site", "same-origin")
                not in ("same-origin", "none")
                or request.headers.get("content-type", "").split(";")[0] != "application/json"
            ):
                return PlainTextResponse(
                    "Same-origin JSON review request required", status_code=403
                )
        response: Response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
            "img-src 'self'; object-src 'none'; base-uri 'none'; "
            "frame-ancestors 'none'; form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(str(assets.joinpath("index.html")), media_type="text/html")

    @app.get("/assets/{name}")
    def asset(name: str) -> FileResponse:
        if name not in ("app.js", "style.css"):
            raise HTTPException(404)
        return FileResponse(
            str(assets.joinpath(name)),
            media_type=("text/javascript" if name == "app.js" else "text/css"),
        )

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        return {
            "chain_id": CHAIN_ID,
            "vault": VAULT,
            "guardian": GUARDIAN,
            "unit": UNIT,
            "health": source_status(store),
            "scope": store.metadata("scope"),
            "counts": store.counts(),
            "policy": policy.definition(),
            "mode": "local review / read-only chain observation",
        }

    @app.get("/api/cases")
    def cases(
        limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=1_000_000)
    ) -> dict[str, Any]:
        return {
            "items": store.cases(limit, offset),
            "offset": offset,
            "total": store.counts()["review_cases"],
        }

    def evidence(case_id: str) -> dict[str, Any]:
        try:
            return bundle(store, case_id, legacy)
        except KeyError:
            raise HTTPException(404, "Case not found") from None

    @app.get("/api/cases/{case_id}")
    def detail(case_id: str) -> dict[str, Any]:
        return evidence(case_id)

    @app.post("/api/cases/{case_id}/decisions")
    async def decide(case_id: str, request: Request) -> dict[str, Any]:
        chunks = []
        size = 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > 16_384:
                raise HTTPException(413, "Decision payload too large")
            chunks.append(chunk)
        try:
            decision = Decision.model_validate_json(b"".join(chunks))
            return store.decide(case_id, decision)
        except ValidationError:
            raise HTTPException(422, "Invalid decision fields") from None
        except ReviewConflictError as exc:
            raise HTTPException(409, str(exc)) from None
        except KeyError:
            raise HTTPException(404, "Case not found") from None

    @app.get("/api/cases/{case_id}/export/{format_name}")
    def export(case_id: str, format_name: str) -> Response:
        if format_name not in ("json", "txt"):
            raise HTTPException(404)
        value = evidence(case_id)
        text = json_brief(value) if format_name == "json" else text_brief(value)
        # A constant filename avoids incorporating untrusted path/input into headers.
        return Response(
            text,
            media_type="application/json" if format_name == "json" else "text/plain",
            headers={"Content-Disposition": f'attachment; filename="review-brief.{format_name}"'},
        )

    return app
