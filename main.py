import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from passlib.apache import HtpasswdFile
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Путь к файлу users.htpasswd
HTPASSWD_FILE_PATH = '/etc/grid-router/users.htpasswd'
# Загрузка файла users.htpasswd
htpasswd = HtpasswdFile(HTPASSWD_FILE_PATH)

# Путь к папке с XML-файлами по умолчанию
DEFAULT_XML_FOLDER = '/etc/grid-router/quota/'

# Метод для получения пути к XML-файлу
def get_xml_file_path(filename, folder=DEFAULT_XML_FOLDER):
    return os.path.join(folder, filename)

# Отображение страницы входа
@app.route('/')
def login():
    return render_template('login.html')

# Проверка данных входа и перенаправление на страницу управления
@app.route('/authenticate', methods=['POST'])
def authenticate():
    username = request.form['username']
    password = request.form['password']

    # Проверка логина и пароля
    if htpasswd.check_password(username, password):
        session['username'] = username
        return redirect('/management')
    else:
        return redirect('/')

# Отображение страницы управления
@app.route('/management')
def management():
    # Проверка аутентификации
    if 'username' not in session:
        return redirect('/')

    username = session['username']
    xml_file_path = get_xml_file_path(f'{username}.xml')

    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    browsers = root.findall(".//browser")
    
    return render_template('management.html', browsers=browsers)

# Выход из аккаунта
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# Обработка формы для добавления разделов
@app.route('/add_section', methods=['POST'])
def add_section():
    # Проверка аутентификации
    if 'username' not in session:
        return redirect('/')

    username = session['username']
    xml_file_path = get_xml_file_path(f'{username}.xml')
    
    browser_name = request.form['browser']
    version_number = request.form['version']
    region_name = request.form['region']
    host_name = request.form['host']
    port = request.form['port']
    count = request.form['count']
    hostusername = request.form.get('username')
    hostpassword = request.form.get('password')
    scheme = request.form.get('scheme')
    vnc = request.form.get('vnc')

    # Чтение XML-файла
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Поиск или создание элемента browser
    browser_element = root.find(".//browser[@name='{}']".format(browser_name))
    if browser_element is None:
        browser_element = ET.SubElement(root, 'browser')
        browser_element.set('name', browser_name)

    # Поиск или создание элемента version внутри browser
    version_element = browser_element.find(".//version[@number='{}']".format(version_number))
    if version_element is None:
        version_element = ET.SubElement(browser_element, 'version')
        version_element.set('number', version_number)

    # Поиск или создание элемента region внутри version
    region_element = version_element.find(".//region[@name='{}']".format(region_name))
    if region_element is None:
        region_element = ET.SubElement(version_element, 'region')
        region_element.set('name', region_name)

    # Создание элемента host внутри region
    host_element = ET.SubElement(region_element, 'host')
    host_element.set('name', host_name)
    host_element.set('port', port)
    host_element.set('count', count)

    if hostusername:
        host_element.set('username', hostusername)
    if hostpassword:
        host_element.set('password', hostpassword)
    if scheme:
        host_element.set('scheme', scheme)
    if vnc:
        host_element.set('vnc', vnc)
    
    # Форматирование XML-файла с отступами
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    formatted_xml_str = "\n".join([line for line in xml_str.split("\n") if line.strip()])

    # Сохранение отформатированного XML-файла без добавления пустых строк
    with open(xml_file_path, 'w') as file:
        file.write(formatted_xml_str)

    return redirect('/management')

# Обработка формы для удаления раздела
@app.route('/remove_section', methods=['POST'])
def remove_section():
    # Проверка аутентификации
    if 'username' not in session:
        return redirect('/')

    username = session['username']
    xml_file_path = get_xml_file_path(f'{username}.xml')

    browser_name = request.form['browser']
    version_number = request.form['version']
    region_name = request.form['region']

    # Чтение XML-файла
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Поиск элемента browser
    browser_element = root.find(".//browser[@name='{}']".format(browser_name))
    if browser_element is None:
        return "Браузер '{}' не найден".format(browser_name)

    # Поиск элемента version внутри browser
    version_element = browser_element.find(".//version[@number='{}']".format(version_number))
    if version_element is None:
        return "Версия '{}' для браузера '{}' не найдена".format(version_number, browser_name)

    # Поиск элемента region внутри version
    region_element = version_element.find(".//region[@name='{}']".format(region_name))
    if region_element is None:
        # Удаление версии из браузера
        browser_element.remove(version_element)

        # Проверка наличия других версий в браузере
        if len(browser_element.findall("version")) == 0:
            # Если нет других версий, удалить браузер из XML-дерева
            root.remove(browser_element)
    else:
        # Удаление региона из версии
        version_element.remove(region_element)

    # Сохранение XML-файла с pretty print
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    formatted_xml_str = "\n".join([line for line in xml_str.split("\n") if line.strip()])

    # Сохранение отформатированного XML-файла без добавления пустых строк
    with open(xml_file_path, 'w') as file:
        file.write(formatted_xml_str)

    return redirect('/management')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5099)
