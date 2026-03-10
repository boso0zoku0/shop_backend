from fast2sms import F2Client

# Инициализация клиента с вашим API ключом
f2 = F2Client(api_key="YOUR_API_KEY")

# Отправка сообщения (можно несколько номеров через запятую)
response = f2.quick_sms(
    numbers="999999999, 1111111111, 8888888888",
    msg="Hello from FastAPI!",
)

print(response.text)  # JSON-ответ от сервера
