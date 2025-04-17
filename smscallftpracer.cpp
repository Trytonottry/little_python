#include <WiFi.h>
#include <ESP32FtpClient.h>

// ��������� Wi-Fi
const char* ssid = "your-ssid";
const char* password = "your-password";

// ��������� FTP
const char* ftp_server = "your-public-ip";  // ��������� IP-����� ��� �������� ���
const char* ftp_user = "username";         // ����� FTP
const char* ftp_password = "password";     // ������ FTP
const int ftp_port = 2121;                 // ���� FTP

// ������ ������� ��� �������������
const int maxIgnoreListSize = 10;  // ������������ ���������� �������
String ignoreList[maxIgnoreListSize];
int ignoreListSize = 0;

WiFiClient client;
FtpClient ftp(client);
HardwareSerial SerialGSM(1);  // UART1 �� ESP32

void setup() {
  Serial.begin(115200);
  SerialGSM.begin(9600, SERIAL_8N1, 16, 17);  // RX=16, TX=17

  // ����������� � Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n���������� � Wi-Fi!");

  // �������� ������ ������������ �������
  loadIgnoreList();

  // ��������� GSM-������
  setupGSM();
}

void loop() {
  // �������� �������� �������
  checkIncomingCalls();

  // �������� �������� SMS
  checkIncomingSMS();

  delay(1000);  // �������� ��� ���������� ��������
}

// ������� ��� ��������, ����� �� ������������ �����
bool isNumberIgnored(String number) {
  for (int i = 0; i < ignoreListSize; i++) {
    if (number == ignoreList[i]) {
      return true;  // ����� ������ � ������ ������������
    }
  }
  return false;  // ����� �� ������ � ������
}

// ������� ��� �������� ������ ������������ �������
void loadIgnoreList() {
  if (ftp.openConnection(ftp_server, ftp_port, ftp_user, ftp_password)) {
    String fileContent;
    if (ftp.readFile("/ignore_list.txt", fileContent)) {
      // ���������� ����� �� ������
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
      Serial.println("������ ������������ ������� ��������!");
    } else {
      Serial.println("������ ������ ����� ignore_list.txt!");
    }
    ftp.closeConnection();
  } else {
    Serial.println("������ ����������� � FTP-������� ��� �������� ������!");
  }
}

// ��������� GSM-������
void setupGSM() {
  SerialGSM.println("AT+CLIP=1");  // ��������� ����������� � �������� �������
  delay(1000);
  SerialGSM.println("AT+CMGF=1");  // ��������� ���������� ������ SMS
  delay(1000);
  SerialGSM.println("AT+CNMI=1,2,0,0,0");  // ����������� � ����� SMS
  delay(1000);
}

// �������� �������� �������
void checkIncomingCalls() {
  if (SerialGSM.available()) {
    String response = SerialGSM.readString();
    Serial.println(response);

    if (response.indexOf("+CLIP:") != -1) {
      int start = response.indexOf("\"") + 1;
      int end = response.indexOf("\"", start);
      String number = response.substring(start, end);

      if (!isNumberIgnored(number)) {
        String callData = number + ",2023-10-01 12:00:00\n";  // ������ ������ � ������
        sendToFTP("/calls.txt", callData);
      } else {
        Serial.println("������ �� ������������� ������: " + number);
      }
    }
  }
}

// �������� �������� SMS
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

// ������ SMS
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
      String smsEntry = sender + "," + text + ",2023-10-01 12:05:00\n";  // ������ ������ � SMS
      sendToFTP("/sms.txt", smsEntry);
    } else {
      Serial.println("SMS �� ������������� ������: " + sender);
    }
  }
}

// �������� ������ �� FTP-������
void sendToFTP(const char* filename, const String& data) {
  if (ftp.openConnection(ftp_server, ftp_port, ftp_user, ftp_password)) {
    if (ftp.appendFile(filename, data.c_str())) {
      Serial.println("������ ���������� �� FTP: " + data);
    } else {
      Serial.println("������ �������� ������ �� FTP!");
    }
    ftp.closeConnection();
  } else {
    Serial.println("������ ����������� � FTP-�������!");
  }
}
