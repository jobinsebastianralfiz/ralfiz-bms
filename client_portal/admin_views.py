"""Admin-facing APIs for managing client portal accounts and posting updates."""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from drf_spectacular.utils import extend_schema

from core.models import Client, Project
from .models import ProjectUpdate, ClientNotification
from .serializers import ProjectUpdateSerializer


class AdminCreateClientAccountView(APIView):
    """Create a login account for an existing client"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        tags=['Client Portal Admin'],
        summary='Create portal login for a client',
        request={'application/json': {'type': 'object', 'properties': {
            'client_id': {'type': 'string', 'format': 'uuid'},
            'username': {'type': 'string'},
            'password': {'type': 'string', 'description': 'Optional. Auto-generated if not provided.'},
        }, 'required': ['client_id']}},
    )
    def post(self, request):
        client_id = request.data.get('client_id')
        if not client_id:
            return Response({'detail': 'client_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'detail': 'Client not found.'}, status=status.HTTP_404_NOT_FOUND)

        if client.user:
            return Response({
                'detail': 'Client already has a portal account.',
                'username': client.user.username,
            }, status=status.HTTP_400_BAD_REQUEST)

        username = request.data.get('username') or client.email or f'client_{client.id.hex[:8]}'
        password = request.data.get('password') or get_random_string(12)

        # Ensure username is unique
        if User.objects.filter(username=username).exists():
            return Response(
                {'detail': f'Username "{username}" already exists. Provide a different username.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            email=client.email,
            password=password,
            first_name=client.name.split()[0] if client.name else '',
            last_name=' '.join(client.name.split()[1:]) if client.name and len(client.name.split()) > 1 else '',
        )

        client.user = user
        client.save(update_fields=['user'])

        return Response({
            'detail': 'Client portal account created successfully.',
            'username': username,
            'password': password,
            'client_id': str(client.id),
            'client_name': client.name,
        }, status=status.HTTP_201_CREATED)


class AdminResetClientPasswordView(APIView):
    """Reset a client's portal password"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        tags=['Client Portal Admin'],
        summary='Reset client portal password',
        request={'application/json': {'type': 'object', 'properties': {
            'client_id': {'type': 'string', 'format': 'uuid'},
            'new_password': {'type': 'string', 'description': 'Optional. Auto-generated if not provided.'},
        }, 'required': ['client_id']}},
    )
    def post(self, request):
        client_id = request.data.get('client_id')
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'detail': 'Client not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not client.user:
            return Response({'detail': 'Client has no portal account.'}, status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get('new_password') or get_random_string(12)
        client.user.set_password(new_password)
        client.user.save()

        return Response({
            'detail': 'Password reset successfully.',
            'username': client.user.username,
            'new_password': new_password,
        })


class AdminDeactivateClientAccountView(APIView):
    """Deactivate a client's portal access"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(tags=['Client Portal Admin'], summary='Deactivate client portal access')
    def post(self, request, client_id):
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'detail': 'Client not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not client.user:
            return Response({'detail': 'Client has no portal account.'}, status=status.HTTP_400_BAD_REQUEST)

        client.user.is_active = not client.user.is_active
        client.user.save(update_fields=['is_active'])

        state = 'activated' if client.user.is_active else 'deactivated'
        return Response({'detail': f'Client portal access {state}.'})


class AdminListClientAccountsView(APIView):
    """List all clients with their portal account status"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(tags=['Client Portal Admin'], summary='List clients with portal account status')
    def get(self, request):
        clients = Client.objects.filter(is_active=True)
        data = []
        for client in clients:
            entry = {
                'id': str(client.id),
                'name': client.name,
                'company_name': client.company_name,
                'email': client.email,
                'has_portal_account': client.user is not None,
            }
            if client.user:
                entry['username'] = client.user.username
                entry['account_active'] = client.user.is_active
                entry['last_login'] = client.user.last_login
            data.append(entry)
        return Response(data)


class AdminPostProjectUpdateView(APIView):
    """Post a project update visible to the client"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        tags=['Client Portal Admin'],
        summary='Post a project update (visible to client)',
        request={'application/json': {'type': 'object', 'properties': {
            'project_id': {'type': 'string', 'format': 'uuid'},
            'title': {'type': 'string'},
            'description': {'type': 'string'},
            'update_type': {'type': 'string', 'enum': ['milestone', 'progress', 'release', 'blocker', 'info']},
            'progress_percentage': {'type': 'integer', 'minimum': 0, 'maximum': 100},
            'is_visible_to_client': {'type': 'boolean', 'default': True},
        }, 'required': ['project_id', 'title', 'description']}},
    )
    def post(self, request):
        project_id = request.data.get('project_id')
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        update = ProjectUpdate.objects.create(
            project=project,
            author=request.user,
            title=request.data.get('title', ''),
            description=request.data.get('description', ''),
            update_type=request.data.get('update_type', 'progress'),
            progress_percentage=request.data.get('progress_percentage'),
            is_visible_to_client=request.data.get('is_visible_to_client', True),
        )

        # Auto-create notification for the client
        if update.is_visible_to_client and project.client.user:
            ClientNotification.objects.create(
                client=project.client,
                title=f'Project Update: {update.title}',
                message=update.description[:200],
                notification_type='project_update',
                project=project,
            )

        return Response(
            ProjectUpdateSerializer(update, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AdminSendClientNotificationView(APIView):
    """Send a custom notification to a client"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        tags=['Client Portal Admin'],
        summary='Send notification to a client',
        request={'application/json': {'type': 'object', 'properties': {
            'client_id': {'type': 'string', 'format': 'uuid'},
            'title': {'type': 'string'},
            'message': {'type': 'string'},
            'project_id': {'type': 'string', 'format': 'uuid'},
        }, 'required': ['client_id', 'title', 'message']}},
    )
    def post(self, request):
        client_id = request.data.get('client_id')
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'detail': 'Client not found.'}, status=status.HTTP_404_NOT_FOUND)

        project = None
        project_id = request.data.get('project_id')
        if project_id:
            try:
                project = Project.objects.get(id=project_id, client=client)
            except Project.DoesNotExist:
                pass

        notification = ClientNotification.objects.create(
            client=client,
            title=request.data.get('title', ''),
            message=request.data.get('message', ''),
            notification_type='general',
            project=project,
        )

        return Response({'detail': 'Notification sent.', 'id': str(notification.id)}, status=status.HTTP_201_CREATED)
