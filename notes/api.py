import uuid

from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, UnidentifiedImageError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from .apiconf import IsNotesUser, NotesAPIMixin
from .links import find_record, set_link
from .models import Asset, Folder, Note
from .pdf import build_pdf
from .serializers import (
    FolderSerializer,
    NoteCreateSerializer,
    NoteDetailSerializer,
    NoteSummarySerializer,
    NoteUpdateSerializer,
    PdfExportSerializer,
)
from .text import extract_text, make_preview

IMAGE_TYPES = {"PNG": "image/png", "JPEG": "image/jpeg", "GIF": "image/gif", "WEBP": "image/webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class PdfThrottle(UserRateThrottle):
    rate = "30/min"


def pdf_response(data, title, inline):
    response = HttpResponse(data, content_type="application/pdf")
    name = (slugify(title)[:80] or "note") + ".pdf"
    response["Content-Disposition"] = f'{"inline" if inline else "attachment"}; filename="{name}"'
    response["Cache-Control"] = "private, no-store"
    # The export dialog previews the PDF in an iframe.
    response["X-Frame-Options"] = "SAMEORIGIN"
    return response


def check_content_shape(kind, content):
    """Boards hold an Excalidraw scene; refuse anything else so a board can't be turned into a doc."""
    if content is None:
        return
    if kind == Note.KIND_BOARD:
        if not isinstance(content.get("elements"), list):
            raise ValidationError({"content": ["A board needs a list of elements."]})
    elif content.get("type") != "doc":
        raise ValidationError({"content": ["A note's content must be a document."]})


def apply_content(note, content):
    note.content = content
    note.search_text = extract_text(note.kind, content)
    note.preview = make_preview(note.search_text)


def apply_link(note, link, user):
    if link is None:
        set_link(note, None, None)
        return
    record = find_record(link["kind"], link["id"], user)
    if record is None:
        raise ValidationError({"link": ["That record can't be found."]})
    set_link(note, link["kind"], record)


def own_notes(user):
    return Note.objects.filter(owner=user).select_related("project", "client", "lead")


class MeView(NotesAPIMixin, APIView):
    """GET /notes/api/auth/me/: the signed-in BMS user, or `{user: null}`."""

    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        if not (user.is_authenticated and IsNotesUser().has_permission(request, self)):
            return Response({"user": None})
        from core.views import _staff_portal_user

        staff_portal = _staff_portal_user(user)
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.get_full_name(),
                "is_staff": user.is_staff,
            },
            # Where "Back to Ralfiz" goes: interns and employees live in the staff portal.
            "home_url": reverse("staff:dashboard") if staff_portal else "/",
            "home_label": "Staff portal" if staff_portal else "Ralfiz BMS",
            "logout_url": reverse("logout"),
        })


class CsrfView(NotesAPIMixin, APIView):
    """GET /notes/api/auth/csrf/ sets the csrftoken cookie for the SPA's first unsafe request."""

    permission_classes = [AllowAny]

    def get(self, request):
        get_token(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class NoteViewSet(NotesAPIMixin, viewsets.GenericViewSet):
    """The signed-in user's notes and boards. No one else's are ever visible.

    list    GET    /notes/api/notes/?q=&kind=&folder=&pinned=1&trash=1
    create  POST   /notes/api/notes/        optional `link: {kind, id}` to a project/client/lead
    read    GET    /notes/api/notes/<id>/
    update  PATCH  /notes/api/notes/<id>/   send `version` with title/content edits; 409 if stale
    delete  DELETE /notes/api/notes/<id>/   moves to trash; deleting from trash is permanent
    restore POST   /notes/api/notes/<id>/restore/
    empty   DELETE /notes/api/notes/trash/
    pdf     GET    /notes/api/notes/<id>/pdf/?inline=1
    export  POST   /notes/api/notes/export-pdf/   {"notes": [ids]} combined into one PDF
    """

    def get_queryset(self):
        return own_notes(self.request.user)

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "user": self.request.user}

    def list(self, request):
        p = request.query_params
        qs = self.get_queryset().filter(deleted_at__isnull=p.get("trash") != "1").defer("content", "search_text")
        if p.get("kind") in (Note.KIND_DOC, Note.KIND_BOARD):
            qs = qs.filter(kind=p["kind"])
        if p.get("folder"):
            try:
                qs = qs.filter(folder_id=uuid.UUID(p["folder"]))
            except ValueError:
                raise ValidationError("Unknown folder.")
        if p.get("pinned") == "1":
            qs = qs.filter(pinned=True)
        if q := p.get("q", "").strip():
            qs = qs.filter(Q(title__icontains=q) | Q(search_text__icontains=q))
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(NoteSummarySerializer(page, many=True).data)

    def create(self, request):
        s = NoteCreateSerializer(data=request.data, context=self.get_serializer_context())
        s.is_valid(raise_exception=True)
        check_content_shape(s.validated_data["kind"], s.validated_data["content"])
        note = Note(
            owner=request.user,
            kind=s.validated_data["kind"],
            title=s.validated_data["title"],
            folder=s.validated_data["folder"],
        )
        apply_link(note, s.validated_data["link"], request.user)
        apply_content(note, s.validated_data["content"])
        note.save()
        return Response(NoteDetailSerializer(note).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        return Response(NoteDetailSerializer(get_object_or_404(self.get_queryset(), pk=pk)).data)

    def partial_update(self, request, pk=None):
        s = NoteUpdateSerializer(data=request.data, context=self.get_serializer_context())
        s.is_valid(raise_exception=True)
        data = s.validated_data
        with transaction.atomic():
            # select_for_update can't lock the nullable joins, so lock the note row alone.
            note = get_object_or_404(Note.objects.select_for_update().filter(owner=request.user), pk=pk)
            if note.deleted_at:
                raise ValidationError("This note is in the trash. Restore it before editing.")
            edits_text = "title" in data or "content" in data
            if edits_text and "version" in data and data["version"] != note.version:
                return Response(
                    {
                        "detail": "This note was changed somewhere else.",
                        "code": "conflict",
                        "note": NoteDetailSerializer(note).data,
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            if "title" in data:
                note.title = data["title"]
            if "content" in data:
                check_content_shape(note.kind, data["content"])
                apply_content(note, data["content"])
            if "pinned" in data:
                note.pinned = data["pinned"]
            if "folder" in data:
                note.folder = data["folder"]
            if "page_settings" in data:
                note.page_settings = data["page_settings"]
            if "link" in data:
                apply_link(note, data["link"], request.user)
            if edits_text:
                note.version += 1
            note.save()
        return Response(NoteDetailSerializer(note).data)

    def destroy(self, request, pk=None):
        note = get_object_or_404(self.get_queryset(), pk=pk)
        if note.deleted_at is None:
            note.deleted_at = timezone.now()
            note.save(update_fields=["deleted_at", "updated_at"])
        else:
            note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        note = get_object_or_404(self.get_queryset(), pk=pk, deleted_at__isnull=False)
        note.deleted_at = None
        note.save(update_fields=["deleted_at", "updated_at"])
        return Response(NoteDetailSerializer(note).data)

    @action(detail=True, methods=["get"], throttle_classes=[PdfThrottle])
    def pdf(self, request, pk=None):
        note = get_object_or_404(self.get_queryset(), pk=pk, deleted_at__isnull=True)
        if note.kind != Note.KIND_DOC:
            raise ValidationError("Only notes can be exported to PDF for now.")
        data = build_pdf([note], request.user)
        return pdf_response(data, note.title, request.query_params.get("inline") == "1")

    @action(
        detail=False, methods=["post"], url_path="export-pdf",
        throttle_classes=[PdfThrottle],
    )
    def export_pdf(self, request):
        s = PdfExportSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        ids = list(dict.fromkeys(s.validated_data["notes"]))
        found = {
            n.id: n
            for n in self.get_queryset().filter(id__in=ids, deleted_at__isnull=True, kind=Note.KIND_DOC)
        }
        if len(found) != len(ids):
            raise ValidationError("Some of these notes can't be exported.")
        notes = [found[i] for i in ids]
        return pdf_response(build_pdf(notes, request.user), notes[0].title, inline=False)

    @action(detail=False, methods=["delete"])
    def trash(self, request):
        self.get_queryset().filter(deleted_at__isnull=False).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FolderViewSet(NotesAPIMixin, viewsets.ModelViewSet):
    serializer_class = FolderSerializer
    pagination_class = None
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        return Folder.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class AssetUploadView(NotesAPIMixin, APIView):
    """POST /notes/api/assets/ (multipart, field `file`). Images only, up to 10 MB."""

    parser_classes = [MultiPartParser]

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            raise ValidationError("Choose a file to upload.")
        if upload.size > MAX_UPLOAD_BYTES:
            raise ValidationError("Images can be up to 10 MB.")
        try:
            with Image.open(upload) as img:
                fmt = img.format
                img.verify()
        except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError):
            raise ValidationError("This file isn't a supported image.")
        if fmt not in IMAGE_TYPES:
            raise ValidationError("Upload a PNG, JPEG, GIF or WebP image.")
        upload.seek(0)
        asset = Asset.objects.create(
            owner=request.user,
            file=upload,
            original_name=upload.name[:255],
            content_type=IMAGE_TYPES[fmt],
            size=upload.size,
        )
        return Response(
            {"id": str(asset.id), "url": f"/notes/api/assets/{asset.id}/", "content_type": asset.content_type},
            status=status.HTTP_201_CREATED,
        )


class AssetFileView(NotesAPIMixin, APIView):
    """GET /notes/api/assets/<id>/ streams the file to its owner only (404 for anyone else)."""

    def get(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk, owner=request.user)
        response = FileResponse(asset.file.open("rb"), content_type=asset.content_type)
        response["Cache-Control"] = "private, max-age=86400"
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Security-Policy"] = "default-src 'none'"
        return response
