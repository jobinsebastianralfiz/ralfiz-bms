from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import Employee


class EmployeeTokenSerializer(TokenObtainPairSerializer):
    """Custom JWT token that includes employee info in response"""

    def _create_employee_from_team_member(self, user):
        """Auto-create Employee profile from TeamMember if it exists"""
        team_member = getattr(user, 'team_profile', None)
        if team_member is None:
            return None

        # Map TeamMember fields to Employee fields
        employment_type_map = {
            'permanent': 'fulltime',
            'freelancer': 'parttime',
        }
        role_to_dept_map = {
            'developer': 'engineering',
            'designer': 'design',
            'project_manager': 'operations',
            'qa': 'engineering',
            'devops': 'engineering',
            'other': 'other',
        }

        # Generate employee_id
        last_emp = Employee.objects.order_by('-employee_id').first()
        if last_emp and last_emp.employee_id.startswith('EMP'):
            try:
                num = int(last_emp.employee_id[3:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        employee_id = f'EMP{num:03d}'

        employee = Employee.objects.create(
            user=user,
            employee_id=employee_id,
            employment_type=employment_type_map.get(team_member.employment_type, 'fulltime'),
            department=role_to_dept_map.get(team_member.role, 'other'),
            designation=team_member.get_role_display(),
            phone=team_member.phone or '',
            monthly_salary=team_member.monthly_salary,
            hourly_rate=team_member.hourly_rate,
            status='active',
        )
        return employee

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
        except Employee.DoesNotExist:
            employee = self._create_employee_from_team_member(user)
            if employee is None and (user.is_superuser or user.is_staff):
                # Auto-create Employee for superusers/staff
                last_emp = Employee.objects.order_by('-employee_id').first()
                if last_emp and last_emp.employee_id.startswith('EMP'):
                    try:
                        num = int(last_emp.employee_id[3:]) + 1
                    except ValueError:
                        num = 1
                else:
                    num = 1
                employee = Employee.objects.create(
                    user=user,
                    employee_id=f'EMP{num:03d}',
                    employment_type='fulltime',
                    role='owner' if user.is_superuser else 'employee',
                    department='operations',
                    designation='Admin',
                    status='active',
                )
            if employee is None:
                raise serializers.ValidationError('No employee profile found for this user.')

        # Auto-set role='owner' for superuser-created employees
        if user.is_superuser and employee.role == 'employee':
            employee.role = 'owner'
            employee.save(update_fields=['role'])

        if employee.status != 'active':
            raise serializers.ValidationError('Your account is inactive. Contact admin.')

        request = self.context.get('request')
        profile_photo_url = None
        photo = employee.profile_photo or employee.face_photo
        if photo and request:
            profile_photo_url = request.build_absolute_uri(photo.url)

        data['employee'] = {
            'id': str(employee.id),
            'employee_id': employee.employee_id,
            'employment_type': employee.employment_type,
            'role': employee.role,
            'department': employee.department,
            'designation': employee.designation,
            'status': employee.status,
            'profile_photo': profile_photo_url,
            'has_face_registered': bool(employee.face_photo),
        }

        return data


class EmployeeTokenObtainView(TokenObtainPairView):
    serializer_class = EmployeeTokenSerializer
