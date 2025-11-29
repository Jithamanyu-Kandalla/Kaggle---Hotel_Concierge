from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Sample room inventory
room_inventory = {
    'single': 5,
    'double': 3,
    'suite': 2
}

bookings = []  # Store bookings: list of {'room_type': str, 'date': str, 'id': int}

booking_id_seq = 1

@app.route('/availability', methods=['POST'])
def check_availability():
    data = request.json
    room_type = data.get('room_type')
    date_str = data.get('date')

    if not room_type or not date_str:
        return jsonify({'error': 'Missing parameters'}), 400

    # Validate room type and date
    if room_type not in room_inventory:
        return jsonify({'available': False, 'message': 'Invalid room type'})

    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        return jsonify({'available': False, 'message': 'Invalid date format. Use YYYY-MM-DD'})

    # Count bookings on the date for room type
    booked_count = sum(1 for b in bookings if b['room_type'] == room_type and b['date'] == date_str)
    available = booked_count < room_inventory[room_type]

    return jsonify({'available': available})


@app.route('/book', methods=['POST'])
def book_room():
    global booking_id_seq
    data = request.json
    room_type = data.get('room_type')
    date_str = data.get('date')

    if not room_type or not date_str:
        return jsonify({'success': False, 'message': 'Missing parameters'}), 400

    if room_type not in room_inventory:
        return jsonify({'success': False, 'message': 'Invalid room type'})

    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD'})

    booked_count = sum(1 for b in bookings if b['room_type'] == room_type and b['date'] == date_str)
    if booked_count >= room_inventory[room_type]:
        return jsonify({'success': False, 'message': 'No rooms available'})

    booking = {'id': booking_id_seq, 'room_type': room_type, 'date': date_str}
    booking_id_seq += 1
    bookings.append(booking)

    return jsonify({'success': True, 'message': 'Room booked successfully', 'booking_id': booking['id']})


if __name__ == '__main__':
    app.run(port=6000, debug=True)
