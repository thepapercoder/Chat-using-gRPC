import grpc
import time
import chat_room_pb2
import chat_room_pb2_grpc
from concurrent import futures
from itertools import islice


class Database(object):

    def __init__(self):
        super(Database, self).__init__()
        self.db = {}

    def get(self, key):
        if key in self.db:
            return self.db[key]
        else:
            return None

    def check_key(self, key):
        if key in self.db:
            return True
        else:
            return False

    def set(self, key, value):
        if key in self.db:
            self.db[key].append(value)
        else:
            self.db[key] = [value]


class UserDatabase(Database):

    def __init__(self):
        super(UserDatabase, self).__init__()

    def set(self, key, value):
        if key in self.db:
            return False
        else:
            self.db[key] = [value]

    def get_user_list(self, limit=10):
        return self._take(limit, self.db.items())

    @staticmethod
    def _take(n, interable):
        return list(islice(interable, n))


class MsgDatabase(Database):

    def __init__(self):
        super(MsgDatabase, self).__init__()

    def get_all_user_msg(self, user_name):
        return self.db[user_name]


class ChatRoomServicer(chat_room_pb2_grpc.ChatRoomServicer):

    def __init__(self):
        self.user_db = UserDatabase()
        self.msg_db = MsgDatabase()

    def RegisterUser(self, request, context):
        user_name = request.user_name
        response = self.user_db.set(user_name, {'user_name': user_name})
        if response:
            return chat_room_pb2.Response(res='Create user "%s" success' % user_name)
        else:
            return chat_room_pb2.Response(res='Username "%s" have already exist' % user_name)

    def ListUser(self, request, context):
        try:
            limit = int(request.limit)
        except ValueError:
            print('Parsing error')
            limit = 10
        for user in self.user_db.get_user_list(limit):
            yield chat_room_pb2.User(user_name=user['user_name'])

    def SendMsg(self, request_iterator, context):
        try:
            for message in request_iterator:
                msg = {
                    'sender': message.sender,
                    'reciver': message.reciver,
                    'msg': message.msg,
                    'time': message.time
                }
                self.msg_db.set(message.reciver, msg)
            return chat_room_pb2.Response(msg="OK")
        except:
            return chat_room_pb2.Response(msg="An error was occur")

    def ReceiveMsg(self, request, context):
        if self.msg_db.check_key(request.user_name):
            for msg in self.msg_db.get_all_user_msg():
                yield msg


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_room_pb2_grpc.add_ChatRoomServicer_to_server(ChatRoomServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            time.sleep(60 * 60 * 24)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()