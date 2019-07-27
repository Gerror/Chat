import threading
import socket
import database


class Server(object):
    def __init__(self):
        self.host = '192.168.0.101'
        self.port = 9000
        
        self.quit = False #Отвечает за то, выключили ли сервер

        self.db = database.DataBase()

        self.onlineUsers = [] #Список онлайн пользователей (идентификатор,сокет)

        self.threads = [] #Список активных потоков
        
        #Begin: Создаем сокет для прослушивания
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(32)
        #End    

    def Start(self):
        #Begin: Создаем поток для прослушивания
        thread_listen = threading.Thread(target = self.Listen)
        thread_listen.start()
        self.threads.append(thread_listen)
        #End

    def Listen(self): #Метод для обработки входящих клиентов
        try:
            while not self.quit:
                client, addr = self.server_socket.accept() 
                clientUsnmCode = client.recv(1024)          #Запрашиваем никнейм пользователя
                clientUsnm = clientUsnmCode.decode('utf8')  #Декодируем никнейм пользователя
                clientId = self.db.GetUserId(clientUsnm)    #Получаем идентификатор зашеднего пользователя

                if(clientId == -1):                         #Если пользователь новый, то добавим его в базу
                    clientId = self.db.AddUser(clientUsnm)

                self.onlineUsers.append((clientId, client)) #Добавляем пользователя в список онлайн

                print("['" + clientUsnm + "' has connected!]")  #Debug

                #Begin: Приветствуем пользователя
                wlcmMsg = ('\n[Server]: Hello, ' + clientUsnm +\
                '\n*ChangeChat if you want to change the chat;' +\
                '\n*CreateChat if you want to create a chat;' +\
                '\n*ChatList if you want to see your chat list;' +\
                '\n*GetChatMessage if you want to see the last 10 messages in the current chat' +\
                '\n*Stop if you want to exit\n')
                client.send(wlcmMsg.encode("utf8"))
                #End: Приветствуем пользователя

                #Begin: Посылаем пользователю список его чатов
                clientChats = self.db.GetChatList(clientId)
                if(clientChats == -1 or len(clientChats) == 0):
                    client.send("None".encode("utf8"))
                else:
                    clientChatsName = []
                    msg = ''
                    for chat in clientChats:
                        msg += 'Id: ' + str(chat[0]) + ' Name: ' + chat[1] + '\n'
                    client.send(msg.encode("utf8"))
                #End: Посылаем пользователю список его чатов
                        
                #Begin: Создаем потоки для работы с каждым клиентом
                thread_client = threading.Thread(target = self.WorkWithClient, \
                args = (client, clientUsnm, clientId))
                thread_client.start()
                self.threads.append(thread_client)
                #End: Создаем потоки для работы с каждым клиентом
        except:
            pass

    def WorkWithClient(self, client, clientUsnm, clientId):   #Метод для работы с клиентами
        try:
            while not self.quit:
                recvMsg = client.recv(1024)         #Прочитали сообщение пользователя
                recvMsg = recvMsg.decode("utf8")    #Декодировали сообщения
                
                #Begin: Проверяем сообщение на случай служебных команд
                if(recvMsg == "*CreateChat"):
                    trueReq = True                  #Переменная, отвечающая за истинность запроса
                    recvMsg = client.recv(1024)     #Считываем имя чата и пользователей
                    recvMsg = recvMsg.decode("utf8") 
                    recvMsg = recvMsg.split()
                    chName = recvMsg[0]              #Имя чата
                    recvMsg = recvMsg[1:]            #Пользователи
                    usIds = [clientId]               #Список пользователей, которых нужно добавить в чат
                    
                    #Begin: Добавляем идентификаторы пользователей
                    for us in recvMsg:
                        usId = self.db.GetUserId(us)
                        if(usId == -1):              #Выдаем ошибку, если такого пользователя нет
                            msg = "[Server]: Invalid request! One user does not exist!"
                            print(msg)
                            client.send(msg.encode("utf8"))
                            trueReq = False
                            break
                        else:                         #Добавляем пользователя, если он существует
                            usIds.append(usId)
                    #End: Добавляем идентификаторы пользователей

                    if(trueReq):
                        chId = self.db.AddChat(chName, usIds)
                        if(chId != -1):
                            msg = "[Server]: Chat created with id " + str(chId)
                            client.send(msg.encode("utf8"))
                        else: 
                            msg = "[Server]: Could not create chat"
                            client.send(msg.encode("utf8"))

                elif(recvMsg == "*ChatList"):
                    clientChats = self.db.GetChatList(clientId)
                    if(clientChats == -1 or len(clientChats) == 0):
                        client.send("None".encode("utf8"))
                    else: 
                        clientChatsName = []            #Список имен чатов клиента
                        msg = ''
                        for chat in clientChats:
                            msg += 'Id: ' + str(chat[0]) + ' Name: ' + chat[1] + "\n"
                        client.send(msg.encode("utf8"))

                elif(recvMsg == "*GetChatMessage"): 
                    msgCount = 10                       #Число сообщений, которое отправим
                    recvMsg = client.recv(64)           #Получить id чата
                    recvMsg = recvMsg.decode("utf8")
                    msgList = self.db.GetChatMessage(int(recvMsg)) 
                    if(len(msgList) == 0):
                        client.send("\nNone".encode("utf8"))
                        continue
                    if(len(msgList) < 10):
                        msgCount = len(msgList)
                    msgList = msgList[len(msgList)-msgCount:] #Обрезаем список до msgCount сообщений
                    
                    chatName = self.db.GetChatName(recvMsg) 
                    msg = ''                                  #Идентифицируем сообщение
                    for tmsg in msgList:
                        username = self.db.GetUserName(tmsg[2])
                        msg += "[" + chatName + "] [" + username + "]: " + tmsg[3] + "\n"
                    client.send(msg.encode("utf8"))
                #End: Проверяем сообщение на случай служебных команд
                
                else:   #Отправляем сообщение в чат. Сообщение имеет вид "id*text"
                    chId = recvMsg[:recvMsg.find("*")]
                    recvMsg = recvMsg[recvMsg.find("*") + 1:]
                    self.SendChatMessage(chId, clientId, recvMsg)
        except:
            for us in self.onlineUsers:
                if(us[0] == clientId):
                    self.onlineUsers.remove(us)
                    print("['" + clientUsnm + "' has disconnected!]")
                    break

    def SendChatMessage(self, chId, usId, msg, nocheck = True, chatUsers = 0): #Метод для отправки сообщения в чат
        try:
            if(nocheck == True):
                chatUsers = self.db.GetChatUsers(chId)
            chatName = self.db.GetChatName(chId)        #Название чата в которое прислали сообщение
            username = self.db.GetUserName(usId)        #Никнейм отправителя
            if(chatUsers == -1 or chatName == -1 or username == -1):        
                return -1
            answer = self.db.AddMessage(chId, usId, msg)
            if(answer == -1):
                return -1

            #Begin: Отправляем сообщения тем, кто онлайн
            for us in chatUsers:
                i = 0
                onlineUsersLen = len(self.onlineUsers) 
                while i < onlineUsersLen:
                    if(self.onlineUsers[i][0] != usId and (self.onlineUsers[i][0] == us)):
                        msgFinal = "[" + chatName + "] [" + username + "]: " + msg
                        self.onlineUsers[i][1].send(msgFinal.encode("utf8"))
                    i += 1
            #End: Отправляем сообщение тем кто онлайн
            return answer
        except:
            return -1

    def Stop(self):
        self.quit = True
        self.server_socket.close()
        
        for us in self.onlineUsers:
            us[1].close()

        for th in self.threads:
            th.join()
