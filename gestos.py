import cv2
import mediapipe as mp
from mediapipe.python.solutions import hands as mp_hands_module
from mediapipe.python.solutions import drawing_utils as mp_drawing
import requests
import threading

# Dirección IP obtenida en la simulación de Wokwi
ESP32_IP = "http://localhost:9080"

# Función para enviar peticiones HTTP sin congelar/pausar la cámara
def enviar_comando_async(cmd):
    def peticion():
        try:
            requests.get(f"{ESP32_IP}/cmd?val={cmd}", timeout=0.5)
        except Exception:
            pass
    threading.Thread(target=peticion, daemon=True).start()

# Inicializar MediaPipe Hands
mp_hands = mp_hands_module
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

def evaluar_gesto(landmarks):
    # Puntos clave:
    # Índice: tip=8, pip=6 | Medio: tip=12, pip=10 | Anular: tip=16, pip=14 | Meñique: tip=20, pip=18
    indice_abierto = landmarks[8].y < landmarks[6].y
    medio_abierto = landmarks[12].y < landmarks[10].y
    anular_abierto = landmarks[16].y < landmarks[14].y
    menique_abierto = landmarks[20].y < landmarks[18].y

    # Gesto 1: Puño cerrado -> 'A' (LED Amarillo 30%)
    if not (indice_abierto or medio_abierto or anular_abierto or menique_abierto):
        return "PUNO", 'A'
    
    # Gesto 2: Amor y Paz / Victoria -> 'B' (LED Azul 70%)
    if indice_abierto and medio_abierto and not anular_abierto and not menique_abierto:
        return "VICTORIA", 'B'

    # Pulgar arriba / abajo
    pulgar_arriba = landmarks[4].y < landmarks[3].y and landmarks[4].y < landmarks[8].y
    pulgar_abajo = landmarks[4].y > landmarks[3].y and landmarks[4].y > landmarks[8].y

    # Gesto 4: Pulgar abajo -> 'D' (Secuencia Modo 1)
    if pulgar_abajo and not (indice_abierto or medio_abierto):
        return "THUMBS_DOWN", 'D'

    # Gesto 5: Pulgar arriba -> 'E' (Secuencia Modo 2)
    if pulgar_arriba and not (indice_abierto or medio_abierto):
        return "THUMBS_UP", 'E'

    return "DESCONOCIDO", None

ultimo_comando = None

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    gesto_detectado = "NINGUNO"
    comando = None

    if results.multi_hand_landmarks:
        # Gesto 3: Dos Palmas -> 'C' (LED Rojo 100%)
        if len(results.multi_hand_landmarks) == 2:
            gesto_detectado = "DOS_PALMAS"
            comando = 'C'
        
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            if gesto_detectado != "DOS_PALMAS":
                gesto_detectado, comando = evaluar_gesto(hand_landmarks.landmark)

    # Enviar la orden al ESP32 solo si el gesto cambió
    if comando and comando != ultimo_comando:
        enviar_comando_async(comando)
        print(f"Comando enviado a Wokwi: {comando}")
        ultimo_comando = comando

    cv2.putText(frame, f"Gesto: {gesto_detectado}", (10, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Control por Gestos - MediaPipe", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()