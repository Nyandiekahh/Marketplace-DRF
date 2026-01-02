"""
Serializers for the messages app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Conversation, Message, MessageAttachment
from ads.serializers import AdListSerializer

User = get_user_model()


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for message attachments."""
    
    class Meta:
        model = MessageAttachment
        fields = ['id', 'file', 'file_type', 'file_size', 'uploaded_at']
        read_only_fields = ['id', 'file_type', 'file_size', 'uploaded_at']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for messages."""
    
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    is_own_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'sender_name',
            'sender_email', 'text', 'is_read', 'read_at',
            'timestamp', 'attachments', 'is_own_message'
        ]
        read_only_fields = [
            'id', 'sender', 'is_read', 'read_at', 'timestamp'
        ]
    
    def get_is_own_message(self, obj):
        """Check if message is from current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.sender == request.user
        return False


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages."""
    
    class Meta:
        model = Message
        fields = ['conversation', 'text']
    
    def validate_conversation(self, value):
        """Validate that user is a participant in the conversation."""
        request = self.context['request']
        if not value.participants.filter(id=request.user.id).exists():
            raise serializers.ValidationError(
                "You are not a participant in this conversation."
            )
        return value
    
    def create(self, validated_data):
        """Create message and update conversation timestamp."""
        message = Message.objects.create(
            sender=self.context['request'].user,
            **validated_data
        )
        
        # Update conversation timestamp
        conversation = validated_data['conversation']
        conversation.save()  # This updates the updated_at field
        
        return message


class ParticipantSerializer(serializers.ModelSerializer):
    """Serializer for conversation participants."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email',
            'profile_picture', 'is_verified'
        ]
        read_only_fields = fields


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer for listing conversations."""
    
    last_message = MessageSerializer(read_only=True)
    other_participant = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    ad = AdListSerializer(read_only=True)
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'other_participant', 'ad', 'last_message',
            'unread_count', 'created_at', 'updated_at'
        ]
    
    def get_other_participant(self, obj):
        """Get the other participant in the conversation."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            other = obj.get_other_participant(request.user)
            if other:
                return ParticipantSerializer(other).data
        return None
    
    def get_unread_count(self, obj):
        """Get unread message count for current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.unread_count(request.user)
        return 0


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Serializer for conversation details."""
    
    messages = MessageSerializer(many=True, read_only=True)
    participants = ParticipantSerializer(many=True, read_only=True)
    ad = AdListSerializer(read_only=True)
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'participants', 'ad', 'messages',
            'created_at', 'updated_at'
        ]


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating conversations."""
    
    recipient_id = serializers.IntegerField(write_only=True)
    ad_id = serializers.IntegerField(write_only=True, required=False)
    initial_message = serializers.CharField(write_only=True)
    
    class Meta:
        model = Conversation
        fields = ['recipient_id', 'ad_id', 'initial_message']
    
    def validate_recipient_id(self, value):
        """Validate that recipient exists and is not the current user."""
        request = self.context['request']
        
        if value == request.user.id:
            raise serializers.ValidationError(
                "You cannot start a conversation with yourself."
            )
        
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Recipient not found.")
        
        return value
    
    def validate_ad_id(self, value):
        """Validate that ad exists if provided."""
        if value:
            from ads.models import Ad
            try:
                Ad.objects.get(id=value, status='active')
            except Ad.DoesNotExist:
                raise serializers.ValidationError("Ad not found or not active.")
        return value
    
    def create(self, validated_data):
        """Create conversation with participants and initial message."""
        from ads.models import Ad
        
        recipient_id = validated_data.pop('recipient_id')
        ad_id = validated_data.pop('ad_id', None)
        initial_message_text = validated_data.pop('initial_message')
        
        current_user = self.context['request'].user
        recipient = User.objects.get(id=recipient_id)
        
        # Check if conversation already exists
        if ad_id:
            ad = Ad.objects.get(id=ad_id)
            existing = Conversation.objects.filter(
                ad=ad,
                participants=current_user
            ).filter(
                participants=recipient
            ).first()
            
            if existing:
                # Add initial message to existing conversation
                Message.objects.create(
                    conversation=existing,
                    sender=current_user,
                    text=initial_message_text
                )
                return existing
        else:
            # Check for existing conversation without ad
            existing = Conversation.objects.filter(
                ad__isnull=True,
                participants=current_user
            ).filter(
                participants=recipient
            ).first()
            
            if existing:
                Message.objects.create(
                    conversation=existing,
                    sender=current_user,
                    text=initial_message_text
                )
                return existing
        
        # Create new conversation
        conversation = Conversation.objects.create(
            ad_id=ad_id if ad_id else None
        )
        conversation.participants.add(current_user, recipient)
        
        # Create initial message
        Message.objects.create(
            conversation=conversation,
            sender=current_user,
            text=initial_message_text
        )
        
        return conversation