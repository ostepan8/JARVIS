import cv2
import mediapipe as mp
import numpy as np
import webbrowser
import time

class HandGestureRecognizer:
    def __init__(self, action_double_high_five, action_rock_sign, action_call_me_sign):
        # Initialize MediaPipe Hands.
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(static_image_mode=False,
                                         max_num_hands=2,
                                         min_detection_confidence=0.9,
                                         min_tracking_confidence=0.9)
        
        # Set gesture states and timers
        self.gesture_state = {
            'double_high_five': False,
            'rock_sign': False,
            'call_me_sign': False
        }
        self.gesture_timers = {
            'double_high_five': 0,
            'rock_sign': 0,
            'call_me_sign': 0
        }

        # Set the required gesture hold times (in seconds) for each gesture.
        self.GESTURE_HOLD_TIMES = {
            'double_high_five': 0.2,  # Longer hold time for 'double_high_five'.
            'rock_sign': 0.2,         # Shorter hold time for 'rock_sign'.
            'call_me_sign': 0.1       # Shorter hold time for 'call_me_sign'.
        }

        # Store the gesture actions
        self.gesture_actions = {
            'double_high_five': action_double_high_five,
            'rock_sign': action_rock_sign,
            'call_me_sign': action_call_me_sign
        }

    def recognize_gesture(self, hand_landmarks, handedness_label):
        """
        Recognizes hand gestures based on finger positions.
        Returns 'open_hand' if the hand is open, or another gesture name.
        """
        # Get landmark positions.
        landmarks = hand_landmarks.landmark

        # Initialize a list to hold finger states.
        fingers_up = []

        # Thumb
        if handedness_label == 'Right':
            # For right hand, thumb tip x < thumb IP x
            if landmarks[self.mp_hands.HandLandmark.THUMB_TIP].x < landmarks[self.mp_hands.HandLandmark.THUMB_IP].x:
                fingers_up.append(1)
            else:
                fingers_up.append(0)
        else:
            # For left hand, thumb tip x > thumb IP x
            if landmarks[self.mp_hands.HandLandmark.THUMB_TIP].x > landmarks[self.mp_hands.HandLandmark.THUMB_IP].x:
                fingers_up.append(1)
            else:
                fingers_up.append(0)

        # Fingers: Check if tip is above PIP joint.
        for finger_tip_id, finger_pip_id in [
            (self.mp_hands.HandLandmark.INDEX_FINGER_TIP, self.mp_hands.HandLandmark.INDEX_FINGER_PIP),
            (self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP, self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP),
            (self.mp_hands.HandLandmark.RING_FINGER_TIP, self.mp_hands.HandLandmark.RING_FINGER_PIP),
            (self.mp_hands.HandLandmark.PINKY_TIP, self.mp_hands.HandLandmark.PINKY_PIP)
        ]:
            if landmarks[finger_tip_id].y < landmarks[finger_pip_id].y:
                fingers_up.append(1)
            else:
                fingers_up.append(0)

        # If all fingers are up, return 'open_hand'.
        if fingers_up == [1, 1, 1, 1, 1]:
            return 'open_hand'

        # Recognize Rock Sign.
        if fingers_up == [0, 1, 0, 0, 1]:
            return 'rock_sign'

        # Recognize Call Me Sign.
        if fingers_up == [1, 0, 0, 0, 1]:
            return 'call_me_sign'

        return None

    def execute_action(self, gesture):
        """
        Executes an action based on the recognized gesture.
        """
        action = self.gesture_actions.get(gesture)
        if action:
            action()  # Call the function mapped to the gesture
        else:
            print(f"No action defined for gesture: {gesture}")

    def run(self):
        """Main method to run the gesture recognition."""
        cap = cv2.VideoCapture(0)

        while True:
            success, frame = cap.read()
            if not success:
                print("Failed to capture image")
                break

            # Flip the frame horizontally for a selfie-view display.
            frame = cv2.flip(frame, 1)

            # Convert the BGR image to RGB before processing.
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False  # Improve performance
            result = self.hands.process(rgb_frame)
            rgb_frame.flags.writeable = True

            current_time = time.time()  # Get the current time

            gestures_detected = []

            if result.multi_hand_landmarks and result.multi_handedness:
                for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                    # Get handedness label ('Left' or 'Right')
                    handedness_label = handedness.classification[0].label

                    # Draw hand landmarks on the frame.
                    self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                    # Recognize gesture.
                    gesture = self.recognize_gesture(hand_landmarks, handedness_label)
                    gestures_detected.append(gesture)

                # Check if both hands are open ('double_high_five' gesture).
                if gestures_detected.count('open_hand') == 2:
                    gesture = 'double_high_five'
                    # Handle gesture execution with timing mechanism.
                    if self.gesture_timers[gesture] == 0:
                        self.gesture_timers[gesture] = current_time
                    else:
                        required_hold_time = self.GESTURE_HOLD_TIMES[gesture]
                        if (current_time - self.gesture_timers[gesture]) >= required_hold_time and not self.gesture_state[gesture]:
                            self.execute_action(gesture)
                            self.gesture_state[gesture] = True
                else:
                    # Reset the timer and state for 'double_high_five' if not detected.
                    self.gesture_timers['double_high_five'] = 0
                    self.gesture_state['double_high_five'] = False

                # Handle individual gestures for each hand.
                for idx, gesture in enumerate(gestures_detected):
                    if gesture in ['rock_sign', 'call_me_sign']:
                        if self.gesture_timers[gesture] == 0:
                            self.gesture_timers[gesture] = current_time
                        else:
                            required_hold_time = self.GESTURE_HOLD_TIMES[gesture]
                            if (current_time - self.gesture_timers[gesture]) >= required_hold_time and not self.gesture_state[gesture]:
                                self.execute_action(gesture)
                                self.gesture_state[gesture] = True
                    else:
                        # Reset timers and states for gestures not detected.
                        for key in ['rock_sign', 'call_me_sign']:
                            self.gesture_timers[key] = 0
                            self.gesture_state[key] = False
            else:
                # Reset timers and states if no hand is detected.
                for key in self.gesture_timers.keys():
                    self.gesture_timers[key] = 0
                    self.gesture_state[key] = False

            # Display the resulting frame.
            cv2.imshow('Hand Gesture Recognition', frame)

            # Exit on pressing 'q'.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Clean up.
        cap.release()
        cv2.destroyAllWindows()


# Example Usage:
if __name__ == "__main__":
    # Define the custom functions for each gesture
    def double_high_five_action():
        print("Double High Five! Opening a website...")
        webbrowser.open("https://www.example.com")

    def rock_sign_action():
        print("Rock Sign! Playing some music...")

    def call_me_sign_action():
        print("Call Me Sign! Sending a message...")

    # Create an instance of HandGestureRecognizer and pass the functions
    recognizer = HandGestureRecognizer(
        double_high_five_action,
        rock_sign_action,
        call_me_sign_action
    )

    # Start the gesture recognition
    recognizer.run()
