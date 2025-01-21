import requests  # For sending POST requests

class BabylonCommunicator:
    def __init__(self, endpoint_url="http://127.0.0.1:5000/send-frame"):
        self.endpoint_url = endpoint_url

    def set_endpoint_url(self, endpoint_url):
        self.endpoint_url = endpoint_url

    def send_message_endpoint(self, message, endpoint_url=None):
        if endpoint_url:
            self.set_endpoint_url(endpoint_url)
        try:
            # Send the message to the Flask server
            response = requests.post(self.endpoint_url, json=message)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to send message: {e}")
            return {"status": "error", "message": str(e)}

    def frame_sender(self, current_frame):
        if current_frame is None:
            print("No frame to send")
            return
        
        if current_frame < 0:
            print("Invalid frame number")
            return
        
        if not isinstance(current_frame, int):
            print("Invalid frame number")
            return

        print(f"Sending frame: {current_frame}")

        # Send the frame to the Flask server
        frame_data = {'frame': current_frame}
        print(self.send_message_endpoint(frame_data, self.endpoint_url))

    def percentage_frame_sender(self, percentage):
        if percentage is None:
            print("No percentage to send")
            return
        
        if percentage < 0 or percentage > 100:
            print("Invalid percentage")
            return
        
        print(f"Sending percentage: {percentage}")

        # Send the percentage to the Flask server
        percentage_data = {'percentage': percentage}
        print(self.send_message_endpoint(percentage_data, self.endpoint_url))
