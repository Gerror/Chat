import threading
import socket
import database

class Server(object):
	def __init__(self):
		self.host = '192.168.0.101' #Хост
		self.port = 9000 #Порт
		
		self.quit = False #Отвечает за то, выключили ли сервер

		self.db = database.DataBase() #Запускаем базу данных

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
				clientUsnmCode = client.recv(1024) #Запрашиваем никнейм пользователя
				clientUsnm = clientUsnmCode.decode('utf8') #Декодируем никнейм пользователя
				clientId = self.db.GetUserId(clientUsnm) #Получаем идентификатор зашеднего пользователя

				if(clientId == -1): #Если пользователь новый, то добавим его в базу
					clientId = self.db.AddUser(clientUsnm)

				self.onlineUsers.append((clientId, client)) #Добавляем пользователя в список онлайн

				print("['" + clientUsnm + "' has connected!]") #Debug

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

	def WorkWithClient(self, client, clientUsnm, clientId): #Метод для работы с клиентами
		try:
			while not self.quit:
				recvMsg = client.recv(1024) #Прочитали сообщение пользователя
				recvMsg = recvMsg.decode("utf8") #Декодировали сообщения
				#Begin: Проверяем сообщение на случай служебных команд
				if(recvMsg == "*CreateChat"): #Запрос на создание чата 
					trueReq = True #Переменная, отвечающая за истинность запроса
					recvMsg = client.recv(1024) #Считываем имя чата и пользователей
					recvMsg = recvMsg.decode("utf8") #Декодируем
					recvMsg = recvMsg.split() #Разбиваем в список
					chName = recvMsg[0] #Имя чата
					recvMsg = recvMsg[1:] #Пользователи
					usIds = [clientId] #Инициализируем идентификаторы пользователей, которых
									   #нужно добавить в чат, clientId - тот кто прислал запрос
					
					#Begin: Добавляем идентификаторы пользователей
					for us in recvMsg:
						usId = self.db.GetUserId(us) #Получаем идентификатор
						
						if(usId == -1): #Выдаем ошибку, если такого пользователя нет
							msg = "[Server]: Invalid request! One user does not exist!"
							print(msg)
							client.send(msg.encode("utf8"))
							trueReq = False
							break
						else: #Добавляем пользователя, если он существует
							usIds.append(usId)
					#End: Добавляем идентификаторы пользователей
					if(trueReq): #В случае, если все пользователи существуют, создаем чат
						chId = self.db.AddChat(chName, usIds) #Создаем чат
						if(chId != -1): #Если всё хорошо, посылаем идентификатор созданного чата
							msg = "[Server]: Chat created with id " + str(chId)
							client.send(msg.encode("utf8"))
						else: #Если что то пошло не так уведомляем об этом пользователя
							msg = "[Server]: Could not create chat"
							client.send(msg.encode("utf8"))

				elif(recvMsg == "*ChatList"): #Запрос на получение списка чатов пользователя
					clientChats = self.db.GetChatList(clientId) #Получаем список чатов
					if(clientChats == -1 or len(clientChats) == 0): #Если он пуст или ошибка
						client.send("None".encode("utf8"))
					else: #Если всё хорошо
						clientChatsName = [] #Список имен чатов клиента
						msg = ''
						for chat in clientChats: #Формируем список и отправляем его
							msg += 'Id: ' + str(chat[0]) + ' Name: ' + chat[1] + "\n"
						client.send(msg.encode("utf8"))

				elif(recvMsg == "*GetChatMessage"): #Получаем msgCount(10) последних сообщений чата
					msgCount = 10
					recvMsg = client.recv(64) #Получить id чата
					recvMsg = recvMsg.decode("utf8") #Декодировать id 
					msgList = self.db.GetChatMessage(int(recvMsg)) #Получаем список сообщений чата
					if(len(msgList) == 0):
						client.send("\nNone".encode("utf8"))
						continue
					if(len(msgList) < 10):
						msgCount = len(msgList)
					msgList = msgList[len(msgList)-msgCount:] #Обрезаем список до msgCount сообщений
					chatName = self.db.GetChatName(recvMsg) #Получаем имя чата
					msg = '' #Идентефицируем сообщение
					for tmsg in msgList: #Формируем сообщения
						username = self.db.GetUserName(tmsg[2]) #Получаем имя пользователя
						msg += "[" + chatName + "] [" + username + "]: " + tmsg[3] + "\n"
					client.send(msg.encode("utf8")) #Отправляем сообщения пользователю
				#End: Проверяем сообщение на случай служебных команд
				else: #Команда не служебная - Отправляем сообщение в чат. Сообщение имеет вид "id*text"
					chId = recvMsg[:recvMsg.find("*")] #Получаем идентификатор чата
					recvMsg = recvMsg[recvMsg.find("*") + 1:] #Получаем сообщение
					self.SendChatMessage(chId, clientId, recvMsg) #Отправляем сообщение в чат
		except:
			for us in self.onlineUsers:
				if(us[0] == clientId):
					self.onlineUsers.remove(us)
					print("['" + clientUsnm + "' has disconnected!]")
					break

	def SendChatMessage(self, chId, usId, msg, nocheck = True, chatUsers = 0): #Метод для отправки сообщения в чат
		try:
			if(nocheck == True):
				chatUsers = self.db.GetChatUsers(chId) #Получаем список пользователей в чате
			chatName = self.db.GetChatName(chId) #Получаем название чата в которое прислали сообщение
			username = self.db.GetUserName(usId) #Получаем никнейм отправителя
			if(chatUsers == -1 or chatName == -1 or username == -1): #Обрабатываем исключения
				return -1
			answer = self.db.AddMessage(chId, usId, msg) #Добавляем сообщение в базу
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

	def Stop(self): #Метод для остановки сервера
		self.quit = True
		self.server_socket.close() #Закрываем слушающий сокет
		
		for us in self.onlineUsers: #Закрываем сокеты
			us[1].close()

		for th in self.threads: #Закрываем потоки 
			th.join()
