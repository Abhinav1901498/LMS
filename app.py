# app.py
import cv2
import mediapipe as mp

# ------------------- HAND TRACKER -------------------
class Tracker():
    def __init__(self, static_image_mode=False, max_num_hands=1,
                 min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.static_image_mode = static_image_mode
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self.hands = mp.solutions.hands.Hands(static_image_mode=self.static_image_mode,
                                              max_num_hands=self.max_num_hands,
                                              min_detection_confidence=self.min_detection_confidence,
                                              min_tracking_confidence=self.min_tracking_confidence)
        self.mpDraw = mp.solutions.drawing_utils
        self.tracking_id = [8, 12]  # Index finger tip & Middle finger tip

    def hand_landmark(self, img):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                self.mpDraw.draw_landmarks(img, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
        return img

    def tracking(self, img):
        tracking_points = []
        dist = 10e5
        x1, y1 = -1, -1
        if self.results.multi_hand_landmarks:
            hand_landmarks = self.results.multi_hand_landmarks[0]
            for id, lm in enumerate(hand_landmarks.landmark):
                if id in self.tracking_id:
                    h, w, c = img.shape
                    x, y = int(lm.x * w), int(lm.y * h)
                    tracking_points.append((x, y))
                    cv2.circle(img, (x, y), 10, (255, 0, 255), cv2.FILLED)

            x1, y1 = tracking_points[0]
            x2, y2 = tracking_points[1]
            x_c, y_c = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (x_c, y_c), 10, (255, 0, 255), cv2.FILLED)
            dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

        return img, dist, x1, y1


# ------------------- CALCULATOR BUTTON -------------------
class Button:
    def __init__(self, x, y, w, h, value,
                 font=cv2.FONT_HERSHEY_COMPLEX,
                 font_color=(255, 255, 255),
                 thick=1, font_size=1.2):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.value = value

        self.font = font
        self.font_color = font_color
        self.thick = thick
        self.font_size = font_size
        self.text_width, self.text_height = cv2.getTextSize(self.value, self.font, self.font_size, self.thick)[0]

    def draw(self, img):
        cv2.rectangle(img, (self.x, self.y), (self.x + self.w, self.y + self.h),
                      (50, 50, 50), cv2.FILLED)
        cv2.rectangle(img, (self.x, self.y), (self.x + self.w, self.y + self.h),
                      (10, 10, 10), 3)
        cv2.putText(img, self.value,
                    (self.x + (self.w - self.text_width) // 2,
                     self.y + (self.h + self.text_height) // 2),
                    self.font, self.font_size, self.font_color, self.thick)
        return img

    def check_click(self, img, dist, x1, y1):
        if (self.x <= x1 <= self.x + self.w) and (self.y <= y1 <= self.y + self.h) and dist <= 35:
            cv2.rectangle(img, (self.x, self.y), (self.x + self.w, self.y + self.h),
                          (0, 255, 0), cv2.FILLED)
            cv2.rectangle(img, (self.x, self.y), (self.x + self.w, self.y + self.h),
                          (10, 10, 10), 3)
            cv2.putText(img, self.value,
                        (self.x + (self.w - self.text_width) // 2,
                         self.y + (self.h + self.text_height) // 2),
                        self.font, self.font_size, self.font_color, self.thick)
            return True
        return False


# ------------------- CALCULATOR UI -------------------
def draw_calculator(img):
    button_list_values = [['7', '8', '9', '^', '('],
                          ['4', '5', '6', '*', ')'],
                          ['1', '2', '3', '-', 'DEL'],
                          ['0', '.', '/', '+', '=']]
    button_list = []
    for i in range(4):
        for j in range(5):
            button_list.append(Button(600 + 80 * j, 200 + 80 * i, 80, 80, button_list_values[i][j]))

    clear_button = Button(840, 520, 160, 80, 'CLEAR')
    button_list.append(clear_button)

    for button in button_list:
        img = button.draw(img)

    img = cv2.rectangle(img, (600, 100), (1000, 200), (50, 50, 50), cv2.FILLED)
    img = cv2.rectangle(img, (600, 100), (1000, 200), (10, 10, 10), 3)
    return img, button_list


# ------------------- MAIN APP -------------------
if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)

    tracker = Tracker()
    equation = ''
    delay = 0

    while True:
        success, img = cap.read()
        img = cv2.flip(img, 1)
        img = tracker.hand_landmark(img)
        img, button_list = draw_calculator(img)
        img, dist, x1, y1 = tracker.tracking(img)

        # ✅ Button click sirf ek hi bar chalega
        if delay == 0:
            for button in button_list:
                if button.check_click(img, dist, x1, y1):
                    if button.value == 'DEL':
                        if equation in ['', 'error']:
                            equation = ''
                        else:
                            equation = equation[:-1]

                    elif button.value == '^':
                        if equation == 'error':
                            equation = ''
                        equation += '**'

                    elif button.value == 'CLEAR':
                        equation = ''

                    elif button.value == '=':
                        if equation == '' or equation == 'error':
                            equation = ''
                        else:
                            try:
                                equation = str(eval(equation))
                            except:
                                equation = 'error'

                    else:
                        if equation == 'error':
                            equation = ''
                        equation += button.value

                    delay = 1   # ✅ ek button press ke baad lock lag jaye
                    break       # ek hi button ek frame me execute ho

        # ✅ Delay counter
        if delay > 0:
            delay += 1
            if delay > 15:   # adjust delay (15 ~ 0.5 sec)
                delay = 0

        cv2.putText(img, equation, (610, 170), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 255), 2)
        cv2.imshow('Hand Calculator', img)

        if cv2.waitKey(1) & 0xFF == 27:  # press ESC to exit
            break

    cap.release()
    cv2.destroyAllWindows()
