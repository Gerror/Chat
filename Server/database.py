import sqlite3
import time

class DataBase(object):
    def __init__(self):
        self.conn = sqlite3.connect("ChatServer.db", check_same_thread = False)
        self.cursor = self.conn.cursor()
        #Таблицу пользователей
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users
                            (id integer PRIMARY KEY, username text NOT NULL,
                            created_at text NOT NULL)"""
                            )
        #Таблица чатов
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS chats
                            (id integer PRIMARY KEY, name text NOT NULL,
                            created_at text NOT NULL)"""
                            )
        #Таблица чат_пользователь (Отношение многие-ко-многим)
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS chat_user (chat_id integer, user_id integer,
                            FOREIGN KEY (chat_id) REFERENCES chats(id)
                            FOREIGN KEY (user_id) REFERENCES users(id))"""
                            )
        #Таблицу сообщений
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS messages
                            (id integer PRIMARY KEY, chat integer NOT NULL,
                            author integer NOT NULL, msg text NOT NULL,
                            created_at text NOT NULL, FOREIGN KEY (author) REFERENCES users(id))"""
                            )

    def AddUser(self, usName):  #Добавить пользователя в базу
        try:
            if(self.GetUserId(usName) != -1):
                return -1
            req = (usName, time.strftime("%Y-%m-%d-%H.%M.%S",time.localtime()))
            self.cursor.execute("INSERT INTO users(username, created_at) VALUES (?,?)", req)
            self.conn.commit()
            usId = self.cursor.lastrowid
            return usId
        except:
            return -1

    def AddChat(self, chatName, chatUsersId): #Добавить чат в базу
        try:
            req = (chatName, time.strftime("%Y-%m-%d-%H.%M.%S",time.localtime()))
            self.cursor.execute("INSERT INTO chats(name, created_at) VALUES (?,?)", req)
            self.conn.commit()
            chId = self.cursor.lastrowid

            for usId in chatUsersId:
                req = (chId, usId)
                self.cursor.execute("INSERT INTO chat_user VALUES (?,?)", req)
                self.conn.commit()
            return chId
        except:
            return -1

    def AddMessage(self, chId, usId, msg):  #Добавить сообщение в базу 
        try:
            req = (chId, usId, msg, time.strftime("%Y-%m-%d-%H.%M.%S",time.localtime()))
            self.cursor.execute("""INSERT INTO messages(chat, author, msg, created_at)
                                VALUES (?,?,?,?)""", req
                                )
            self.conn.commit()
            msgId = self.cursor.lastrowid
            return msgId
        except:
            return -1

    def GetChatList(self, usId): #Получить список чатов пользователя
        try:
            req = """SELECT id, name, created_at
                    FROM (chats LEFT JOIN chat_user ON id = chat_id)
                    LEFT OUTER JOIN (SELECT chat, MAX(created_at) AS last_msg_time 
                    FROM messages GROUP BY chat) AS chmsg ON id = chmsg.chat 
                    WHERE id = chat_id AND user_id = """ + str(usId) + """ 
                    ORDER BY chmsg.last_msg_time DESC"""
            self.cursor.execute(req)
            chatList = self.cursor.fetchall()
            return chatList
        except:
            return -1

    def GetChatMessage(self, chId): #Получить список ВСЕХ сообщений чата
        try:
            req = "SELECT * FROM messages WHERE chat = " + str(chId) + " ORDER BY created_at"
            self.cursor.execute(req)
            msgList = self.cursor.fetchall()
            return msgList
        except:
            return -1 
        
    def GetChatUsers(self, chatId): #Получить идентификаторы пользователей чата
        try:
            req = "SELECT user_id FROM chat_user WHERE chat_id = " + str(chatId)
            self.cursor.execute(req)
            chatUsersIdTemp = self.cursor.fetchall()
            chatUsersId = []
            for chUs in chatUsersIdTemp:
                chatUsersId.append(chUs[0])
            return chatUsersId
        except:
            return -1

    def GetChatName(self, chatId):  #Получить имя чата по идентификатору
        try:
            req = "SELECT name FROM chats WHERE id = " + str(chatId)
            self.cursor.execute(req)
            chatName = self.cursor.fetchone()
            return chatName[0]
        except:
            return -1

    def GetUserId(self, username):  #Получить идентификатор пользователя по имени
        try:
            req = "SELECT id FROM users WHERE username = '" + username + "'"
            self.cursor.execute(req)
            userId = self.cursor.fetchone()
            return userId[0]
        except:
            return -1

    def GetUserName(self, usId):    #Получить имя пользователя по идентификатору
        try:
            req = "SELECT username FROM users WHERE id = " + str(usId)
            self.cursor.execute(req)
            usname = self.cursor.fetchone()
            return usname[0]
        except:
            return -1