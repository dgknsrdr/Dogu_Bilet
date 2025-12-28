Doğu Bilet – Bus Ticket Reservation System with AI Chatbot

Doğu Bilet is a web-based bus ticket reservation system developed using Flask and SQLite.
The project allows users to search for bus trips, purchase tickets, select seats, manage their profile,
and request ticket refunds through a user-friendly interface.

In addition to standard ticketing features, the system includes an AI-powered chatbot
that helps users with ticket-related questions and trip searches.

--------------------------------------------------
Features
--------------------------------------------------

User Features:
- User registration and login system
- Session and cookie-based authentication
- Search bus trips by departure city, destination city, and date
- View available trips with duration and price
- Seat selection with real-time seat availability
- Ticket purchase and ticket refund (before trip time)
- View active and past tickets
- Profile information update
- Password change with security rules

Admin Features:
- Admin panel with system statistics
- Total user, trip, and ticket counts
- Daily trip count
- Ticket refund statistics
- Dynamic statistical charts generated with Matplotlib
- Charts are generated server-side and displayed using Base64 encoding

AI Chatbot Features:
- Integrated AI chatbot powered by Google Gemini API
- Understands natural language Turkish queries
- Detects trip search requests (departure, destination, date)
- Queries real data from the database
- Automatically redirects users to the trip list when matching trips are found
- Provides guidance for ticket purchase, refunds, and system usage
- Restricts conversation to ticket system related topics

--------------------------------------------------
Technologies Used
--------------------------------------------------

Backend:
- Python
- Flask
- SQLite

Frontend:
- HTML
- CSS
- Jinja2 Templates

Data & Utilities:
- Pandas
- Matplotlib
- Base64 image encoding

APIs:
- OpenRouteService API (for distance, duration, and price calculation)
- Google Gemini API (AI chatbot)

--------------------------------------------------
Project Structure
--------------------------------------------------

- app.py / views.py        -> Main Flask application
- templates/              -> HTML templates
- static/                 -> CSS and static files
- dogubilet.db            -> SQLite database
- .env                    -> Environment variables (API keys, secret key)

--------------------------------------------------
Notes
--------------------------------------------------

- This project uses a development server and is not intended for production use.
- API keys are loaded securely from environment variables.
- The chatbot works only for logged-in users.
- The system automatically updates outdated trip dates to keep data relevant.

--------------------------------------------------
Author
--------------------------------------------------

Developed by: Doğukan Serdar
