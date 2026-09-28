from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from app.application.document_service import DocumentValidationError
from app.security.web import authorize_profile, verify_csrf

from .public_context import container, redirect, render_page


router = APIRouter()


@router.get("/p/{profile_id}/documents")
def documents(request: Request, profile_id: str):
    authorize_profile(request, profile_id)
    docs = container(request).documents.list_for_profile(profile_id)
    return render_page(request, "documents.html", {"profile_id": profile_id, "documents": docs})


@router.post("/p/{profile_id}/documents")
async def upload_document(
    request: Request,
    profile_id: str,
    csrf: str = Form(...),
    document_type: str = Form(...),
    purpose: str = Form(...),
    file: UploadFile = File(...),
):
    authorize_profile(request, profile_id)
    verify_csrf(request, csrf)
    content = await file.read()
    try:
        container(request).documents.upload(
            profile_id,
            file.filename or "document",
            file.content_type,
            content,
            document_type,
            purpose,
        )
    except DocumentValidationError as exc:
        docs = container(request).documents.list_for_profile(profile_id)
        return render_page(
            request,
            "documents.html",
            {"profile_id": profile_id, "documents": docs, "error": str(exc)},
            400,
        )
    return redirect(f"/p/{profile_id}/documents")


@router.get("/p/{profile_id}/documents/{document_id}/download")
def download_document(request: Request, profile_id: str, document_id: str, token: str):
    authorize_profile(request, profile_id)
    try:
        metadata, content = container(request).documents.download(profile_id, document_id, token)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    headers = {"Content-Disposition": f'attachment; filename="{metadata["original_name"]}"'}
    return Response(content=content, media_type=metadata["mime_type"], headers=headers)


@router.post("/p/{profile_id}/documents/{document_id}/delete")
def delete_document(request: Request, profile_id: str, document_id: str, csrf: str = Form(...)):
    authorize_profile(request, profile_id)
    verify_csrf(request, csrf)
    try:
        container(request).documents.delete(profile_id, document_id)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    return redirect(f"/p/{profile_id}/documents")
