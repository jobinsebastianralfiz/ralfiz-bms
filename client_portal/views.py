from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema, extend_schema_view

from core.models import (
    Client, Project, Task, Invoice, Quote, Document, ActivityLog
)
from .models import ProjectComment, ProjectUpdate, ClientNotification
from .permissions import IsClient, IsClientOrAdmin
from .serializers import (
    ClientProfileSerializer, ProjectListSerializer, ProjectDetailSerializer,
    TaskSummarySerializer, InvoiceListSerializer, InvoiceDetailSerializer,
    QuoteListSerializer, QuoteDetailSerializer,
    ProjectCommentSerializer, ProjectCommentCreateSerializer,
    ProjectUpdateSerializer, ClientNotificationSerializer,
    DocumentSerializer, DashboardSerializer, ClientChangePasswordSerializer,
)


def get_client(request):
    """Helper to get the Client object for the authenticated user"""
    return request.user.client_profile


# ─── Dashboard ───────────────────────────────────────────────────

class ClientDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(
        tags=['Client Portal'],
        summary='Client dashboard with stats and overview',
        responses=DashboardSerializer,
    )
    def get(self, request):
        client = get_client(request)
        projects = Project.objects.filter(client=client)

        active_statuses = ['confirmed', 'in_progress', 'review']
        active_projects = projects.filter(status__in=active_statuses)

        all_invoices = Invoice.objects.filter(client=client).exclude(status='cancelled')
        pending_invoices = all_invoices.exclude(status='paid')

        total_invoiced = all_invoices.aggregate(t=Sum('total_amount'))['t'] or 0
        total_paid = all_invoices.aggregate(t=Sum('amount_paid'))['t'] or 0

        recent_updates = ProjectUpdate.objects.filter(
            project__client=client,
            is_visible_to_client=True
        )[:10]

        unread_count = ClientNotification.objects.filter(
            client=client, is_read=False
        ).count()

        data = {
            'client': ClientProfileSerializer(client).data,
            'stats': {
                'total_projects': projects.count(),
                'active_projects': active_projects.count(),
                'completed_projects': projects.filter(status='completed').count(),
                'total_invoiced': float(total_invoiced),
                'total_paid': float(total_paid),
                'balance_due': float(total_invoiced - total_paid),
                'pending_invoices': pending_invoices.count(),
            },
            'active_projects': ProjectListSerializer(active_projects[:5], many=True).data,
            'recent_updates': ProjectUpdateSerializer(
                recent_updates, many=True, context={'request': request}
            ).data,
            'pending_invoices': InvoiceListSerializer(pending_invoices[:5], many=True).data,
            'unread_notifications': unread_count,
        }
        return Response(data)


# ─── Profile ─────────────────────────────────────────────────────

class ClientProfileView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(tags=['Client Portal'], summary='Get client profile')
    def get(self, request):
        client = get_client(request)
        return Response(ClientProfileSerializer(client).data)

    @extend_schema(tags=['Client Portal'], summary='Update client profile')
    def patch(self, request):
        client = get_client(request)
        serializer = ClientProfileSerializer(client, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ClientChangePasswordView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(tags=['Client Portal'], summary='Change password')
    def post(self, request):
        serializer = ClientChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Password updated successfully.'})


# ─── Projects ────────────────────────────────────────────────────

class ClientProjectListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = ProjectListSerializer

    @extend_schema(tags=['Client Portal'], summary='List all projects')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        client = get_client(self.request)
        qs = Project.objects.filter(client=client)

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Search
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

        return qs


class ClientProjectDetailView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(tags=['Client Portal'], summary='Project detail with tasks and financials')
    def get(self, request, project_id):
        client = get_client(request)
        try:
            project = Project.objects.get(id=project_id, client=client)
        except Project.DoesNotExist:
            return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(ProjectDetailSerializer(project, context={'request': request}).data)


# ─── Task Board ──────────────────────────────────────────────────

class ClientTaskBoardView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(tags=['Client Portal'], summary='Kanban task board for a project')
    def get(self, request, project_id):
        client = get_client(request)
        try:
            project = Project.objects.get(id=project_id, client=client)
        except Project.DoesNotExist:
            return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        tasks = project.tasks.all()
        data = {
            'project': {'id': str(project.id), 'name': project.name},
            'board': {
                'todo': TaskSummarySerializer(tasks.filter(status='todo'), many=True).data,
                'in_progress': TaskSummarySerializer(tasks.filter(status='in_progress'), many=True).data,
                'review': TaskSummarySerializer(tasks.filter(status='review'), many=True).data,
                'completed': TaskSummarySerializer(tasks.filter(status='completed'), many=True).data,
            },
            'stats': {
                'total': tasks.count(),
                'todo': tasks.filter(status='todo').count(),
                'in_progress': tasks.filter(status='in_progress').count(),
                'review': tasks.filter(status='review').count(),
                'completed': tasks.filter(status='completed').count(),
            }
        }
        return Response(data)


# ─── Invoices ────────────────────────────────────────────────────

class ClientInvoiceListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = InvoiceListSerializer

    @extend_schema(tags=['Client Portal'], summary='List all invoices')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        client = get_client(self.request)
        qs = Invoice.objects.filter(client=client)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs


class ClientInvoiceDetailView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(tags=['Client Portal'], summary='Invoice detail with line items and payments')
    def get(self, request, invoice_id):
        client = get_client(request)
        try:
            invoice = Invoice.objects.get(id=invoice_id, client=client)
        except Invoice.DoesNotExist:
            return Response({'detail': 'Invoice not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Mark as viewed if sent
        if invoice.status == 'sent':
            invoice.status = 'viewed'
            invoice.save(update_fields=['status'])

        return Response(InvoiceDetailSerializer(invoice, context={'request': request}).data)


# ─── Quotes ──────────────────────────────────────────────────────

class ClientQuoteListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = QuoteListSerializer

    @extend_schema(tags=['Client Portal'], summary='List all quotes')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        client = get_client(self.request)
        return Quote.objects.filter(client=client)


class ClientQuoteDetailView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(tags=['Client Portal'], summary='Quote detail with line items')
    def get(self, request, quote_id):
        client = get_client(request)
        try:
            quote = Quote.objects.get(id=quote_id, client=client)
        except Quote.DoesNotExist:
            return Response({'detail': 'Quote not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Mark as viewed if sent
        if quote.status == 'sent':
            quote.status = 'viewed'
            quote.save(update_fields=['status'])

        return Response(QuoteDetailSerializer(quote, context={'request': request}).data)


class ClientQuoteRespondView(APIView):
    """Client can accept or reject a quote"""
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(
        tags=['Client Portal'],
        summary='Accept or reject a quote',
        request={'application/json': {'type': 'object', 'properties': {
            'action': {'type': 'string', 'enum': ['accept', 'reject']},
            'notes': {'type': 'string'},
        }, 'required': ['action']}},
    )
    def post(self, request, quote_id):
        client = get_client(request)
        try:
            quote = Quote.objects.get(id=quote_id, client=client)
        except Quote.DoesNotExist:
            return Response({'detail': 'Quote not found.'}, status=status.HTTP_404_NOT_FOUND)

        if quote.status not in ('sent', 'viewed'):
            return Response(
                {'detail': 'This quote cannot be responded to in its current status.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        action = request.data.get('action')
        if action not in ('accept', 'reject'):
            return Response({'detail': 'Action must be "accept" or "reject".'}, status=status.HTTP_400_BAD_REQUEST)

        quote.status = 'accepted' if action == 'accept' else 'rejected'
        quote.save(update_fields=['status'])

        # Log the action
        notes = request.data.get('notes', '')
        if notes:
            quote.client_notes = notes
            quote.save(update_fields=['client_notes'])

        return Response({
            'detail': f'Quote {action}ed successfully.',
            'status': quote.status,
        })


# ─── Comments ────────────────────────────────────────────────────

class ClientCommentListView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(tags=['Client Portal'], summary='List comments for a project')
    def get(self, request, project_id):
        client = get_client(request)
        try:
            project = Project.objects.get(id=project_id, client=client)
        except Project.DoesNotExist:
            return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Only top-level, non-internal comments (replies are nested)
        comments = ProjectComment.objects.filter(
            project=project, is_internal=False, parent__isnull=True
        )
        return Response(ProjectCommentSerializer(
            comments, many=True, context={'request': request}
        ).data)


class ClientCommentCreateView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(tags=['Client Portal'], summary='Post a comment on a project')
    def post(self, request):
        serializer = ProjectCommentCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(author=request.user, is_internal=False)
        return Response(
            ProjectCommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


# ─── Project Updates / Timeline ─────────────────────────────────

class ClientProjectUpdatesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = ProjectUpdateSerializer

    @extend_schema(tags=['Client Portal'], summary='Project timeline / updates')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        client = get_client(self.request)
        project_id = self.kwargs['project_id']
        return ProjectUpdate.objects.filter(
            project__id=project_id,
            project__client=client,
            is_visible_to_client=True,
        )


# ─── Notifications ───────────────────────────────────────────────

class ClientNotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = ClientNotificationSerializer

    @extend_schema(tags=['Client Portal'], summary='List notifications')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        client = get_client(self.request)
        return ClientNotification.objects.filter(client=client)


class ClientNotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(tags=['Client Portal'], summary='Mark all notifications as read')
    def post(self, request):
        client = get_client(request)
        updated = ClientNotification.objects.filter(
            client=client, is_read=False
        ).update(is_read=True)
        return Response({'detail': f'{updated} notifications marked as read.'})


class ClientNotificationMarkSingleReadView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(tags=['Client Portal'], summary='Mark a single notification as read')
    def post(self, request, notification_id):
        client = get_client(request)
        try:
            notification = ClientNotification.objects.get(id=notification_id, client=client)
        except ClientNotification.DoesNotExist:
            return Response({'detail': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'detail': 'Notification marked as read.'})


# ─── Documents ───────────────────────────────────────────────────

class ClientDocumentListView(APIView):
    permission_classes = [IsAuthenticated, IsClient]

    @extend_schema(tags=['Client Portal'], summary='List documents for a project')
    def get(self, request, project_id):
        client = get_client(request)
        try:
            project = Project.objects.get(id=project_id, client=client)
        except Project.DoesNotExist:
            return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        ct = ContentType.objects.get_for_model(Project)
        documents = Document.objects.filter(content_type=ct, object_id=str(project.id))
        return Response(DocumentSerializer(
            documents, many=True, context={'request': request}
        ).data)


# ─── All Tasks (across projects) ────────────────────────────────

class ClientAllTasksView(generics.ListAPIView):
    """View all tasks across all client projects"""
    permission_classes = [IsAuthenticated, IsClient]
    serializer_class = TaskSummarySerializer

    @extend_schema(tags=['Client Portal'], summary='All tasks across all projects')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        client = get_client(self.request)
        qs = Task.objects.filter(project__client=client)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        priority = self.request.query_params.get('priority')
        if priority:
            qs = qs.filter(priority=priority)

        return qs
