import requests , logging, time, sched                  
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, base
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from bs4 import BeautifulSoup
from telegram.ext.callbackcontext import CallbackContext
from dotenv import dotenv_values

config = dotenv_values(".env")
token = config['token']

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

scheduler = sched.scheduler(time.time, time.sleep)

updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher

updater.start_webhook(listen="0.0.0.0",        
                        port=int(PORT),                       
                        url_path=token) 
  
updater.bot.setWebhook('https://prenota-bot-py.herokuapp.com/' + token) 


class lecture:
    def __init__(self, date=None, location=None, params=None) -> None:
        self.date = date,
        self.location = location
        self.params = params

    def generate_message(self):
        return self.date + " " + self.location

def time_string_to_unix(date, time_param):
    string = date + ' ' + time_param
    return time.mktime(time.strptime(string, "%d/%m/%Y %H:%M:%S"))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

login_url = "http://prenota.unior.it/studenti/main0.php"
book_url = "http://prenota.unior.it/studenti/ajax-dettaglio-domanda.php"
allLecturesUrl = "http://prenota.unior.it/studenti/main0.php?action=prenota&IdCorsoLaurea=94"

LECTURE, GET_DATE, GET_TIME = range(3)

login_data = {
    "username": "v.aversa2@studenti.unior.it",
    "password": "Pubqlts1",
    "login": "Login"
}

def book_course(params):
    res = requests.post(book_url, data=params)
    return res.text

def login():
    res = requests.post(login_url, data=login_data)
    return res.cookies.items()

def get_lectures():
    res = requests.get(allLecturesUrl, cookies={
        'STUDENTIPRENOTAcookieid': 'v.aversa2%40studenti.unior.it'
    })
    return res.text

def open_course(id):
    res = requests.post(book_url, data={
        "userid": "v.aversa2@studenti.unior.it",
        "IdModulo": str(id),
        "action": "dettagli_corso"
    })
    soup = BeautifulSoup(res.text, 'html.parser')
    tbody = soup.find('tbody')
    temp = None
    params = None
    for tr in tbody.find_all('tr'):
        if temp == None:
            for p in tr.find_all('p'):
                if p.find('a'):
                    if(type(p.find('a').attrs.get('title') != None and p.find('a').attrs.get('title').__contains__('disponibili'))):
                        if(p.find('a').attrs.get('title').__contains__('disponibili')): temp = tr
                        break
    if(temp != None):
        work = temp.find('a').attrs.get('href')
        start = work.find('(')
        end = work.find(')')
        params = work[start + 1:end].split(',')
    return params

cookie = login()
soup = BeautifulSoup(get_lectures(), 'html.parser')
all_courses_raw = soup.find_all(style="font-size: 1.1em; color: #A22E37;")
all_courses = []

for course in all_courses_raw:
    start = course.a.attrs['href'].find('(')
    end = course.a.attrs['href'].find(')')
    courseValue = course.a.attrs['href'][start + 1:end]
    all_courses.append(
        {'name': course.a.string, 'id': courseValue})

user_courses = []

for course in all_courses:
    if(course['name'].__contains__('Grimaldi Claudio')):
        user_courses.append(course)
    elif(course['name'].__contains__('Longobardi Ferdinando')):
        user_courses.append(course)
    elif(course['name'].__contains__('Librandi')):
        user_courses.append(course)
    elif(course['name'].__contains__('Capezio')):
        user_courses.append(course)
    elif(course['name'].__contains__("D'Anna")):
        user_courses.append(course)
    elif(course['name'].__contains__("I MC (A-L) (Kenawi")):
        user_courses.append(course)
    elif(course['name'].__contains__("I MC (A-L) (Alhusseini")):
        user_courses.append(course)
    elif(course['name'].__contains__("I-II MC/PR (Sarr")):
        user_courses.append(course)
    elif(course['name'].__contains__("I-II MC/PR (Sarr")):
        user_courses.append(course)
    
def start_book(update: Update, context: CallbackContext):
    format_courses = []
    for course in user_courses:
        message = course['name']
        format_courses.append(message)
    reply_keyboard = [format_courses]

    update.message.reply_text(
        'Ciao! Quale corso desideri prenotare?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Scegli quale corso prenotare'
        ),
    )
    return LECTURE

def lecture_show(update: Update, context: CallbackContext):
    for course in user_courses:
        if(course['name'] == update.message.text):
            context.user_data['lecture'] = course
            break
    update.message.reply_text(
        'Quando desideri che prenoti il corso "' + update.message.text +
        ' "? \n Immetere prima la data ES 09/11/2021',
        reply_markup=ReplyKeyboardRemove(),
    )
    return GET_DATE

def get_date(update: Update, context: CallbackContext):
    context.user_data['date'] = update.message.text
    update.message.reply_text(
        'A che ora vuoi che provi a prenotare? Es 02:30:00'
    )
    return GET_TIME

def book(id, context, update):
    fetch_params = open_course(id)
    if(fetch_params != None):
        params = {
            "userid": "v.aversa2@studenti.unior.it",
            "IdModulo": fetch_params[0][1:fetch_params[0].__len__() - 1],
            "dateP": fetch_params[1][1:fetch_params[1].__len__() - 1],
            "IdOrario": fetch_params[2][1:fetch_params[2].__len__() - 1],
            "numberP": fetch_params[3][1:fetch_params[3].__len__() - 1],
            "IdPrenotazione": fetch_params[4][1:fetch_params[4].__len__() - 1],
            "action": "prenota_corso"
        }
        book_course(params)
        logger.info('Sto provando a prenotare %s', context.user_data['lecture']['name'])
        update.message.reply_text('Sto provando a prenotare ' + context.user_data['lecture']['name'])
        update.message.reply_text('Lezione prenotata corretamente')
    else:
        logger.info('Error while booking')
        update.message.reply_text('Errore, probabilmente i posti erano esauriti.')

def get_time(update: Update, context: CallbackContext):
    context.user_data['time'] = update.message.text
    update.message.reply_text('Proverò a prenotare ' +
         context.user_data['lecture']['name'] + context.user_data['date'] + ' ' + context.user_data['time'])
    unix = time_string_to_unix(context.user_data['date'],context.user_data['time'])
    delta = unix - time.time()
    print(delta)
    scheduler.enter(delta, 0 ,book, argument=(context.user_data['lecture']['id'], context, update,))
    scheduler.run()
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Okay, prenotazione annullata.'
    )
    return ConversationHandler.END

booking_handler = ConversationHandler(
    entry_points=[CommandHandler('prenota', start_book)],
    states={
        LECTURE: [MessageHandler(Filters.text & ~Filters.command, lecture_show)],
        GET_DATE: [MessageHandler(Filters.text, get_date)],
        GET_TIME: [MessageHandler(Filters.text, get_time)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

dispatcher.add_handler(booking_handler)

updater.start_polling()
updater.idle()
