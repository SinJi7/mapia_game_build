from datetime import datetime, timedelta
from random import randint

import time


#######
#게임 종류에 따라 교체가능한, 직업함수

#Users는 참조

#######

#역할은?
class Game:
  __game_players: list = []
  __game_time: dict

  __tmp_vote_user:str = None
  __tmp_job_message = {
    "mapia" : "",
    "citizen" : "",
    "police" : "",
    "doctor" : ""
  }
  #initializer area

  #parm 유저 식별자(이름)
  def __init__(self, playerDict:dict):
    playerIds = [i for i in playerDict] 
    rand_jobs :list = self.__makeRandomJob(len(playerIds))

    self.__set_game_time("afternoon") #{ "time" : "aftermoon", "next" : datetime.now() + timedelta(seconds=90)}

    for idx in range(len(playerIds)):
      self.__game_players.append({"name": playerIds[idx], "job_name": rand_jobs[idx], "live": True})

    #self.jobls = [Player(playerIds[i], rand_jobs[i]) for i in range(len(playerIds))]

  #player count
  #return: random job list [mapia... citizen]
  #parm: playerCount(player count), mapia_count: default 2
  def __makeRandomJob(self, playerCount:int, mapia_count:int = 2):
    POLICE_CNT = 1
    CITIZEN_CNT = playerCount - mapia_count - POLICE_CNT
    base_job_ls = ["mapia" for _ in range(mapia_count)] + ["police"] + ["citizen" for _ in range(CITIZEN_CNT)]
    
    rand_job_ls = [base_job_ls.pop(randint(0, i-1)) for i in range(len(base_job_ls), 0, -1)]
    return rand_job_ls # [mapia... citizen]

  #param: find_user_name
  #return: user_dict
  def __findUser(self, find_user_name) -> dict:
    #if can't find user, return this
    base = {"name": "null", "job_name": "citizen", "live": False}

    if find_user_name == "base":
      return base
      
    for user_dict in self.__game_players:
      if user_dict["name"] == find_user_name:
        base = user_dict
    return base

  #getter
  def get_skill_res(self, user_name) -> str:
    job_name = self.getPlayerJob(user_name=user_name)
    message = self.__tmp_job_message[job_name]
    return message

  def getUserLive(self) -> list:
    return [{"name" : player_dict["name"], "live" : player_dict["live"]} for player_dict in self.__game_players]

  def getTime(self):
    return self.__game_time["time"]
    
  def getPalyerToString(self):
    res = [f"Name: {user['name']} job_name: {user['job_name']}" for user in self.__game_players]
    return "\n".join(res)

  def getPlayerJob(self, user_name):
    user_obj = self.__findUser(user_name)
    return user_obj["job_name"]

  def isPlayerMapia(self, user_name):
    user_obj:dict = self.__findUser(user_name)
    return "mapia" == user_obj["job_name"]

  def isAlive(self, user_name):
    return self.__findUser(user_name)["live"]

  #game control

  def isVoteTime(self):
    if self.__game_time["time"] == "aftermoon" and self.__game_time["next"] <= datetime.now():
      return True

  def isEndGame(self):  
    mapia = 0
    citizen = 0
    for user in self.__game_players:
      mapia += 1 if user["job_name"] == "mapia" and user["live"] else 0 #마피아인 유저수
      citizen += 1 if user["job_name"] != "mapia" and user["live"] else 0 #마피아가 아닌 유저 수

    print(f"마피아 유저수: {mapia}, 시민 수: {citizen}")
    
    if mapia == 0:
      return "시민승리"
    elif citizen == 0:
      return "마피아 승리"
    else:
      return False

  #############################################
  #private game control
  #############################################

  def __kill_the_player(self, user_name) -> None:
    if "user_name" == "base": return
    for user_dict in self.__game_players:
      if user_name == user_dict["name"]:
        user_dict["live"] = False

  #setter
  def __set_game_time(self, time_type:str) -> None:
    #time_type_seconds:dict = {"afternoon": 120,"night": 60,"vote": 20}
    time_type_seconds:dict = {"afternoon": 60,"night": 20,"vote": 40}
    next_second = time_type_seconds[time_type]

    self.__game_time = {
      "time":time_type, 
      "next" : datetime.now() + timedelta(seconds=next_second)
    }

  ##############################################
  #Staging Code
  ##############################################

  #득표율 반환
  def __get_mode_user(self, targets, filter_job=False):
    if filter_job:
      check_job = lambda send_name : self.__findUser(send_name)["job_name"] == filter_job
      vote_user = [target["target_name"] for target in targets if check_job(target["send_name"])]
    else: 
      vote_user = [target["target_name"] for target in targets]

    if not vote_user: return {"base" : 0} #타켓이 없을 경우

    vote_target:list = list(set(vote_user))
    vote_count:dict = {target_name : vote_target.count(target_name) for target_name in vote_target}
    #
    return vote_count # {user_name: count, user_name: count} 득표율? 반환


  #사형 여부 판단
  def __process_vote(self, targets):
    vote_count = self.__get_mode_user(targets=targets)
    election_user = max(vote_count.keys(), key=(lambda x : vote_count[x]))

    #동점자 확인 (빈 리스트 활용)
    if [count for count in vote_count if vote_count[election_user] == count]:
      return f"동점자가 존재합니다. {self.__tmp_vote_user} 생존"

    if self.__tmp_vote_user == election_user:
      self.__kill_the_player(election_user)
      if self.isPlayerMapia(election_user):
        return f"{election_user} 사망 [{election_user}님은 마피아 입니다]"
      else:
        return f"{election_user} 사망 [{election_user}님은 마피아가 아닙니다]"
    return f"{self.__tmp_vote_user} 생존"
  
  #사형 대상 투표
  def __process_afternoon_vote(self, targets):
    vote_count = self.__get_mode_user(targets=targets)
    election_user = max(vote_count.keys(), key=(lambda x : vote_count[x]))
    self.__tmp_vote_user = election_user
    return f"{self.__tmp_vote_user} 님이 투표에 의해 재판이 진행됩니다."
    
  def __process_classic_job(self, targets):
    vote_count_mapia = self.__get_mode_user(targets=targets, filter_job="mapia")
    vote_count_police= self.__get_mode_user(targets=targets, filter_job="police")
    election_user_mapia = max(vote_count_mapia.keys(), key=(lambda x : vote_count_mapia[x]))
    election_user_police = max(vote_count_police.keys(), key=(lambda x : vote_count_police[x]))

    #경찰처리
    police_msg = "마피아 입니다" if self.isPlayerMapia(election_user_police) else "마피아가 아닙니다."
    self.__tmp_job_message["police"] = f"{election_user_police}님은 {police_msg}"
    #마피아 처리
    self.__kill_the_player(election_user_mapia)
    return f"{election_user_mapia} 사망 [마피아의 총에 맞았습니다]]"

  #타켓 처리함수
  def process_target(self, time_type, targets: dict):
    effetive_target:list = []

    for target_dict in targets:
      user_info:dict = self.__findUser(target_dict["send_user_name"])

      alive = user_info["live"]

      job_name = user_info["job_name"]
      send_name = target_dict["send_user_name"]
      target_name = target_dict["target_user_name"]

      if alive: #생존유저 필터링
        effetive_target.append({
          "send_name" : send_name,
          "job_name" : job_name,
          "target_name" : target_name
        })
    
    #res에서는 메세지를 반환 받아야함
    res = ""
    if time_type == "afternoon":
      res = self.__process_classic_job(effetive_target)
    if time_type == "vote":
      res = self.__process_afternoon_vote(effetive_target)
    if time_type == "night":
      res = self.__process_vote(effetive_target)
    return res

  #function: time check, change time
  def change_time(self):
    def get_next(now_time):
      TIME_LS = ["afternoon","vote","night"]
      now_idx = TIME_LS.index(now_time)
      return TIME_LS[(now_idx + 1) % 3]
    
    #if now time is change time, call setter
    if datetime.now() >= self.__game_time["next"]:

      next_time:str = get_next(self.__game_time["time"])

      self.__set_game_time(time_type=next_time)
      return next_time
    else: 
      return False
  ##############################################

