"""
Views for the messages app.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch

from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    MessageCreateSerializer
)


class ConversationListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for conversations.
    GET: List user's conversations.
    POST: Create new conversation.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.request.method == 'POST':
            return ConversationCreateSerializer
        return ConversationListSerializer
    
    def get_queryset(self):
        """Return user's conversations."""
        return Conversation.objects.filter(
            participants=self.request.user
        ).select_related('ad').prefetch_related(
            'participants',
            Prefetch(
                'messages',
                queryset=Message.objects.order_by('-timestamp')[:1]
            )
        ).distinct()


class ConversationDetailView(generics.RetrieveAPIView):
    """
    API endpoint for conversation details.
    GET: Retrieve conversation with messages.
    """
    
    serializer_class = ConversationDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's conversations."""
        return Conversation.objects.filter(
            participants=self.request.user
        ).select_related('ad').prefetch_related(
            'participants',
            'messages',
            'messages__sender'
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve conversation and mark messages as read."""
        instance = self.get_object()
        
        # Mark all messages in this conversation as read for current user
        Message.objects.filter(
            conversation=instance,
            is_read=False
        ).exclude(
            sender=request.user
        ).update(is_read=True)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MessageListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for messages in a conversation.
    GET: List messages in a conversation.
    POST: Send a new message.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer
    
    def get_queryset(self):
        """Return messages for the specified conversation."""
        conversation_id = self.kwargs.get('conversation_id')
        
        # Verify user is participant
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=self.request.user
        )
        
        return Message.objects.filter(
            conversation=conversation
        ).select_related('sender').order_by('-timestamp')
    
    def list(self, request, *args, **kwargs):
        """List messages and mark as read."""
        queryset = self.get_queryset()
        
        # Mark messages as read
        conversation_id = self.kwargs.get('conversation_id')
        Message.objects.filter(
            conversation_id=conversation_id,
            is_read=False
        ).exclude(
            sender=request.user
        ).update(is_read=True)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MarkAsReadView(APIView):
    """
    API endpoint to mark messages as read.
    POST: Mark all messages in a conversation as read.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, conversation_id):
        """Mark all messages in conversation as read."""
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )
        
        updated_count = Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(
            sender=request.user
        ).update(is_read=True)
        
        return Response({
            'message': f'{updated_count} messages marked as read.'
        }, status=status.HTTP_200_OK)


class UnreadCountView(APIView):
    """
    API endpoint to get unread message count.
    GET: Get total unread message count for user.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get total unread count."""
        unread_count = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False
        ).exclude(
            sender=request.user
        ).count()
        
        return Response({
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)


class DeleteConversationView(generics.DestroyAPIView):
    """
    API endpoint to delete a conversation.
    DELETE: Remove user from conversation.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return user's conversations."""
        return Conversation.objects.filter(participants=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Remove user from conversation participants."""
        instance = self.get_object()
        
        # Remove user from participants
        instance.participants.remove(request.user)
        
        # If no participants left, delete conversation
        if instance.participants.count() == 0:
            instance.delete()
        
        return Response(
            {'message': 'Conversation deleted.'},
            status=status.HTTP_204_NO_CONTENT
        )