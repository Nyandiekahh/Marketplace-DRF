from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Conversation, Message

class ConversationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        return Response({'results': []})

class ConversationDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request, pk):
        return Response({'messages': []})

class CreateConversationView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        return Response({'id': 1, 'message': 'Conversation created'})

class SendMessageView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def create(self, request, pk):
        return Response({'message': 'Message sent'})
