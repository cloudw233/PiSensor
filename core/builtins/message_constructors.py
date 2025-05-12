from copy import deepcopy
from typing import Union

from extensions.deepseek import get_deepseek_anwser
from extensions.weather import QWeather
from .assigned_element import *
from ..pydantic_models import Indices, WeatherDaily


class MessageChainInstance:
    messages: list = None
    serialized: bool = None

    def deserialize(self):
        if not self.serialized:
            return self.messages
        self.messages = [{"meta": element.Meta.type, "data": element.dump()} for element in self.messages]
        self.serialized = False
        return self.messages

    def serialize(self):
        if self.serialized:
            return self.messages
        msg_chain_lst = []
        for _ in self.messages:
            meta = _.get("meta")
            data = _.get("data")
            match meta:
                case "AccountElement":
                    msg_chain_lst.append(AccountElement(**data))
                case "SensorElement":
                    msg_chain_lst.append(SensorElement(**data))
                case "WeatherElement":
                    msg_chain_lst.append(WeatherElement(**data))
                case "WeatherInfoElement":
                    msg_chain_lst.append(WeatherInfoElement(**data))
                case "UIElement":
                    msg_chain_lst.append(UIElement(**data))
                case "HeartElement":
                    msg_chain_lst.append(HeartElement(**data))
                case "DeepSeekElement":
                    msg_chain_lst.append(DeepSeekElement(**data))
                case "DeepSeekAnswerElement":
                    msg_chain_lst.append(DeepSeekAnswerElement(**data))
                case "ResponseElement":
                    msg_chain_lst.append(ResponseElement(**data))
                case _:
                    assert False, f"Unknown message type: {meta}"
        self.messages = msg_chain_lst
        self.serialized = True
        return self.messages

    @classmethod
    def assign(cls,
               elements: list[Union[
                   AccountElement,
                   SensorElement,
                   WeatherElement,
                   WeatherInfoElement,
                   UIElement,
                   HeartElement,
                   DeepSeekElement,
                   DeepSeekAnswerElement,
                   ResponseElement]]) -> "MessageChain":
        cls.serialized = True
        cls.messages = elements
        return deepcopy(cls())

    @classmethod
    def assign_deserialized(cls, elements: list[dict]) -> "MessageChain":
        cls.serialized = False
        cls.messages = elements
        return deepcopy(cls())


async def process_message(httpx_client, msgchain):
    message_lst = []
    for element in msgchain.messages:
        match element.Meta.type:
            case "WeatherElement":
                # message_lst.append(await QWeather(httpx_client).get_weather_element(element))
                message_lst.append(WeatherInfoElement(
            indices=[Indices(
                date='2222-22-2',
                type='114514',
                name='指数',
                level='12',
                category='xd',
                text='适合玩原神',
            )],
            daily=[WeatherDaily(fxDate="1",
                                sunrise="2",
                                sunset="3",
                                moonrise="4",
                                moonset='5',
                                moonPhase='6',
                                moonPhaseIcon='7',
                                tempMax='8',
                                tempMin='9',
                                iconDay='100',
                                textDay='114514',
                                iconNight='100',
                                textNight='1919810',
                                wind360Day='11',
                                windDirDay='111',
                                windScaleDay='1111',
                                windSpeedDay='11111',
                                wind360Night='111111',
                                windDirNight='11111111',
                                windScaleNight='11111111',
                                windSpeedNight='111111',
                                humidity='1111111',
                                precip='1111111',
                                pressure='1111111',
                                vis='11111',
                                cloud='1111',
                                uvIndex='111',
                                )],
            city="qufu",
            city_id="114514",
            lat="114",
            lon="514"
        ))
            case "DeepSeekElement":
                __answer = await get_deepseek_anwser(element.question)
                message_lst.append(
                    DeepSeekAnswerElement(
                        answer=__answer,
                        question=element.question,
                    ))
            case _:
                message_lst.append(element)
    message_lst.append(ResponseElement(ret_code=0, message="Data received"))
    return MessageChain(message_lst)

MessageChain = MessageChainInstance.assign
MessageChainD = MessageChainInstance.assign_deserialized

"""
WeatherInfoElement(
            indices=[Indices(
                date='2222-22-2',
                type='114514',
                name='指数',
                level='12',
                category='xd',
                text='适合玩原神',
            )],
            daily=[WeatherDaily(fxDate="1",
                                sunrise="2",
                                sunset="3",
                                moonrise="4",
                                moonset='5',
                                moonPhase='6',
                                moonPhaseIcon='7',
                                tempMax='8',
                                tempMin='9',
                                iconDay='100',
                                textDay='114514',
                                iconNight='100',
                                textNight='1919810',
                                wind360Day='11',
                                windDirDay='111',
                                windScaleDay='1111',
                                windSpeedDay='11111',
                                wind360Night='111111',
                                windDirNight='11111111',
                                windScaleNight='11111111',
                                windSpeedNight='111111',
                                humidity='1111111',
                                precip='1111111',
                                pressure='1111111',
                                vis='11111',
                                cloud='1111',
                                uvIndex='111',
                                )],
            city="qufu",
            city_id="114514",
            lat="114",
            lon="514"
        ))"""

__all__ = ["MessageChain", "MessageChainD", "process_message"]