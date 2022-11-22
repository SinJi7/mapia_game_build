import threading

from mapia_core.Core import Game
import time
from datetime import datetime, timedelta

import asyncio
from flask import request

class Container(threading.Thread):
    """클래스 생성시 threading.Thread를 상속받아 만들면 된다"""
    __RoomValid = True #방 유효

    #오너 결정 추가 필요
    def __init__(self, name, func):
        #"""__init__ 메소드 안에서 threading.Thread를 init한다"""
        threading.Thread.__init__(self)
        
        #User Data
        self.__OWNER:str = ""
        self.__NAME:str = name
        self.__Users = {} # key is name
        
        self.__Game = None #Use Gaem class

        self.__emit = func 

        #임시데이터들 초기화 함수 필요
        self.__target_collect = []
    
    # def isRoomId(self, ID):
    #     return True if ID == self.__RoomID else False

    #tmp data 관리
    #게임 영역에서 작동한다
    def isTarget_CollectComplete(self) -> bool:
        return len(self.__target_collect) == len(self.__Users)

    def Target_clear(self) -> None:
        self.__target_collect.clear()
    
    ###########
    # 호출시 현재 타겟을 수집 하고 반환한다
    # sever.py send_target에 의존하고 있다.
    def Target_Colleting(self, type) -> list: #sever.py에서 호출해야 함
        self.__emit("get_target", {"type": type}, room=self.__NAME)
        time.sleep(1)

        if type == "vote":
            self.send_system_message("투표 결과를 수집합니다.")
        elif type == "night":
            self.send_system_message("밤이 되었습니다.")
        elif type == "afternoon":
            self.send_system_message("아침이 되었습니다.")
        
        #수집 기간 설정
        end_collect_time = datetime.now() + timedelta(seconds=3)
        while len(self.__target_collect) == len(self.__Game.getUserLive()):
            if end_collect_time <= datetime.now() : break

        res_targets = self.__target_collect[:]
        self.Target_clear()
        return res_targets

    def addTarget(self, target: dict):
        self.__target_collect.append(target)    
    
    def change_time(self):
        return self.__Game.change_time()
        
    def apply_target_to_game(self, time_type, targets) -> list:
        #직업 처리는 여기서 만들기
        res_messages = self.__Game.process_target(time_type, targets=targets)
        return res_messages

    ####################################
    #게임 시작 / 종료
    def startGameSetting(self) -> bool:
        self.__Game = Game(self.__Users)

        self.update_user_state()
        ##############################################
        self.__emit("game_start", {}, room=self.__NAME)
        #job setting, mapia join
        ##############################################

    def update_user_state(self):
        for user_dict in self.__Game.getUserLive():
            self.__Users[user_dict["name"]]["info"] = "alive" if user_dict["live"] else "Death"
        self.__emit("user_update", {"users": self.__userFilter("info")}, room=self.__NAME)

    def endGame(self) -> dict:
        game_res = self.__Game.end_game()
        self.__Game = None
        return game_res
    #####################################

    def getJob(self, user_name):
        return self.__Game.getPlayerJob(user_name=user_name)

    def isPlayGame(self) -> bool:
        return self.__Game != None 

    def isOwner(self, name:str) -> bool:
        return self.__OWNER == name #임시 코드
        
    def isMapiaUser(self, user_name):
        return self.__Game.isPlayerMapia(user_name=user_name)

    def isDeadUser(self, user_name):
        return self.__Game.isAlive() == False

    def isRoomMemberCount(self) -> bool:
        member_cnt = len([i for i in self.__Users])
        print(member_cnt)
        return True if (member_cnt < 6) else False

    def send_skill_result(self, user_name):
        message = self.__Game.get_skill_res(user_name)
        player_job = self.__Game.getPlayerJob(user_name=user_name)

        if player_job == "police":
            self.send_system_message(message=message, private=True)
        return

    #game 영역에서 private 옵션 사용 금지(게임 시작 유저에게 메세지가 간다)
    def send_system_message(self, message, private=False):
        body = {
            "room_name": self.__NAME,
            "user_name": "admin",
            "message": message
        }
        if private:
            self.__emit("message", body)
        else:
            self.__emit("message", body, to=self.__NAME)
        

    #parm: data{user_name, room_name, message}
    def sendMessage(self, data) -> None: #sever.py 에서 호출 해야함
        # self.__emit("message", data, to=self.__NAME)
        # return
        user_name = data["user_name"]
        
        if self.isPlayGame():
            if not self.__Game.isAlive():
                self.__emit("message", data, room=f"{self.__NAME}_dead")
                #dead user일 경우 밑으로 가지 않아야 한다.
            elif "afternoon" == self.__Game.getTime():
                self.__emit("message", data, to=self.__NAME)
            elif "night" == self.__Game.getTime() and self.__Game.isPlayerMapia(user_name):
                self.__emit("message", data, room=f"{self.__NAME}_mapia")
        else:
            self.__emit("message", data, to=self.__NAME) #게임 플레이 중이 아닐 경우
        return

    #False일 경우 객체 제거
    def isRoomValid(self) -> bool:
        return self.__RoomValid

    def doGame(self):
        #종료 조건
        win_msg = self.__Game.isEndGame()
        if win_msg:
            end_message = self.__Game.getPalyerToString() + f"\n{win_msg}"
            self.send_system_message(end_message)
            return True
        else:
            return False

    #원하는 키를 받아서 반환
    def __userFilter(self, *args):
        result_user_ls = []

        for user_naem_key in self.__Users:
            #user name is default key
            user = {}
            user["user_name"] = user_naem_key
            #if args is in UserKeys, add User dict 
            for get_key in args:
                if get_key in self.__Users[user_naem_key]:
                    user[get_key] = self.__Users[user_naem_key][get_key]

            result_user_ls.append(user)

        return result_user_ls


    def addUser(self, name):
        self.__Users[name] = {"info": "chat", "token":"no implement"}

        self.__emit("user_update", {"users": self.__userFilter("info")}, room=self.__NAME)


    def delUser(self, user_token):
        self.__User.pop(user_token)
    
    def isInUser(self, user_token):
        return True if user_token in self.__Users else False


def make_container_start(name, emit):
    container = Container(name, func=emit)
    #container.start()
    return container
    

