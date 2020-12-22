# =============================================================================
# >> IMPORTS
# =============================================================================
from colors import GREEN,RED,YELLOW, WHITE
from cvars import ConVar
from engines.precache import Model
from engines.sound import Sound
from entities.entity import Entity
from events import Event
from events.hooks import PreEvent
from filters.players import PlayerIter
from listeners import OnClientActive, OnClientDisconnect, OnEntityCreated
from listeners.tick import Delay, Repeat
from messages import HudMsg
from messages.base import SayText2
from players.entity import Player
from players.helpers import playerinfo_from_index
import random


# =============================================================================
# >> GLOBAL VARS
# =============================================================================
catcher = {}
game_active = 0

# =============================================================================
# >> CONFIG
# =============================================================================

round_end_time = 5
round_start_time = 10
round_duration = 180

catcher_color = RED

YAY_SOUND = Sound('source-python/catch/yay.wav',download=True)

BOO_SOUND = Sound('source-python/catch/boo.wav',download=True)

CATCH_MODEL = Model('models/combine_soldier.mdl')

# =============================================================================
# >> LISTENERS
# =============================================================================
for player in PlayerIter():
    catcher[player.userid] = 0

# =============================================================================
# >> LISTENERS
# =============================================================================
@OnClientActive
def on_client_active(index):
    catcher[Player(index).userid] = 0
    if _get_player_count() == 2:
        global game_active
        game_active = 1
        _start_countdown(round_start_time)
        
@OnClientDisconnect
def on_client_disconnect(index):
    player = Player(index)
    if catcher[player.userid] == 1:
        _stop_round()
        Delay(1.0, _reset_round)
    if _get_player_count() == 2:
        _stop_round()
    
@OnEntityCreated
def on_entity_created(entity):
    if "weapon_" in entity.classname and entity.classname != "weapon_crowbar":
        entity.remove()
    
# =============================================================================
# >> EVENTS
# =============================================================================
@PreEvent('player_hurt')
def _pre_player_hurt(ev):
    victim = Player.from_userid(ev['userid'])
    if ev['attacker'] != 0:
        victim.health = 100
    if ev['attacker']:
        if ev['attacker'] != ev['userid']:
            attacker = Player.from_userid(ev['attacker'])
            if catcher[attacker.userid] == 1:
                if attacker.active_weapon.classname in ['weapon_crowbar','weapon_stunstick']:
                    catch(attacker.userid,victim.userid)
                    
def client_command(userid, __cmd__):
	engine_server.client_command(edict_from_userid(userid), __cmd__)
        
@Event('player_spawn')
def _player_spawn(ev):
    player = Player.from_userid(ev['userid'])
    player.delay(0.1,strip,(player.userid,))
    player.color = WHITE
    set_runner_model(player.index)
    

# =============================================================================
# >> FUNCTIONS
# =============================================================================
@Repeat
def _show_catcher():
    global game_active
    if game_active == 1:
        if _get_catcher():
            catch_player = Player.from_userid(_get_catcher())
            HudMsg(
                message="%s is the catcher" % catch_player.name,
                x=-1,
                y=0.03,
                color1=GREEN,
                color2=GREEN,
                effect=2,
                fade_in=0.01,
                fade_out=1.5,
                hold_time=0.5,
                fx_time=1.0,
                channel=1,
            ).send()
_show_catcher.start(0.5)

def _show_timeleft(duration):
    global game_active
    if game_active == 1:
        if _get_catcher():
            minutes, seconds = divmod(duration, 60)
            if minutes:
                HudMsg(
                    message="%s Minutes and %s Seconds remaining" % (minutes,seconds),
                    x=-1,
                    y=0.07,
                    color1=GREEN,
                    color2=GREEN,
                    effect=2,
                    fade_in=0.01,
                    fade_out=1.5,
                    hold_time=1.0,
                    fx_time=1.0,
                    channel=2,
                ).send()
            else:
                HudMsg(
                    message="%s Seconds remaining" % (seconds),
                    x=-1,
                    y=0.07,
                    color1=GREEN,
                    color2=GREEN,
                    effect=2,
                    fade_in=0.01,
                    fade_out=1.5,
                    hold_time=1.0,
                    fx_time=1.0,
                    channel=2,
                ).send()        
            if duration > 0:
               Delay(1.0, _show_timeleft,(duration-1,))
            else:
                _end_round()


def strip(userid):
    player = Player.from_userid(userid)
    entity = Entity.create('player_weaponstrip')
    entity.strip(activator=player)
    entity.remove()
    player.give_named_item('weapon_crowbar')
    
def set_runner_model(index):
    rand = random.choice([1,2])
    if rand == 1:
        random_model = random.randrange(1,7)
        Player(index).model = Model('models/humans/group03/female_0%s.mdl' % random_model)
    if rand == 2:
        random_model = random.randrange(1,9)
        Player(index).model = Model('models/humans/group03/male_0%s.mdl' % random_model)


def choose_catcher():
    global game_active
    if game_active == 1:
        player_list = []
        for player in PlayerIter('alive'):
            player_list.append(player.userid)
        random_player = Player.from_userid(random.choice(player_list))
        random_player.color = catcher_color
        random_player.model = CATCH_MODEL
        catcher[random_player.userid] = 1
        SayText2("\x04[Catch] %s \x03is the \x04first catcher!" % random_player.name).send()
        HudMsg(
            message="%s is the first catcher!\n\nRun away to stay alive." % random_player.name,
            x=-1,
            y=-0.5,
            color1=GREEN,
            color2=GREEN,
            effect=2,
            fade_in=0.01,
            fade_out=1.5,
            hold_time=4.0,
            fx_time=1.0,
            channel=0,
        ).send()
        _show_timeleft(round_duration)
    
def catch(attacker,victim):
    global game_active
    if game_active == 1:
        catcher[attacker] = 0
        catcher[victim] = 1
        player = Player.from_userid(victim)
        player.color = catcher_color
        player.model = CATCH_MODEL
        attacker = Player.from_userid(attacker)
        attacker.color = WHITE
        set_runner_model(attacker.index)
        SayText2("\x04[Catch] %s \x03is the \x04new catcher!" % player.name).send()
        HudMsg(
            message="%s catched %s!\n\nHe is the new catcher." % (attacker.name,Player.from_userid(victim).name),
            x=-1,
            y=-0.5,
            color1=GREEN,
            color2=GREEN,
            effect=2,
            fade_in=0.01,
            fade_out=1.5,
            hold_time=2.0,
            fx_time=1.0,
            channel=0,
        ).send()
    
    
def _end_round():
    global game_active
    if game_active == 1:
        player = Player.from_userid(_get_catcher())
        player.take_damage(10000)
        BOO_SOUND.play(player.index)
        for winning_players in PlayerIter():
            if catcher[winning_players.userid] == 0:
                YAY_SOUND.play(winning_players.index)
        _start_end_countdown(player.userid,round_end_time)
        catcher[player.userid] = 0
        player.color = WHITE
        HudMsg(
                message="",
                x=-1,
                y=0.07,
                color1=GREEN,
                color2=GREEN,
                effect=2,
                fade_in=0.01,
                fade_out=1.5,
                hold_time=1.0,
                fx_time=1.0,
                channel=2,
            ).send()
        HudMsg(
                message="",
                x=-1,
                y=0.07,
                color1=GREEN,
                color2=GREEN,
                effect=2,
                fade_in=0.01,
                fade_out=1.5,
                hold_time=1.0,
                fx_time=1.0,
                channel=1,
            ).send()
            
def _stop_round():
    global game_active
    if game_active == 1:
        game_active = 0
        player = Player.from_userid(_get_catcher())
        if _get_catcher():
            catcher[player.userid] = 0
        HudMsg(
                message="",
                x=-1,
                y=0.07,
                color1=GREEN,
                color2=GREEN,
                effect=2,
                fade_in=0.01,
                fade_out=1.5,
                hold_time=1.0,
                fx_time=1.0,
                channel=2,
            ).send()
        HudMsg(
                message="",
                x=-1,
                y=0.07,
                color1=GREEN,
                color2=GREEN,
                effect=2,
                fade_in=0.01,
                fade_out=1.5,
                hold_time=1.0,
                fx_time=1.0,
                channel=1,
            ).send()
        HudMsg(
                message="",
                x=-1,
                y=0.07,
                color1=GREEN,
                color2=GREEN,
                effect=2,
                fade_in=0.01,
                fade_out=1.5,
                hold_time=1.0,
                fx_time=1.0,
                channel=0,
            ).send()
            
def _start_end_countdown(userid,countdown):
    global game_active
    if game_active == 1:
        player = Player.from_userid(userid)
        HudMsg(
            message="%s couldn't catch up!\n\nNext round starts in %s seconds." % (player.name,countdown),
            x=-1,
            y=-0.5,
            color1=GREEN,
            color2=GREEN,
            effect=2,
            fade_in=0.01,
            fade_out=1.5,
            hold_time=1.5,
            fx_time=1.0,
            channel=0,
        ).send()
        if countdown > 0:
            Delay(1.0,_start_end_countdown,(userid,countdown-1))
        else:
            ConVar('mp_restartgame').set_float(1.0)
            Delay(2.5,_start_countdown,(round_start_time,))
            HudMsg(
            message="",
            x=-1,
            y=-0.5,
            color1=GREEN,
            color2=GREEN,
            effect=2,
            fade_in=0.01,
            fade_out=1.5,
            hold_time=1.5,
            fx_time=1.0,
            channel=0,
            ).send()
            for player in PlayerIter():
                catcher[player.userid] = 0
        
def _start_countdown(countdown):
    global game_active
    if game_active == 1:
        HudMsg(
            message="Preparing new round!\n\nFirst catcher will be chosen in %s seconds." % (countdown),
            x=-1,
            y=-0.5,
            color1=GREEN,
            color2=GREEN,
            effect=2,
            fade_in=0.01,
            fade_out=1.5,
            hold_time=1.5,
            fx_time=1.0,
            channel=0,
        ).send()    
        if countdown > 0:
            Delay(1.0,_start_countdown,(countdown-1,))
        else:
            choose_catcher()
    
def _start_round():
    global game_active
    if game_active == 1:
        _start_countdown(round_start_time)
        
def _reset_round():
    global game_active
    game_active = 1
    _start_countdown(round_start_time)
    
def _get_catcher():
    for player in PlayerIter():
        if catcher[player.userid] == 1:
            return player.userid
            
def _get_player_count():
    count = 0
    for player in PlayerIter():
        count += 1
    return count
