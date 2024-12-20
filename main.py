import os
import csv
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from prettytable import PrettyTable

options = webdriver.ChromeOptions()
options.add_argument(fr'user-data-dir={os.getcwd()}\ChromeProfile')
options.add_argument("--headless")
browser = webdriver.Chrome(options=options)
timeout = 5
last_page = 0
data = [['id', 'dispatch_time', 'task', 'participant', 'compiler', 'verdict', 'points', 'execution_time', 'memory']]


def sign_in():
    try:
        login_field = browser.find_element(By.ID, 'passp-field-login')
        login_field.send_keys(input("Введите логин или почту: "))
        btn = browser.find_element(By.ID, 'passp:sign-in')
        btn.click()
        passwd_field = WebDriverWait(browser, timeout).until(ec.presence_of_element_located((By.ID, 'passp-field-passwd')))
        passwd_field.send_keys(input("Введите пароль: "))
        btn = browser.find_element(By.ID, 'passp:sign-in')
        btn.click()
        btn = WebDriverWait(browser, timeout).until(ec.presence_of_element_located((By.XPATH,
                                                                              '//*[@id="root"]/div/div[2]/div[2]/div/div/div[2]/div[3]/div/div/div/div[1]/form/div/div[3]/div/button')))
        btn.click()
        confirmation_code_field = WebDriverWait(browser, timeout).until(
            ec.presence_of_element_located((By.XPATH, '//*[@id="passp-field-phoneCode"]')))
        tooltip = browser.find_element(By.XPATH,
                                       '//*[@id="root"]/div/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/h1').text
        confirmation_code = input(f"{tooltip}: ")
        confirmation_code_field.send_keys(confirmation_code)
    except TimeoutException:
        print("Loading took too much time!")


def next_page():
    global last_page
    ul = WebDriverWait(browser, timeout).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="mount"]/div[2]/div[2]/main/div/div[3]/div[3]/ul')))
    for li in ul.find_elements(By.TAG_NAME, "li"):
        if li.text.isdigit():
            if last_page < int(li.text):
                try:
                    li.click()
                    last_page += 1
                    return True
                except ElementClickInterceptedException:
                    pass
        continue
    else:
        return False


if __name__ == "__main__":
    browser.get("https://admin.contest.yandex.ru/contests")
    if browser.current_url.startswith("https://passport.yandex.ru"):
        sign_in()

    WebDriverWait(browser, timeout).until(
        ec.presence_of_element_located((By.XPATH, '//*[@id="mount"]/div[2]/main/div[2]/div[2]/table/tbody')))
    soup = BeautifulSoup(browser.page_source, 'lxml')

    # Счетчик соревнований
    print(soup.find("div", attrs={"class": "pager__total-items-message"}).text)

    table = PrettyTable(("ID", "Название", "Дата начала", "Дата окончания", "Автор"))
    for tr in soup.find("tbody"):
        table.add_row([td.text for td in tr])
    print(table)
    contest_id = input("Введите id соревнования: ")
    browser.get(f"https://admin.contest.yandex.ru/contests/{contest_id}/submissions")
    # TODO
    # Переключение страниц и подгрузка данных
    while next_page():
        WebDriverWait(browser, timeout).until(
            ec.presence_of_element_located((By.XPATH, '//*[@id="mount"]/div[2]/div[2]/main/div/div[3]/div[2]/div/div/div[2]/div/table/thead')))
        soup = BeautifulSoup(browser.page_source, 'lxml')
        tbody = soup.find_all("tbody")[1]

        table = PrettyTable(['ID', 'Время отправки', 'Задача', 'Участник', 'Компилятор', 'Вердикт', 'Баллы', 'Время выполнения', 'Память'])
        for tr in tbody.find_all("tr", attrs={"class": "CompoundTable-TableRow CompoundTable-TableRow_type_body"}):
            row = [td.text for td in tr]
            row = row[:-1]
            table.add_row(row)
            row[0] = int(row[0])
            row[1] = datetime.strptime(row[1], '%d.%m.%y %H:%M:%S')
            row[6] = int(row[6]) if row[6] else None
            row[7] = (int(row[7].split()[0]) if row[7].split()[1] == 'мс' else float(row[7].split()[0]) * 1000) if row[6] else 0
            row[8] = float(row[8].split()[0]) if row[6] else 0
            data.append(row)
        print(table)
        print(f'стр. {last_page}\n')
    else:
        print("Страницы закончились. Сохранение...")

    with open(f'contest{contest_id}.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerows(data)

    print(f"Данные сохраненны в файл contest{contest_id}.csv")
