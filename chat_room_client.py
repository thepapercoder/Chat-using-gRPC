import grpc
import chat_room_pb2
import chat_room_pb2_grpc



def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = chat_room_pb2_grpc.ChatRoomStub(channel)

if __name__ == '__main__':
    run()