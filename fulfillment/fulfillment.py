import os
import requests
from flask import Flask, request, jsonify

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

app = Flask(__name__)

BACKEND_URL = 'http://localhost:6000'

# Load Google calendar credentials JSON path from environment variable
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')
GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 'primary')

# Initialize Google Calendar API service
SCOPES = ['https://www.googleapis.com/auth/calendar']

credentials = None
calendar_service = None

def init_calendar_service():
    global credentials, calendar_service
    if not GOOGLE_CREDENTIALS_JSON:
        print("Google credentials JSON environment variable not set.")
        return None

    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_JSON, scopes=SCOPES)
    calendar_service = build('calendar', 'v3', credentials=credentials)
    return calendar_service

init_calendar_service()


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(force=True)
    intent = req['queryResult']['intent']['displayName']
    params = req['queryResult'].get('parameters', {})

    if intent == 'BookRoom':
        return handle_book_room(params)
    elif intent == 'CheckAvailability':
        return handle_check_availability(params)
    elif intent == 'ExplainServices':
        return handle_explain_services()
    elif intent == 'CancelBooking':
        return handle_cancel_booking(params)
    else:
        return jsonify({'fulfillmentText': "Sorry, I did not understand your request."})


def handle_book_room(params):
    room_type = params.get('room-type')
    date = params.get('date')

    if not room_type or not date:
        return jsonify({'fulfillmentText': "Please provide the type of room and the booking date."})

    # Check availability from backend
    availability_resp = requests.post(f'{BACKEND_URL}/availability', json={'room_type': room_type, 'date': date})
    if availability_resp.ok and availability_resp.json().get('available'):
        # Book the room
        book_resp = requests.post(f'{BACKEND_URL}/book', json={'room_type': room_type, 'date': date})
        if book_resp.ok and book_resp.json().get('success'):
            booking_id = book_resp.json().get('booking_id')
            # Add to Google Calendar
            add_event_to_calendar(room_type, date)

            # Mock payment processing
            payment_success = mock_payment_processing()

            if payment_success:
                response_text = f"Your {room_type} room is booked for {date} successfully. Payment processed and confirmation sent."
            else:
                response_text = f"Your {room_type} room is booked for {date}, but payment failed. Please complete payment promptly."

            return jsonify({'fulfillmentText': response_text})
        else:
            return jsonify({'fulfillmentText': "Sorry, booking failed on backend."})
    else:
        return jsonify({'fulfillmentText': f"Sorry, no {room_type} rooms are available on {date}."})


def handle_check_availability(params):
    room_type = params.get('room-type')
    date = params.get('date')

    if not room_type or not date:
        return jsonify({'fulfillmentText': "Please provide the room type and date to check availability."})

    availability_resp = requests.post(f'{BACKEND_URL}/availability', json={'room_type': room_type, 'date': date})
    if availability_resp.ok:
        available = availability_resp.json().get('available', False)
        if available:
            response_text = f"The {room_type} room is available on {date}."
        else:
            response_text = f"Sorry, the {room_type} room is not available on {date}."
        return jsonify({'fulfillmentText': response_text})
    else:
        return jsonify({'fulfillmentText': "Backend service is unavailable, please try again later."})


def handle_explain_services():
    services_text = (
        "Our hotel offers the following services:\n"
        "- Room bookings: single, double, and suites\n"
        "- Spa and wellness facilities\n"
        "- Gym access\n"
        "- Fine dining and room service\n"
        "- Event and conference facilities"
    )
    return jsonify({'fulfillmentText': services_text})

def handle_cancel_booking(params):
    # For simplicity, we won't implement full cancellation, just confirm understanding
    return jsonify({'fulfillmentText': "Booking cancellation service will be available soon."})

def add_event_to_calendar(room_type, date_str):
    if calendar_service is None:
        print("Google Calendar service is not initialized.")
        return False

    event = {
        'summary': f'Hotel Room Booking: {room_type}',
        'start': {'date': date_str},
        'end': {'date': date_str},
        'description': 'Reservation confirmed via Concierge Agent.',
    }

    try:
        event_result = calendar_service.events().insert(
            calendarId=GOOGLE_CALENDAR_ID, body=event).execute()
        print(f'Event created: {event_result.get("htmlLink")}')
        return True
    except Exception as e:
        print(f'Failed to create calendar event: {e}')
        return False

def mock_payment_processing():
    # Simulate payment success
    print("Processing payment (mock)...")
    return True


if __name__ == '__main__':
    app.run(port=5000, debug=True)
