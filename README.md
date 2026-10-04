# INTENSIDAD-LUMINICA-MEDIAPIPE
# Sistema de Control de Iluminación por Gestos con MediaPipe y ESP32

Este proyecto implementa un sistema de control de iluminación en tiempo real mediante el procesamiento de gestos manuales con visión por computadora[cite: 1]. Utiliza **Python (MediaPipe + OpenCV)** para el análisis de video y un microcontrolador **ESP32** (simulado en **Wokwi**) para ejecutar los comandos de iluminación mediante salidas PWM y secuencias automatizadas[cite: 1].

---

## 1. Requisitos y Tecnologías Utilizadas

### **Entorno de Software**
* **Sistema Operativo:** Windows 10 / 11
* **Lenguaje y Entorno:** Python 3.12 (VS Code)
* **Simulador de Hardware:** Wokwi Simulator (`Wokwi-GUEST` Virtual WiFi)
* **Herramienta de Puente de Red:** Wokwi IoT Network Gateway (`wokwigw.exe` v2.0.1)[cite: 7]

### **Librerías de Python**
* `opencv-python` (Captura de video y renderizado de interfaz)
* `mediapipe` (v0.10.14 - Detección de puntos clave / landmarks de la mano)
* `requests` (Envío de peticiones HTTP asíncronas)

---

## 2. Esquema de Hardware y Conexiones (ESP32)

El circuito está montado sobre una tarjeta ESP32 DevKit v1 en Wokwi con las siguientes salidas a LEDs a través de resistencias limitadoras de corriente de 220 Ω:

| Componente | Pin GPIO ESP32 | Tipo de Señal | Función |
| :--- | :---: | :---: | :--- |
| **LED Amarillo** | GPIO 18 | Salida PWM (`ledc`) | Iluminación de baja intensidad (30%) / Secuencias[cite: 1] |
| **LED Azul** | GPIO 19 | Salida PWM (`ledc`) | Iluminación de media intensidad (70%) / Secuencias[cite: 1] |
| **LED Rojo** | GPIO 21 | Salida PWM (`ledc`) | Iluminación de alta intensidad (100%) / Secuencias[cite: 1] |

---

## 3. Matriz de Gestos, Comandos y Acciones

El script de Python analiza las posiciones relativas de las articulaciones de la mano y las traduce a comandos HTTP que recibe el servidor web montado en el ESP32:

| Gesto Detectado | Comando HTTP | Estado / Acción en el ESP32 |
| :--- | :---: | :--- |
| **Puño Cerrado** (`PUNO`) | `GET /cmd?val=A` | Enciende el **LED Amarillo** al **30% de brillo** via PWM[cite: 1]. Apaga los demás. |
| **Victoria / Amor y Paz** (`VICTORIA`) | `GET /cmd?val=B` | Enciende el **LED Azul** al **70% de brillo** via PWM[cite: 1]. Apaga los demás. |
| **Dos Palmas Abiertas** (`DOS_PALMAS`) | `GET /cmd?val=C` | Enciende el **LED Rojo** al **100% de brillo**[cite: 1]. Apaga los demás. |
| **Pulgar Abajo** (`THUMBS_DOWN`) | `GET /cmd?val=D` | Ejecuta el **Modo 1**: Secuencia de barrido continuo (Amarillo -> Azul -> Rojo)[cite: 1]. |
| **Pulgar Arriba** (`THUMBS_UP`) | `GET /cmd?val=E` | Ejecuta el **Modo 2**: Parpadeo o destello simultáneo de los 3 LEDs[cite: 1]. |

---

## 4. Código Fuente

### 4.1 Código C++ para ESP32 (`sketch.ino`)

```cpp
#include <WiFi.h>
#include <WebServer.h>

#define LED_AMARILLO 18
#define LED_AZUL     19
#define LED_ROJO     21

// Parámetros del PWM
#define FREC_PWM 5000
#define RES_PWM  8

WebServer server(80);

void apagarLeds() {
  ledcWrite(LED_AMARILLO, 0);
  ledcWrite(LED_AZUL, 0);
  ledcWrite(LED_ROJO, 0);
}

void modo1() {
  for (int i = 0; i < 3; i++) {
    ledcWrite(LED_AMARILLO, 255); delay(200); apagarLeds();
    ledcWrite(LED_AZUL, 255);     delay(200); apagarLeds();
    ledcWrite(LED_ROJO, 255);     delay(200); apagarLeds();
  }
}

void modo2() {
  for (int i = 0; i < 4; i++) {
    ledcWrite(LED_AMARILLO, 255);
    ledcWrite(LED_AZUL, 255);
    ledcWrite(LED_ROJO, 255);
    delay(250);
    apagarLeds();
    delay(250);
  }
}

void setup() {
  Serial.begin(115200);

  // Nueva sintaxis para ESP32 Arduino Core v3.0+
  ledcAttach(LED_AMARILLO, FREC_PWM, RES_PWM);
  ledcAttach(LED_AZUL, FREC_PWM, RES_PWM);
  ledcAttach(LED_ROJO, FREC_PWM, RES_PWM);

  apagarLeds();

  // Conexión a la red WiFi virtual de Wokwi
  WiFi.begin("Wokwi-GUEST", "", 6);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi Conectada!");
  Serial.print("Direccion IP del ESP32: ");
  Serial.println(WiFi.localIP());

  // Servidor Web para procesar los gestos enviados desde Python
  server.on("/cmd", []() {
    if (server.hasArg("val")) {
      char cmd = server.arg("val")[0];
      switch (cmd) {
        case 'A': apagarLeds(); ledcWrite(LED_AMARILLO, (int)(255 * 0.30)); break;
        case 'B': apagarLeds(); ledcWrite(LED_AZUL, (int)(255 * 0.70)); break;
        case 'C': apagarLeds(); ledcWrite(LED_ROJO, 255); break;
        case 'D': modo1(); break;
        case 'E': modo2(); break;
      }
      server.send(200, "text/plain", "OK");
    }
  });

  server.begin();
}

void loop() {
  server.handleClient();
}
```
---

## 5. Guía de Configuración y Ejecución Paso a Paso

1. **Iniciar la Simulación en Wokwi:**
   * Abrir el circuito en Wokwi, compilar el código C++ y presionar el botón de **Play ($\triangleright$)**[cite: 6].
   * Verificar en el *Serial Monitor* que el ESP32 se haya conectado a la red virtual `Wokwi-GUEST` y tomar nota de la IP asignada (por ejemplo, `10.10.0.2`)[cite: 6].

2. **Establecer el Puente de Red Local (`wokwigw.exe`):**
   * Abrir la terminal de comandos de Windows (CMD) directamente en la carpeta donde se descargó la utilidad `wokwigw.exe`[cite: 8]:
     ```cmd
     cd "C:\Users\ingea\Downloads\wokwigw_v2.0.1_Windows_64bit"
     ```
   * Ejecutar el comando para redirigir el puerto local `9080` hacia la IP privada de la simulación (`10.10.0.2:80`)[cite: 8, 9]:
     ```cmd
     wokwigw.exe --forward 9080:10.10.0.2:80
     ```
   * Dejar abierta la ventana de la consola donde se muestra el estado `:9080 -> 10.10.0.2:80`[cite: 8, 9].

3. **Ejecutar el Script de Control en Python:**
   * Abrir el archivo `gestos.py` en VS Code y verificar que la variable apunte al puente local[cite: 8]:
     ```python
     ESP32_IP = "http://localhost:9080"
     ```
   * Iniciar el script ejecutando en la terminal[cite: 2]:
     ```bash
     python gestos.py
     ```
   * Posicionarse frente a la cámara web y realizar los gestos manuales para enviar los comandos en tiempo real[cite: 1, 2].

---

## 6. Problemas Presentados y Soluciones Implementadas

### **1. Incompatibilidad de Sintaxis PWM en ESP32 Arduino Core v3.0+**
* **Problema:** Al intentar compilar el código del ESP32 en versiones recientes de la plataforma, el compilador arrojaba errores como `error: 'ledcSetup' was not declared in this scope` y `error: 'ledcAttachPin' was not declared`.
* **Causa:** Las versiones más recientes del núcleo de Arduino para ESP32 cambiaron la API de control de temporizadores PWM, eliminando la gestión manual de canales.
* **Solución:** Se actualizó todo el código C++ a la nueva API utilizando la función unificada `ledcAttach(pin, frecuencia, resolución)` y modificando `ledcWrite(pin, valor)` para aplicar la modulación PWM directamente sobre el número de pin correspondiente.

### **2. Restricción de Gateway Privado en Wokwi y Error `no route to host`**
* **Problema:** Al enviar solicitudes HTTP desde Python directamente a la IP `10.10.0.2`, el script no lograba conectarse[cite: 6, 8]. Al intentar usar la función *Private IoT Gateway* en la web de Wokwi, la plataforma mostraba el aviso *"This feature is only available for paying users"*[cite: 8]. Adicionalmente, al usar `wokwigw.exe` sin parámetros, la consola mostraba el error `error dialing "10.13.37.2:80": connect tcp: no route to host`[cite: 8].
* **Causa:** La IP `10.10.0.2` pertenece a la red interna de los servidores virtuales de Wokwi y no es accesible desde la LAN física del computador sin enrutamiento[cite: 6]. Por defecto, la utilidad `wokwigw.exe` apunta a la subred `10.13.37.x`, la cual no coincidía con el segmento asignado al ESP32[cite: 8].
* **Solución:** Se utilizó el parámetro `--forward` en la consola de comandos de Windows (`wokwigw.exe --forward 9080:10.10.0.2:80`)[cite: 8, 9]. Esto estableció un puente de red entre el puerto local `9080` de la máquina y la IP real asignada al microcontrolador en la simulación, permitiendo el control HTTP 100% gratuito sin requerir suscripciones pagas[cite: 8, 9].

### **3. Detección Inestable del Gesto Pulgar Abajo (`THUMBS_DOWN`)**
* **Problema:** El modelo de MediaPipe presentaba falsos positivos o ignoraba el gesto de pulgar hacia abajo, clasificándolo erróneamente como un puño cerrado (`PUNO`).
* **Causa:** La condición previa evaluaba la posición vertical del pulgar en relación con la punta del dedo índice, lo cual generaba inconsistencias si la mano se inclinaba levemente hacia los lados.
* **Solución:** Se refactorizó la lógica en la función `evaluar_gesto()` para analizar la geometría interna del propio pulgar, verificando que la punta del dedo descendiera respecto a sus articulaciones base (`landmarks[4].y > landmarks[3].y > landmarks[2].y`), sumado a la verificación de que los cuatro dedos restantes (índice, medio, anular y meñique) estuvieran completamente cerrados.
