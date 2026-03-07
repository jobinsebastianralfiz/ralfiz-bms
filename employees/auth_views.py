from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers


class EmployeeTokenSerializer(TokenObtainPairSerializer):
    """Custom JWT token that includes employee info in response"""

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add employee info to response
        user = self.user
        data['user'] = {
            'id': user.pk,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        }

        try:
            employee = user.employee_profile
            data['employee'] = {
                'id': str(employee.id),
                'employee_id': employee.employee_id,
                'employment_type': employee.employment_type,
                'department': employee.department,
                'designation': employee.designation,
                'status': employee.status,
                'has_face_registered': bool(employee.face_photo),
            }
        except Exception:
            raise serializers.ValidationError('No employee profile found for this user.')

        if hasattr(user, 'employee_profile') and user.employee_profile.status != 'active':
            raise serializers.ValidationError('Your account is inactive. Contact admin.')

        return data


class EmployeeTokenObtainView(TokenObtainPairView):
    serializer_class = EmployeeTokenSerializer
