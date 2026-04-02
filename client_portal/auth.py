from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers


class ClientTokenSerializer(TokenObtainPairSerializer):
    """Custom JWT token that validates client access and returns client info"""

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # Must have a client profile
        client = getattr(user, 'client_profile', None)
        if client is None:
            raise serializers.ValidationError('No client portal access for this account.')

        if not client.is_active:
            raise serializers.ValidationError('Your client account is inactive. Contact support.')

        data['user'] = {
            'id': user.pk,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        }

        data['client'] = {
            'id': str(client.id),
            'name': client.name,
            'company_name': client.company_name,
            'email': client.email,
            'phone': client.phone,
        }

        return data


class ClientTokenObtainView(TokenObtainPairView):
    serializer_class = ClientTokenSerializer
