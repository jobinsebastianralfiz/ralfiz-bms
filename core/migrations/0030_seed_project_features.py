from django.db import migrations


SEED = [
    ('Website', 'Marketing / informational website', [
        'Responsive design',
        'Blog / News section',
        'Contact form',
        'Newsletter signup',
        'Photo gallery',
        'SEO optimization',
        'Google Analytics',
        'Social media integration',
        'Multi-language support',
        'Live chat',
        'CMS admin panel',
    ]),
    ('E-commerce', 'Online store with cart and payments', [
        'Product catalog',
        'Shopping cart',
        'Payment gateway (Razorpay/Stripe)',
        'Wishlist',
        'Product reviews & ratings',
        'Inventory management',
        'Coupons & discounts',
        'Order tracking',
        'Customer accounts',
        'Admin dashboard',
        'Shipping integration',
        'GST invoicing',
        'Multi-vendor support',
    ]),
    ('Web Application', 'Custom web app / SaaS platform', [
        'User authentication',
        'Role-based permissions',
        'Admin dashboard',
        'Reports & analytics',
        'API access',
        'Search & filters',
        'File uploads',
        'Notifications (email/push)',
        'Data export (CSV/Excel/PDF)',
        'Activity logs',
        'Third-party integrations',
    ]),
    ('Mobile App', 'iOS / Android mobile app', [
        'User authentication',
        'Push notifications',
        'Offline mode',
        'Biometric login',
        'In-app purchases',
        'Camera / photo upload',
        'GPS / location services',
        'Social login',
        'Chat / messaging',
        'Deep linking',
    ]),
]


def seed(apps, schema_editor):
    ProjectType = apps.get_model('core', 'ProjectType')
    ProjectFeature = apps.get_model('core', 'ProjectFeature')
    for type_order, (pt_name, pt_desc, features) in enumerate(SEED):
        pt, _ = ProjectType.objects.get_or_create(
            name=pt_name,
            defaults={'description': pt_desc, 'sort_order': type_order},
        )
        for feat_order, label in enumerate(features):
            ProjectFeature.objects.get_or_create(
                project_type=pt, label=label,
                defaults={'sort_order': feat_order},
            )


def unseed(apps, schema_editor):
    ProjectType = apps.get_model('core', 'ProjectType')
    ProjectType.objects.filter(name__in=[n for n, _, _ in SEED]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_projecttype_projectfeature_featurerequestlink'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
