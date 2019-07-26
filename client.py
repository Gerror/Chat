import socket
import time
import threading

class Client(object):
	def __init__(self):
		self.host = '192.168.0.101'
		self.port = 9000
		self.socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.quit = False
		self.curChat = 0
		self.clientChatsId = []
		self.lastMsg = 0

	def Start(self):				
		self.socket_client.connect((self.host, self.port))

		print("Enter your username:")
		self.username = input()
		self.socket_client.send(self.username.encode("utf8"))

		answHelp = self.socket_client.recv(1024)
		print(answHelp.decode("utf8"))

		print("Your chats:")
		answChats = self.socket_client.recv(5120)
		answChats = answChats.decode("utf8")
		print(answChats)
		if(answChats != "None"):
			answChats = answChats.split()
			answChatsLen = len(answChats)
			count = 1
			while count <= answChatsLen:
				self.clientChatsId.append(int(answChats[count]))
				count = count + 4

		self.thread_recv = threading.Thread(target = self.RecvMessage)
		self.thread_recv.start()

		self.SendMessage()

	def Stop(self):
		quit = True
		self.socket_client.close()
		self.thread_recv.join()

	def RecvMessage(self):
		try: #Здесь мы разрываем соединение
			while not self.quit:
				answ = self.socket_client.recv(1024)
				answ = answ.decode("utf8")
				print(answ)
				chName = answ[:answ.find(' ')]
				if(chName == '[Server]:'):
					try:
						answ = answ.split()
						newChat = int(answ[len(answ) - 1])
						if(answ[1] == 'Chat' and answ[2] == 'created'):
							self.clientChatsId.append(newChat)
					except:
						continue
		except:
			self.socket_client.close()
			print("Server disconnected! Please, enter *Stop.")

	def SendMessage(self):
		try:
			while not self.quit:
				msgNoChat = input()
				
				if(msgNoChat == "*Stop"):
					self.Stop()
					break

				elif(msgNoChat == "*ChangeChat"):
					print("Enter chat id:")
					inputId = int(input())

					if inputId not in self.clientChatsId:
						print("Bad id!")
					else:
						self.curChat = inputId
					continue
				elif(msgNoChat == "*CreateChat"):
					msg = ''
					
					self.socket_client.send("*CreateChat".encode("utf8"))
					print("Enter chat name:")
					chName = input()
					msg = msg + chName + ' '
					
					print("Enter usernames separated by a space:")
					usnames = input()
					msg = msg + usnames + ' '
					self.socket_client.send(msg.encode("utf8"))
					continue
				elif(msgNoChat == "*ChatList"):
					self.socket_client.send("*ChatList".encode("utf8"))
					continue
				elif(msgNoChat == "*GetChatMessage"):
					if(self.curChat == 0):
						print("Change chat!")
						continue
					self.socket_client.send("*GetChatMessage".encode("utf8"))
					self.socket_client.send(str(self.curChat).encode("utf8"))
					continue

				if(self.curChat == 0):
					print("Change chat!")
				else:
					msg = str(self.curChat) + '*' + msgNoChat
					self.socket_client.send(msg.encode("utf8"))
		except:
			pass


def  main():
	cl = Client()
	cl.Start()

if __name__ == '__main__':
	main()