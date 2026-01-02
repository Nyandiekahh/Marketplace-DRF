"""
Views for the moderation app.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q
from django.contrib.auth import get_user_model

from .models import Report, Review, VerificationBadge, ContentFlag
from .serializers import (
    ReportSerializer,
    ReportDetailSerializer,
    ReviewSerializer,
    UserReviewsSummarySerializer,
    VerificationBadgeSerializer,
    ContentFlagSerializer
)

User = get_user_model()


class ReportCreateView(generics.CreateAPIView):
    """
    API endpoint to create a report.
    POST: Create a new report for ad/user/message.
    """
    
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]


class ReportListView(generics.ListAPIView):
    """
    API endpoint to list reports.
    GET: List all reports (admin only).
    """
    
    serializer_class = ReportDetailSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """Return reports with optional filtering."""
        queryset = Report.objects.select_related(
            'reporter', 'reported_ad', 'reported_user',
            'reported_message', 'resolved_by'
        )
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by type
        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(report_type=type_filter)
        
        return queryset.order_by('-created_at')


class ReportDetailView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for report details.
    GET: Retrieve report details (admin only).
    PUT/PATCH: Update report status (admin only).
    """
    
    serializer_class = ReportDetailSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Report.objects.all()


class ResolveReportView(APIView):
    """
    API endpoint to resolve a report.
    POST: Mark report as resolved (admin only).
    """
    
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk):
        """Resolve report."""
        report = get_object_or_404(Report, pk=pk)
        notes = request.data.get('notes', '')
        
        report.resolve(admin_user=request.user, notes=notes)
        
        return Response({
            'message': 'Report resolved successfully.',
            'report': ReportDetailSerializer(report).data
        }, status=status.HTTP_200_OK)


class ReviewCreateView(generics.CreateAPIView):
    """
    API endpoint to create a review.
    POST: Create a review for a user.
    """
    
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserReviewsListView(generics.ListAPIView):
    """
    API endpoint to list reviews for a user.
    GET: List all reviews received by a user.
    """
    
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Return reviews for specified user."""
        user_id = self.kwargs.get('user_id')
        return Review.objects.filter(
            reviewed_user_id=user_id
        ).select_related('reviewer', 'ad').order_by('-created_at')


class UserReviewsSummaryView(APIView):
    """
    API endpoint to get user reviews summary.
    GET: Get summary of user's reviews (average rating, distribution, etc.).
    """
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, user_id):
        """Get reviews summary for user."""
        user = get_object_or_404(User, pk=user_id)
        
        reviews = Review.objects.filter(reviewed_user=user)
        
        # Calculate average rating
        avg_rating = reviews.aggregate(
            average=Avg('rating')
        )['average'] or 0
        
        # Count total reviews
        total_reviews = reviews.count()
        
        # Rating distribution
        rating_distribution = {
            '5': reviews.filter(rating=5).count(),
            '4': reviews.filter(rating=4).count(),
            '3': reviews.filter(rating=3).count(),
            '2': reviews.filter(rating=2).count(),
            '1': reviews.filter(rating=1).count(),
        }
        
        # Recent reviews
        recent_reviews = reviews.select_related('reviewer', 'ad')[:5]
        
        data = {
            'average_rating': round(avg_rating, 2),
            'total_reviews': total_reviews,
            'rating_distribution': rating_distribution,
            'recent_reviews': ReviewSerializer(recent_reviews, many=True).data
        }
        
        return Response(data, status=status.HTTP_200_OK)


class MyReviewsView(generics.ListAPIView):
    """
    API endpoint to list user's given reviews.
    GET: List reviews given by authenticated user.
    """
    
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return reviews given by user."""
        return Review.objects.filter(
            reviewer=self.request.user
        ).select_related('reviewed_user', 'ad').order_by('-created_at')


class VerificationBadgeListView(generics.ListAPIView):
    """
    API endpoint to list verification badges.
    GET: List badges for a user.
    """
    
    serializer_class = VerificationBadgeSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Return badges for specified user."""
        user_id = self.kwargs.get('user_id')
        return VerificationBadge.objects.filter(
            user_id=user_id
        ).select_related('verified_by')


class GrantBadgeView(generics.CreateAPIView):
    """
    API endpoint to grant a verification badge.
    POST: Grant badge to a user (admin only).
    """
    
    serializer_class = VerificationBadgeSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_create(self, serializer):
        """Save badge with verifier."""
        serializer.save(verified_by=self.request.user)


class RevokeBadgeView(generics.DestroyAPIView):
    """
    API endpoint to revoke a verification badge.
    DELETE: Revoke badge (admin only).
    """
    
    permission_classes = [permissions.IsAdminUser]
    queryset = VerificationBadge.objects.all()


class ContentFlagListView(generics.ListAPIView):
    """
    API endpoint to list content flags.
    GET: List flagged content (admin only).
    """
    
    serializer_class = ContentFlagSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """Return content flags with optional filtering."""
        queryset = ContentFlag.objects.select_related('ad', 'reviewed_by')
        
        # Filter by reviewed status
        is_reviewed = self.request.query_params.get('is_reviewed')
        if is_reviewed is not None:
            queryset = queryset.filter(
                is_reviewed=is_reviewed.lower() == 'true'
            )
        
        # Filter by flag type
        flag_type = self.request.query_params.get('flag_type')
        if flag_type:
            queryset = queryset.filter(flag_type=flag_type)
        
        return queryset.order_by('-created_at')


class ReviewContentFlagView(APIView):
    """
    API endpoint to review a content flag.
    POST: Mark flag as reviewed (admin only).
    """
    
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk):
        """Review content flag."""
        flag = get_object_or_404(ContentFlag, pk=pk)
        
        from django.utils import timezone
        flag.is_reviewed = True
        flag.reviewed_by = request.user
        flag.reviewed_at = timezone.now()
        flag.save()
        
        return Response({
            'message': 'Content flag reviewed.',
            'flag': ContentFlagSerializer(flag).data
        }, status=status.HTTP_200_OK)


class UserStatisticsView(APIView):
    """
    API endpoint to get user moderation statistics.
    GET: Get statistics for a user (admin only).
    """
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, user_id):
        """Get moderation statistics for user."""
        user = get_object_or_404(User, pk=user_id)
        
        # Get statistics
        stats = {
            'reports_made': Report.objects.filter(reporter=user).count(),
            'reports_received': Report.objects.filter(
                Q(reported_user=user) |
                Q(reported_ad__seller=user)
            ).count(),
            'reviews_given': Review.objects.filter(reviewer=user).count(),
            'reviews_received': Review.objects.filter(reviewed_user=user).count(),
            'average_rating': Review.objects.filter(
                reviewed_user=user
            ).aggregate(avg=Avg('rating'))['avg'] or 0,
            'badges': VerificationBadgeSerializer(
                user.badges.all(),
                many=True
            ).data,
            'flagged_ads': ContentFlag.objects.filter(
                ad__seller=user
            ).count(),
        }
        
        return Response(stats, status=status.HTTP_200_OK)