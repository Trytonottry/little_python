#include <WiFi.h>
#include <ESP32FtpClient.h>

// Настройки Wi-Fi
const char* ssid = "your-ssid";
const char* password = "your-password";

// Настройки FTP
const char* ftp_server = "your-public-ip";  // Публичный IP-адрес или доменное имя
const char* ftp_user = "username";         // Логин FTP
const char* ftp_password = "password";     // Пароль FTP
const int ftp_port = 2121;                 // Порт FTP

// Список номеров для игнорирования
const int maxIgnoreListSize = 10;  // Максимальное количество номеров
String ignoreList[maxIgnoreListSize];
int ignoreListSize = 0;

WiFiClient client;
FtpClient ftp(client);
HardwareSerial SerialGSM(1);  // UART1 на ESP32

void setup() {
  Serial.begin(115200);
  SerialGSM.begin(9600, SERIAL_8N1, 16, 17);  // RX=16, TX=17

  // Подключение к Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nПодключено к Wi-Fi!");

  // Загрузка списка игнорируемых номеров
  loadIgnoreList();

  // Настройка GSM-модуля
  setupGSM();
}

void loop() {
  // Проверка входящих звонков
  checkIncomingCalls();

  // Проверка входящих SMS
  checkIncomingSMS();

  delay(1000);  // Задержка для уменьшения нагрузки
}

// Функция для проверки, нужно ли игнорировать номер
bool isNumberIgnored(String number) {
  for (int i = 0; i < ignoreListSize; i++) {
    if (number == ignoreList[i]) {
      return true;  // Номер найден в списке игнорируемых
    }
  }
  return false;  // Номер не найден в списке
}

// Функция для загрузки списка игнорируемых номеров
void loadIgnoreList() {
  if (ftp.openConnection(ftp_server, ftp_port, ftp_user, ftp_password)) {
    String fileContent;
    if (ftp.readFile("/ignore_list.txt", fileContent)) {
      // Разделение файла на строки
      int startIndex = 0;
      int endIndex = fileContent.indexOf('\n');
      while (endIndex != -1 && ignoreListSize < maxIgnoreListSize) {
        String number = fileContent.substring(startIndex, endIndex);
        number.trim();
        if (number.length() > 0) {
          ignoreList[ignoreListSize++] = number;
        }
        startIndex = endIndex + 1;
        endIndex = fileContent.indexOf('\n', startIndex);
      }
      Serial.println("Список игнорируемых номеров загружен!");
    } else {
      Serial.println("Ошибка чтения файла ignore_list.txt!");
    }
    ftp.closeConnection();
  } else {
    Serial.println("Ошибка подключения к FTP-серверу для загрузки списка!");
  }
}

// Настройка GSM-модуля
void setupGSM() {
  SerialGSM.println("AT+CLIP=1");  // Включение уведомлений о входящих звонках
  delay(1000);
  SerialGSM.println("AT+CMGF=1");  // Установка текстового режима SMS
  delay(1000);
  SerialGSM.println("AT+CNMI=1,2,0,0,0");  // Уведомления о новых SMS
  delay(1000);
}

// Проверка входящих звонков
void checkIncomingCalls() {
  if (SerialGSM.available()) {
    String response = SerialGSM.readString();
    Serial.println(response);

    if (response.indexOf("+CLIP:") != -1) {
      int start = response.indexOf("\"") + 1;
      int end = response.indexOf("\"", start);
      String number = response.substring(start, end);

      if (!isNumberIgnored(number)) {
        String callData = number + ",2023-10-01 12:00:00\n";  // Пример данных о звонке
        sendToFTP("/calls.txt", callData);
      } else {
        Serial.println("Звонок от игнорируемого номера: " + number);
      }
    }
  }
}

// Проверка входящих SMS
void checkIncomingSMS() {
  if (SerialGSM.available()) {
    String response = SerialGSM.readString();
    Serial.println(response);

    if (response.indexOf("+CMTI:") != -1) {
      int index = response.indexOf(",") + 1;
      String smsIndex = response.substring(index);
      smsIndex.trim();
      readSMS(smsIndex);
    }
  }
}

// Чтение SMS
void readSMS(String index) {
  SerialGSM.println("AT+CMGR=" + index);
  delay(1000);

  if (SerialGSM.available()) {
    String smsData = SerialGSM.readString();
    Serial.println(smsData);

    int senderStart = smsData.indexOf("\"") + 1;
    int senderEnd = smsData.indexOf("\"", senderStart);
    String sender = smsData.substring(senderStart, senderEnd);

    int textStart = smsData.indexOf("\n") + 1;
    String text = smsData.substring(textStart);
    text.trim();

    if (!isNumberIgnored(sender)) {
      String smsEntry = sender + "," + text + ",2023-10-01 12:05:00\n";  // Пример данных о SMS
      sendToFTP("/sms.txt", smsEntry);
    } else {
      Serial.println("SMS от игнорируемого номера: " + sender);
    }
  }
}

// Отправка данных на FTP-сервер
void sendToFTP(const char* filename, const String& data) {
  if (ftp.openConnection(ftp_server, ftp_port, ftp_user, ftp_password)) {
    if (ftp.appendFile(filename, data.c_str())) {
      Serial.println("Данные отправлены на FTP: " + data);
    } else {
      Serial.println("Ошибка отправки данных на FTP!");
    }
    ftp.closeConnection();
  } else {
    Serial.println("Ошибка подключения к FTP-серверу!");
  }
}
