    #include <WiFi.h>
#include <PubSubClient.h>

const int PIN_ADC = 34;
const int PIN_ADC_CORRIENTE = 35;

const float frecuencia_red = 50.0;
const int muestrasPorPeriodo = 1000;
const int periodos = 10;
const int N = muestrasPorPeriodo * periodos;

const float ganancia = 65.934;
const float gananciaI = 0.35;//0.26617

const char* ssid = "iPhone (113)";
const char* password = "mateosilva";
const char* mqtt_server = "172.20.10.3";

WiFiClient espClient;
PubSubClient client(espClient);

const int LED = 2;
bool activo = false;

void callback(char* topic, byte* payload, unsigned int length) {
  if (payload[0] == '1') {
    activo = true;
  }
  else if (payload[0] == '0') {
    activo = false;
  }
}

float v[N];
float i[N];

unsigned long Ts_us;

void setup() {
  Serial.begin(115200);

  pinMode(LED, OUTPUT);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Conectando WiFi...");
  }

  Serial.println("WiFi conectado");

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  while (!client.connected()) {
    Serial.println("Conectando MQTT...");
    client.connect("ESP32");
    delay(500);
  }

  Serial.println("MQTT conectado");

  client.subscribe("esp/comando");

  Serial.println("Suscripto a esp/comando");

  delay(2000);
}

void loop() {
  client.loop();

  if (activo) {
    digitalWrite(LED, HIGH);
  }
  else {
    digitalWrite(LED, LOW);
  }

  float fs = frecuencia_red * muestrasPorPeriodo;

  Ts_us = (unsigned long)((1.0 / fs) * 1e6);

  Serial.println("Iniciando medicion...");

  // 1. ADQUISICIÓN
  unsigned long t0 = micros();

  for (int k = 0; k < N; k++) {
    while (micros() - t0 < (unsigned long)k * Ts_us);

    v[k] = analogRead(PIN_ADC);
    i[k] = analogRead(PIN_ADC_CORRIENTE);
  }

  // 2. CÁLCULO DE VALOR MEDIO (Offset DC)
  float suma = 0;
  float sumaI = 0;

  for (int k = 0; k < N; k++){
    suma += v[k];
    sumaI += i[k];
  }

  float media_adc = suma / N;
  float media_adc_I = sumaI / N;

  // 3. CÁLCULO DE VRMS (Sobre señal centrada)
  float suma_cuadrados = 0;
  float suma_cuadrados_I = 0;

  for (int k = 0; k < N; k++) {
    float v_centrado = (float)v[k] - media_adc;
    float i_centrado = (float)i[k] - media_adc_I;

    suma_cuadrados += v_centrado * v_centrado;
    suma_cuadrados_I += i_centrado * i_centrado;
  }

  float vrms_adc = sqrt(suma_cuadrados / N);
  float irms_adc = sqrt(suma_cuadrados_I / N);

  // 4. CONTEO DE CRUCES (Frecuencia)
  int cruces = 0;
  bool senal_estaba_abajo = false;
  float umbral_histeresis = 25.0;

  for (int k = 0; k < N; k++) {
    float valor_centrado = v[k] - media_adc;

    if (senal_estaba_abajo) {
      if (valor_centrado > umbral_histeresis) {
        cruces++;
        senal_estaba_abajo = false;
      }
    }
    else {
      if (valor_centrado < -umbral_histeresis) {
        senal_estaba_abajo = true;
      }
    }
  }

  // 5. CONVERSIÓN A UNIDADES FÍSICAS (Voltios)
  float duracion_s = (micros() - t0) / 1000000.0;
  float frecuencia_medida = cruces / duracion_s;

  // Convertimos el Vrms e Irms de "cuentas de ADC" a Voltios/Ampers reales
  float vrms_voltios = (vrms_adc / 4095.0) * 3.3 * ganancia;
  float offset_voltios = (media_adc / 4095.0) * 3.3;

  float irms_amper = (irms_adc / 4095.0) * 3.3 * gananciaI;
  

  float offset_amper = (media_adc_I / 4095.0) * 3.3;

  // Potencia activa
  // i[k] atrasada 8,23 grados con respecto a la real
  // es decir, i[k] corresponde a ireal[k-23]
  // ya que se toman 1000 muestras por ciclo -> 360/1000=0.36 -> 0.36*238,23

  float pa = 0;

  /*for (int k = 23; k < N; k++) {
    pa += (((v[k] / 4095.0) * 3.3 * ganancia) ) * (((i[k - 23] / 4095.0) * 3.3 * gananciaI));
  }*/
  
  // Probá sin compensar desfase
for (int k = 0; k < N; k++) {
    float v_inst = (((float)v[k] - media_adc) / 4095.0) * 3.3 * ganancia;
    float i_inst = (((float)i[k] - media_adc_I) / 4095.0 )* 3.3 * gananciaI;
    pa += v_inst * i_inst;
}
pa /= (N);

  // Factor de potencia
  float fp = pa / (vrms_voltios * irms_amper);

  // RESULTADOS
  Serial.println("--- Medicion Realizada ---");

  Serial.print("Vrms (AC): ");
  Serial.print(vrms_voltios, 3);
  Serial.println(" V");

  Serial.print("V Offset (DC):  ");
  Serial.print(offset_voltios, 3);
  Serial.println(" V");

  Serial.print("Frecuencia: ");
  Serial.print(frecuencia_medida, 2);
  Serial.println(" Hz");

  Serial.println("--------------------------\n");

  Serial.print("Irms (AC):  ");
  Serial.print(irms_amper, 3);
  Serial.println(" A");

  Serial.print("I Offset (DC):  ");
  Serial.print(offset_amper, 3);
  Serial.println(" A");

  Serial.print("Potencia activa:  ");
  Serial.print(pa, 3);
  Serial.println(" W");

  Serial.print("Factor de potencia:  ");
  Serial.print(fp, 3);

  char buffer[10];

dtostrf(vrms_voltios, 6, 3, buffer);
client.publish("VRMS", buffer);
delay(1000);

dtostrf(irms_amper, 6, 3, buffer);
client.publish("IRMS", buffer);
delay(1000);

dtostrf(frecuencia_medida, 6, 2, buffer);
client.publish("FRECUENCIA", buffer);
delay(1000);

dtostrf(fp, 6, 3, buffer);
client.publish("FP", buffer);
delay(1000);
}
