# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from telegram.ext import Updater, CommandHandler
import logging
import config
import dateparser
from datetime import datetime, time, timedelta


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def get_html(url):
    r = requests.get(url)
    return r.text


def get_all_links(html):
    soup = BeautifulSoup(html, 'lxml')
    matches = soup.find_all('div', class_='matche__score')
    urls = []
    for url in matches:
        u = url.find('a').get('href')
        urls.append('https://www.cybersport.ru' + u)
    return urls


def get_match_info(html):
    soup = BeautifulSoup(html, 'lxml')
    match_info = []
    tournament = soup.find('div', class_='duel__wrapper container').find('a').contents[0]
    tournament = ' '.join(tournament.split())
    match_time = soup.find('time').contents[0]
    match_time = ' '.join(match_time.split())
    match_time = dateparser.parse(match_time)
    if datetime.now()+timedelta(hours=24) <= match_time:
        return None
    match_time = str(match_time. strftime('%H:%M %d/%m/%y'))
    try:
        team1 = soup.find('div', class_='matche__team matche__team--left').find('span', class_='visible-xs--inline-block').contents[0]
    except AttributeError:
        team1 = 'TBD'
    try:
        team2 = soup.find('div', class_='matche__team matche__team--right').find('span', class_='visible-xs--inline-block').contents[0]
    except AttributeError:
        team2 = 'TBD'
    tbd1 = soup.find('div', class_='duel__team duel__team--left ').find('h2').contents[0]
    tbd2 = soup.find('div', class_='duel__team duel__team--right ').find('h2').contents[0]
    if tbd1 == 'TBD':
        team1 = 'TBD'
    if tbd2 == 'TBD':
        team2 = 'TBD'
    match_info.append(tournament)
    match_info.append(match_time)
    match_info.append(team1)
    match_info.append(team2)
    return match_info


def crawler():
    links = get_all_links(get_html(config.url))
    today_matches = []
    for l in links:
        today_matches.append(get_match_info(get_html(l)))
    return today_matches


def start():
    pass


def post(bot, update):
    print('post')
    get_matches = crawler()
    today_matches = {}
    for match in get_matches:
        if match[0] in today_matches:
            today_matches[match[0]].append(match[1:])
        else:
            today_matches[match[0]] = [match[1:]]
    today_matches_markdown = str('Матчи на ближайшие сутки: \n\n')
    for match in today_matches.items():
        matches = str()
        for m in match[1]:
            matches += m[0] + ' ' + m[1] + ' vs ' + m[2] + '\n'
        today_matches_markdown += '*' + match[0] + '*:\n' + matches + "\n"
    bot.send_message(chat_id=config.chat_id, text=today_matches_markdown, parse_mode='Markdown')


def main():
    updater = Updater(config.token)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("post", post))
    dp.add_error_handler(error)
    updater.start_webhook(listen="0.0.0.0",
                          port=config.port,
                          url_path=config.token)
    updater.bot.set_webhook(config.bot_url + config.token)

    now = datetime.now()
    now_time = now.time()
    job_queue = updater.job_queue
    if time(5, 30) <= now_time <= time(7, 30):
        job = job_queue.run_once(post, 0)
    updater.idle()


if __name__ == '__main__':
    main()