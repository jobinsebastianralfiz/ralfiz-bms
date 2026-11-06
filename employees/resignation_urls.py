from django.urls import path

from . import resignation_views as v

urlpatterns = [
    # More specific paths first: a bare <token> would otherwise swallow them.
    path('<str:token>/done/', v.resignation_done, name='resignation_done'),
    path('<str:token>/letter/', v.resignation_document, {'kind': 'letter'}, name='resignation_letter'),
    path('<str:token>/letter.pdf', v.resignation_document_pdf, {'kind': 'letter'}, name='resignation_letter_pdf'),
    path('<str:token>/relieving/', v.resignation_document, {'kind': 'relieving'}, name='relieving_letter'),
    path('<str:token>/relieving.pdf', v.resignation_document_pdf, {'kind': 'relieving'}, name='relieving_letter_pdf'),
    path('<str:token>/certificate.pdf', v.resignation_certificate_pdf, name='resignation_certificate_pdf'),
    path('<str:token>/thanks/', v.resignation_thanks, name='resignation_thanks'),
    path('<str:token>/thanks.pdf', v.resignation_thanks_pdf, name='resignation_thanks_pdf'),
    path('<str:token>/', v.resignation_form, name='resignation_form'),
]
