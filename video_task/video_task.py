from common.log import logger
import requests
import os
from typing import List, Tuple, Optional
import concurrent.futures
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from config import conf


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

评分标准 (1-5分):
1分：需要更多练习，加油！
2分：有进步空间，继续努力！
3分：表现不错，再接再厉！
4分：非常棒，继续保持！
5分：太棒了，你是小小英语达人！

要求:
1. 精确分析：准确识别跟读内容与原文的差异。
2. 积极鼓励：即使在指出错误时，也要用积极的语言表达。
3. 具体指导：提供明确、可操作的改进建议。
4. 全面评估：考虑发音、流畅度、语调等多个方面。

行为准则:
1. 保护隐私：不存储或分享小朋友的个人信息。
2. 公平公正：根据实际表现评分，保持评价的一致性。
3. 积极激励：强调进步和潜力，激发继续学习的动力。
4. 适应性：根据不同小朋友的水平调整评价的深度和复杂度。

评价格式:
1. 总体评分：给出1-5分的评分并简要说明。
2. 发音分析：指出发音优秀的地方和需要改进的音素。
3. 流畅度评价：评价跟读的流畅程度和节奏感。
4. 具体建议：提供2-3个针对性的改进建议。
5. 鼓励总结：以积极的话语结束，鼓励继续学习。

今日跟读内容:
{daily_content}

注意事项:
1. 评价时要考虑到儿童的心理特点，用温和、鼓励的语气。
2. 避免使用过于专业或复杂的语言学术语。
3. 如果跟读内容与原文差异过大，礼貌地请求重新提供更准确的跟读内容。
4. 强调进步和努力的重要性，而不仅仅是结果。

请根据以上指南，对小朋友的跟读情况进行评估和反馈。
评分要考虑到跟读材料的篇幅和难度，尽可能给出具体的建议和鼓励。尽可能给出满分或者高分以鼓励小朋友继续学习的动力。

json格式输出。
仅输出分数score和评价内容response。
示例输出：
{{
    "score": 5,
    "response": ""
}}

"""


# 定义一个函数，用于生成对小朋友跟读情况的评估和反馈
def generate_peppa_reading_evaluation(openai_apikey, daily_content,user_name,user_info, user_readings):
    # 生成评估的prompt
    sys_prompt = generate_peppa_reading_evaluation_prompt(daily_content)
    # 将用户的跟读内容加入到prompt中
    model = "gpt-4o-mini"

    user_prompt = f"""
这是{user_name}小朋友的过往跟读情况:
{str(user_info)}  

你是通过对比小朋友的跟读识别出来的字幕与今日跟读任务做比较来考评跟读的，
只要跟读出来的字幕和今日跟读任务几乎一致，就说明跟读的很好，直接给5分，不要编造需要改进的点。
如果跟读出来的字幕和今日跟读任务有差异，具体指出读错的单词或者少读漏读的句子等，不要编造需要改进的点。少部分错读也给4分，多处错读给3分，大部分错读给2分，完全不认识给1分。
主要从完整度，单词准确度，等多个方面评价，对跟读情况进行评估和反馈,对比过往的跟读表现（比如前几天的跟读成绩或者今天的上一次的跟读成绩做比较）给出一些鼓励和具体的建议。
请逐字逐句的对比小朋友的跟读内容和今日跟读任务的内容，给出评分和评价，适当的指出漏读、错读、发音不标准等。评价尽可能正面，鼓励小朋友继续学习。
json格式输出score和response
以下是小朋友跟读视频的英文字幕：\n"""+user_readings
    messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}]

    # 调用OpenAI API生成评估结果
    response = get_response_from_gpt(openai_apikey, model, messages,)
    res = response['choices'][0]['message']['content']
    # 返回生成的评估结果
    return res


class AudioProcessor:
    def __init__(self, api_base: str, api_key: str):
        self.api_base = api_base
        self.api_key = api_key

    def extract_audio(self, video_path: str) -> str:
        """从视频中提取音频"""
        try:
            audio_path = os.path.splitext(video_path)[0] + ".wav"
            video = VideoFileClip(video_path)
            video.audio.write_audiofile(audio_path)
            logger.info(f"Audio extracted from {video_path} to {audio_path}")
            return audio_path
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise

    def split_audio(self, audio_path: str, segment_length: int = 55000, overlap: int = 5000) -> List[str]:
        """将音频分割成重叠的片段"""
        try:
            audio = AudioSegment.from_wav(audio_path)
            duration = len(audio)
            segments = []

            # 如果音频长度小于segment_length，直接返回整个音频
            if duration <= segment_length:
                segments.append(audio_path)
                logger.info(f"Audio {audio_path} is shorter than segment length, using as a single segment")
                return segments

            for start in range(0, duration, segment_length - overlap):
                end = min(start + segment_length, duration)
                segment = audio[start:end]
                segment_path = f"{audio_path[:-4]}_{start}_{end}.wav"
                segment.export(segment_path, format="wav")
                segments.append(segment_path)
            logger.info(f"Audio {audio_path} split into {len(segments)} segments")
            return segments
        except Exception as e:
            logger.error(f"Error splitting audio: {str(e)}")
            raise

    def transcribe_segment(self, segment_path: str) -> Tuple[str, str]:
        """转录单个音频片段"""
        try:
            with open(segment_path, "rb") as file:
                url = f'{self.api_base}/audio/transcriptions'
                headers = {'Authorization': f'Bearer {self.api_key}'}
                files = {"file": file}
                data = {"model": "whisper-1"}
                response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
                response.raise_for_status()
                text = response.json()['text']
                logger.info(f"Transcribed segment: {segment_path}")
                return segment_path, text
        except Exception as e:
            logger.error(f"Error transcribing segment {segment_path}: {str(e)}")
            return segment_path, ""

    def transcribe_audio(self, segments: List[str]) -> str:
        """并发转录所有音频片段"""
        try:
            if not segments:
                logger.warning("No audio segments to transcribe")
                return ""

            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(executor.map(self.transcribe_segment, segments))

            # 如果只有一个片段，直接返回其转录结果
            if len(results) == 1:
                return results[0][1]

            # 按原始顺序排序结果
            sorted_results = sorted(results, key=lambda x: int(x[0].split('_')[-2]))

            # 合并文本，去除重复
            full_text = ""
            for _, text in sorted_results:
                if text not in full_text[-100:]:  # 检查最后100个字符以避免重复
                    full_text += text + " "

            logger.info("All segments transcribed and merged")
            return full_text.strip()
        except Exception as e:
            logger.error(f"Error in transcribe_audio: {str(e)}")
            raise


def process_video(context, conf):
    """处理视频并返回转录文本"""
    try:
        cmsg = context["msg"]
        cmsg.prepare()
        video_path = context.content
        print(f"视频文件路径：{video_path}")

        logger.info(f"Processing video: {video_path}")

        api_base = conf().get("open_ai_api_base") or "https://api.openai.com/v1"
        api_key = conf().get("open_ai_api_key")

        processor = AudioProcessor(api_base, api_key)

        audio_path = processor.extract_audio(video_path)
        segments = processor.split_audio(audio_path)
        text = processor.transcribe_audio(segments)

        # 清理临时文件，如果存在，就删除
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(video_path):
            os.remove(video_path)
        for segment in segments:
            if os.path.exists(segment):
                os.remove(segment)

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