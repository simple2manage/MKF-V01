# masterdata/models.py
from django.db import models
from accounts.models import CustomUser


# ------------------ Machine Master ------------------
class MachineType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class MachineRegistration(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='machines')
    name = models.ForeignKey(MachineType, on_delete=models.CASCADE, related_name='registrations')

    registration_number = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='machine_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.registration_number or 'No Reg No'}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['registration_number'],
                name='unique_registration_number_not_null',
                condition=~models.Q(registration_number=None)
            )
        ]


# ------------------ Input Master ------------------

class InputCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Input Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    
class InputSubCategory(models.Model):
    category = models.ForeignKey(InputCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Input Sub Categories"
        unique_together = ('category', 'name')  # Prevent duplicate subcategory names within same category
        ordering = ['category__name', 'name']
    
    def __str__(self):
        category_name = self.category.name if self.category else "No Category"
        return f"{category_name} - {self.name}"


class Input(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('litre', 'Litre'),
        # ('gram', 'Gram'),
        # ('ml', 'Millilitre'),
        ('piece', 'Piece'),
        ('packet', 'Packet'),
        ('bottle', 'Bottle'),
        ('bag', 'Bag'),
    ]
    
    FORM_TYPE_CHOICES = [
        ('powder', 'Powder'),
        ('liquid', 'Liquid'),
        ('granules', 'Granules'),
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('spray', 'Spray'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(InputCategory, on_delete=models.CASCADE, related_name='inputs')
    subcategory = models.ForeignKey(InputSubCategory, on_delete=models.CASCADE, related_name='inputs', blank=True, null=True)
    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES, default='powder')
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category__name', 'subcategory__name', 'name']
    
    def __str__(self):
        return self.name if self.name else "Unnamed Input"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Validate that subcategory belongs to the selected category
        if self.subcategory and self.subcategory.category != self.category:
            raise ValidationError("Subcategory must belong to the selected category.")


class InputMaster(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='inputs')  # NEW
    name = models.ForeignKey(Input, on_delete=models.CASCADE, related_name='input_masters')
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='input_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        input_name = self.name.name if self.name else "No Input"
        user_display = self.user.name if self.user and self.user.name else (
            self.user.phone_number if self.user else "No User"
        )
        return f"{input_name} - {user_display}"
    
    @property
    def unit_display(self):
        return self.name.get_unit_display()
    
    @property
    def form_type_display(self):
        return self.name.get_form_type_display()
    
    @property
    def category_name(self):
        return self.name.category.name
    
    @property
    def subcategory_name(self):
        return self.name.subcategory.name if self.name.subcategory else None
    
    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock
   