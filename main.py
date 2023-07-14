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

    browsers = []

    # Получение списка браузеров, версий и регионов
    for browser_element in root.findall('browser'):
        browser = {'name': browser_element.get('name'), 'versions': []}
        for version_element in browser_element.findall('version'):
            version = {'number': version_element.get('number'), 'regions': []}
            for region_element in version_element.findall('region'):
                region = {'name': region_element.get('name'), 'hosts': []}
                for host_element in region_element.findall('host'):
                    host = {'name': host_element.get('name'), 'port': host_element.get('port'),
                            'count': host_element.get('count')}
                    region['hosts'].append(host)
                region['hosts'] = sorted(region['hosts'], key=lambda x: x['name'])  # Сортировка хостов по имени
                version['regions'].append(region)
            version['regions'] = sorted(version['regions'], key=lambda x: x['name'])  # Сортировка регионов по имени
            browser['versions'].append(version)
        browsers.append(browser)
    
    return render_template('management.html', browsers=browsers)

# Выход из аккаунта
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# Метод для добавления разделов <browser>, <version> и <region>
@app.route('/add_section', methods=['POST'])
def add_section():
    # Проверка аутентификации
    if 'username' not in session:
        return redirect('/')

    username = session['username']
    xml_file_path = get_xml_file_path(f'{username}.xml')

    browser = request.form['browser']
    version = request.form['version']
    region = request.form['region']

    # Загрузка XML-файла
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Поиск соответствующего браузера
    browser_element = root.find(f"./browser[@name='{browser}']")
    if browser_element is None:
        # Браузер не найден, создаем новый
        browser_element = ET.SubElement(root, 'browser')
        browser_element.set('name', browser)
        browser_element.set('defaultVersion', version)

    # Поиск соответствующей версии
    version_element = browser_element.find(f"./version[@number='{version}']")
    if version_element is None:
        # Версия не найдена, создаем новую
        version_element = ET.SubElement(browser_element, 'version')
        version_element.set('number', version)

    # Поиск соответствующего региона
    region_element = version_element.find(f"./region[@name='{region}']")
    if region_element is None:
        # Регион не найден, создаем новый
        region_element = ET.SubElement(version_element, 'region')
        region_element.set('name', region)

    # Сохранение XML-файла с pretty print
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    formatted_xml_str = "\n".join([line for line in xml_str.split("\n") if line.strip()])

    # Сохранение отформатированного XML-файла без добавления пустых строк
    with open(xml_file_path, 'w') as file:
        file.write(formatted_xml_str)

    return redirect('/management')


# Метод для добавления <host> с атрибутами
@app.route('/add_host', methods=['POST'])
def add_host():
    # Проверка аутентификации
    if 'username' not in session:
        return redirect('/')

    username = session['username']
    xml_file_path = get_xml_file_path(f'{username}.xml')

    browser_name = request.form['browser']
    version_number = request.form['version']
    region_name = request.form['region']
    host_name = request.form['host']
    host_port = request.form['port']
    host_count = request.form['count']
    host_username = request.form.get('username')  # Получение опционального атрибута username
    host_password = request.form.get('password')  # Получение опционального атрибута password
    host_scheme = request.form.get('scheme')  # Получение опционального атрибута scheme
    host_vnc = request.form.get('vnc')

    # Загрузка XML-файла
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Поиск браузера
    browser_element = root.find(f"browser[@name='{browser_name}']")
    if browser_element is None:
        # Браузер не найден, создаем новый
        browser_element = ET.SubElement(root, 'browser', name=browser_name)

    # Поиск версии
    version_element = browser_element.find(f"version[@number='{version_number}']")
    if version_element is None:
        # Версия не найдена, создаем новую
        version_element = ET.SubElement(browser_element, 'version', number=version_number)

    # Поиск региона
    region_element = version_element.find(f"region[@name='{region_name}']")
    if region_element is None:
        # Регион не найден, создаем новый
        region_element = ET.SubElement(version_element, 'region', name=region_name)

    # Создание элемента хоста
    host_element = ET.SubElement(region_element, 'host', name=host_name, port=host_port, count=host_count)
    if host_username:
        host_element.set('username', host_username)
    if host_password:
        host_element.set('password', host_password)
    if host_scheme:
        host_element.set('scheme', host_scheme)
    if host_vnc:
        host_element.set('vnc', host_vnc)

    # Сохранение XML-файла с pretty print
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

# Удаление хоста
@app.route('/remove_host', methods=['POST'])
def remove_host():
    # Проверка аутентификации
    if 'username' not in session:
        return redirect('/')

    # Получение данных из формы
    browser_name = request.form['browser']
    version_number = request.form['version']
    region_name = request.form['region']
    host_name = request.form['host']

    username = session['username']
    # Получение пути к XML-файлу
    xml_file_path = get_xml_file_path(f'{username}.xml')

    # Загрузка XML-файла
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    region_element = root.find(
        f"browser[@name='{browser_name}']/version[@number='{version_number}']/region[@name='{region_name}']"
    )
    # Поиск хоста
    host_element = region_element.find(".//host[@name='{}']".format(host_name))
    if host_element is not None:
        # Удаление хоста из раздела
        region_element.remove(host_element)

        # Сохранение XML-файла с pretty print
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        formatted_xml_str = "\n".join([line for line in xml_str.split("\n") if line.strip()])

        # Сохранение отформатированного XML-файла без добавления пустых строк
        with open(xml_file_path, 'w') as file:
            file.write(formatted_xml_str)

    return redirect('/management')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5099)
