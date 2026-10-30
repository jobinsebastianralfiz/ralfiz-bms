from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from notes.api import apply_content
from notes.apiconf import NotesAPIMixin
from notes.models import Note
from notes.pages import clean_page_settings
from notes.serializers import NoteDetailSerializer

from .models import Template
from .serializers import SaveTemplateSerializer, TemplateDetailSerializer, TemplateSummarySerializer


class TemplateViewSet(NotesAPIMixin, viewsets.GenericViewSet):
    """Built-in templates plus the signed-in user's own.

    list    GET    /notes/api/templates/
    read    GET    /notes/api/templates/<id>/        includes content, for the preview
    save    POST   /notes/api/templates/             {note, name, description, category}: save a note as a template
    delete  DELETE /notes/api/templates/<id>/        own templates only
    use     POST   /notes/api/templates/<id>/use/    creates a note from it
    """

    pagination_class = None

    def get_queryset(self):
        return Template.objects.filter(is_active=True).filter(Q(owner__isnull=True) | Q(owner=self.request.user))

    def list(self, request):
        qs = self.get_queryset().defer("content")
        return Response(TemplateSummarySerializer(qs, many=True).data)

    def retrieve(self, request, pk=None):
        return Response(TemplateDetailSerializer(get_object_or_404(self.get_queryset(), pk=pk)).data)

    def create(self, request):
        s = SaveTemplateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        note = Note.objects.filter(owner=request.user, pk=data["note"], deleted_at__isnull=True).first()
        if note is None or note.kind != Note.KIND_DOC:
            raise ValidationError("Only your own notes can be saved as templates.")
        template = Template.objects.create(
            owner=request.user,
            name=data["name"],
            description=data["description"],
            category=data["category"],
            note_title=note.title,
            content=note.content or {"type": "doc", "content": []},
            page_settings=clean_page_settings(note.page_settings or {}),
        )
        return Response(TemplateSummarySerializer(template).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        template = get_object_or_404(self.get_queryset(), pk=pk, owner=request.user)
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def use(self, request, pk=None):
        template = get_object_or_404(self.get_queryset(), pk=pk)
        note = Note(
            owner=request.user,
            title=template.note_title or template.name,
            page_settings=clean_page_settings(template.page_settings or {}),
        )
        apply_content(note, template.content)
        note.save()
        return Response(NoteDetailSerializer(note).data, status=status.HTTP_201_CREATED)
