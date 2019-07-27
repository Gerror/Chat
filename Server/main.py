import threading
import chatserver
from flask import Flask, jsonify, request

app = Flask(__name__)

def main():
    server = chatserver.Server()
    thread_server = threading.Thread(target = server.Start())
    thread_server.start()

    #Begin: API
    @app.route('/users/add', methods = ['POST'])
    def users_add(): #Добавляем пользователя
        try:
            data = request.get_json()
            answer = server.db.AddUser(data['username'])
            if(answer == -1):
                return "\n422 Unprocessable Entity"
            answer = '\n' + str(answer)
            return answer
        except:
            return "\n400 Bad Request"

    @app.route('/chats/add', methods = ['POST'])
    def chats_add(): #Добавляем чат
        try:
            data = request.get_json()
            chName = data['name']
            users = [int(us) for us in data['users']]
            answer = server.db.AddChat(chName, users)
            if(answer == -1):
                return "\n500 Internal Server Error"
            answer = '\n' + str(answer)
            return answer
        except:
            return "\n400 Bad Request"

    @app.route('/messages/add', methods = ['POST'])
    def messages_add(): #Отправляем сообщение в чат
        try:
            data = request.get_json()
            chId = int(data['chat'])
            author = int(data['author'])
            text = str(data['text'])

            chatUsers = server.db.GetChatUsers(chId) #Получаем список пользователей в чате
            if(chatUsers == -1):
                return "\n400 Bad Request"
            
            userInChat = False  #Состоит ли отправитель в чате
            for us in chatUsers:
                if(us == author):
                    userInChat = True
            if not userInChat:
                return "\n400 Bad Request"
            
            answer = server.SendChatMessage(chId, author, text, False, chatUsers)
            if(answer == -1):
                return "\n500 Internal Server Error"
            answer = '\n' + str(answer)
            return answer
        except:
            return "\n400 Bad Request"

    @app.route('/chats/get', methods = ['POST'])
    def chats_get():    #Получаем список чатов пользователя
        try:
            data = request.get_json()
            usId = int(data['user'])
            answer = server.db.GetChatList(usId)
            if(answer == -1 or len(answer) == 0):
                return "\n422 Unprocessable Entity"
            return jsonify(answer)
        except:
            return "\n400 Bad Request"

    @app.route('/messages/get', methods = ['POST'])
    def messages_get():     #Получаем ВСЕ сообщения из чата
        try:
            data = request.get_json()
            chId = int(data['chat'])
            answer = server.db.GetChatMessage(chId)
            if(answer == -1 or len(answer) == 0):
                return "\n422 Unprocessable Entity"
            return jsonify(answer)
        except:
            return "\n400 Bad Request"
    #End: API

    r = app.run(host = 'localhost', port = 9000) #Примет None когда нажмем Ctrl+C

    if(r == None):  #Точка выхода из программы
        server.Stop()

if __name__ == '__main__':
    main()