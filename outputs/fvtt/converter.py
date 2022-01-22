import os
import random

from math import floor
import string
from extractor import constants

from configparser import ConfigParser
from logging import Logger
from extractor.creature_schema import SpellcastingSchema

from outputs.fvtt.types import CompendiumTypes
from outputs.fvtt.compendium_loader import CompendiumLoader

from extractor.creature import Creature

from typing import Any

class FVTTConverter(object):

    __SIZEMAP = {
        constants.SIZES.tiny.name: "tiny",
        constants.SIZES.small.name: "sm",
        constants.SIZES.medium.name: "med",
        constants.SIZES.large.name: "lg",
        constants.SIZES.huge.name: "huge",
        constants.SIZES.gargantuan.name: "grg"
    }

    __SKILLSMAP = {
        constants.SKILLS.acrobatics.name: "acr",
        constants.SKILLS.animal_handling.name: "ani",
        constants.SKILLS.arcana.name: "arc",
        constants.SKILLS.athletics.name: "ath",
        constants.SKILLS.deception.name: "dec",
        constants.SKILLS.history.name: "his",
        constants.SKILLS.insight.name: "ins",
        constants.SKILLS.intimidation.name: "itm",
        constants.SKILLS.investigation.name: "inv",
        constants.SKILLS.medicine.name: "med",
        constants.SKILLS.nature.name: "nat",
        constants.SKILLS.perception.name: "prc",
        constants.SKILLS.performance.name: "prf",
        constants.SKILLS.religion.name: "rel",
        constants.SKILLS.sleight_of_hand.name: "slt",
        constants.SKILLS.stealth.name: "ste",
        constants.SKILLS.survival.name: "sur"
    }

    __SKILLATRMAP = {
        "acr":"dex",
        "ani":"wis",
        "arc":"int",
        "ath":"str",
        "dec":"cha",
        "his":"int",
        "ins":"wis",
        "itm":"cha",
        "inv":"int",
        "med":"wis",
        "nat":"int",
        "prc":"wis",
        "prf":"cha",
        "per":"cha",
        "rel":"int",
        "slt":"dex",
        "ste":"dex",
        "sur":"wis"
    }

    __IDCHARS = string.ascii_letters + "0123456789"

    def __generate_id(self):
        return "".join([random.choice(FVTTConverter.__IDCHARS) for i in range(16)])

    def __make_feature(self, title: str, description: str, get_image: bool=True):
        return  {
        "_id": self.__generate_id(),
        "name": title,
        "type": "feat",
        "img": self.cl.query_compendium_image(title),
        "data": {
          "description": {"value": f"<p>{description}</p>", "chat": "","unidentified": ""},
          "source": "",
          "activation": {"type": "","cost": None,"condition": ""},
          "duration": {"value": None,"units": ""},
          "target": {"value": None,"width": None,"units": "","type": ""},
          "range": {"value": None,"long": None,"units": ""},
          "uses": {"value": 0,"max": 0,"per": None},
          "consume": {"type": "","target": None,"amount": None},
          "ability": None,
          "actionType": "",
          "attackBonus": 0,
          "chatFlavor": "",
          "critical": {"threshold": None,"damage": ""},
          "damage": {"parts": [],"versatile": ""},
          "formula": "",
          "save": {"ability": "","dc": None,"scaling": "spell"},
          "requirements": "",
          "recharge": {"value": None,"charged": False},
          "attunement": 0
        },
        "effects": [],
        "folder": None,
        "sort": 200001,
        "permission": {"default": 0},
        "flags": {}
      }

    def __init__(self, config: ConfigParser, logger: Logger):
        self.config = config
        self.logger = logger.getChild("fvtt_conv")
        self.cl = CompendiumLoader(config, logger)

    def __handle_dr(self, values, enums):
        custom = []
        dis = []
        for di in values:
            if di["pre_text"] != "" or di["post_text"] != "":
                    custom.append("".join([di["pre_text"], ",".join(di["type"]), di["post_text"]]))
            else:
                for d in di["type"]:
                    print(d, d in enums)
                    if d in enums:
                        dis.append(d)
                    else:
                        custom.append(d)
        return {"value":dis, "custom":",".join(custom)}

    def convert_creature(self, creature: Creature) -> Any:
        '''Converts a creature from the default format to the FoundryVTT Actor format'''

        new_creature = {}
        cr = creature.data

        #### Header ####
        new_creature["name"] = cr["name"]
        new_creature["type"] = "npc"
        new_creature["img"] = "icons/svg/mystery-man.svg"

        ### Creature Data ###
        data = {}
        data['abilities'] = self.ability_scores(cr, data)
        data['attributes'] = self.attributes(cr, data)
        data['details'] = self.details(cr, data)
        data['traits'] = self.traits(cr, data)
        data["skills"] = self.skills(cr, data)
        new_creature["items"] = []

        if "spellcasting" in cr:
            spell_items, spell_data = self.spells(cr, data)
            print(spell_items)
            new_creature["items"] += spell_items
            data["spells"] = spell_data
        

        new_creature['data'] = data
        return new_creature

    def ability_scores(self, data, current_state):
        conv = {}
        for abs in constants.enum_values(constants.SHORT_ABILITIES):
            if abs in data['abilities']:
                ab_data = data['abilities'][abs]
            else:
                ab_data = 10
            if "saves" in data and abs in data["saves"]:
                ab_save = data["saves"][abs]
            else:
                ab_save = 0
            ab_mod = int((ab_data - 10) / 2)

            conv[abs] = {
                'value': ab_data,
                "proficient": ab_save != 0,
                "bonuses": {"check":"", "save":""},
                "min": 3,
                "mod": ab_mod,
                "save": ab_mod + ab_save,
                "prof": ab_save != 0,
                "saveBonus": 0,
                "checkBonus": 0,
                "dc": 10 + ab_mod + 2 #Why?
            }
        
        return conv


    def attributes(self, data, current_state):
        conv = {}

        ### AC
        ac = {"flat":10, "calc":'natural', 'formula':'', 'min':10}
        if 'ac' in data and len(data['ac']) > 0:
            ac['flat'] = data['ac'][0]['ac'],
        else:
            ac['calc']  = 'default'
        conv["ac"] = ac

        ### HP
        hp = {"value":0, "min":0, "max":0, "temp":0, "tempmax":0, "formula":""}
        if 'hp' in data:
            if 'special' in data['hp']:
                hp["value"] = data['hp']['special']
                hp["max"] = data['hp']['special']
            else:
                hp["value"] = data["hp"]["average"]
                hp["max"] = data["hp"]["average"]
                hp["formula"] = data["hp"]["formula"]
        conv["hp"] = hp

        ### Init
        init = {"value":0, "bonus": 0, "mod": 0, "total": 0, "prof": 0}
        if "abilities" in data and "dex" in data["abilities"]:
            init['value'] = data['abilities']['dex']
            init['bonus'] = data['abilities']['dex']
            init['total'] = data['abilities']['dex']
        conv['init'] = init

        ### Movement
        move = {'burrow':0, 'climb':0, 'fly':0, 'walk':0, 'units':'ft', 'hover':False}
        if 'speed' in data:
            for entry in data['speed']:
                move[entry['type']] = entry['distance']
                move['units'] = entry['measure']
        conv['movement'] = move

        ### Senses
        senses = {"darkvision": 120,"blindsight": 0,"tremorsense": 0,"truesight": 0,"units": "ft","special": ""}
        if "senses" in data:
            for entry in data["senses"]:
                senses[entry["sense"]] = entry["distance"]
                senses["units"] = entry["measure"]
        conv["senses"] = senses
    

        if "proficiency" in data:
            conv["prof"] = data["proficiency"]
        elif "cr" in data:
            conv["prof"] = floor(int(data["cr"]["cr"]) / 4) + 2
        else:
            conv["prof"] = 0

        ### Spellcasting Ability
        conv["spellcasting"] = ""
        if "spellcasting" in data:
            for sc in data["spellcasting"]:
                if "mod" in sc:
                    mod = sc["mod"]
                    conv["spellcasting"] = mod
                    conv["spelldc"] =  8 + current_state["abilities"][mod]["mod"] + conv["prof"]
                    conv["spellLevel"] = sc["spellcastingLevel"] if "spellcastingLevel" in sc else 0
                    break

        return conv

    def details(self, data, current_state):
        conv = {}

        conv["biography"] = {}
        
        if "alignment" in data:
            conv["alignment"] = data["alignment"]

        if "type" in data:
            conv["type"] = {
                "type": data["type"]["type"],
                "swarm": data["type"]["swarm_size"] if data["type"]["swarm"] else ""
            }

        if "cr" in data:
            conv["cr"] = data["cr"]["cr"]

        return conv

    def traits(self, data, current_state):
        conv = {}

        if "size" in data:
            conv["size"] = self.__SIZEMAP[data["size"][0].lower()]

        damage_types = constants.enum_values(constants.DAMAGE_TYPES)
        condition_types = constants.enum_values(constants.CONDITIONS)

        if "damage_immunities" in data:
            conv["di"] = self.__handle_dr(data["damage_immunities"], damage_types)

        if "damage_resistances" in data:
            conv["dr"] = self.__handle_dr(data["damage_resistances"], damage_types)

        if "damage_vulnerabilities" in data:
            conv["dv"] = self.__handle_dr(data["damage_vulnerabilities"], damage_types)

        if "condition_immunities" in data:
            conv["ci"] = self.__handle_dr(data["condition_immunities"], condition_types)
            
        if "languages" in data:
            for l in data["languages"]:
                conv["languages"] = {
                    "value": data["languages"],
                    "custom":""
                }

        return conv

    def skills(self, data, current_state):
        conv = {}
        prof = current_state["attributes"]["prof"]
        if "skills" in data:
            for sk in data["skills"]:
                skill = self.__SKILLSMAP[sk["skill"].lower()]
                atr = self.__SKILLATRMAP[skill]
                total = sk["mod"]
                mod = current_state["abilities"][atr]["mod"]

                if total >= 2*mod + prof:
                    prof_level = 2
                elif total >= mod + prof:
                    prof_level = 1
                else:
                    prof_level = 0

                conv[skill] = {
                    "value": prof_level,
                    "ability": atr,
                    "bonuses": {"check":"", "passive":""},
                    "mod":mod,
                    "bonus":total - (mod * prof_level + prof),
                    "passive": 10 + total,
                    "prof": prof,
                    "total":total
                }

        return conv

    def __format_spellcasting_text(self, data: SpellcastingSchema) -> str:
        levels = []
        for sl in data["levels"]:
            if sl['frequency'] == constants.SPELL_FREQUENCIES.will.name:
                freq = 'At will'
            elif sl['frequency'] == constants.SPELL_FREQUENCIES.daily.name:                
                freq = f"{sl['slots']}/day" if "slots" in sl else "1/day"
            elif sl['frequency'] == constants.SPELL_FREQUENCIES.rest.name:                
                freq = f"{sl['slots']}/long or short rest" if "slots" in sl else "1/long or short rest"
            elif sl['frequency'] == constants.SPELL_FREQUENCIES.levelled.name and not sl["level"] == "cantrip":
                l = sl["level"] + {"1":"st", "2":"nd", "3":"rd", "4":"th", "5":"th", "6":"th", "7":"th", "8":"th", "9":"th"}
                freq = f'{l} level ({sl["slots"] if "slots" in sl else 1} slots)'
            elif sl['frequency'] == constants.SPELL_FREQUENCIES.cantrip.name or sl["level"] == "cantrip":
                freq = 'Cantrip (at will)'
            
            if "each" in sl and sl["each"]:
                freq += " each"

            levels.append(f'{freq}: {",".join(sl["spells"])}')

        text = data["text"] + "</br>" + "</br>".join(levels)
        if "post_text" in data:
            text += f"</br>{data['post_text']}"

        return text

    def spells(self, data, current_state):
        spell_items = []
        spell_data = {
            "spell1": {"value": 0,"override": None, "max": 0},
            "spell2": {"value": 0,"override": None, "max": 0},
            "spell3": {"value": 0,"override": None, "max": 0},
            "spell4": {"value": 0,"override": None, "max": 0},
            "spell5": {"value": 0,"override": None, "max": 0},
            "spell6": {"value": 0,"override": None, "max": 0},
            "spell7": {"value": 0,"override": None, "max": 0},
            "spell8": {"value": 0,"override": None, "max": 0},
            "spell9": {"value": 0,"override": None, "max": 0},
            "spell0": {"value": 0,"override": None, "max": 0},
            "pact":   {"value": 0,"override": None, "max": 0},       
        }

        if "spellcasting" not in data:
            return spell_items, spell_data

        for sc in data["spellcasting"]:
            feat = self.__make_feature(sc["title"], self.__format_spellcasting_text(sc))
            spell_items.append(feat)

            for level in sc["levels"]:
                for s in level["spells"]:
                    resolved_spell = self.cl.query_compendium(CompendiumTypes.Item, s)
                    if resolved_spell is None:
                        self.logger.warning(f"Could not find spell {s} in compendium")
                        continue

                    spell_items.append(resolved_spell)


        return spell_items, spell_data