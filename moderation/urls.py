"""
URL configuration for moderation app.
"""

from django.urls import path
from .views import (
    ReportCreateView,
    ReportListView,
    ReportDetailView,
    ResolveReportView,
    ReviewCreateView,
    UserReviewsListView,
    UserReviewsSummaryView,
    MyReviewsView,
    VerificationBadgeListView,
    GrantBadgeView,
    RevokeBadgeView,
    ContentFlagListView,
    ReviewContentFlagView,
    UserStatisticsView,
)

app_name = 'moderation'

urlpatterns = [
    # Reports
    path('reports/', ReportCreateView.as_view(), name='report_create'),
    path('reports/list/', ReportListView.as_view(), name='report_list'),
    path('reports/<int:pk>/', ReportDetailView.as_view(), name='report_detail'),
    path('reports/<int:pk>/resolve/', ResolveReportView.as_view(), name='resolve_report'),
    
    # Reviews
    path('reviews/', ReviewCreateView.as_view(), name='review_create'),
    path('reviews/my/', MyReviewsView.as_view(), name='my_reviews'),
    path('reviews/user/<int:user_id>/', UserReviewsListView.as_view(), name='user_reviews'),
    path('reviews/user/<int:user_id>/summary/', UserReviewsSummaryView.as_view(), name='user_reviews_summary'),
    
    # Verification Badges
    path('badges/user/<int:user_id>/', VerificationBadgeListView.as_view(), name='user_badges'),
    path('badges/grant/', GrantBadgeView.as_view(), name='grant_badge'),
    path('badges/<int:pk>/revoke/', RevokeBadgeView.as_view(), name='revoke_badge'),
    
    # Content Flags
    path('flags/', ContentFlagListView.as_view(), name='content_flags'),
    path('flags/<int:pk>/review/', ReviewContentFlagView.as_view(), name='review_flag'),
    
    # User Statistics
    path('stats/user/<int:user_id>/', UserStatisticsView.as_view(), name='user_statistics'),
]