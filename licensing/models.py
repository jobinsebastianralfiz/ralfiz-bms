import uuid
import json
import base64
import hashlib
from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend


class LicenseKey(models.Model):
    """Model to store RSA key pairs for license signing"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, default="RetailEase Pro")
    private_key = models.TextField(help_text="PEM encoded private key (keep secret!)")
    public_key = models.TextField(help_text="PEM encoded public key (embed in app)")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "License Key Pair"
        verbose_name_plural = "License Key Pairs"
    
    def __str__(self):
        return f"{self.name} - {'Active' if self.is_active else 'Inactive'}"
    
    @classmethod
    def generate_key_pair(cls, name="RetailEase Pro", key_size=4096):
        """Generate a new RSA key pair"""
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # Serialize public key
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return cls.objects.create(
            name=name,
            private_key=private_pem,
            public_key=public_pem,
            is_active=True
        )
    
    def get_private_key(self):
        """Load and return the private key object"""
        return serialization.load_pem_private_key(
            self.private_key.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
    
    def get_public_key(self):
        """Load and return the public key object"""
        return serialization.load_pem_public_key(
            self.public_key.encode('utf-8'),
            backend=default_backend()
        )


class License(models.Model):
    """Model to store issued licenses"""

    LICENSE_TYPE_CHOICES = [
        ('trial', 'Trial (30 days)'),
        ('basic', 'Basic (1 year)'),
        ('professional', 'Professional (1 year)'),
        ('enterprise', 'Enterprise (1 year)'),
        ('lifetime', 'Lifetime'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key_pair = models.ForeignKey(LicenseKey, on_delete=models.PROTECT, related_name='licenses')

    # Link to Client (optional - for tracking)
    client = models.ForeignKey(
        'core.Client',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='licenses',
        help_text='Link this license to an existing client'
    )

    # Customer Information
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_company = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # License Details
    license_type = models.CharField(max_length=20, choices=LICENSE_TYPE_CHOICES, default='basic')
    machine_id = models.CharField(max_length=64, blank=True, help_text="Hardware fingerprint (filled on activation)")
    max_activations = models.PositiveIntegerField(default=1)
    current_activations = models.PositiveIntegerField(default=0)
    
    # Validity
    issued_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # The actual license key (signed data)
    license_code = models.TextField(blank=True, help_text="The signed license code to give to customer")
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "License"
        verbose_name_plural = "Licenses"
    
    def __str__(self):
        return f"{self.customer_name} - {self.license_type} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Auto-set valid_until based on license type if not set
        if not self.valid_until:
            if self.license_type == 'trial':
                self.valid_until = timezone.now() + timedelta(days=30)
            elif self.license_type == 'lifetime':
                self.valid_until = timezone.now() + timedelta(days=36500)  # 100 years
            else:
                self.valid_until = timezone.now() + timedelta(days=365)  # 1 year
        
        # Generate license code if not present
        if not self.license_code:
            self.license_code = self.generate_license_code()
        
        super().save(*args, **kwargs)
    
    def generate_license_code(self):
        """Generate a cryptographically signed license code"""
        # Create license payload
        payload = {
            'lid': str(self.id),  # License ID
            'cname': self.customer_name,
            'cemail': self.customer_email,
            'ltype': self.license_type,
            'vfrom': self.valid_from.isoformat(),
            'vuntil': self.valid_until.isoformat(),
            'maxact': self.max_activations,
            'iat': timezone.now().isoformat(),  # Issued at
        }
        
        # Convert payload to JSON and encode
        payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        payload_bytes = payload_json.encode('utf-8')
        
        # Sign the payload with RSA private key
        private_key = self.key_pair.get_private_key()
        signature = private_key.sign(
            payload_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Combine payload and signature
        license_data = {
            'p': base64.b64encode(payload_bytes).decode('utf-8'),  # payload
            's': base64.b64encode(signature).decode('utf-8'),      # signature
            'v': 1  # version
        }
        
        # Encode to base64 for easy transport
        license_json = json.dumps(license_data, separators=(',', ':'))
        license_code = base64.b64encode(license_json.encode('utf-8')).decode('utf-8')
        
        # Format as readable chunks (5 chars separated by dash)
        # First add a checksum prefix
        checksum = hashlib.sha256(license_code.encode()).hexdigest()[:8].upper()
        
        return f"REP-{checksum}-{license_code}"
    
    def is_valid(self):
        """Check if license is currently valid"""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.valid_from <= now <= self.valid_until
        )
    
    def days_remaining(self):
        """Get days remaining on license"""
        if not self.is_valid():
            return 0
        remaining = self.valid_until - timezone.now()
        return max(0, remaining.days)
    
    @classmethod
    def validate_license_code(cls, license_code, public_key_pem, machine_id=None):
        """
        Validate a license code using the public key.
        Returns (is_valid, payload_or_error)
        """
        try:
            # Remove prefix if present
            if license_code.startswith('REP-'):
                parts = license_code.split('-', 2)
                if len(parts) >= 3:
                    license_code = parts[2]
            
            # Decode base64
            license_json = base64.b64decode(license_code.encode('utf-8')).decode('utf-8')
            license_data = json.loads(license_json)
            
            # Extract payload and signature
            payload_bytes = base64.b64decode(license_data['p'])
            signature = base64.b64decode(license_data['s'])
            
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            # Verify signature
            public_key.verify(
                signature,
                payload_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Signature valid, parse payload
            payload = json.loads(payload_bytes.decode('utf-8'))
            
            # Check expiry
            valid_until = datetime.fromisoformat(payload['vuntil'])
            if timezone.is_naive(valid_until):
                valid_until = timezone.make_aware(valid_until)
            
            if timezone.now() > valid_until:
                return False, "License has expired"
            
            # Check valid_from
            valid_from = datetime.fromisoformat(payload['vfrom'])
            if timezone.is_naive(valid_from):
                valid_from = timezone.make_aware(valid_from)
            
            if timezone.now() < valid_from:
                return False, "License is not yet valid"
            
            return True, payload
            
        except Exception as e:
            return False, f"Invalid license: {str(e)}"


class LicenseActivation(models.Model):
    """Track license activations on different machines"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name='activations')
    machine_id = models.CharField(max_length=64)
    machine_name = models.CharField(max_length=200, blank=True)
    activated_at = models.DateTimeField(auto_now_add=True)
    last_check = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = ['license', 'machine_id']
        ordering = ['-activated_at']
    
    def __str__(self):
        return f"{self.license.customer_name} - {self.machine_id[:16]}..."
