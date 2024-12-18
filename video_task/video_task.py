from common.log import logger
import requests
import os
import time
from typing import Optional
from config import conf
from moviepy.editor import VideoFileClip
import azure.cognitiveservices.speech as speechsdk


def get_response_from_gpt(openai_apikey, model, messages, temperature=0, max_tokens=4000, response_format=None):
    if response_format is not None:
        response_format = {"type": "json_object"}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_apikey}"
    }

    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}
    }

    if response_format:
        data["response_format"] = response_format

    base_url = "https://api.openai.com/v1/chat/completions"

    try:
        proxy = ""
        proxies = {"http": proxy, "https": proxy} if proxy else None

        response = requests.post(base_url, headers=headers, json=data, proxies=proxies, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"Error in API call: Status {response.status_code}, Content: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    except Exception as e:
        logger.exception(f"Error in API call: {str(e)}")
        raise


def generate_peppa_assistant_prompt():
    return f"""
任务，角色扮演:
你是佩奇小助手，一个专门为"小猪佩奇英语学习打卡群"设计的AI助手。你拥有丰富的儿童英语教育经验，主要负责回答群内的文本问题和解答小朋友及家长关于英语学习的相关问题。

角色定位:
作为一个AI驱动的英语学习助手，你的目标是激发孩子们学习英语的兴趣，提供专业的指导和积极的支持。你应该像一个友善、有耐心的英语老师一样与群成员互动。

核心能力:
1. 英语学习指导：提供适合儿童的英语学习方法和技巧。
2. 问题解答：回答关于英语学习、小猪佩奇动画内容的相关问题。
3. 学习资源推荐：推荐适合不同等级学习者的英语学习资源。
4. 学习动机激励：通过积极的语言鼓励孩子们坚持学习。

等级系统:
参考王者荣耀的等级，学习者分为以下等级：青铜、白银、黄金、白金、钻石、王者。在回答时可以根据询问者的等级给出相应的建议。
达到对应等级的学习者可以获得相应的称号和奖励。

要求:
1. 友好亲和：使用温暖、鼓励的语气，适合与儿童和家长交流。
2. 简明扼要：回答应简洁明了，易于理解。
3. 积极正面：以积极的方式回应，激发学习兴趣。
4. 个性化建议：根据询问者的具体情况给出个性化的建议。

行为准则:
1. 保护隐私：不收集或存储群成员的个人信息。
2. 适度鼓励：给予适度的表扬和鼓励，避免过度吹捧。
3. 专业性：确保所有建议和信息都基于可靠的英语教育理论。
4. 正面引导：遇到消极情绪时，以积极的方式引导。

交互风格:
1. 活泼有趣：使用生动、有趣的语言，可以适当引用小猪佩奇中的元素。
2. 简单直接：使用简单的词汇和句子结构，确保儿童和家长都能理解。
3. 鼓励互动：通过提问或小游戏激发群成员的参与度。


注意事项:
1. 始终以佩奇小助手的身份回应，保持角色一致性。
2. 不评价小朋友的跟读表现，这是佩奇跟读评价小助手的工作。
3. 如果遇到无法回答的问题，礼貌地表示会进一步学习或建议咨询其他专业人士。
4. 避免使用过于复杂的英语术语。
5. 鼓励家长参与孩子的英语学习过程。


请根据以上指南，回答群内成员的问题，提供英语学习建议和支持。

"""


def generate_peppa_reading_evaluation_prompt(daily_content):
    return f"""
任务，角色扮演:
你是佩奇跟读评价小助手，一个专门为"小猪佩奇英语学习打卡群"设计的AI评估助手。你的主要任务是评估小朋友的英语跟读情况，分析跟读内容与原文的差异，并提供专业、鼓励性的评价。

角色定位:
作为一个AI驱动的英语跟读评估助手，你的目标是通过精确的分析和积极的反馈，帮助小朋友提高英语口语能力。你应该像一个专业、友善的语音教练一样进行评估。

核心能力:
1. 文本比对分析：逐字逐句分析跟读内容与原文的差异。
2. 发音评估：识别并评价发音的准确性，包括单个音素和音调。
3. 流畅度分析：评估跟读的流畅程度和节奏感。
4. 个性化反馈：根据分析结果提供针对性的改进建议。

要求:
1. 精确分析：逐字逐句的对比，准确识别小朋友跟读视频中的字幕与跟读任务原文的差异。
2. 积极鼓励：即使在指出错误时，也要用积极的语言表达。
3. 具体指导：提供明确、可操作的改进建议。
4. 全面评估：考虑发音、流畅度、语调等多个方面。
5. 具体建议：如有改进地方，就提供个针对性的改进建议。以表扬和鼓励为主。
6. 鼓励总结：以积极的话语结束，鼓励继续学习。

请根据以上指南，逐步思考（COT），对小朋友的跟读情况进行评估和反馈，鼓励为主。

json格式输出。
仅输出逐步思考COT,分数score和评价内容response。
示例输出：
{{
    "COT": "...下面开始逐字逐句比对小朋友的跟读内容和今日跟读任务的内容...",
    "score": "#给出1-5分的评分",
    "response": "...评价内容..."
}}

"""


# 定义一个函数，用于生成对小朋友跟读情况的评估和反馈
def generate_peppa_reading_evaluation(openai_apikey, daily_content,user_name,user_info, user_readings):
    # 生成评估的prompt
    sys_prompt = generate_peppa_reading_evaluation_prompt(daily_content)
    # 将用户的跟读内容加入到prompt中
    model = "gpt-4o"

    user_prompt = f"""
这是{user_name}小朋友的过往跟读情况:
```
{str(user_info)}  
```

今日跟读内容:
{daily_content}

这是小朋友的跟读视频识别出来的英文内容：
```
{str(user_readings)}
```

通过小朋友的语音跟读识别出来的英文字幕，一句一句的对比，注意对比的时候自动对齐对应的句子再逐句对比，给出评分和评价。

如果跟读出来的字幕和今日跟读任务有差异：
    - 少部分错读也给5分
    - 多处错读给4分
    - 大部分错读给3分，不要给出2分以下评分。
    - 如果跟读内容与原文差异过大，礼貌地请求重新提供更准确的跟读内容。告诉他可以@你询问今日跟读任务的内容，你会提供今日跟读任务的文本和音频。
    - 主要从完整度，单词准确度，等多个方面评价，对跟读情况进行评估和反馈,
    - 对比过往的跟读表现（比如前几天的跟读成绩或者今天的上一次的跟读成绩做比较）给出一些鼓励和具体的建议。
    - 对重复发音放宽松标准, 
    - 对于单词发音错误，导致识别的文字和原句差别较大的提高标准一定要纠错揪出来：
        - 必须完整的给出读错的整个句子的原文和读错的整个句子，并指出读错的单词，以及改进发音意见。
        - 如果有读错请输出以下3项：
        - 跟读原句子：I like apples.
        - 实际跟读：I like banana.
        - 改进意见：读的非常棒，但是应该读apples，不是banana。
如果跟读出来的字幕和今日跟读任务几乎一致，或者仅有少数错误：
    - 就说明跟读的很好，直接给5分，不要编造需要改进的点。
    - 对于少出错误，也要输出以下3项，例如：
        - 跟读原句子：I like apples.
        - 实际跟读：I like banana.
        - 改进意见：读的非常棒，但是应该读apples，不是banana。 
请逐步思考（COT），逐字逐句比对小朋友的跟读内容和今日跟读任务的内容，适当的指出漏读、错读、发音不标准等。评价尽可能正面，鼓励小朋友继续学习。

不好的response样例（原因，没有具体的列出3项，跟读原句子，实际跟读，改进意见）:
"Ethan，你的跟读非常棒！你已经很接近原文了，只是有一些小地方需要注意。比如，'Daddy Pig'的发音要更清晰一些，避免被识别成'Daddy Pick'。还有'Peppa'的发音要注意，不要被识别成'Pipe'。这些都是小问题，相信你很快就能改进。继续加油哦！你已经做得很好了，期待你下次的精彩表现！"

好的response样例：
""
Ethan，你的跟读非常棒！你已经很接近原文了，只是有一些小地方需要注意。
比如：
    - 跟读原句子：But Daddy pig's glasses are not there.
    - 实际跟读：But Daddy picks glasses are not there.
    - 这里的'Daddy Pig'的发音要更清晰一些，避免被识别成'Daddy Pick'。
比如：
    - 跟读原句子：Peppa and George cannot find Daddy Pig's glasses anywhere.
    - 实际跟读：Pipe and George cannot find Daddy Pig's glasses anywhere.
    - 这里的'Peppa'的发音要注意，不要被识别成'Pipe'。
这些都是小问题，相信你很快就能改进。继续加油哦！你已经做得很好了，期待你下次的精彩表现！
""

json格式输出COT,score,response:
格式样例：
{{
    "COT": "逐字逐句比对小朋友的跟读内容和今日跟读任务的内容...",
    "score": "#给出1-5分的评分",
    "response": "...评价内容..."
}}
"""
    messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}]

    # 调用OpenAI API生成评估结果
    response = get_response_from_gpt(openai_apikey, model, messages,)
    res = response['choices'][0]['message']['content']
    # 返回生成的评估结果
    return res


class AudioProcessor:
    def __init__(self):
        self.api_key = conf().get("azure_voice_api_key")
        self.api_region = conf().get("azure_voice_region")
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.api_key,
            region=self.api_region
        )
        self.speech_config.speech_recognition_language = "en-US"

    def transcribe_audio(self, audio_path: str) -> str:
        """转录长音频文件"""
        try:
            audio_input = speechsdk.AudioConfig(filename=audio_path)
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_input
            )

            done = False
            all_results = []

            # 处理中间识别结果
            def recognizing_cb(evt):
                logger.debug(f'RECOGNIZING: {evt.result.text}')

            # 处理最终识别结果
            def recognized_cb(evt):
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    logger.info(f'RECOGNIZED: {evt.result.text}')
                    all_results.append(evt.result.text)
                elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                    logger.warning(f"NOMATCH: {evt.result.no_match_details}")

            # 处理取消和错误情况
            def canceled_cb(evt):
                nonlocal done
                logger.warning(f'CANCELED: {evt}')
                if evt.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {evt.error_details}")
                done = True

            # 处理会话结束
            def session_stopped_cb(evt):
                nonlocal done
                logger.info(f'SESSION STOPPED {evt}')
                done = True

            # 连接所有回调事件
            speech_recognizer.recognizing.connect(recognizing_cb)
            speech_recognizer.recognized.connect(recognized_cb)
            speech_recognizer.session_started.connect(
                lambda evt: logger.info(f'SESSION STARTED: {evt}')
            )
            speech_recognizer.session_stopped.connect(session_stopped_cb)
            speech_recognizer.canceled.connect(canceled_cb)

            # 开始连续识别
            speech_recognizer.start_continuous_recognition()

            # 等待识别完成
            while not done:
                time.sleep(.5)

            # 确保所有识别都完成后再停止
            speech_recognizer.stop_continuous_recognition()

            # 合并所有识别结果
            final_text = " ".join(all_results)
            logger.info(f"Final transcription length: {len(final_text.split())} words")
            return final_text

        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return ""


def process_video(context):
    """处理视频并返回转录文本"""
    try:
        cmsg = context["msg"]
        cmsg.prepare()
        video_path = context.content
        logger.info(f"Processing video: {video_path}")

        processor = AudioProcessor()
        audio_path = os.path.splitext(video_path)[0] + ".wav"

        # 提取音频
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        logger.info(f"Audio extracted from {video_path} to {audio_path}")

        # 转录音频
        text = processor.transcribe_audio(audio_path)
        logger.info(f"Transcription result: {text}")
        # 删除临时文件
        os.remove(audio_path)
        os.remove(video_path)

        logger.info("Video processing completed successfully")
        return text

    except Exception as e:
        logger.error(f"Error in process_video: {str(e)}")
        raise


def get_tts_file_url(user_id: str, voice_provider: str, voice_name: str, text: str) -> Optional[str]:
    """
    获取TTS生成的音频文件URL

    :param user_id: 用户ID
    :param voice_provider: 语音提供商
    :param voice_name: 语音名称
    :param text: 需要转换为语音的文本
    :return: 生成的音频文件URL，如果发生错误则返回None
    """

    payload = {
        "user_id": user_id,
        "voice_provider": voice_provider,
        "voice_name": voice_name,
        "text": text
    }

    try:
        response = requests.post(conf().get("TTS_URL"), json=payload, timeout=30)
        response.raise_for_status()  # 如果状态码不是200，会抛出HTTPError异常

        result = response.json()
        if result.get("status") == "success" and result.get("code") == 200:
            return result.get("file_url")
        else:
            logger.error(f"TTS service returned unexpected result: {result}")
            return None

    except requests.RequestException as e:
        logger.exception(f"Error in get_tts_file_url: {str(e)}")
        return None

def read_text_file(file_path):
    """
    读取文本文件内容
    :param file_path: 文件路径
    :return: 文件内容
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            return content
    except Exception as e:
        logger.error(f"Error reading text file: {str(e)}")
        return None