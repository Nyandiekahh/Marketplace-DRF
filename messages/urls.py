"""
URL configuration for messages app.
"""

from django.urls import path
from .views import (
    ConversationListCreateView,
    ConversationDetailView,
    MessageListCreateView,
    MarkAsReadView,
    UnreadCountView,
    DeleteConversationView,
)

app_name = 'messages'

urlpatterns = [
    # Conversations
    path('conversations/', ConversationListCreateView.as_view(), name='conversation_list_create'),
    path('conversations/<int:pk>/', ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversations/<int:pk>/delete/', DeleteConversationView.as_view(), name='conversation_delete'),
    
    # Messages
    path('conversations/<int:conversation_id>/messages/', MessageListCreateView.as_view(), name='message_list_create'),
    path('conversations/<int:conversation_id>/mark-read/', MarkAsReadView.as_view(), name='mark_as_read'),
    
    # Unread count
    path('unread-count/', UnreadCountView.as_view(), name='unread_count'),
]