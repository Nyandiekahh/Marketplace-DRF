# Marketplace Backend - Django Classifieds Platform

A comprehensive Django REST API backend for a classifieds marketplace platform similar to Jiji.co.ke.

## Features

- **User Management**: Registration, authentication (JWT), email/phone verification, profile management
- **Categories**: Hierarchical category system with unlimited nesting
- **Advertisements**: Full CRUD operations, image uploads, search, filtering
- **Messaging**: Real-time chat between buyers and sellers (WebSockets)
- **Moderation**: User reviews, reporting system, content moderation
- **Premium Features**: Ad boosting, VIP listings, featured ads
- **Search**: Full-text search with Elasticsearch
- **Caching**: Redis-based caching for performance
- **Background Tasks**: Celery for async email/SMS notifications
- **API Documentation**: Auto-generated Swagger/ReDoc documentation

## Tech Stack

- **Framework**: Django 5.0, Django REST Framework 3.14
- **Database**: PostgreSQL
- **Cache**: Redis
- **Search**: Elasticsearch
- **Task Queue**: Celery with Redis broker
- **Storage**: AWS S3 (production) / Local (development)
- **Real-time**: Django Channels (WebSockets)
- **Authentication**: JWT (SimpleJWT)
- **Documentation**: drf-spectacular (OpenAPI 3.0)

## Project Structure

```
marketplace/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
├── marketplace/
│   ├── settings/
│   │   ├── base.py          # Base settings
│   │   ├── dev.py           # Development settings
│   │   └── prod.py          # Production settings
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── users/                    # User management app
│   ├── models.py            # CustomUser, Location, UserVerification
│   ├── serializers.py       # User serializers
│   ├── views.py             # Auth & profile views
│   ├── tasks.py             # Celery tasks for emails/SMS
│   └── urls.py
├── categories/               # Category management app
│   ├── models.py            # Category model
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── ads/                      # Advertisement app
│   ├── models.py            # Ad, Image, Favorite models
│   ├── serializers.py
│   ├── views.py
│   ├── filters.py
│   ├── search_indexes.py    # Elasticsearch indexes
│   └── urls.py
├── messages/                 # Messaging app
│   ├── models.py            # Conversation, Message
│   ├── serializers.py
│   ├── views.py
│   ├── consumers.py         # WebSocket consumers
│   └── urls.py
├── moderation/              # Moderation app
│   ├── models.py            # Review, Report
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
└── payments/                # Premium features app
    ├── models.py            # PremiumSubscription
    ├── serializers.py
    ├── views.py
    └── urls.py
```

## Installation & Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Elasticsearch 8+ (optional for search)
- Node.js (for frontend, optional)

### Step 1: Clone & Setup Virtual Environment

```bash
# Create project directory
mkdir marketplace && cd marketplace

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Database Setup

```bash
# Create PostgreSQL database
createdb marketplace_db

# Or using psql:
psql -U postgres
CREATE DATABASE marketplace_db;
CREATE USER marketplace_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE marketplace_db TO marketplace_user;
\q
```

### Step 3: Environment Variables

Copy `.env.example` to `.env` and update with your values:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- Database credentials
- AWS S3 credentials (for production)
- Email settings (SMTP)
- Twilio credentials (for SMS)
- Redis URL
- Elasticsearch host

### Step 4: Run Migrations

```bash
# Apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Step 5: Load Initial Data (Optional)

Create initial categories:

```bash
python manage.py shell
```

```python
from categories.models import Category

# Main categories
vehicles = Category.objects.create(name='Vehicles', order=1)
mobiles = Category.objects.create(name='Mobile Phones & Tablets', order=2)
electronics = Category.objects.create(name='Electronics', order=3)
property = Category.objects.create(name='Property', order=4)
home = Category.objects.create(name='Home, Furniture & Garden', order=5)
fashion = Category.objects.create(name='Fashion', order=6)
jobs = Category.objects.create(name='Jobs', order=7)
services = Category.objects.create(name='Services', order=8)

# Subcategories for Vehicles
Category.objects.create(name='Cars', parent=vehicles, order=1)
Category.objects.create(name='Motorcycles & Scooters', parent=vehicles, order=2)
Category.objects.create(name='Vehicle Parts & Accessories', parent=vehicles, order=3)

# Subcategories for Mobile Phones
Category.objects.create(name='Mobile Phones', parent=mobiles, order=1)
Category.objects.create(name='Tablets', parent=mobiles, order=2)
Category.objects.create(name='Accessories', parent=mobiles, order=3)
```

### Step 6: Start Development Server

```bash
# Run Django development server
python manage.py runserver

# In separate terminals:

# Start Celery worker
celery -A marketplace worker -l info

# Start Celery beat (for scheduled tasks)
celery -A marketplace beat -l info

# Start Redis (if not running)
redis-server
```

## API Endpoints

### Authentication & Users

```
POST   /api/users/register/              - Register new user
POST   /api/users/login/                 - Login user
POST   /api/users/token/refresh/         - Refresh JWT token
POST   /api/users/verify/email/          - Verify email with code
POST   /api/users/verify/phone/          - Verify phone with code
POST   /api/users/verify/resend/         - Resend verification code
GET    /api/users/profile/               - Get user profile
PUT    /api/users/profile/               - Update user profile
POST   /api/users/password/reset/        - Request password reset
POST   /api/users/password/reset/confirm/ - Confirm password reset
POST   /api/users/block/                 - Block a user
GET    /api/users/blocked/               - List blocked users
DELETE /api/users/unblock/<id>/          - Unblock a user
```

### Categories

```
GET    /api/categories/                  - List all root categories
GET    /api/categories/all/              - List all categories (flat)
GET    /api/categories/<slug>/           - Get category details
POST   /api/categories/admin/create/     - Create category (admin)
PUT    /api/categories/admin/<slug>/update/ - Update category (admin)
DELETE /api/categories/admin/<slug>/delete/ - Delete category (admin)
```

### Advertisements

```
GET    /api/ads/                         - List ads (with filters)
POST   /api/ads/                         - Create new ad
GET    /api/ads/<slug>/                  - Get ad details
PUT    /api/ads/<slug>/                  - Update ad (owner only)
DELETE /api/ads/<slug>/                  - Delete ad (owner only)
GET    /api/ads/search/                  - Search ads
POST   /api/ads/favorites/               - Add to favorites
DELETE /api/ads/favorites/<id>/          - Remove from favorites
GET    /api/ads/my-ads/                  - Get user's ads
POST   /api/ads/<slug>/boost/            - Boost ad to premium
```

### Messages

```
GET    /api/messages/conversations/      - List user's conversations
POST   /api/messages/conversations/      - Start new conversation
GET    /api/messages/<conversation_id>/  - Get conversation messages
POST   /api/messages/<conversation_id>/  - Send message
```

### Moderation

```
POST   /api/moderation/reports/          - Report ad/user
GET    /api/moderation/reports/          - List reports (admin)
POST   /api/moderation/reviews/          - Create review
GET    /api/moderation/reviews/<user_id>/ - Get user reviews
```

### API Documentation

```
GET    /api/docs/                        - Swagger UI
GET    /api/redoc/                       - ReDoc documentation
GET    /api/schema/                      - OpenAPI schema (JSON)
```

## Testing

```bash
# Run all tests
pytest

# Run specific app tests
pytest users/tests.py

# Run with coverage
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Deployment

### Using Docker (Recommended)

```dockerfile
# Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y postgresql-client

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "marketplace.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: marketplace_db
      POSTGRES_USER: marketplace
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  web:
    build: .
    command: gunicorn marketplace.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis

  celery:
    build: .
    command: celery -A marketplace worker -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### Deploy to Production

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or deploy to platforms:
# - Heroku: See docs/heroku-deployment.md
# - AWS: See docs/aws-deployment.md
# - DigitalOcean: See docs/digitalocean-deployment.md
```

## Environment-Specific Settings

```bash
# Development
export DJANGO_SETTINGS_MODULE=marketplace.settings.dev
python manage.py runserver

# Production
export DJANGO_SETTINGS_MODULE=marketplace.settings.prod
gunicorn marketplace.wsgi:application
```

## Security Checklist

- [ ] Change SECRET_KEY in production
- [ ] Set DEBUG=False in production
- [ ] Configure ALLOWED_HOSTS
- [ ] Use HTTPS (SSL certificates)
- [ ] Enable CSRF protection
- [ ] Set secure cookie flags
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up Sentry for error tracking
- [ ] Regular security updates

## Performance Optimization

1. **Database**:
   - Add indexes on frequently queried fields
   - Use select_related() and prefetch_related()
   - Implement database query caching

2. **Caching**:
   - Cache expensive queries with Redis
   - Use template fragment caching
   - Implement API response caching

3. **Static Files**:
   - Use CDN for static assets
   - Enable compression (gzip)
   - Optimize images before upload

4. **Search**:
   - Use Elasticsearch for full-text search
   - Implement search result caching
   - Add search filters and facets

## Monitoring

- **Application Monitoring**: Sentry
- **Performance**: New Relic / DataDog
- **Logs**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Uptime**: UptimeRobot / Pingdom

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

This project is licensed under the MIT License.

## Support

For support, email support@marketplace.com or join our Slack channel.

## Acknowledgments

- Inspired by Jiji.co.ke
- Built with Django and Django REST Framework
- Community contributors