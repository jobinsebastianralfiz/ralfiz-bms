from .models import CompanySettings


def company_settings(request):
    """Add company settings to all templates"""
    return {
        'company': CompanySettings.get_settings()
    }
