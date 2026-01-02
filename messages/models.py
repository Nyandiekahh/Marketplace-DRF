"""
Models for the messages app.
"""

from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """
    Model for conversations between users.
    Can be linked to a specific ad.
    """
    
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        verbose_name='Participants'
    )
    ad = models.ForeignKey(
        'ads.Ad',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        verbose_name='Related Ad'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
        ]
    
    def __str__(self):
        participant_emails = [p.email for p in self.participants.all()[:2]]
        if self.ad:
            return f"Conversation about {self.ad.title}: {', '.join(participant_emails)}"
        return f"Conversation: {', '.join(participant_emails)}"
    
    @property
    def last_message(self):
        """Get the last message in the conversation."""
        return self.messages.first()
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation."""
        return self.participants.exclude(id=user.id).first()
    
    def unread_count(self, user):
        """Get count of unread messages for a user."""
        return self.messages.filter(
            is_read=False
        ).exclude(sender=user).count()


class Message(models.Model):
    """
    Model for individual messages within a conversation.
    """
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Conversation'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Sender'
    )
    text = models.TextField(verbose_name='Message Text')
    is_read = models.BooleanField(
        default=False,
        verbose_name='Is Read'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Read At'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Sent At'
    )
    
    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['conversation', '-timestamp']),
            models.Index(fields=['sender', '-timestamp']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.sender.email}: {self.text[:50]}"
    
    def mark_as_read(self):
        """Mark message as read."""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class MessageAttachment(models.Model):
    """
    Model for message attachments (images, files).
    """
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Message'
    )
    file = models.FileField(
        upload_to='message_attachments/',
        verbose_name='File'
    )
    file_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='File Type'
    )
    file_size = models.IntegerField(
        default=0,
        verbose_name='File Size (bytes)'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Message Attachment'
        verbose_name_plural = 'Message Attachments'
    
    def __str__(self):
        return f"Attachment for message {self.message.id}"
    
    def save(self, *args, **kwargs):
        """Override save to set file type and size."""
        if self.file:
            self.file_size = self.file.size
            # Get file extension
            import os
            self.file_type = os.path.splitext(self.file.name)[1]
        super().save(*args, **kwargs)