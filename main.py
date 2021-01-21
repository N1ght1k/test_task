import os
import requests
from datetime import datetime
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


# Обрезание строки с названием задания если длина больше 48 символов
def cut_task_title(title):
    short_title = title
    if len(short_title) > 48:
        short_title = short_title[:48] + '...'
    return short_title


# Переименование старого файла по шаблону
def rename_file(name, path):
    with open(path, "r", encoding='utf-8') as file:
        line = file.readlines()[1]
    text_date = line.split('> ')[1].strip()   # Берем дату формирования отчета из 2 строки после символа '> '
    old_date = datetime.strptime(text_date, '%d.%m.%Y %H:%M')   # Преобразуем строку в дату
    new_date = old_date.strftime("%Y-%m-%dT%H:%M")  # Преобразуем дату в строку по шаблону
    new_filename = 'old_' + name[:-4] + '_' + new_date + '.txt'
    new_path_file = os.path.join("tasks", new_filename)
    os.rename(path, new_path_file)


# Формирование файла отчета
def write_file(path, company_name, name, email, completed_user_tasks, remaining_user_tasks):
    with open(path, "w", encoding='utf-8') as file:
        now = datetime.today()
        file.write('Отчёт для %s.\n' % company_name)
        file.write('%s <%s> %s\n' % (name, email, now.strftime("%d.%m.%Y %H:%M")))
        if len(completed_user_tasks) + len(remaining_user_tasks) > 0:
            file.write('Всего задач: %s\n\n' % (len(completed_user_tasks) + len(remaining_user_tasks)))
            if len(completed_user_tasks) > 0:
                file.write('Завершенные задачи (%s):\n' % len(completed_user_tasks))
                file.writelines("%s\n" % user_task for user_task in completed_user_tasks)
            else:
                file.write('У пользователя нет завершенных задач!!!\n')
            file.write('\n')
            if len(remaining_user_tasks) > 0:
                file.write('Оставшиеся задачи (%s):\n' % len(remaining_user_tasks))
                file.writelines("%s\n" % user_task for user_task in remaining_user_tasks)
            else:
                file.write('У пользователя нет оставшихся задач!!!')
        else:
            file.write('У пользователя нет задач!!!')


# Проверка на пустые позиции json с пользователями
def check_for_empty_users(user_data):
    if 'name' and 'username' and 'email' in user_data and 'name' in user_data['company']:
        if user_data['name'] and user_data['username'] and user_data['email'] and user_data['company']['name']:
            return True
    return False


# Проверка на пустые позиции json с задачами
def check_for_empty_tasks(task_data):
    if 'userId' and 'title' and 'completed' in task_data:
        if task_data['userId'] and task_data['title'] and type(task_data['completed']) == bool:
            return True
    return False


# Проверка на наличие папки tasks, если нет то создаем её
if not os.path.isdir('tasks'):
     os.mkdir('tasks')

url_users = 'https://json.medrating.org/users'
url_tasks = 'https://json.medrating.org/todos'

# Получаем json c API, делаем до 5 попыток через увеличивающийся интервал
s = requests.Session()

retries = Retry(total=5,
                backoff_factor=0.1,
                status_forcelist=[500, 502, 503, 504])

s.mount('https://', HTTPAdapter(max_retries=retries))

users = s.get(url_users).json()
tasks = s.get(url_tasks).json()

# Перебираем и проверяем полученные значения с API, наполняем списки задач по каждому пользователю,
# переименовываем файлы при необходимости, или добавляем новый отчет
for user in users:
    completed_tasks = []    # Список завершенных задач пользователя
    remaining_tasks = []    # Список незавершенных задач пользователя

    if check_for_empty_users(user):
        for task in tasks:
            if check_for_empty_tasks(task):
                if task['userId'] == user['id']:
                    if task['completed']:
                        completed_tasks.append(cut_task_title(task['title']))
                    else:
                        remaining_tasks.append(cut_task_title(task['title']))

        filename = '%s.txt' % user['username']
        path_file = os.path.join("tasks", filename)

        if os.path.exists(path_file):
            rename_file(filename, path_file)

        write_file(path_file, user['company']['name'], user['name'], user['email'], completed_tasks,
                   remaining_tasks)
