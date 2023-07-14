# Используем базовый образ Python
FROM python:3.9

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем зависимости и файлы приложения в контейнер
COPY requirements.txt .
COPY main.py .
COPY templates/ templates/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5099
# Указываем команду для запуска приложения
CMD ["python", "main.py"]
