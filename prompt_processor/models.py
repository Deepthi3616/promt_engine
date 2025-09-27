from django.db import models
from django.contrib.auth.models import User
import json
from django.core.exceptions import ValidationError

class PromptConversion(models.Model):
    """Main model for storing prompt conversions"""
    
    # User who created this (optional, for multi-user support)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Original prompt and conversion
    original_prompt = models.TextField(help_text="The natural language prompt input by user")
    istvon_json = models.JSONField(help_text="The generated ISTVON JSON structure")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Status and quality tracking
    success_flag = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    validation_passed = models.BooleanField(default=False)
    
    # User feedback
    user_rating = models.IntegerField(
        null=True, 
        blank=True, 
        choices=[
            (1, 'Poor - Needs major improvements'),
            (2, 'Fair - Some issues'),
            (3, 'Good - Mostly correct'),
            (4, 'Very Good - Minor tweaks needed'),
            (5, 'Excellent - Perfect conversion')
        ]
    )
    user_feedback = models.TextField(blank=True, null=True)
    
    # Usage tracking
    times_used = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['success_flag']),
        ]
    
    def __str__(self):
        return f"Conversion {self.id}: {self.original_prompt[:50]}..."
    
    def clean(self):
        """Validate the ISTVON JSON structure"""
        if self.istvon_json:
            required_keys = ['instructions', 'source_data', 'tools', 'variables', 'outcome', 'notification']
            for key in required_keys:
                if key not in self.istvon_json:
                    raise ValidationError(f'ISTVON JSON missing required key: {key}')
    
    def get_instructions(self):
        """Helper method to get instructions from JSON"""
        return self.istvon_json.get('instructions', '') if self.istvon_json else ''
    
    def get_topic(self):
        """Helper method to get topic from variables"""
        if self.istvon_json and 'variables' in self.istvon_json:
            return self.istvon_json['variables'].get('topic', 'Unknown')
        return 'Unknown'


class ISTVONTemplate(models.Model):
    """Reusable ISTVON templates for common patterns"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    template_json = models.JSONField(
        help_text="ISTVON structure with placeholder values"
    )
    
    # Categorization
    category = models.CharField(
        max_length=50,
        choices=[
            ('content', 'Content Creation'),
            ('analysis', 'Data Analysis'),
            ('coding', 'Code Generation'),
            ('communication', 'Communication'),
            ('research', 'Research'),
            ('other', 'Other')
        ],
        default='other'
    )
    
    # Usage tracking
    use_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Visibility
    is_public = models.BooleanField(default=True, help_text="Available to all users")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-use_count', 'name']
    
    def __str__(self):
        return self.name
    
    def increment_usage(self):
        """Increment the usage counter"""
        self.use_count += 1
        self.save(update_fields=['use_count'])


class ConversionFeedback(models.Model):
    """Detailed feedback on conversions for improvement"""
    
    conversion = models.OneToOneField(PromptConversion, on_delete=models.CASCADE)
    
    # Specific component ratings
    instructions_quality = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    source_data_accuracy = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    tools_appropriateness = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    variables_completeness = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    outcome_specification = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    notification_relevance = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    
    # Improvement suggestions
    suggested_improvements = models.JSONField(
        default=dict,
        help_text="Specific improvements for each component"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback for {self.conversion.id}"


class ConversionAnalytics(models.Model):
    """Analytics data for conversion patterns"""
    
    date = models.DateField()
    
    # Daily statistics
    total_conversions = models.IntegerField(default=0)
    successful_conversions = models.IntegerField(default=0)
    failed_conversions = models.IntegerField(default=0)
    average_rating = models.FloatField(null=True, blank=True)
    
    # Popular patterns
    most_common_tools = models.JSONField(default=list)
    most_common_formats = models.JSONField(default=list)
    most_common_topics = models.JSONField(default=list)
    
    # Performance metrics
    average_processing_time = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics for {self.date}"


# Custom managers for common queries
class SuccessfulConversionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(success_flag=True, validation_passed=True)

class RecentConversionManager(models.Manager):
    def get_queryset(self):
        from django.utils import timezone
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        return super().get_queryset().filter(created_at__gte=thirty_days_ago)

# Add managers to the PromptConversion model
PromptConversion.add_to_class('successful', SuccessfulConversionManager())
PromptConversion.add_to_class('recent', RecentConversionManager())
